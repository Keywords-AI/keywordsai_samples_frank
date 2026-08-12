"""The onboarding agent loop — Claude Agent SDK, dogfooding Respan.

Wiring (the whole point):
  - LLM routed through the Respan **gateway** (cost control + gateway dogfood)
  - Instrumented with **respan-instrumentation-claude-agent-sdk** (every session = a trace)
  - Driven by the **respan skill** (the onboarding playbook already shipped in the SDK)

The agent works inside an already-cloned checkout (see sandbox.py) and edits files in
place; the runner commits + opens the PR afterward.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from .config import OnboardingRequest, Product, TracingMode


@dataclass
class AgentResult:
    summary: str            # human-readable "what I did", for the PR body
    changed_files: list[str]
    ran_verify: bool
    trace_id: str | None    # this onboarding session's own trace (the dogfood aha)


def _build_prompt(req: OnboardingRequest) -> str:
    """Turn the config contract into a precise instruction for the skill.

    The skill (`/respan`) knows HOW to integrate; the config says WHAT the user chose,
    so the agent implements deterministically instead of asking mid-run.
    """
    lines = [
        "Use the /respan skill to onboard this repository. Follow the config exactly; "
        "do not ask the user questions — every choice is already decided below.",
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
        lines.append(f"  Endpoint: {t.endpoint.value}. API key is read from env RESPAN_API_KEY (never commit it).")
    if req.product in (Product.gateway, Product.both) and req.gateway:
        g = req.gateway
        lines.append(
            f"GATEWAY: funding={g.funding.value} (already provisioned), providers={g.providers or 'openai-compatible'}, "
            f"caching={g.enable_caching}, fallbacks={g.enable_fallbacks}. "
            "Repoint the LLM client base_url to the Respan gateway."
        )
    lines += [
        "",
        "When done, run the app's smallest verify path if one exists and confirm a trace/log "
        "would appear. Summarize exactly what you changed for a PR description.",
    ]
    return "\n".join(lines)


def run_agent(workdir: Path, req: OnboardingRequest) -> AgentResult:
    """Run the Claude Agent SDK against the cloned repo in `workdir`.

    Requires (set by the runner / sandbox env):
      - ANTHROPIC_BASE_URL  -> the Respan gateway (once it exposes an Anthropic-compatible
        endpoint). Until then, run direct and cap cost at the orchestrator (see runner).
      - ANTHROPIC_API_KEY / RESPAN_API_KEY as appropriate.
    """
    # Dogfood: instrument this agent's own run with Respan tracing.
    #   from respan import Respan
    #   from respan_instrumentation_claude_agent_sdk import ClaudeAgentSDKInstrumentor
    #   Respan(instrumentations=[ClaudeAgentSDKInstrumentor()],
    #          app_name="respan-integration-agent", environment="onboarding")
    #
    # Cost control: route the model through the gateway.
    #   os.environ["ANTHROPIC_BASE_URL"] = gateway_url  # once Anthropic-compat lands
    #
    # Drive the skill with the config-derived prompt.
    #   import claude_agent_sdk
    #   async for msg in claude_agent_sdk.query(
    #       prompt=_build_prompt(req),
    #       options=ClaudeAgentOptions(cwd=str(workdir), model="claude-sonnet-5",
    #                                  permission_mode="acceptEdits"),
    #   ): ...
    #
    # TODO(v0): implement the loop above, collect changed files (git status), capture the
    # session trace_id (get_client().get_current_trace_id()), and return AgentResult.
    _ = (os.environ, _build_prompt(req))  # referenced so the wiring is explicit
    raise NotImplementedError(
        "v0: wire claude_agent_sdk.query with the /respan skill, gateway base_url, and "
        "ClaudeAgentSDKInstrumentor. See the docstring above for the exact wiring."
    )
