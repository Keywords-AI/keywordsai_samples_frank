"""Session orchestrator: validate → (prep) → clone → agent → PR.

The request carries an explicit controller model, turn limit, SDK budget, and timeout.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json

from . import github
from .agent import run_agent, _git_changed, PYTHON_SDK_CONDITIONAL_DEPENDENCY
from .config import OnboardingRequest, Product, TracingMode
from .deployment import discover_consumed_requirements, repair_consumed_requirements
from .sandbox import checkout
from .skill import validate_skill_source
from .toolchain import ToolchainError, preflight_toolchain, finalize_lockfiles


@dataclass
class SessionResult:
    summary: str
    trace_id: str | None
    changed_files: list[str]
    diff: str
    pr: github.OpenedPR | None  # None in v0a (no token → no PR, just the diff)
    validation_errors: list[str] = field(default_factory=list)
    setup_receipt: dict = field(default_factory=dict)


def _preflight(req: OnboardingRequest) -> None:
    """Fail fast on prep the onboarding depends on.

    Gateway onboarding is worthless if the account can't route a call, so verify funding
    (credits balance > 0, or BYOK keys present) BEFORE we clone or spend a token on the agent.
    """
    if req.product in (Product.gateway, Product.both):
        # TODO(v0): call the Respan API to confirm credits balance > 0 (or BYOK configured).
        # Raise a clear error the dashboard can surface ("add credits before onboarding").
        pass


def run_session(
    req: OnboardingRequest, *, respan_api_key: str, github_token: str | None = None
) -> SessionResult:
    _preflight(req)
    validate_skill_source()
    branch = f"respan/onboard-{req.product.value}"
    title = f"Add Respan {req.product.value} instrumentation"
    with checkout(req.repo_url, req.base_branch, token=github_token) as workdir:
        # Missing tools are an operator setup failure, before any paid model call.
        toolchain = preflight_toolchain(workdir)
        deployment = discover_consumed_requirements(workdir)
        setup_context = "Lock tools verified by the runner: " + json.dumps(toolchain.to_dict())
        setup_context += "\n" + deployment.to_prompt()
        result = run_agent(
            workdir, req, respan_api_key=respan_api_key,
            **req.controller.model_dump(),
            setup_context=setup_context,
        )
        if not result.changed_files:
            raise RuntimeError("agent produced no changes")
        errors = []
        setup = {"toolchain": toolchain.to_dict(), "deployment": deployment.to_dict()}
        if req.tracing and req.tracing.mode is TracingMode.auto:
            current_deployment = discover_consumed_requirements(workdir)
            delivery = repair_consumed_requirements(
                workdir, current_deployment, result.changed_files, PYTHON_SDK_CONDITIONAL_DEPENDENCY,
            )
            setup["deployment_after_edits"] = current_deployment.to_dict()
            setup["dependency_delivery"] = delivery
            errors.extend(str(issue) for issue in delivery["issues"])
        if not errors:
            try:
                setup["lock_finalization"] = finalize_lockfiles(
                    workdir, toolchain, timeout_seconds=600,
                )
            except ToolchainError as exc:
                errors.append(str(exc))
        # Trusted finalization can add requirements/locks after the model's result.
        changed_files = _git_changed(workdir)
        diff = _git_diff(workdir)
        pr = None
        if github_token and not errors:  # Block PR delivery of incomplete dependency setup.
            github.commit_branch(workdir, branch, title)
            pr = github.open_pr(workdir, branch, title, result.summary, github_token)
    return SessionResult(
        summary=result.summary,
        trace_id=result.trace_id,
        changed_files=changed_files,
        diff=diff,
        pr=pr,
        validation_errors=errors,
        setup_receipt=setup,
    )


def _git_diff(workdir) -> str:
    import os
    import subprocess
    import tempfile

    # Include new files and staged edits without changing the checkout's real index.
    with tempfile.TemporaryDirectory(prefix="respan-diff-") as tmp:
        env = {**os.environ, "GIT_INDEX_FILE": os.path.join(tmp, "index")}
        command = ["git", "-C", str(workdir)]
        for args in (["read-tree", "HEAD"], ["add", "--all", "--", "."]):
            subprocess.run(command + args, env=env, check=True, capture_output=True)
        return subprocess.run(
            command + ["diff", "--cached", "--binary", "--no-ext-diff", "--no-textconv", "HEAD", "--"],
            env=env, check=True, capture_output=True, text=True,
        ).stdout
