"""Session orchestrator: validate → (prep) → clone → agent → PR.

This is the whole loop, and the place cost is capped for v0 (max turns/tokens) until the
gateway exposes an Anthropic-compatible endpoint the agent can route through.
"""

from __future__ import annotations

from dataclasses import dataclass

from . import github
from .agent import run_agent
from .config import OnboardingRequest, Product
from .sandbox import checkout


@dataclass
class SessionResult:
    summary: str
    trace_id: str | None
    changed_files: list[str]
    diff: str
    pr: github.OpenedPR | None  # None in v0a (no token → no PR, just the diff)


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
    branch = f"respan/onboard-{req.product.value}"
    title = f"Add Respan {req.product.value} instrumentation"
    with checkout(req.repo_url, req.base_branch, token=github_token) as workdir:
        result = run_agent(workdir, req, respan_api_key=respan_api_key)
        if not result.changed_files:
            raise RuntimeError("agent produced no changes")
        diff = _git_diff(workdir)
        pr = None
        if github_token:  # v0b: deliver as a PR; v0a: just the diff
            github.commit_branch(workdir, branch, title)
            pr = github.open_pr(workdir, branch, title, result.summary, github_token)
    return SessionResult(
        summary=result.summary,
        trace_id=result.trace_id,
        changed_files=result.changed_files,
        diff=diff,
        pr=pr,
    )


def _git_diff(workdir) -> str:
    import subprocess

    return subprocess.run(
        ["git", "-C", str(workdir), "diff"], capture_output=True, text=True
    ).stdout
