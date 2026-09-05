"""Ephemeral checkout for a session.

v0: a local temp dir (run on your machine).
v1: the same interface, backed by a Railway container that is torn down after the session.
"""

from __future__ import annotations

import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator
from urllib.parse import urlsplit

from .github import GitHubDeliveryError, authenticated_git, parse_repository, validate_branch


@contextmanager
def checkout(repo_url: str, base_branch: str = "main", token: str | None = None) -> Iterator[Path]:
    """Clone `repo_url`@`base_branch` into a temp dir; clean up on exit."""
    validate_branch(base_branch)
    if token is not None:
        repo_url = parse_repository(repo_url).url
    elif urlsplit(repo_url).username or urlsplit(repo_url).password:
        raise GitHubDeliveryError("Clone URLs must not contain credentials.")
    with tempfile.TemporaryDirectory(prefix="respan-integration-agent-") as tmp:
        workdir = Path(tmp) / "repo"
        authenticated_git(
            Path(tmp), "clone", "--depth", "1", "--branch", base_branch,
            "--", repo_url, str(workdir), token=token,
        )
        yield workdir
