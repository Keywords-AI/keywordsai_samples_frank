"""The onboarding agent loop — Claude Agent SDK, routed through the Respan gateway.

Dogfood, by construction:
  - LLM runs through the Respan **gateway** (only RESPAN_API_KEY needed — the gateway
    handles provider auth and enforces the account budget). Cost control + gateway dogfood.
    See https://respan.ai/docs/integrations/gateway/claude-agent-sdk
  - Instrumented with **respan-instrumentation-claude-agent-sdk** — every session is a trace.
  - Driven by the **/respan skill** (the onboarding playbook already shipped in the SDK).

The agent edits an already-cloned checkout in place; the runner commits + opens the PR.
"""

from __future__ import annotations

import asyncio
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .config import OnboardingRequest, Product, TracingMode

# Respan endpoint (tracing ingest + gateway share this base).
RESPAN_BASE_URL = os.environ.get("RESPAN_BASE_URL", "https://api.respan.ai/api")


@dataclass
class AgentResult:
    summary: str            # "what I did", for the PR body
    changed_files: list[str]
    trace_id: str | None    # this session's own trace (the dogfood aha)


def _build_prompt(req: OnboardingRequest) -> str:
    """Turn the config contract into a precise instruction for the skill.

    The skill (`/respan`) knows HOW to integrate; the config says WHAT the user chose,
    so the agent implements deterministically instead of asking mid-run.
    """
    lines = [
        "Use the /respan skill to onboard this repository. Follow the config exactly; "
        "do not ask questions — every choice is already decided below. Make the edits, "
        "then stop (do not commit or push; the harness handles that).",
        "",
    ]
    if req.product in (Product.tracing, Product.both) and req.tracing:
        t = req.tracing
        lines.append(f"TRACING: mode={t.mode.value}.")
        if t.mode is TracingMode.auto:
            lines.append("  Auto — add Respan() init only. No decorators, no framework instrumentor.")
        else:
            lines.append(
                f"  Full — framework_instrumentor={t.framework_instrumentor or 'none (direct-SDK)'}, "
                f"decorators={t.use_decorators}, workflows={t.workflows or 'agent-chosen'}."
            )
        if t.environment or t.service_name:
            lines.append(f"  Tags: environment={t.environment}, service={t.service_name}.")
        lines.append(f"  Endpoint: {t.endpoint.value}. Key comes from env RESPAN_API_KEY (never commit it).")
    if req.product in (Product.gateway, Product.both) and req.gateway:
        g = req.gateway
        lines.append(
            f"GATEWAY: funding={g.funding.value} (already provisioned), "
            f"providers={g.providers or 'openai-compatible'}, caching={g.enable_caching}, "
            f"fallbacks={g.enable_fallbacks}. Repoint the LLM client base_url to the Respan gateway."
        )
    lines += [
        "",
        "Summarize exactly what you changed, for a PR description.",
    ]
    return "\n".join(lines)


def run_agent(
    workdir: Path,
    req: OnboardingRequest,
    *,
    respan_api_key: str,
    model: str = "sonnet",
    max_turns: int = 40,
) -> AgentResult:
    """Run the Claude Agent SDK against the cloned repo, gateway-routed + traced."""
    # Dogfood: instrument this run with Respan tracing (same key + account as the gateway).
    from respan import Respan
    from respan_instrumentation_claude_agent_sdk import ClaudeAgentSDKInstrumentor

    Respan(
        instrumentations=[ClaudeAgentSDKInstrumentor()],
        api_key=respan_api_key,
        app_name="respan-integration-agent",
        environment="onboarding",
    )
    return asyncio.run(_run(workdir, req, respan_api_key, model, max_turns))


async def _run(
    workdir: Path, req: OnboardingRequest, respan_api_key: str, model: str, max_turns: int
) -> AgentResult:
    import claude_agent_sdk
    from claude_agent_sdk import ClaudeAgentOptions, ResultMessage

    options = ClaudeAgentOptions(
        model=model,
        max_turns=max_turns,            # orchestrator cost cap
        cwd=str(workdir),
        permission_mode="acceptEdits",  # apply edits without prompting
        env={
            # Route the model through the Respan gateway — only the Respan key is needed.
            "ANTHROPIC_API_KEY": respan_api_key,
            "ANTHROPIC_AUTH_TOKEN": respan_api_key,
            "ANTHROPIC_BASE_URL": f"{RESPAN_BASE_URL}/anthropic/",
        },
    )

    summary = ""
    async for message in claude_agent_sdk.query(prompt=_build_prompt(req), options=options):
        if isinstance(message, ResultMessage) and message.result:
            summary = message.result

    trace_id = None
    try:
        from respan import get_client

        trace_id = get_client().get_current_trace_id()
    except Exception:
        pass  # the trace still lands; we just couldn't grab the id inline

    return AgentResult(
        summary=summary or "Applied Respan integration.",
        changed_files=_git_changed(workdir),
        trace_id=trace_id,
    )


def _git_changed(workdir: Path) -> list[str]:
    out = subprocess.run(
        ["git", "status", "--porcelain"], cwd=workdir, capture_output=True, text=True
    ).stdout
    return [line[3:] for line in out.splitlines() if line.strip()]


# NOTE (sandbox/v1): the agent reads the /respan skill from ~/.claude/skills. Locally
# that's already installed (via `respan setup`); the Railway sandbox image must provision
# it (e.g. bundle skill-refs from @respan/cli) before running.
