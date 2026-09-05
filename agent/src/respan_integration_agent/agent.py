"""The onboarding agent loop — Claude Agent SDK, routed through the Respan gateway.

Dogfood, by construction:
  - LLM runs through the Respan **gateway** (only RESPAN_API_KEY needed — the gateway
    handles provider auth and enforces the account budget). Cost control + gateway dogfood.
    See https://respan.ai/docs/integrations/gateway/claude-agent-sdk
  - Instrumented with **respan-instrumentation-claude-agent-sdk** — every session is a trace.
  - Driven by the **/respan skill** (the onboarding playbook already shipped in the SDK).

The agent edits a cloned checkout; the runner returns its diff and optionally opens a PR.
"""

from __future__ import annotations

import asyncio
import base64
import os
from contextlib import aclosing
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote

from .config import ControllerConfig, OnboardingRequest, Product, TracingMode
from .skill import ProvisionedSkill, provision_respan_skill, validate_skill_source

# Respan endpoint (tracing ingest + gateway share this base).
RESPAN_BASE_URL = os.environ.get("RESPAN_BASE_URL", "https://api.respan.ai/api")

PYTHON_SDK_REQUIRES = ">=3.11,<3.14"
PYTHON_SDK_CONDITIONAL_DEPENDENCY = (
    "respan-ai==4.2.3; python_version >= '3.11' and python_version < '3.14'"
)
PYTHON_SDK_POETRY_DEPENDENCY = (
    'respan-ai = { version = "4.2.3", python = ">=3.11,<3.14" }'
)

PYTHON_AUTO_CONTRACT = f"""Verified Python Auto tracing contract (respan-ai 4.2.3):
- Add respan-ai==4.2.3 as a required runtime dependency in the selected app's
  matching manifest. Do not add a new optional dependency extra unless requested.
- The installed SDK metadata declares Requires-Python: {PYTHON_SDK_REQUIRES}.
  Preserve the target's existing declared Python support; do not narrow it to fit
  this SDK. Prefer a matching app manifest whose runtime already satisfies that
  range. Otherwise use the conditional runtime dependency
  {PYTHON_SDK_CONDITIONAL_DEPENDENCY}
  or the package manager's equivalent Python constraint. Do not add an unconditional
  SDK dependency to a project whose declared Python range includes unsupported versions.
  For Poetry, add this entry to the existing [tool.poetry.dependencies] table:
  {PYTHON_SDK_POETRY_DEPENDENCY}
- The import is from respan import Respan. Supported initializer keys for this task
  are api_key, base_url, app_name, and environment. Do not invent tags, endpoint,
  or service_name constructor arguments. The request's service_name maps to app_name.
- Endpoint platform means leave base_url at the SDK default; it is not an endpoint
  constructor argument. Preserve existing provider client credentials and routing.
- Preserve operation without Respan: guard SDK import and initialization on
  RESPAN_API_KEY and initialize before the first LLM client use. Keep the prefixed
  aliases below so insertion inside a function cannot shadow existing os/sys/Respan
  names used earlier or later in that function. Add app_name/environment from config:
```python
import os as _respan_os

if _respan_os.getenv("RESPAN_API_KEY"):
    import sys as _respan_sys

    if not ((3, 11) <= _respan_sys.version_info[:2] < (3, 14)):
        raise RuntimeError("Respan tracing requires Python >=3.11,<3.14 when RESPAN_API_KEY is set")
    from respan import Respan as _Respan

    _respan = _Respan(api_key=_respan_os.environ["RESPAN_API_KEY"])
```
  Do not import or initialize Respan when the key is missing. Do not add
  except ImportError/pass or swallow other setup failures: a configured but missing
  dependency must fail visibly. Never print or commit the API key.
- Initialize Respan once in shared app startup. If multiple entrypoints need setup,
  reuse one idempotent setup helper; do not add independent initializers to library
  modules or client modules. Preserve existing deployment entrypoint selection.
- This contract is supplied and verified. No package-index or documentation lookup
  is needed to implement Python Auto tracing. Use it instead of guessing APIs.
"""


def _claude_config_directory() -> Path:
    configured = os.environ.get("CLAUDE_CONFIG_DIR")
    directory = Path(configured).expanduser() if configured else Path.home() / ".claude"
    return directory.resolve()


def validate_skill_directory() -> Path:
    """Check the installed prerequisite before cloning or starting a model call."""
    skill_dir = _claude_config_directory() / "skills" / "respan"
    for relative in ("SKILL.md", "references/tracing.md"):
        if not (skill_dir / relative).is_file():
            raise ValueError(f"Missing Respan skill prerequisite: {skill_dir / relative}")
    return skill_dir


@dataclass
class AgentResult:
    summary: str            # "what I did", for the PR body
    changed_files: list[str]
    trace_id: str | None    # this session's own trace (the dogfood aha)


def _build_prompt(req: OnboardingRequest, workdir: Path, *, skill: ProvisionedSkill | None = None,
                  setup_context: str = "") -> str:
    """Turn the config contract into a precise instruction for the skill.

    The skill (`/respan`) knows HOW to integrate; the config says WHAT the user chose,
    so the agent implements deterministically instead of asking mid-run.
    """
    skill_dir = skill.skill_dir if skill else _claude_config_directory() / "skills" / "respan"
    lines = [
        "Use the /respan skill to onboard this repository. Follow the config exactly; "
        "do not ask questions — every choice is already decided below. Make the edits, "
        "then stop (do not commit or push; the harness handles that).",
        f"Target repository root: {workdir.resolve()}. Make all application edits inside this root.",
        f"Skill documentation directory: {skill_dir}. This contains documentation only; "
        "it and CLAUDE_CONFIG_DIR are not the target repository.",
        "Use Read, Glob, Grep, and Edit to inspect and change files. Bash remains "
        "available when permitted, but do not depend on it for reading or editing.",
        "Prefer an existing deployable app, server, or CLI entrypoint over shared "
        "library internals when one exists. Start from the documented actual launch "
        "command and trace its entrypoint, dependency manifest, and consumed lockfile; "
        "do not assume root requirements or a legacy prototype serve the deployed app. "
        "Update the manifest used by that launch path and keep frozen lockfiles coherent. "
        "The trusted runner checks lock tooling before this session and updates/checks "
        "lockfiles after your edits. Do not install tools, invoke package managers, "
        "compile or execute the application, or hand-edit generated lockfiles. "
        "Do not spend model turns on shell version or syntax checks; the runner owns "
        "dependency finalization and reports any blocker. "
        "Do not guess transitive version fixes or migrate the provider SDK to fit the "
        "instrumentation. Report incompatible dependencies or unsupported SDK paths. "
        "Inspect focused relevant sections rather than a large library module.",
        "Use Glob to resolve unknown paths before Read. Read accepts files, not directories. "
        "Do not repeat missing paths or guess nearby filenames; discover the existing path first.",
        "If any tool is denied, do not repeat it or rephrase the same denied action. "
        "Use an allowed Read/Glob/Grep/Edit alternative; if none can complete the task, "
        "stop immediately and report the blocked step. Never loop on permissions or lookups.",
        "",
    ]
    if setup_context:
        lines.extend(["Verified setup and deployment evidence (read-only):", setup_context, ""])
    if req.product in (Product.tracing, Product.both) and req.tracing:
        t = req.tracing
        lines.append(
            f"First Read the tracing reference file at {skill_dir / 'references' / 'tracing.md'}, "
            "then operate on the target repository root specified above."
        )
        lines.append(f"TRACING: mode={t.mode.value}.")
        if t.mode is TracingMode.auto:
            lines.append("  Auto — add Respan() init only. No decorators, no framework instrumentor.")
            lines.append(PYTHON_AUTO_CONTRACT)
        else:
            lines.append(
                f"  Full — framework_instrumentor={t.framework_instrumentor or 'none (direct-SDK)'}, "
                f"decorators={t.use_decorators}, workflows={t.workflows or 'agent-chosen'}."
            )
        if t.environment or t.service_name:
            lines.append(f"  Initialization: environment={t.environment}, app_name={t.service_name}.")
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
    model: str = "claude-sonnet-5",
    max_turns: int | None = None,
    max_budget_usd: float | None = None,
    timeout_seconds: float = 600,
    setup_context: str = "",
) -> AgentResult:
    """Run the Claude Agent SDK against the cloned repo, gateway-routed + traced."""
    limits = ControllerConfig(
        model=model, max_turns=max_turns,
        max_budget_usd=max_budget_usd, timeout_seconds=timeout_seconds,
    )
    validate_skill_source()
    # Dogfood: instrument this run with Respan tracing (same key + account as the gateway).
    from respan import Respan
    from respan_instrumentation_claude_agent_sdk import ClaudeAgentSDKInstrumentor

    Respan(
        instrumentations=[ClaudeAgentSDKInstrumentor()],
        api_key=respan_api_key,
        app_name="respan-integration-agent",
        environment="onboarding",
    )
    with provision_respan_skill() as skill:
        return asyncio.run(_run(workdir, req, respan_api_key, limits, skill=skill,
                                setup_context=setup_context))


async def _run(
    workdir: Path, req: OnboardingRequest, respan_api_key: str, limits: ControllerConfig,
    *, skill: ProvisionedSkill | None = None, setup_context: str = "",
) -> AgentResult:
    import claude_agent_sdk
    from claude_agent_sdk import ClaudeAgentOptions, ResultMessage

    config_dir = skill.config_dir if skill else _claude_config_directory()
    from .github import capture_checkout_identity, verify_checkout_identity
    identity = capture_checkout_identity(workdir) if (workdir / ".git").exists() else None
    options = ClaudeAgentOptions(
        model=limits.model,
        max_turns=limits.max_turns,
        max_budget_usd=limits.max_budget_usd,
        cwd=str(workdir),
        add_dirs=[str(config_dir / "skills" / "respan")],
        tools=["Skill", "Read", "Glob", "Grep", "Edit", "Write", "Bash"],
        permission_mode="acceptEdits",  # apply edits without prompting
        env=_controller_environment(workdir, config_dir, respan_api_key),
    )

    summary = ""
    trace_id = None
    terminal_error = None
    try:
        async with asyncio.timeout(limits.timeout_seconds):
            async with aclosing(claude_agent_sdk.query(
                prompt=_build_prompt(req, workdir, skill=skill, setup_context=setup_context),
                options=options,
            )) as messages:
                async for message in messages:
                    if isinstance(message, ResultMessage):
                        # Capture while the instrumented iterator's span is still active.
                        trace_id = _current_trace_id() or trace_id
                        if message.is_error:
                            terminal_error = _result_error(message, respan_api_key)
                        elif message.result:
                            summary = message.result
    except TimeoutError as exc:
        raise TimeoutError(
            f"Controller exceeded {limits.timeout_seconds:g} second timeout"
        ) from exc
    # Let the instrumented query drain and close before raising a terminal failure.
    if terminal_error:
        raise RuntimeError(terminal_error)

    if identity:
        verify_checkout_identity(workdir, identity)
    return AgentResult(
        summary=summary or "Applied Respan integration.",
        changed_files=_git_changed(workdir),
        trace_id=trace_id,
    )


def _controller_environment(workdir: Path, config_dir: Path, key: str) -> dict[str, str]:
    """Override SDK-inherited credentials; GitHub publishing stays in the runner."""
    allowed = {"PATH", "LANG", "LC_ALL", "TERM", "TMPDIR", "TMP", "TEMP",
               "SYSTEMROOT", "WINDIR", "COMSPEC", "PATHEXT"}
    env = {name: value if name in allowed else "" for name, value in os.environ.items()}
    private_home = config_dir / "home"
    env.update({
        "HOME": str(private_home), "XDG_CONFIG_HOME": str(private_home / ".config"),
        "NETRC": os.devnull, "CLAUDE_CONFIG_DIR": str(config_dir),
        "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_COUNT": "0",
        "GIT_DIR": str(workdir / ".git"), "GIT_WORK_TREE": str(workdir),
        "GIT_INDEX_FILE": str(workdir / ".git" / "index"), "GIT_TERMINAL_PROMPT": "0",
        "ANTHROPIC_API_KEY": key, "ANTHROPIC_AUTH_TOKEN": key,
        "ANTHROPIC_BASE_URL": f"{RESPAN_BASE_URL}/anthropic/",
    })
    return env


def _current_trace_id() -> str | None:
    # Trace capture is best-effort; publishing can still return the exact PR identity.
    try:
        from respan import get_client
        return get_client().get_current_trace_id()
    except Exception:
        return None


def _result_error(message, respan_api_key: str) -> str:
    details = []
    result = getattr(message, "result", None)
    if isinstance(result, str) and result.strip():
        details.append(result.strip())
    errors = getattr(message, "errors", None)
    if isinstance(errors, list):
        details.extend(error.strip() for error in errors if isinstance(error, str) and error.strip())
    reason = "; ".join(dict.fromkeys(details)) or "SDK reported an error result"
    subtype = getattr(message, "subtype", None)
    label = "Controller failed" if subtype in (None, "success") else f"Controller stopped ({subtype})"
    status = getattr(message, "api_error_status", None)
    if isinstance(status, int):
        label += f" [HTTP {status}]"
    rendered = f"{label}: {reason}"
    if respan_api_key:
        for value in {respan_api_key, quote(respan_api_key, safe=""), base64.b64encode(respan_api_key.encode()).decode()}:
            rendered = rendered.replace(value, "[REDACTED]")
    return rendered[:2000]


def _git_changed(workdir: Path) -> list[str]:
    from .github import changed_files
    return changed_files(workdir)


# The public run_agent path provisions the bundled skill into a private configuration.
# add_dirs grants reference access; lock work belongs to the trusted runner, not Bash.
