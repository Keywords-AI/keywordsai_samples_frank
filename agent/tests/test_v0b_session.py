"""v0b session boundaries with real local Git and no model or network calls."""
from __future__ import annotations

import asyncio
import base64
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from dataclasses import dataclass
import io
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from urllib.parse import quote

from respan_integration_agent import agent, cli, github, runner, sandbox
from respan_integration_agent.config import ControllerConfig, OnboardingRequest
from respan_integration_agent.skill import provision_respan_skill


REPO = "https://github.com/fixture-owner/session-fixture.git"
BASE = "release/next"
TOKEN = "fixture/github+publication-key"
RESPAN_KEY = "fixture/respan+gateway-key"


class V0bSessionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.seed = self.root / "seed"
        self.seed.mkdir()
        self.bare = self.root / "origin.git"
        self.git = github.authenticated_git
        self.git(self.seed, "init", "--quiet", "--template=", f"--initial-branch={BASE}")
        (self.seed / "app.py").write_text("print('original')\n")
        (self.seed / "obsolete.py").write_text("# remove this fixture\n")
        (self.seed / "image.bin").write_bytes(b"\x00\xfforiginal\x00")
        self.git(self.seed, "add", "--all")
        self.commit(self.seed, "fixture baseline")
        self.base_sha = self.git(self.seed, "rev-parse", "HEAD")
        self.git(self.root, "clone", "--quiet", "--bare", str(self.seed), str(self.bare))
        self.git(self.seed, "remote", "add", "origin", str(self.bare))
        self.req = OnboardingRequest(repo_url=REPO, base_branch=BASE, product="tracing",
                                     tracing={"mode": "full"})
        self.checkouts = []
        self.clone_calls = []
        self.generation = None
        self.published = {}

    def commit(self, repo, message):
        self.git(repo, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                 "commit", "--quiet", "-m", message)

    def clone_transport(self, workdir, *args, **kwargs):
        # Only the transport destination is substituted. The real checkout,
        # validation, patch replay, commit, and cleanup remain in production code.
        self.assertEqual(args[0], "clone")
        self.assertIn(REPO, args)
        self.clone_calls.append((args, dict(kwargs)))
        self.assertNotIn(TOKEN, " ".join(args))
        self.assertEqual(kwargs.pop("token"), TOKEN)
        local_args = tuple(str(self.bare) if value == REPO else value for value in args)
        return self.git(workdir, *local_args, **kwargs)

    @contextmanager
    def local_checkout(self, repo_url, base_branch, token=None):
        self.assertEqual((repo_url, base_branch, token), (REPO, BASE, TOKEN))
        with patch.object(sandbox, "authenticated_git", side_effect=self.clone_transport):
            with sandbox.checkout(repo_url, base_branch, token=token) as workdir:
                self.checkouts.append(workdir)
                config = (workdir / ".git/config").read_text()
                self.assertNotIn(TOKEN, config)
                self.assertNotIn("x-access-token", config)
                yield workdir

    def edit(self, workdir, req, **kwargs):
        self.generation = workdir
        self.assertEqual(req.base_branch, BASE)
        self.assertEqual(kwargs["respan_api_key"], RESPAN_KEY)
        self.assertNotIn(TOKEN, kwargs["setup_context"])
        (workdir / "app.py").write_text("print('generated')\n")
        (workdir / "obsolete.py").unlink()
        (workdir / "image.bin").write_bytes(b"\x00\xfechanged\x00\xff")
        nested = workdir / "telemetry" / "nested helper.py"
        nested.parent.mkdir()
        nested.write_text("# generated nested fixture\n")
        return agent.AgentResult("Generated fixture integration", agent._git_changed(workdir), "a" * 32)

    def finalize(self, workdir, receipt, **kwargs):
        self.assertEqual(workdir, self.generation)
        (workdir / "finalization.txt").write_text("trusted finalization addition\n")
        return [{"checked": True}]

    def publish(self, workdir, branch, title, body, token, **kwargs):
        self.assertNotEqual(workdir, self.generation)
        self.assertEqual(workdir, self.checkouts[-1])
        self.assertEqual(token, TOKEN)
        self.assertEqual(kwargs["repo_url"], REPO)
        self.assertEqual(kwargs["base_branch"], BASE)
        self.assertEqual(self.git(workdir, "rev-parse", "HEAD^"), self.base_sha)
        self.assertEqual(kwargs["head_sha"], self.git(workdir, "rev-parse", "HEAD"))
        self.assertFalse(github.changed_files(workdir))
        self.assertEqual((workdir / "image.bin").read_bytes(), b"\x00\xfechanged\x00\xff")
        self.assertFalse((workdir / "obsolete.py").exists())
        self.assertTrue((workdir / "telemetry/nested helper.py").is_file())
        self.assertTrue((workdir / "finalization.txt").is_file())
        self.assertIn(self.base_sha, body)
        self.assertIn("a" * 32, body)
        self.assertNotIn(TOKEN, body)
        self.published = {
            "branch": branch,
            "sha": kwargs["head_sha"],
            "diff": self.git(workdir, "diff", "--binary", "--no-ext-diff", "--no-textconv",
                             "HEAD^", "HEAD", "--", strip=False),
            "tree": self.git(workdir, "rev-parse", "HEAD^{tree}"),
        }
        return github.OpenedPR("https://github.com/fixture-owner/session-fixture/pull/1",
                               1, branch, kwargs["head_sha"], BASE)

    @contextmanager
    def session(self, *, edit=None, publish=None):
        with patch.object(runner, "checkout", self.local_checkout), \
                patch.object(runner, "run_agent", side_effect=edit or self.edit) as model, \
                patch.object(runner, "finalize_lockfiles", side_effect=self.finalize), \
                patch.object(github, "open_pr", side_effect=publish or self.publish) as opened:
            yield model, opened

    def run_session(self):
        return runner.run_session(self.req, respan_api_key=RESPAN_KEY, github_token=TOKEN)

    def test_fresh_delivery_checkout_commits_exact_finalized_binary_patch(self):
        with self.session() as (model, opened):
            result = self.run_session()
        self.assertFalse(result.validation_errors)
        self.assertEqual(model.call_count, 1)
        self.assertEqual(opened.call_count, 1)
        self.assertEqual(len(set(self.checkouts)), 2)
        self.assertEqual(result.diff, self.published["diff"])
        self.assertIn("GIT binary patch", result.diff)
        self.assertEqual(set(result.changed_files), {
            "app.py", "obsolete.py", "image.bin", "telemetry/nested helper.py", "finalization.txt",
        })
        self.assertEqual(result.delivery_receipt["base_sha"], self.base_sha)
        self.assertEqual(result.delivery_receipt["head_sha"], self.published["sha"])
        self.assertEqual(result.delivery_receipt["tree_sha"], self.published["tree"])
        self.assertTrue(result.delivery_receipt["branch_pushed"])
        self.assertEqual(self.git(self.bare, "rev-parse", BASE), self.base_sha)
        self.assertTrue(all(not path.exists() for path in self.checkouts))

    def test_base_branch_moving_during_generation_keeps_diff_and_blocks_publish(self):
        def edit_and_advance(*args, **kwargs):
            result = self.edit(*args, **kwargs)
            (self.seed / "upstream.txt").write_text("concurrent upstream change\n")
            self.git(self.seed, "add", "--all")
            self.commit(self.seed, "advance upstream")
            self.git(self.seed, "push", "origin", BASE)
            return result

        with self.session(edit=edit_and_advance) as (_, opened), \
                patch.object(github, "commit_branch") as commit:
            result = self.run_session()
        opened.assert_not_called()
        commit.assert_not_called()
        self.assertIsNone(result.pr)
        self.assertIn("Base branch moved", result.validation_errors[0])
        self.assertIn("GIT binary patch", result.diff)
        self.assertIn("nested helper.py", result.diff)
        self.assertFalse(result.delivery_receipt["branch_pushed"])
        self.assertIsNone(result.delivery_receipt["head_sha"])
        self.assertEqual(result.delivery_receipt["base_sha"], self.base_sha)
        self.assertNotEqual(self.git(self.bare, "rev-parse", BASE), self.base_sha)

    def test_api_failure_after_push_retains_diff_and_recovery_identity(self):
        def fail_after_push(*args, **kwargs):
            self.publish(*args, **kwargs)
            error = github.GitHubDeliveryError("Branch was pushed, but PR creation could not be confirmed.")
            error.branch = args[1]
            error.head_sha = kwargs["head_sha"]
            error.branch_pushed = True
            raise error

        with self.session(publish=fail_after_push):
            result = self.run_session()
        self.assertIsNone(result.pr)
        self.assertEqual(result.diff, self.published["diff"])
        self.assertIn("PR_DELIVERY_FAILED", result.validation_errors[0])
        self.assertEqual(result.delivery_receipt["branch"], self.published["branch"])
        self.assertEqual(result.delivery_receipt["head_sha"], self.published["sha"])
        self.assertTrue(result.delivery_receipt["branch_pushed"])
        self.assertTrue(all(not path.exists() for path in self.checkouts))

    def test_generated_secret_text_is_redacted_and_never_published(self):
        forms = {
            form for secret in (TOKEN, RESPAN_KEY)
            for form in (secret, quote(secret, safe=""), base64.b64encode(secret.encode()).decode(),
                         base64.b64encode(f"x-access-token:{secret}".encode()).decode())
        }

        def leaking_edit(workdir, req, **kwargs):
            result = self.edit(workdir, req, **kwargs)
            (workdir / "leaked.txt").write_text("\n".join(forms) + "\n")
            return agent.AgentResult("\n".join(forms), agent._git_changed(workdir), result.trace_id)

        with self.session(edit=leaking_edit) as (_, opened), \
                patch.object(github, "commit_branch") as commit:
            result = self.run_session()
        opened.assert_not_called()
        commit.assert_not_called()
        self.assertEqual(len(self.checkouts), 1)
        self.assertIn("SECRET_IN_GENERATED_OUTPUT", result.validation_errors[0])
        self.assertIn("[REDACTED]", result.diff)
        self.assertIn("[REDACTED]", result.summary)
        for form in forms:
            self.assertNotIn(form, result.diff + result.summary)

    def test_generated_secret_filename_is_redacted_in_all_returned_output(self):
        encoded = quote(TOKEN, safe="")

        def leaking_path(workdir, req, **kwargs):
            result = self.edit(workdir, req, **kwargs)
            (workdir / f"{encoded}.txt").write_text("ordinary fixture content\n")
            return agent.AgentResult(result.summary, agent._git_changed(workdir), result.trace_id)

        with self.session(edit=leaking_path) as (_, opened):
            result = self.run_session()
        opened.assert_not_called()
        self.assertIn("SECRET_IN_GENERATED_OUTPUT", result.validation_errors[0])
        self.assertNotIn(encoded, repr(result))
        self.assertIn("[REDACTED].txt", result.changed_files)
        self.assertIn("ordinary fixture content", result.diff)

    def test_binary_secret_is_detected_before_git_patch_encoding_can_hide_it(self):
        def leaking_binary(workdir, req, **kwargs):
            result = self.edit(workdir, req, **kwargs)
            (workdir / "image.bin").write_bytes(b"\x00\xff" + RESPAN_KEY.encode() + b"\x00")
            encoded_patch = runner._git_diff(workdir)
            self.assertIn("GIT binary patch", encoded_patch)
            self.assertNotIn(RESPAN_KEY, encoded_patch)
            return result

        with self.session(edit=leaking_binary) as (_, opened), \
                patch.object(github, "commit_branch") as commit:
            result = self.run_session()
        opened.assert_not_called()
        commit.assert_not_called()
        self.assertIn("SECRET_IN_GENERATED_OUTPUT", result.validation_errors[0])
        self.assertNotIn("GIT binary patch", result.diff)
        self.assertNotIn(RESPAN_KEY, repr(result))
        self.assertEqual(len(self.checkouts), 1)

    def test_clone_uses_token_free_arguments_and_persisted_origin(self):
        with self.local_checkout(REPO, BASE, TOKEN) as workdir:
            self.assertEqual(self.git(workdir, "rev-parse", "HEAD"), self.base_sha)
            self.assertEqual(self.git(workdir, "remote", "get-url", "origin"), str(self.bare))
        self.assertEqual(len(self.clone_calls), 1)
        args, kwargs = self.clone_calls[0]
        self.assertEqual(kwargs["token"], TOKEN)
        self.assertIn(REPO, args)
        self.assertNotIn(TOKEN, " ".join(args))
        self.assertIn("--", args)

    def test_cli_publishing_requires_explicit_token_option(self):
        config = self.root / "request.json"
        config.write_text(self.req.model_dump_json())
        result = runner.SessionResult("fixture", None, ["app.py"], "fixture diff", None)
        env = {"RESPAN_API_KEY": RESPAN_KEY, "GH_TOKEN": TOKEN, "GITHUB_TOKEN": TOKEN,
               "DEPLOY_SECRET": TOKEN}
        for arguments, expected in (([], None), (["--token-env", "DEPLOY_SECRET"], TOKEN)):
            with self.subTest(arguments=arguments), patch.dict(os.environ, env), \
                    patch.object(cli, "run_session", return_value=result) as run, \
                    redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertEqual(cli.main(["run", "--config", str(config), *arguments]), 0)
            self.assertEqual(run.call_args.kwargs["github_token"], expected)

    def test_cli_missing_selected_token_fails_before_session(self):
        config = self.root / "request.json"
        config.write_text(self.req.model_dump_json())
        with patch.dict(os.environ, {"RESPAN_API_KEY": RESPAN_KEY}, clear=True), \
                patch.object(cli, "run_session") as run, redirect_stderr(io.StringIO()) as err:
            self.assertEqual(cli.main(["run", "--config", str(config), "--token-env", "UNSET_FIXTURE_TOKEN"]), 2)
        run.assert_not_called()
        self.assertIn("unset or empty", err.getvalue())

    def test_cli_failed_delivery_is_nonzero_and_prints_retained_diff_and_identity(self):
        config = self.root / "request.json"
        config.write_text(self.req.model_dump_json())
        result = runner.SessionResult(
            "Unverified success", None, ["app.py"], "retained reviewable diff", None,
            ["PR_DELIVERY_FAILED"], {}, {"branch": "respan/fixture", "head_sha": "b" * 40,
                                       "branch_pushed": True},
        )
        out, err = io.StringIO(), io.StringIO()
        with patch.dict(os.environ, {"RESPAN_API_KEY": RESPAN_KEY, "GH_TOKEN": TOKEN}), \
                patch.object(cli, "run_session", return_value=result), \
                redirect_stdout(out), redirect_stderr(err):
            code = cli.main(["run", "--config", str(config), "--token-env", "GH_TOKEN"])
        self.assertEqual(code, 1)
        self.assertIn(result.diff, out.getvalue())
        self.assertIn("respan/fixture", out.getvalue())
        self.assertIn("b" * 40, out.getvalue())
        self.assertNotIn("Unverified success", out.getvalue())
        self.assertNotIn(TOKEN, out.getvalue() + err.getvalue())

    def test_sdk_environment_masks_ambient_credentials_and_uses_private_home(self):
        @dataclass
        class Result:
            result: str = "fixture"
            is_error: bool = False

        captured = {}
        ambient = {"GH_TOKEN": TOKEN, "GITHUB_TOKEN": TOKEN, "DEPLOY_SECRET": TOKEN,
                   "GIT_ASKPASS": "/ambient/credential-helper", "AWS_SECRET_ACCESS_KEY": "unrelated-secret",
                   "HOME": str(self.root / "operator-home"), "PATH": os.environ.get("PATH", "")}

        async def query(**kwargs):
            options = kwargs["options"]
            effective = {**os.environ, **options.env}
            captured["effective"] = effective
            for key, value in ambient.items():
                if key in {"HOME", "PATH"}:
                    continue
                self.assertFalse(effective.get(key), key)
                self.assertNotIn(value, kwargs["prompt"])
            self.assertTrue(Path(effective["HOME"]).is_dir())
            self.assertNotEqual(effective["HOME"], ambient["HOME"])
            self.assertEqual(effective["ANTHROPIC_API_KEY"], RESPAN_KEY)
            self.assertEqual(effective["ANTHROPIC_AUTH_TOKEN"], RESPAN_KEY)
            self.assertEqual(effective["PATH"], ambient["PATH"])
            yield Result()

        sdk = SimpleNamespace(query=query, ClaudeAgentOptions=SimpleNamespace, ResultMessage=Result)
        trace = SimpleNamespace(get_client=lambda: SimpleNamespace(get_current_trace_id=lambda: "c" * 32))
        with patch.dict(os.environ, ambient), patch.dict("sys.modules", {"claude_agent_sdk": sdk, "respan": trace}), \
                provision_respan_skill() as skill:
            asyncio.run(agent._run(self.seed, self.req, RESPAN_KEY, ControllerConfig(), skill=skill))
            self.assertTrue(Path(captured["effective"]["HOME"]).is_relative_to(skill.config_dir))
            for key, value in ambient.items():
                self.assertEqual(os.environ[key], value)
        self.assertFalse(Path(captured["effective"]["HOME"]).exists())

    def test_sdk_git_metadata_tampering_is_rejected_before_post_model_git(self):
        @dataclass
        class Result:
            result: str = "fixture"
            is_error: bool = False

        calls_before_tampering = []

        async def query(**kwargs):
            calls_before_tampering.append(git.call_count)
            config = self.seed / ".git/config"
            config.write_text(config.read_text() + "\n[core]\n\tfsmonitor = forbidden-fixture-command\n")
            yield Result()

        sdk = SimpleNamespace(query=query, ClaudeAgentOptions=SimpleNamespace, ResultMessage=Result)
        trace = SimpleNamespace(get_client=lambda: SimpleNamespace(get_current_trace_id=lambda: None))
        with patch.dict("sys.modules", {"claude_agent_sdk": sdk, "respan": trace}), \
                provision_respan_skill() as skill, \
                patch.object(github, "authenticated_git", wraps=self.git) as git, \
                patch.object(agent, "_git_changed") as changed, \
                self.assertRaisesRegex(github.GitHubDeliveryError, "changed Git metadata"):
            asyncio.run(agent._run(self.seed, self.req, RESPAN_KEY, ControllerConfig(), skill=skill))
        changed.assert_not_called()
        self.assertEqual(git.call_count, calls_before_tampering[0])


if __name__ == "__main__":
    unittest.main()
