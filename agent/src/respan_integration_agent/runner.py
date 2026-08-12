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
    pr: github.OpenedPR
    summary: str
    trace_id: str | None


def _preflight(req: OnboardingRequest) -> None:
    """Fail fast on prep the onboarding depends on.

    Gateway onboarding is worthless if the account can't route a call, so verify funding
    (credits balance > 0, or BYOK keys present) BEFORE we clone or spend a token on the agent.
    """
    if req.product in (Product.gateway, Product.both):
        # TODO(v0): call the Respan API to confirm credits balance > 0 (or BYOK configured).
        # Raise a clear error the dashboard can surface ("add credits before onboarding").
        pass


def run_session(req: OnboardingRequest, *, github_token: str) -> SessionResult:
    _preflight(req)
    branch = f"respan/onboard-{req.product.value}"
    with checkout(req.repo_url, req.base_branch, token=github_token) as workdir:
        result = run_agent(workdir, req)
        if not github.changed_files(workdir):
            raise RuntimeError("agent produced no changes — nothing to open a PR for")
        title = f"Add Respan {req.product.value} instrumentation"
        github.commit_branch(workdir, branch, title)
        pr = github.open_pr(workdir, branch, title, result.summary, github_token)
    return SessionResult(pr=pr, summary=result.summary, trace_id=result.trace_id)
