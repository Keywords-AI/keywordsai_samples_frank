"""Branch → commit → open PR.

v0 uses a user-supplied token; v1 uses the GitHub App installation token (PR-only scope,
no force-push).
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class OpenedPR:
    url: str
    number: int
    branch: str


def _git(workdir: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=workdir, check=True, capture_output=True, text=True
    ).stdout.strip()


def changed_files(workdir: Path) -> list[str]:
    out = _git(workdir, "status", "--porcelain")
    return [line[3:] for line in out.splitlines() if line.strip()]


def commit_branch(workdir: Path, branch: str, message: str) -> None:
    _git(workdir, "checkout", "-b", branch)
    _git(workdir, "add", "-A")
    # Commit as the app; keep the trailer for provenance.
    _git(workdir, "-c", "user.name=respan-integration-agent", "-c", "user.email=agent@respan.ai",
         "commit", "-m", message)


def open_pr(workdir: Path, branch: str, title: str, body: str, token: str) -> OpenedPR:
    """Push the branch and open a PR.

    TODO(v0): push with the token and create the PR via the GitHub REST API
    (POST /repos/{owner}/{repo}/pulls). Prefer `gh` if available, else `requests`.
    Returns the PR url/number so the dashboard can link it.
    """
    _ = (workdir, branch, title, body, token)
    raise NotImplementedError(
        "v0: push branch + POST /repos/{owner}/{repo}/pulls (gh or REST). "
        "Body should be a checklist: 'set RESPAN_API_KEY', 'credits added ✓', 'first trace →'."
    )
