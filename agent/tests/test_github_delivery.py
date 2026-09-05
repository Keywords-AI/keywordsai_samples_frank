"""GitHub delivery regressions: local Git plus HTTP doubles, no remote writes."""
from __future__ import annotations

import base64
from contextlib import contextmanager
import copy
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from respan_integration_agent import github


TOKEN = "fixture-github-token-do-not-send"
REPO = "https://github.com/fixture-owner/fixture-repo.git"
BRANCH = "respan/onboard-tracing-0123456789abcdef0123456789abcdef"
BASE = "release/next"


class GitHubDeliveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.repo = self.root / "checkout"
        self.repo.mkdir()
        self.bare = self.root / "remote.git"
        self.git = github.authenticated_git
        self.git(self.repo, "init", "--quiet", "--template=", f"--initial-branch={BASE}")
        (self.repo / "app.py").write_text("print('before')\n")
        self.git(self.repo, "add", "--all")
        self.git(self.repo, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                 "commit", "--quiet", "-m", "baseline")
        self.base_sha = self.git(self.repo, "rev-parse", "HEAD")
        self.git(self.root, "clone", "--quiet", "--bare", str(self.repo), str(self.bare))
        self.git(self.repo, "remote", "add", "origin", REPO)
        self.calls = []
        self.api_calls = []
        self.pr_values = []
        self.push_lost_response = False
        self.push_race = False
        self.failed_push_readback = False
        self.post_lost_response = False
        self.post_failure = None

    def prepare(self):
        (self.repo / "app.py").write_text("print('traced')\n")
        (self.repo / "new helper.py").write_text("new tracing helper\n")
        self.sha = github.commit_branch(self.repo, BRANCH, "Add tracing")
        return self.sha

    def pr_json(self):
        return {
            "number": 7, "html_url": "https://github.com/fixture-owner/fixture-repo/pull/7",
            "state": "open", "draft": True,
            "base": {"ref": BASE, "repo": {"full_name": "fixture-owner/fixture-repo"}},
            "head": {"ref": BRANCH, "sha": self.sha, "repo": {"full_name": "fixture-owner/fixture-repo"}},
        }

    def transport(self, workdir, *args, **kwargs):
        self.calls.append((args, kwargs.copy()))
        if args and args[0] in {"ls-remote", "push"}:
            self.assertIn(REPO, args)
            self.assertEqual(kwargs.get("token"), TOKEN)
            self.assertNotIn(TOKEN, " ".join(args))
            if args[0] == "ls-remote" and self.failed_push_readback and any(call[0][0] == "push" for call in self.calls):
                raise github.GitHubDeliveryError("Git operation timed out.")
            mapped = tuple(str(self.bare) if arg == REPO else arg for arg in args)
            if args[0] == "push" and self.push_race:
                self.git(self.bare, "update-ref", f"refs/heads/{BRANCH}", self.base_sha)
            output = self.git(workdir, *mapped)
            if args[0] == "push" and self.push_lost_response:
                raise github.GitHubDeliveryError("Git operation timed out.")
            return output
        return self.git(workdir, *args, **kwargs)

    def api(self, method, path, token, payload=None):
        self.assertEqual(token, TOKEN)
        self.api_calls.append((method, path, copy.deepcopy(payload)))
        if method == "GET":
            self.assertIn("head=fixture-owner%3Arespan%2Fonboard-", path)
            self.assertIn("base=release%2Fnext", path)
            self.assertIn("state=all", path)
            return copy.deepcopy(self.pr_values)
        self.assertEqual(method, "POST")
        if self.post_failure:
            raise self.post_failure
        self.pr_values = [self.pr_json()]
        if self.post_lost_response:
            raise github.GitHubDeliveryError("GitHub API response could not be confirmed.")
        return self.pr_json()

    @contextmanager
    def delivery_transport(self):
        with patch.object(github, "authenticated_git", side_effect=self.transport), \
                patch.object(github, "_api", side_effect=self.api), \
                patch.object(github.time, "sleep"):
            yield

    def deliver(self, **overrides):
        options = dict(repo_url=REPO, base_branch=BASE, head_sha=self.sha)
        options.update(overrides)
        return github.open_pr(self.repo, BRANCH, "Add tracing", "Review the generated patch.", TOKEN, **options)

    def test_non_main_base_complete_push_and_draft_pr(self):
        self.prepare()
        with self.delivery_transport():
            result = self.deliver()
        self.assertEqual(result.head_sha, self.sha)
        self.assertEqual(result.base_branch, BASE)
        self.assertTrue(result.draft)
        self.assertEqual(self.git(self.bare, "rev-parse", f"refs/heads/{BRANCH}"), self.sha)
        self.assertEqual(self.git(self.bare, "rev-parse", f"refs/heads/{BASE}"), self.base_sha)
        self.assertEqual(self.git(self.repo, "show", "-s", "--format=%an <%ae>"), "respan-integration-agent <agent@respan.ai>")
        self.assertIn("new helper.py", self.git(self.bare, "ls-tree", "--name-only", BRANCH))
        push = [args for args, _ in self.calls if args[0] == "push"]
        self.assertEqual(push, [("push", "--porcelain", f"--force-with-lease=refs/heads/{BRANCH}:", REPO,
                                f"{self.sha}:refs/heads/{BRANCH}")])
        posted = [payload for method, _, payload in self.api_calls if method == "POST"]
        self.assertEqual(len(posted), 1)
        self.assertEqual(posted[0]["head"], BRANCH)
        self.assertEqual(posted[0]["base"], BASE)
        self.assertTrue(posted[0]["draft"])

    def test_collision_does_not_update_existing_branch(self):
        self.prepare()
        self.git(self.bare, "update-ref", f"refs/heads/{BRANCH}", self.base_sha)
        with self.delivery_transport(), self.assertRaisesRegex(github.GitHubDeliveryError, "different commit") as raised:
            self.deliver()
        self.assertEqual(self.git(self.bare, "rev-parse", BRANCH), self.base_sha)
        self.assertFalse(raised.exception.branch_pushed)
        self.assertFalse(self.api_calls)
        self.assertFalse(any(args[0] == "push" for args, _ in self.calls))

    def test_retry_reconciles_exact_existing_pr_without_writes(self):
        self.prepare()
        with self.delivery_transport():
            first = self.deliver()
            self.calls.clear()
            self.api_calls.clear()
            second = self.deliver()
        self.assertEqual(first, second)
        self.assertFalse(any(args[0] == "push" for args, _ in self.calls))
        self.assertEqual([method for method, _, _ in self.api_calls], ["GET"])

    def test_create_only_lease_rejects_branch_created_after_probe(self):
        self.prepare()
        self.push_race = True
        with self.delivery_transport(), self.assertRaises(github.GitHubDeliveryError):
            self.deliver()
        self.assertEqual(self.git(self.bare, "rev-parse", BRANCH), self.base_sha)
        self.assertFalse(self.api_calls)

    def test_ambiguous_post_is_reconciled_without_second_post(self):
        self.prepare()
        self.post_lost_response = True
        with self.delivery_transport():
            result = self.deliver()
        self.assertEqual(result.number, 7)
        self.assertEqual([method for method, _, _ in self.api_calls], ["GET", "POST", "GET"])

    def test_ambiguous_push_is_verified_before_pr_creation(self):
        self.prepare()
        self.push_lost_response = True
        with self.delivery_transport():
            result = self.deliver()
        self.assertEqual(result.head_sha, self.sha)
        self.assertEqual(sum(args[0] == "push" for args, _ in self.calls), 1)

    def test_failed_creation_preserves_branch_and_sha_for_recovery(self):
        self.prepare()
        self.post_failure = github.GitHubDeliveryError("GitHub API request failed (HTTP 403).", status=403)
        with self.delivery_transport(), self.assertRaises(github.GitHubDeliveryError) as raised:
            self.deliver()
        self.assertEqual(raised.exception.branch, BRANCH)
        self.assertEqual(raised.exception.head_sha, self.sha)
        self.assertTrue(raised.exception.branch_pushed)
        self.assertNotIn(TOKEN, str(raised.exception))
        self.assertEqual(self.git(self.bare, "rev-parse", BRANCH), self.sha)
        self.assertEqual([method for method, _, _ in self.api_calls], ["GET", "POST"])

    def test_failed_push_readback_reports_unknown_publication_state(self):
        self.prepare()
        self.failed_push_readback = True
        with self.delivery_transport(), self.assertRaises(github.GitHubDeliveryError) as raised:
            self.deliver()
        self.assertIsNone(raised.exception.branch_pushed)
        self.assertEqual(raised.exception.branch, BRANCH)
        self.assertEqual(raised.exception.head_sha, self.sha)
        self.assertEqual(self.git(self.bare, "rev-parse", BRANCH), self.sha)
        self.assertFalse(self.api_calls)

    def test_unconfirmed_post_stops_after_bounded_reads(self):
        self.prepare()
        self.post_failure = github.GitHubDeliveryError("GitHub API response could not be confirmed.")
        with self.delivery_transport(), self.assertRaisesRegex(github.GitHubDeliveryError, "same branch and commit") as raised:
            self.deliver()
        self.assertTrue(raised.exception.branch_pushed)
        self.assertEqual([method for method, _, _ in self.api_calls], ["GET", "POST", "GET", "GET", "GET"])

    def test_closed_or_changed_existing_pr_is_not_recreated(self):
        self.prepare()
        with self.delivery_transport():
            self.deliver()
            self.pr_values[0]["state"] = "closed"
            self.api_calls.clear()
            with self.assertRaisesRegex(github.GitHubDeliveryError, "identity"):
                self.deliver()
        self.assertEqual([method for method, _, _ in self.api_calls], ["GET"])

    def test_tampered_origin_or_head_refuses_network_write(self):
        self.prepare()
        self.git(self.repo, "remote", "set-url", "origin", "https://github.com/other/repo.git")
        with self.delivery_transport(), self.assertRaisesRegex(github.GitHubDeliveryError, "origin"):
            self.deliver()
        self.assertFalse(self.api_calls)
        self.assertFalse(any(args[0] in {"push", "ls-remote"} for args, _ in self.calls))
        self.git(self.repo, "remote", "set-url", "origin", REPO)
        with self.delivery_transport(), self.assertRaisesRegex(github.GitHubDeliveryError, "head changed"):
            self.deliver(head_sha="0" * 40)

    def test_dirty_checkout_and_base_branch_are_refused(self):
        self.prepare()
        (self.repo / "forgotten.txt").write_text("not committed\n")
        with self.delivery_transport(), self.assertRaisesRegex(github.GitHubDeliveryError, "uncommitted"):
            self.deliver()
        with self.assertRaisesRegex(github.GitHubDeliveryError, "base branch"):
            github.open_pr(self.repo, BASE, "title", "body", TOKEN, repo_url=REPO, base_branch=BASE)
        self.assertFalse(self.api_calls)

    def test_commit_disables_local_hooks_and_preserves_path_names(self):
        marker = self.root / "hook-ran"
        hook = self.repo / ".git/hooks/post-commit"
        hook.parent.mkdir(exist_ok=True)
        hook.write_text(f"#!/bin/sh\ntouch '{marker}'\n")
        hook.chmod(0o755)
        self.git(self.repo, "config", "core.hooksPath", str(hook.parent))
        self.git(self.repo, "config", "commit.gpgSign", "true")
        (self.repo / "line\nbreak.py").write_text("fixture\n")
        self.assertEqual(github.changed_files(self.repo), ["line\nbreak.py"])
        self.prepare()
        self.assertFalse(marker.exists())
        self.assertFalse(github.changed_files(self.repo))
        self.assertEqual(self.git(self.bare, "rev-parse", BASE), self.base_sha)

    def test_edited_config_is_rejected_before_any_git_process(self):
        expected = github.capture_checkout_identity(self.repo)
        config = self.repo / ".git/config"
        config.write_text(config.read_text() + "\n[core]\n\tfsmonitor = hostile-command\n")
        with patch.object(github, "authenticated_git") as git, \
                self.assertRaisesRegex(github.GitHubDeliveryError, "changed Git metadata"):
            github.verify_checkout_identity(self.repo, expected)
        git.assert_not_called()

    def test_git_redirect_and_protected_directories_are_rejected_before_git(self):
        expected = github.capture_checkout_identity(self.repo)
        gitdir = self.repo / ".git"
        saved = self.repo / "saved-metadata"
        gitdir.rename(saved)
        for kind in ("redirect file", "symlink"):
            with self.subTest(kind=kind):
                if kind == "redirect file":
                    gitdir.write_text(f"gitdir: {saved}\n")
                else:
                    gitdir.symlink_to(saved, target_is_directory=True)
                with patch.object(github, "authenticated_git") as git, self.assertRaises(github.GitHubDeliveryError):
                    github.verify_checkout_identity(self.repo, expected)
                git.assert_not_called()
                gitdir.unlink()
        saved.rename(gitdir)
        (gitdir / "config.worktree").mkdir()
        with patch.object(github, "authenticated_git") as git, self.assertRaisesRegex(github.GitHubDeliveryError, "regular files"):
            github.capture_checkout_identity(self.repo)
        git.assert_not_called()

    def test_invalid_urls_never_become_authenticated_destinations(self):
        self.assertEqual(github.parse_repository(REPO).full_name, "fixture-owner/fixture-repo")
        for value in ["http://github.com/a/b", "https://token@github.com/a/b", "https://github.com.evil/a/b",
                      "https://github.com/a/b?token=secret", "https://github.com/a/b#fragment", "git@github.com:a/b",
                      "https://github.com:443/a/b", "https://github.com/a/b/tree/main", "https://github.com/a/%2e%2e",
                      "https://github.com/a/..", " https://github.com/a/b", "https://github.com/a/\nb"]:
            with self.subTest(value=value), self.assertRaises(github.GitHubDeliveryError) as raised:
                github.parse_repository(value)
            self.assertNotIn(value, str(raised.exception))

    def test_response_repository_base_head_sha_and_draft_are_validated(self):
        self.prepare()
        good = self.pr_json()
        variants = []
        for group, key, value in [("base", "ref", "main"), ("head", "ref", "other"), ("head", "sha", "0" * 40)]:
            wrong = copy.deepcopy(good)
            wrong[group][key] = value
            variants.append(wrong)
        for group in ("base", "head"):
            wrong = copy.deepcopy(good)
            wrong[group]["repo"]["full_name"] = "other/repo"
            variants.append(wrong)
        for key, value in [("draft", False), ("number", True), ("html_url", "https://evil.example/pull/7")]:
            wrong = copy.deepcopy(good)
            wrong[key] = value
            variants.append(wrong)
        for value in variants:
            with self.subTest(value=value), self.assertRaises(github.GitHubDeliveryError):
                github._validate_pr(value, github.parse_repository(REPO), BRANCH, BASE, self.sha)


class GitHubTransportTests(unittest.TestCase):
    def test_token_only_in_transient_header_and_ambient_secrets_are_removed(self):
        with patch.dict(os.environ, {"GITHUB_TOKEN": TOKEN, "RESPAN_API_KEY": "fixture-respan-secret",
                                   "GIT_TRACE_CURL": "1", "GIT_CONFIG_COUNT": "1", "GIT_CONFIG_VALUE_0": TOKEN}):
            env = github._git_env(TOKEN)
        self.assertNotIn("GITHUB_TOKEN", env)
        self.assertNotIn("RESPAN_API_KEY", env)
        self.assertNotIn("GIT_TRACE_CURL", env)
        for key in ("HOME", "XDG_CONFIG_HOME", "NETRC", "CURL_HOME"):
            self.assertEqual(env[key], os.devnull)
        configs = [(env[f"GIT_CONFIG_KEY_{i}"], env[f"GIT_CONFIG_VALUE_{i}"]) for i in range(int(env["GIT_CONFIG_COUNT"]))]
        self.assertIn(("http.followRedirects", "false"), configs)
        self.assertIn(("core.hooksPath", os.devnull), configs)
        self.assertIn(("push.followTags", "false"), configs)
        encoded = base64.b64encode(f"x-access-token:{TOKEN}".encode()).decode()
        self.assertEqual(configs[-1], ("http.https://github.com/.extraHeader", f"Authorization: Basic {encoded}"))
        self.assertNotIn(TOKEN, str(env))

    def test_git_error_does_not_expose_stderr_or_token_arguments(self):
        with patch.object(github.subprocess, "Popen") as popen:
            process = popen.return_value
            process.communicate.return_value = ("", f"server reflected {TOKEN}")
            process.returncode = 1
            with self.assertRaises(github.GitHubDeliveryError) as raised:
                github.authenticated_git(None, "ls-remote", REPO, token=TOKEN)
        self.assertNotIn(TOKEN, str(raised.exception))
        self.assertNotIn(TOKEN, str(popen.call_args.args))
        self.assertEqual(popen.call_args.kwargs["stdin"], subprocess.DEVNULL)
        self.assertEqual(process.communicate.call_args.kwargs["timeout"], 120)

    def test_git_timeout_kills_and_reaps_process_group(self):
        with patch.object(github.subprocess, "Popen") as popen, patch.object(github.os, "killpg") as kill:
            process = popen.return_value
            process.pid = 12345
            process.communicate.side_effect = [subprocess.TimeoutExpired("git", 0.1, stderr=TOKEN), ("", "")]
            with self.assertRaisesRegex(github.GitHubDeliveryError, "timed out") as raised:
                github.authenticated_git(None, "ls-remote", REPO, token=TOKEN, timeout=0.1)
        self.assertNotIn(TOKEN, str(raised.exception))
        kill.assert_called_once_with(12345, github.signal.SIGKILL)
        self.assertEqual(process.communicate.call_count, 2)

    def test_api_request_headers_payload_and_no_redirect(self):
        with patch.object(github, "build_opener") as build:
            response = build.return_value.open.return_value.__enter__.return_value
            response.read.return_value = b'{"number": 7}'
            self.assertEqual(github._api("POST", "/repos/a/b/pulls", TOKEN, {"draft": True}), {"number": 7})
        request = build.return_value.open.call_args.args[0]
        self.assertEqual(request.full_url, "https://api.github.com/repos/a/b/pulls")
        self.assertEqual(request.get_header("Authorization"), f"Bearer {TOKEN}")
        self.assertNotIn(TOKEN, request.full_url)
        self.assertEqual(json.loads(request.data), {"draft": True})
        self.assertEqual(build.return_value.open.call_args.kwargs["timeout"], 30)
        handler = build.call_args.args[0]
        self.assertIsNone(handler.redirect_request(request, None, 302, "redirect", {}, "https://evil.example"))

    def test_http_and_transport_errors_never_expose_response_content(self):
        failures = [HTTPError("https://api.github.com", 403, TOKEN, {}, io.BytesIO(TOKEN.encode())),
                    HTTPError("https://api.github.com", 302, TOKEN, {}, io.BytesIO(TOKEN.encode())),
                    URLError(TOKEN), TimeoutError(TOKEN)]
        for failure in failures:
            with self.subTest(kind=type(failure).__name__), patch.object(github, "build_opener") as build:
                build.return_value.open.side_effect = failure
                with self.assertRaises(github.GitHubDeliveryError) as raised:
                    github._api("GET", "/repos/a/b/pulls", TOKEN)
                self.assertNotIn(TOKEN, str(raised.exception))

    def test_successful_delete_accepts_empty_204_and_closes_response(self):
        with patch.object(github, "build_opener") as build:
            response = build.return_value.open.return_value.__enter__.return_value
            response.status = 204
            response.read.return_value = b""
            self.assertIsNone(github._api("DELETE", "/repos/a/b/git/refs/heads/respan/fixture", TOKEN))
        build.return_value.open.return_value.__exit__.assert_called_once()


if __name__ == "__main__":
    unittest.main()
