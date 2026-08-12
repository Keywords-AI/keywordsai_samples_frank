"""Ephemeral checkout for a session.

v0: a local temp dir (run on your machine).
v1: the same interface, backed by a Railway container that is torn down after the session.
"""

from __future__ import annotations

import subprocess
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


def _authed_url(repo_url: str, token: str | None) -> str:
    """Embed a token for cloning a private repo (never logged/committed)."""
    if not token or "@" in repo_url or not repo_url.startswith("https://"):
        return repo_url
    return repo_url.replace("https://", f"https://x-access-token:{token}@", 1)


@contextmanager
def checkout(repo_url: str, base_branch: str = "main", token: str | None = None) -> Iterator[Path]:
    """Clone `repo_url`@`base_branch` into a temp dir; clean up on exit."""
    with tempfile.TemporaryDirectory(prefix="respan-integration-agent-") as tmp:
        workdir = Path(tmp) / "repo"
        subprocess.run(
            ["git", "clone", "--depth", "1", "--branch", base_branch,
             _authed_url(repo_url, token), str(workdir)],
            check=True, capture_output=True, text=True,
        )
        yield workdir
