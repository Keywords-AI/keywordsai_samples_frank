"""Exercise setup ownership and CLI outcomes on synthetic Git fixtures."""
from contextlib import contextmanager, redirect_stderr, redirect_stdout
import io
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from respan_integration_agent import agent, cli, runner, toolchain
from respan_integration_agent.config import OnboardingRequest


class SetupPipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.git("init", "-q")
        self.git("config", "user.name", "Setup fixture")
        self.git("config", "user.email", "fixture@example.invalid")
        (self.repo / "app.py").write_text("# original fixture\n")
        (self.repo / "pyproject.toml").write_text('[project]\nname="fixture"\nversion="0.0.0"\n')
        self.git("add", ".")
        self.git("commit", "-qm", "fixture")
        self.request = OnboardingRequest(repo_url=str(self.repo), product="tracing")

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.repo), *args], check=True,
                              capture_output=True, text=True).stdout

    @contextmanager
    def checkout(self, *args, **kwargs):
        yield self.repo

    def model_edit(self, *args, **kwargs):
        self.assertIn("Lock tools verified by the runner", kwargs["setup_context"])
        (self.repo / "app.py").write_text("# generated fixture edit\n")
        return agent.AgentResult("Generated summary", ["app.py"], None)

    def test_missing_lock_tool_prevents_model_call(self):
        (self.repo / "poetry.lock").write_text("fixture lock\n")
        with patch.object(runner, "checkout", self.checkout), \
                patch.object(runner, "run_agent") as model, \
                patch.dict(os.environ, {}, clear=True), \
                patch.object(toolchain.shutil, "which", return_value=None):
            with self.assertRaises(toolchain.ToolchainError) as error:
                runner.run_session(self.request, respan_api_key="fixture-key")
        self.assertEqual(error.exception.code, "TOOLCHAIN_MISSING")
        model.assert_not_called()

    def test_trusted_finalization_additions_are_in_delivered_patch(self):
        def finalize(root, receipt, **kwargs):
            self.assertIn("generated", (root / "app.py").read_text())
            self.assertEqual(receipt.repository, str(root))
            (root / "uv.lock").write_text("# trusted generated fixture lock\n")
            return [{"checked": True}]

        with patch.object(runner, "checkout", self.checkout), \
                patch.object(runner, "run_agent", side_effect=self.model_edit), \
                patch.object(runner, "finalize_lockfiles", side_effect=finalize):
            result = runner.run_session(self.request, respan_api_key="fixture-key")
        self.assertFalse(result.validation_errors)
        self.assertIn("uv.lock", result.changed_files)
        self.assertIn("+" + "# trusted generated fixture lock", result.diff)
        self.assertEqual(result.setup_receipt["lock_finalization"], [{"checked": True}])

    def test_new_nested_initializer_triggers_bundled_dependency_repair(self):
        backend = self.repo / "backend"
        backend.mkdir()
        (backend / "requirements.txt").write_text("idna==3.10\n")
        (backend / "runtime-requirements.txt").write_text("idna==3.10\n")
        (self.repo / "build.sh").write_text("python -m pip install --target bundle -r backend/runtime-requirements.txt\n")
        self.git("add", ".")
        self.git("commit", "-qm", "deployment fixture")

        def edit(*args, **kwargs):
            nested = backend / "telemetry"
            nested.mkdir()
            (nested / "__init__.py").write_text("from respan import Respan\n")
            (backend / "requirements.txt").write_text(agent.PYTHON_SDK_CONDITIONAL_DEPENDENCY + "\n")
            changed = agent._git_changed(self.repo)
            self.assertIn("backend/telemetry/__init__.py", changed)
            return agent.AgentResult("fixture edit", changed, None)

        with patch.object(runner, "checkout", self.checkout), \
                patch.object(runner, "run_agent", side_effect=edit):
            result = runner.run_session(self.request, respan_api_key="fixture-key")
        self.assertFalse(result.validation_errors)
        self.assertIn("backend/runtime-requirements.txt", result.changed_files)
        self.assertIn(agent.PYTHON_SDK_CONDITIONAL_DEPENDENCY, (backend / "runtime-requirements.txt").read_text())
        self.assertIn("backend/telemetry/__init__.py", result.diff)

    def test_changed_paths_preserve_newlines_and_rename_endpoints(self):
        unusual = 'nested folder/line\nbreak-雪.py'
        path = self.repo / unusual
        path.parent.mkdir()
        path.write_text("fixture\n")
        self.git("mv", "app.py", "renamed app.py")
        changed = set(agent._git_changed(self.repo))
        self.assertTrue({unusual, "app.py", "renamed app.py"}.issubset(changed))

    def test_failed_finalization_keeps_reviewable_diff_and_blocks_pr(self):
        failure = toolchain.ToolchainError("LOCK_FINALIZATION_FAILED", "fixture resolution failure")
        with patch.object(runner, "checkout", self.checkout), \
                patch.object(runner, "run_agent", side_effect=self.model_edit), \
                patch.object(runner, "finalize_lockfiles", side_effect=failure), \
                patch.object(runner.github, "commit_branch") as commit, \
                patch.object(runner.github, "open_pr") as pr:
            result = runner.run_session(self.request, respan_api_key="fixture-key",
                                        github_token="fixture-token")
        self.assertIn("generated fixture edit", result.diff)
        self.assertIn("LOCK_FINALIZATION_FAILED", result.validation_errors[0])
        commit.assert_not_called()
        pr.assert_not_called()

    def test_cli_partial_result_is_nonzero_and_keeps_diff(self):
        config = self.root / "request.json"
        config.write_text(self.request.model_dump_json())
        result = runner.SessionResult("Unverified generated success", None, ["app.py"],
                                      "reviewable patch", None, ["LOCK_FINALIZATION_FAILED"])
        out, err = io.StringIO(), io.StringIO()
        with patch.dict(os.environ, {"RESPAN_API_KEY": "fixture-key"}), \
                patch.object(cli, "run_session", return_value=result), \
                redirect_stdout(out), redirect_stderr(err):
            code = cli.main(["run", "--config", str(config)])
        self.assertEqual(code, 1)
        self.assertIn("reviewable patch", out.getvalue())
        self.assertNotIn("Unverified generated success", out.getvalue())
        self.assertIn("LOCK_FINALIZATION_FAILED", err.getvalue())

    def test_cli_setup_does_not_require_model_credentials(self):
        with patch.dict(os.environ, {}, clear=True), \
                patch.object(cli, "bootstrap_toolchain", return_value={"tool_bin": "/fixture/bin"}) as setup, \
                redirect_stdout(io.StringIO()):
            self.assertEqual(cli.main(["setup", "--toolchain-dir", str(self.root / "tools")]), 0)
        setup.assert_called_once_with(self.root / "tools")

    def test_cli_reports_corrupt_skill_as_setup_error(self):
        config = self.root / "request.json"
        config.write_text(self.request.model_dump_json())
        err = io.StringIO()
        with patch.dict(os.environ, {"RESPAN_API_KEY": "fixture-key"}), \
                patch.object(runner, "validate_skill_source", side_effect=ValueError("Bundled skill hash mismatch")), \
                patch.object(runner, "checkout") as clone, \
                patch.object(runner, "run_agent") as model, redirect_stderr(err):
            self.assertEqual(cli.main(["run", "--config", str(config)]), 2)
        self.assertIn("Bundled skill hash mismatch", err.getvalue())
        clone.assert_not_called()
        model.assert_not_called()
