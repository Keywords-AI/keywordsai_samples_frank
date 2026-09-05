#!/usr/bin/env python3
"""Run one live v0b CLI fixture, verify its PR, and clean up owned resources.

Credentials: RESPAN_API_KEY and V0B_GITHUB_TOKEN. Never runs the fixture app.
Only three sanitized evidence files are retained outside the checkout.
"""
from __future__ import annotations

import argparse
import ast
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from datetime import datetime, timedelta, timezone
import hashlib
from importlib.metadata import version
import io
import json
import os
from pathlib import Path
import re
import signal
import sys
import tempfile
from urllib.parse import quote, urlencode
from uuid import uuid4

from respan_integration_agent import github
from respan_integration_agent.runner import _redact_secrets

ROOT = Path(__file__).resolve().parents[1]
GUIDE = ROOT / "INTEGRATION_TRACE_ACCEPTANCE_RULES.md"
FIXTURE = ROOT / "agent/tests/fixtures/v0b"
MODEL = "claude-sonnet-5"
PACKAGES = ("respan-integration-agent", "claude-agent-sdk", "respan-ai", "respan-tracing", "respan-sdk",
            "respan-instrumentation-claude-agent-sdk", "opentelemetry-claude-agent-sdk")


class CheckError(RuntimeError):
    """A fixed, safe harness validation error."""


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha256(content):
    return hashlib.sha256(content).hexdigest()


def save(path, value, secrets=()):
    text = value if isinstance(value, str) else json.dumps(value, indent=2, sort_keys=True) + "\n"
    if _redact_secrets(text, *secrets) != text:
        raise CheckError("Evidence contained a credential; artifact withheld.")
    if len(text.encode()) > 1_000_000:
        raise CheckError("Evidence exceeded the artifact size limit.")
    path.write_text(text)


@contextmanager
def quiet_capture():
    """Keep Python CLI output in memory; discard native and library diagnostics."""
    stdout, stderr = io.StringIO(), io.StringIO()
    descriptors = (os.dup(1), os.dup(2))
    with open(os.devnull, "w") as sink:
        try:
            os.dup2(sink.fileno(), 1)
            os.dup2(sink.fileno(), 2)
            with redirect_stdout(stdout), redirect_stderr(stderr):
                yield stdout
        finally:
            for fd, original in zip((1, 2), descriptors):
                os.dup2(original, fd)
                os.close(original)


def ref_sha(repo, branch, token):
    try:
        value = github._api("GET", f"/repos/{repo.full_name}/git/ref/heads/{quote(branch, safe='/')}", token)
    except github.GitHubDeliveryError as exc:
        if exc.status == 404:
            return None
        raise
    if value.get("ref") != f"refs/heads/{branch}" or value.get("object", {}).get("type") != "commit":
        raise CheckError("Unexpected branch identity.")
    sha = value["object"]["sha"]
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise CheckError("Invalid branch commit identity.")
    return sha


def check_pr(value, repo, resource):
    if value.get("state") not in {"open", "closed"}:
        raise CheckError("Unexpected PR state.")
    github._validate_pr({**value, "state": "open"}, repo, resource["head_branch"],
                        resource["base_branch"], resource["head_sha"])


def cleanup(repo, token, resource):
    result = {"pr_closed": "not_created", "head_deleted": "not_created", "base_deleted": "not_created", "errors": []}
    branch, sha = resource.get("head_branch"), resource.get("head_sha")
    try:
        if branch and sha:
            query = urlencode({"state": "all", "head": f"{repo.owner}:{branch}", "base": resource["base_branch"], "per_page": 100})
            values = github._api("GET", f"/repos/{repo.full_name}/pulls?{query}", token)
            if not isinstance(values, list) or len(values) > 1:
                raise CheckError("Fixture PR is not unique.")
            for value in values:
                check_pr(value, repo, resource)
                resource["pr_number"] = value["number"]
                path = f"/repos/{repo.full_name}/pulls/{value['number']}"
                if value["state"] == "open":
                    github._api("PATCH", path, token, {"state": "closed"})
                value = github._api("GET", path, token)
                check_pr(value, repo, resource)
                if value["state"] != "closed":
                    raise CheckError("Fixture PR closure was not confirmed.")
                result["pr_closed"] = True
    except Exception as exc:
        result["errors"].append("PR cleanup: " + type(exc).__name__)
    for kind in ("head", "base"):
        branch, sha = resource.get(f"{kind}_branch"), resource.get(f"{kind}_sha")
        if not branch or not sha:
            continue
        try:
            actual = ref_sha(repo, branch, token)
            if actual is not None:
                if actual != sha or result["errors"]:
                    raise CheckError("Resource changed or PR cleanup failed; branch retained.")
                github._api("DELETE", f"/repos/{repo.full_name}/git/refs/heads/{quote(branch, safe='/')}", token)
            if ref_sha(repo, branch, token) is not None:
                raise CheckError("Branch deletion was not confirmed.")
            result[f"{kind}_deleted"] = True
        except Exception as exc:
            result["errors"].append(f"{kind} cleanup: " + type(exc).__name__)
    return result


def verify_pr(repo, token, resource, directory, expected_diff):
    head, base = resource["head_sha"], resource["base_sha"]
    value = github._api("GET", f"/repos/{repo.full_name}/pulls/{resource['pr_number']}", token)
    check_pr(value, repo, resource)
    if value["state"] != "open" or value["base"]["sha"] != base:
        raise CheckError("Draft PR does not use the exact fixture base.")
    if ref_sha(repo, resource["base_branch"], token) != base or ref_sha(repo, resource["head_branch"], token) != head:
        raise CheckError("Fixture refs differ from the delivery receipt.")
    workdir = directory / "readback"
    github.authenticated_git(directory, "clone", "--depth", "2", "--branch", resource["head_branch"], repo.url, str(workdir), token=token)
    if github.authenticated_git(workdir, "rev-parse", "HEAD") != head:
        raise CheckError("Fetched PR head differs from GitHub REST.")
    tree = github.authenticated_git(workdir, "rev-parse", "HEAD^{tree}")
    commit = github._api("GET", f"/repos/{repo.full_name}/git/commits/{head}", token)
    if commit["sha"] != head or commit["tree"]["sha"] != tree or resource.get("tree_sha") != tree:
        raise CheckError("CLI, GitHub, and fetched commit trees disagree.")
    patch = github.authenticated_git(workdir, "diff", "--binary", "--no-ext-diff", "--no-textconv", base, head, "--", strip=False)
    if not patch or patch != expected_diff:
        raise CheckError("GitHub patch differs from the finalized CLI patch.")
    index = directory / "replay-index"
    github.authenticated_git(workdir, "read-tree", base, index_file=index)
    github.authenticated_git(workdir, "apply", "--cached", "--binary", "-", input_text=patch, index_file=index)
    if github.authenticated_git(workdir, "write-tree", index_file=index) != tree:
        raise CheckError("Exact patch replay does not reproduce the PR tree.")
    paths = [p for p in github.authenticated_git(workdir, "diff", "--name-only", "-z", base, head).split("\0") if p]
    if not {"app.py", "requirements.txt"}.issubset(paths):
        raise CheckError("Fixture app and dependency manifest were not both integrated.")
    for path in paths:
        if path.endswith(".py"):
            ast.parse(github.authenticated_git(workdir, "show", f"{head}:{path}", strip=False))
    if "respan-ai==4.2.3" not in github.authenticated_git(workdir, "show", f"{head}:requirements.txt"):
        raise CheckError("Expected Respan runtime dependency is absent.")
    return {"draft": True, "base_sha_unchanged": True, "head_sha_verified": True, "tree_sha": tree,
            "exact_patch_replay": True, "changed_files": paths, "patch_sha256": sha256(patch.encode()),
            "python_syntax": "passed", "target_application_execution": "NOT_RUN", "target_trace_acceptance": "NOT_RUN"}, patch


def execute(args):
    repo = github.parse_repository("https://github.com/" + args.repo)
    output = args.output.expanduser().resolve()
    if output.is_relative_to(ROOT) or output.exists():
        raise CheckError("Output must be a new directory outside the checkout.")
    output.mkdir(parents=True, mode=0o700)
    guide = GUIDE.read_bytes()  # Before credentials, network, or fixture preparation.
    run_id = "v0b-smoke-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ-") + uuid4().hex
    resource = {"base_branch": "respan/v0b-fixture-" + uuid4().hex, "base_sha": None,
                "head_branch": None, "head_sha": None, "pr_number": None}
    receipt = {"schema": "v0b-live-cli-v1", "run_id": run_id, "repository": repo.full_name,
               "runner_source_sha256": sha256(Path(__file__).read_bytes()),
               "controller_source_sha256": sha256("\n".join(
                   path.relative_to(ROOT).as_posix() + ":" + sha256(path.read_bytes())
                   for path in sorted((ROOT / "agent/src/respan_integration_agent").rglob("*"))
                   if path.is_file() and "__pycache__" not in path.parts
               ).encode()),
               "guide": {"path": GUIDE.name, "sha256": sha256(guide), "read_at": utc()},
               "fixture": {name: sha256((FIXTURE / name).read_bytes()) for name in ("app.py", "requirements.txt")},
               "packages": {name: version(name) for name in PACKAGES}, "runner": "official cli.main", "mode": "v0b tracing auto",
               "model": MODEL, "expected_resolved_model": MODEL, "route": "https://api.respan.ai/api/anthropic/",
               "max_turns": None, "max_budget_usd": None, "timeout_seconds": 600,
               "marker": {"metadata__run_id": run_id}, "producer_profile": "claude-agent-sdk-controller-v1",
               "service": "respan-integration-agent", "environment": "onboarding",
               "expected_outcome": "One draft PR with exact fixture patch/tree/base verification, followed by owned cleanup",
               "expected_roles": ["one controller workflow", "one aggregate agent LLM span", "dynamic tool spans"],
               "expected_tools": ["Skill", "Read", "Glob", "Grep", "Edit", "Write", "Bash"],
               "usage_authority": "SDK ResultMessage numeric totals; MCP fields checked separately",
               "audit": {"deadline_seconds": 240, "stable_observations_required": 2, "observation_skew_seconds": 45},
               "registered_warnings": [],
               "known_external_gaps": ["Instrumentation 0.2.1 may omit tool-call IDs; this is a gap to audit, not an acceptance waiver"],
               "gates": {"controller": "required", "PR_delivery": "required", "cleanup": "required",
                         "target_application": "NOT_RUN", "MCP_semantic_acceptance": "external read-only audit required"}}
    verification = {"run_id": run_id, "status": "preparing", "resources": resource, "controller_trace_id": None, "cli_exit_code": None}
    save(output / "receipt.json", receipt)
    save(output / "verification.json", verification)
    save(output / "generated.patch", "")
    token, respan, generated_patch, secrets = None, None, "", ()
    fixture_push_attempted = False
    captured_result = {}
    prior_profile = sys.getprofile()

    def profile(frame, event, value):
        if event != "return":
            return
        module, name = frame.f_globals.get("__name__"), frame.f_code.co_name
        if module == "respan_integration_agent.runner" and name == "run_session" and value is not None:
            captured_result["diff"] = value.diff
        elif module == "respan_integration_agent.github" and name == "commit_branch" and isinstance(value, str):
            resource.update(head_branch=frame.f_locals["branch"], head_sha=value)
            # Persist owned identity before the following push, including cancellation recovery.
            save(output / "verification.json", verification, secrets)
        elif module == "respan_integration_agent.agent" and name == "_run":
            message = frame.f_locals.get("message")
            if type(message).__name__ == "ResultMessage":
                captured_result["sdk"] = {key: getattr(message, key, None) for key in ("num_turns", "total_cost_usd", "duration_ms", "duration_api_ms")}

    with tempfile.TemporaryDirectory(prefix="respan-v0b-live-") as temporary:
        directory = Path(temporary)
        try:
            fixture_repo = directory / "fixture"
            fixture_repo.mkdir()
            github.authenticated_git(fixture_repo, "init", "--quiet", "--template=", "--initial-branch", resource["base_branch"])
            for name in receipt["fixture"]:
                (fixture_repo / name).write_bytes((FIXTURE / name).read_bytes())
            github.authenticated_git(fixture_repo, "add", "--all")
            github.authenticated_git(fixture_repo, "-c", "user.name=respan-v0b-fixture", "-c", "user.email=fixture@respan.ai", "commit", "--quiet", "-m", "Temporary v0b verification fixture")
            resource["base_sha"] = github.authenticated_git(fixture_repo, "rev-parse", "HEAD")
            receipt.update(base_branch=resource["base_branch"], base_sha=resource["base_sha"])
            if sha256(GUIDE.read_bytes()) != receipt["guide"]["sha256"]:
                raise CheckError("Trace guide changed during fixture preparation.")
            receipt["guide"]["read_at"] = utc()
            receipt["bound_at"] = utc()
            save(output / "receipt.json", receipt)
            key, token = os.environ.get("RESPAN_API_KEY"), os.environ.get("V0B_GITHUB_TOKEN")
            if not key or not token:
                raise CheckError("Set RESPAN_API_KEY and V0B_GITHUB_TOKEN before a live attempt.")
            secrets = (key, token)
            if os.environ.get("RESPAN_BASE_URL", "https://api.respan.ai/api") != "https://api.respan.ai/api":
                raise CheckError("This fixture requires the declared Anthropic gateway route.")
            info = github._api("GET", f"/repos/{repo.full_name}", token)
            if info.get("full_name", "").lower() != repo.full_name.lower():
                raise CheckError("Target repository identity differs.")
            verification.update(default_branch=info["default_branch"], default_base_sha=ref_sha(repo, info["default_branch"], token), status="creating_fixture")
            save(output / "verification.json", verification, secrets)
            fixture_push_attempted = True
            github.authenticated_git(fixture_repo, "push", "--porcelain", f"--force-with-lease=refs/heads/{resource['base_branch']}:", repo.url, f"{resource['base_sha']}:refs/heads/{resource['base_branch']}", token=token)
            if ref_sha(repo, resource["base_branch"], token) != resource["base_sha"]:
                raise CheckError("Fixture base push was not confirmed.")
            config = {"repo_url": repo.url, "base_branch": resource["base_branch"], "product": "tracing", "tracing": {"mode": "auto"},
                      "controller": {"model": MODEL, "max_turns": None, "max_budget_usd": None, "timeout_seconds": 600}}
            config_path = directory / "config.json"
            config_path.write_text(json.dumps(config))
            verification.update(started_at=utc(), status="running")
            save(output / "verification.json", verification, secrets)
            with quiet_capture() as stdout:
                from respan import Respan, propagate_attributes, workflow
                from respan_instrumentation_claude_agent_sdk import ClaudeAgentSDKInstrumentor
                from respan_integration_agent.cli import main as cli_main
                respan = Respan(api_key=key, instrumentations=[ClaudeAgentSDKInstrumentor()], app_name="respan-integration-agent", environment="onboarding")

                @workflow(name="v0b-cli-smoke")
                def run_cli(run_id, repository, base_sha):
                    code = cli_main(["run", "--config", str(config_path), "--token-env", "V0B_GITHUB_TOKEN"])
                    verification["cli_exit_code"] = code
                    if code:
                        raise CheckError(f"Official CLI returned {code}.")
                    return {"cli_exit_code": code, "run_id": run_id, "repository": repository,
                            "base_sha": base_sha, "head_sha": resource.get("head_sha")}

                sys.setprofile(profile)
                try:
                    with propagate_attributes(metadata={"run_id": run_id, "case": "v0b-cli", "role": "controller", "repository": repo.full_name, "base_sha": resource["base_sha"]}):
                        try:
                            run_cli(run_id, repo.full_name, resource["base_sha"])
                        finally:
                            respan.flush()
                finally:
                    sys.setprofile(prior_profile)
                    text = stdout.getvalue()
                    for line in text.splitlines():
                        if line.startswith("PR delivery: "):
                            value = json.loads(line.removeprefix("PR delivery: "))
                            resource.update(head_branch=value.get("branch"), head_sha=value.get("head_sha"), tree_sha=value.get("tree_sha"), pr_number=value.get("pr_number"))
                    trace = re.search(r"\(session ([0-9a-f]{32})\)", text)
                    if trace:
                        verification["controller_trace_id"] = trace.group(1)
                    pr = re.search(r"^PR:\s+https://github.com/[^\s]+/pull/(\d+)$", text, re.MULTILINE)
                    if pr:
                        resource["pr_number"] = int(pr.group(1))
                    generated_patch = captured_result.get("diff", "")
                    verification["sdk"] = captured_result.get("sdk")
            verification["ended_at"] = utc()
            verification["delivery"], generated_patch = verify_pr(repo, token, resource, directory, generated_patch)
            verification["status"] = "verified"
        except BaseException as exc:
            verification.update(ended_at=utc(), status="failed", error_type=type(exc).__name__)
            verification["error"] = _redact_secrets(str(exc), *secrets) if isinstance(exc, (CheckError, github.GitHubDeliveryError)) else type(exc).__name__
        finally:
            sys.setprofile(prior_profile)
            if respan:
                try:
                    with quiet_capture():
                        respan.flush()
                        respan.shutdown()
                except Exception:
                    verification.update(status="failed", telemetry_shutdown="failed")
            verification["cleanup"] = cleanup(repo, token, resource) if fixture_push_attempted else {"status": "no_remote_resources"}
            if fixture_push_attempted and verification.get("default_branch"):
                try:
                    verification["default_branch_unchanged"] = ref_sha(repo, verification["default_branch"], token) == verification["default_base_sha"]
                except Exception:
                    verification["default_branch_unchanged"] = None
                if verification["cleanup"]["errors"] or verification["default_branch_unchanged"] is not True:
                    verification["status"] = "failed"
            if verification.get("started_at"):
                verification["observation_window"] = {
                    "start_time": (datetime.fromisoformat(verification["started_at"]) - timedelta(seconds=45)).isoformat(),
                    "end_time": (datetime.fromisoformat(verification["ended_at"]) + timedelta(seconds=45)).isoformat()}
            if _redact_secrets(generated_patch, *secrets) != generated_patch:
                generated_patch = "# Patch withheld because it contained a credential.\n"
                verification.update(status="failed", secret_scan="failed")
            else:
                verification["secret_scan"] = "passed"
            save(output / "generated.patch", generated_patch, secrets)
            save(output / "verification.json", verification, secrets)
    verification["local_temporary_directory_removed"] = not directory.exists()
    save(output / "verification.json", verification, secrets)
    print(json.dumps({"run_id": run_id, "status": verification["status"], "controller_trace_id": verification["controller_trace_id"], "artifacts": ["receipt.json", "verification.json", "generated.patch"]}))
    return 0 if verification["status"] == "verified" else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, help="GitHub owner/repository receiving the temporary fixture")
    parser.add_argument("--output", required=True, type=Path, help="new evidence directory outside this checkout")
    args = parser.parse_args()
    def interrupted(signum, frame):
        raise InterruptedError("Live verification interrupted; owned cleanup follows.")
    signal.signal(signal.SIGTERM, interrupted)
    try:
        return execute(args)
    except Exception as exc:
        print(json.dumps({"status": "failed_before_run", "error_type": type(exc).__name__}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
