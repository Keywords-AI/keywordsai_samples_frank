"""Bounded v0b GitHub delivery using an operator token in transient headers."""
from __future__ import annotations

import base64
from dataclasses import dataclass
import hashlib
from http.client import HTTPException
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


class GitHubDeliveryError(RuntimeError):
    """Sanitized failure with the identity needed to recover partial delivery."""

    def __init__(self, message: str, *, status: int | None = None):
        super().__init__(message)
        self.status = status
        self.branch: str | None = None
        self.head_sha: str | None = None
        self.branch_pushed: bool | None = False


@dataclass(frozen=True)
class Repository:
    owner: str
    name: str

    @property
    def full_name(self) -> str:
        return f"{self.owner}/{self.name}"

    @property
    def url(self) -> str:
        return f"https://github.com/{self.full_name}.git"


@dataclass
class OpenedPR:
    url: str
    number: int
    branch: str
    head_sha: str = ""
    base_branch: str = ""
    draft: bool = True


def parse_repository(repo_url: str) -> Repository:
    """Accept only credential-free HTTPS GitHub owner/repository URLs."""
    try:
        if not isinstance(repo_url, str) or any(ord(char) <= 32 or ord(char) == 127 for char in repo_url):
            raise ValueError
        parsed = urlsplit(repo_url)
        parts = parsed.path.rstrip("/").split("/")
        if (parsed.scheme != "https" or parsed.netloc != "github.com"
                or parsed.query or parsed.fragment or len(parts) != 3 or parts[0]):
            raise ValueError
        owner, name = parts[1:]
        if name.endswith(".git"):
            name = name[:-4]
        if (not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]{0,38}", owner)
                or not re.fullmatch(r"[A-Za-z0-9_.-]{1,100}", name)
                or name in {".", ".."}):
            raise ValueError
        return Repository(owner, name)
    except (TypeError, ValueError):
        raise GitHubDeliveryError("Expected an HTTPS github.com owner/repository URL without credentials.") from None


def _git_env(token: str | None) -> dict[str, str]:
    # Never inherit Git tracing/config routing or unrelated service credentials.
    allowed = {"PATH", "TMPDIR", "TMP", "TEMP", "LANG", "LC_ALL", "SYSTEMROOT"}
    env = {key: value for key, value in os.environ.items() if key in allowed}
    env.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1", GIT_TERMINAL_PROMPT="0")
    env.update(HOME=os.devnull, XDG_CONFIG_HOME=os.devnull, NETRC=os.devnull, CURL_HOME=os.devnull)
    config = [
        ("credential.helper", ""), ("core.askPass", ""),
        ("core.hooksPath", os.devnull), ("commit.gpgSign", "false"),
        ("init.templateDir", ""), ("core.fsmonitor", "false"), ("core.attributesFile", os.devnull),
        ("push.followTags", "false"), ("push.gpgSign", "false"),
        ("push.recurseSubmodules", "no"), ("submodule.recurse", "false"),
        ("http.followRedirects", "false"), ("http.extraHeader", ""),
        ("http.https://github.com/.extraHeader", ""),
        ("http.saveCookies", "false"), ("http.cookieFile", ""),
    ]
    if token:
        if not isinstance(token, str) or any(ord(char) <= 32 or ord(char) == 127 for char in token):
            raise GitHubDeliveryError("GitHub token must be nonempty and contain no whitespace.")
        encoded = base64.b64encode(f"x-access-token:{token}".encode()).decode()
        config.append(("http.https://github.com/.extraHeader", f"Authorization: Basic {encoded}"))
    env["GIT_CONFIG_COUNT"] = str(len(config))
    for index, (key, value) in enumerate(config):
        env[f"GIT_CONFIG_KEY_{index}"] = key
        env[f"GIT_CONFIG_VALUE_{index}"] = value
    return env


def authenticated_git(
    workdir: Path | None, *args: str, token: str | None = None, timeout: float = 120,
    input_text: str | None = None, index_file: Path | None = None,
    strip: bool = True,
) -> str:
    """Run bounded Git without credential-bearing arguments or raw diagnostics."""
    if timeout <= 0:
        raise GitHubDeliveryError("Git timeout must be positive.")
    env = _git_env(token)
    if index_file is not None:
        env["GIT_INDEX_FILE"] = str(index_file.resolve())
    try:
        process = subprocess.Popen(
            ["git", *args], cwd=workdir, env=env, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, stdin=subprocess.PIPE if input_text is not None else subprocess.DEVNULL,
            text=True, start_new_session=True,
        )
    except OSError:
        raise GitHubDeliveryError("Could not start Git.") from None
    try:
        stdout, _ = process.communicate(input=input_text, timeout=timeout)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.communicate()
        raise GitHubDeliveryError("Git operation timed out.") from None
    if process.returncode:
        raise GitHubDeliveryError(f"Git operation failed (exit {process.returncode}); check repository access and branch state.")
    return stdout.rstrip("\n") if strip else stdout


def validate_branch(branch: str) -> None:
    if not isinstance(branch, str) or branch.startswith("-"):
        raise GitHubDeliveryError("Invalid branch name.")
    authenticated_git(None, "check-ref-format", "--branch", branch)


def changed_files(workdir: Path) -> list[str]:
    out = authenticated_git(workdir, "status", "--porcelain=v1", "-z", "--untracked-files=all", "--no-renames")
    return [record[3:] for record in out.split("\0") if record]


def _protected_checkout_metadata(workdir: Path) -> dict[str, str | None]:
    """Read the private checkout's routing files without invoking Git."""
    gitdir = workdir / ".git"
    if gitdir.is_symlink() or not gitdir.is_dir():
        raise GitHubDeliveryError("Expected a private Git checkout with unchanged Git metadata.")
    protected = {}
    try:
        for name in ("config", "HEAD", "commondir", "config.worktree"):
            path = gitdir / name
            if path.is_symlink() or (path.exists() and not path.is_file()):
                raise GitHubDeliveryError("Checkout Git metadata must be regular files, not symlinks or directories.")
            if path.exists():
                with path.open("rb") as source:
                    content = source.read(1_048_577)
                if len(content) > 1_048_576:
                    raise GitHubDeliveryError("Checkout Git metadata exceeded the size limit.")
                protected[name] = hashlib.sha256(content).hexdigest()
            else:
                protected[name] = None
    except OSError:
        raise GitHubDeliveryError("Could not verify checkout Git metadata.") from None
    return protected


def capture_checkout_identity(workdir: Path) -> dict:
    """Capture protected Git routing files and the base commit before generation."""
    protected = _protected_checkout_metadata(workdir)
    return {"base_sha": authenticated_git(workdir, "rev-parse", "HEAD"), "protected": protected}


def verify_checkout_identity(workdir: Path, expected: dict) -> None:
    """Reject edited Git metadata before any post-generation Git subprocess."""
    if _protected_checkout_metadata(workdir) != expected["protected"]:
        raise GitHubDeliveryError("Generation changed Git metadata; publishing is blocked.")
    if authenticated_git(workdir, "rev-parse", "HEAD") != expected["base_sha"]:
        raise GitHubDeliveryError("Generation changed the base commit; publishing is blocked.")


def commit_branch(workdir: Path, branch: str, message: str) -> str:
    """Create a new owned branch and commit the complete reviewed checkout."""
    validate_branch(branch)
    if not branch.startswith("respan/"):
        raise GitHubDeliveryError("Delivery requires a new respan/ session branch.")
    authenticated_git(workdir, "checkout", "-b", branch)
    authenticated_git(workdir, "add", "--all", "--", ".")
    authenticated_git(
        workdir, "-c", "user.name=respan-integration-agent", "-c", "user.email=agent@respan.ai",
        "commit", "--no-verify", "-m", message,
    )
    return authenticated_git(workdir, "rev-parse", "HEAD")


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _api(method: str, path: str, token: str, payload: dict | None = None) -> object:
    data = json.dumps(payload).encode() if payload is not None else None
    request = Request(
        "https://api.github.com" + path, data=data, method=method,
        headers={"Accept": "application/vnd.github+json", "Authorization": f"Bearer {token}",
                 "X-GitHub-Api-Version": "2026-03-10", "Content-Type": "application/json",
                 "User-Agent": "respan-integration-agent"},
    )
    try:
        with build_opener(_NoRedirect()).open(request, timeout=30) as response:
            raw = response.read(2_000_001)
            if len(raw) > 2_000_000:
                raise GitHubDeliveryError("GitHub API response exceeded the size limit.")
            if response.status == 204 and not raw:
                return None
            return json.loads(raw)
    except HTTPError as exc:
        raise GitHubDeliveryError(f"GitHub API request failed (HTTP {exc.code}).", status=exc.code) from None
    except (URLError, OSError, TimeoutError, ValueError, HTTPException):
        raise GitHubDeliveryError("GitHub API response could not be confirmed.") from None


def _validate_pr(value: object, repo: Repository, branch: str, base: str, sha: str) -> OpenedPR:
    try:
        number = value["number"]
        if (type(number) is not int or number <= 0
                or value["state"] != "open" or value["draft"] is not True
                or value["base"]["ref"] != base or value["head"]["ref"] != branch
                or value["head"]["sha"] != sha
                or value["base"]["repo"]["full_name"].lower() != repo.full_name.lower()
                or value["head"]["repo"]["full_name"].lower() != repo.full_name.lower()
                or value["html_url"].lower() != f"https://github.com/{repo.full_name}/pull/{number}".lower()):
            raise ValueError
        return OpenedPR(value["html_url"], number, branch, sha, base)
    except (KeyError, TypeError, AttributeError, ValueError):
        raise GitHubDeliveryError("GitHub pull request identity, draft status, or head commit did not match this delivery.") from None


def _existing_pr(repo: Repository, branch: str, base: str, sha: str, token: str) -> OpenedPR | None:
    query = urlencode({"head": f"{repo.owner}:{branch}", "base": base, "state": "all", "per_page": 100})
    values = _api("GET", f"/repos/{repo.full_name}/pulls?{query}", token)
    if not isinstance(values, list) or len(values) >= 100:
        raise GitHubDeliveryError("Could not establish a unique existing pull request for this delivery.")
    if not values:
        return None
    if len(values) != 1:
        raise GitHubDeliveryError("Multiple pull requests already use this delivery branch.")
    return _validate_pr(values[0], repo, branch, base, sha)


def _remote_head(workdir: Path, repo: Repository, branch: str, token: str) -> str | None:
    output = authenticated_git(workdir, "ls-remote", "--refs", repo.url, f"refs/heads/{branch}", token=token)
    if not output:
        return None
    lines = output.splitlines()
    fields = lines[0].split() if len(lines) == 1 else []
    if len(fields) != 2 or fields[1] != f"refs/heads/{branch}" or not re.fullmatch(r"[0-9a-f]{40}", fields[0]):
        raise GitHubDeliveryError("Could not verify the remote delivery branch.")
    return fields[0]


def open_pr(
    workdir: Path, branch: str, title: str, body: str, token: str, *,
    repo_url: str, base_branch: str, head_sha: str | None = None,
) -> OpenedPR:
    """Push and verify one branch, then create/reconcile one draft PR.

    Retrying with the same branch/SHA reconciles an existing PR. An ambiguous
    POST is followed only by bounded reads, never by another POST.
    """
    repo = parse_repository(repo_url)
    validate_branch(base_branch)
    validate_branch(branch)
    if branch == base_branch or not branch.startswith("respan/"):
        raise GitHubDeliveryError("Refusing to push the base branch or a non-session branch.")
    if not token:
        raise GitHubDeliveryError("A GitHub token is required for PR delivery.")
    _git_env(token)
    sha = head_sha
    pushed: bool | None = False
    try:
        origin = parse_repository(authenticated_git(workdir, "remote", "get-url", "origin"))
        if origin.full_name.lower() != repo.full_name.lower():
            raise GitHubDeliveryError("Checkout origin does not match the requested repository.")
        if authenticated_git(workdir, "branch", "--show-current") != branch:
            raise GitHubDeliveryError("Checkout is not on the owned delivery branch.")
        local_sha = authenticated_git(workdir, "rev-parse", "HEAD")
        sha = sha or local_sha
        if local_sha != sha or not re.fullmatch(r"[0-9a-f]{40}", sha):
            raise GitHubDeliveryError("Checkout head changed before PR delivery.")
        if changed_files(workdir):
            raise GitHubDeliveryError("Checkout has uncommitted changes after the delivery commit.")
        remote_sha = _remote_head(workdir, repo, branch, token)
        if remote_sha is not None and remote_sha != sha:
            raise GitHubDeliveryError("Delivery branch already exists with a different commit; nothing was pushed.")
        if remote_sha is None:
            push_error = None
            pushed = None  # Unknown until readback; a lost response may conceal success.
            try:
                # The empty expected ref is a create-only compare-and-swap:
                # even a branch created after ls-remote cannot be overwritten.
                # It never permits an update to an existing branch.
                authenticated_git(
                    workdir, "push", "--porcelain", f"--force-with-lease=refs/heads/{branch}:",
                    repo.url, f"{sha}:refs/heads/{branch}", token=token,
                )
            except GitHubDeliveryError as exc:
                push_error = exc
            if _remote_head(workdir, repo, branch, token) != sha:
                pushed = False
                raise push_error or GitHubDeliveryError("Remote branch head did not match after push.")
        pushed = True
        existing = _existing_pr(repo, branch, base_branch, sha, token)
        if existing:
            return existing
        try:
            value = _api("POST", f"/repos/{repo.full_name}/pulls", token, {
                "title": title, "body": body, "head": branch, "base": base_branch,
                "draft": True, "maintainer_can_modify": False,
            })
            return _validate_pr(value, repo, branch, base_branch, sha)
        except GitHubDeliveryError as exc:
            if exc.status in {401, 403, 404}:
                raise
            for attempt in range(3):
                if attempt:
                    time.sleep(0.25 * attempt)
                try:
                    existing = _existing_pr(repo, branch, base_branch, sha, token)
                except GitHubDeliveryError:
                    continue
                if existing:
                    return existing
            raise GitHubDeliveryError("Branch was pushed, but PR creation could not be confirmed; retry with this same branch and commit.") from None
    except GitHubDeliveryError as exc:
        exc.branch, exc.head_sha, exc.branch_pushed = branch, sha, pushed
        raise
