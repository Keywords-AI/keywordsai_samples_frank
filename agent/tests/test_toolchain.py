"""Trusted toolchain tests; fixtures contain metadata only, no target application."""
from __future__ import annotations

import os
from pathlib import Path
import signal
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch

from respan_integration_agent import toolchain


class ToolchainTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.bin = self.root / "tools"
        self.bin.mkdir()
        for manager in toolchain.PINNED_TOOLS:
            executable = self.bin / manager
            executable.write_text("fixture executable\n")
            executable.chmod(0o755)

    def project(self, manager="poetry", directory="."):
        root = self.repo / directory
        root.mkdir(parents=True, exist_ok=True)
        (root / "pyproject.toml").write_text('[project]\nname="fixture"\nversion="0.0.0"\n[tool.' + manager + ']\n')
        (root / (manager + ".lock")).write_text("original lock\n")
        return root

    def preflight(self):
        def version(argv, **kwargs):
            manager = Path(argv[0]).name
            return f"{manager} {toolchain.PINNED_TOOLS[manager]}"
        with patch.object(toolchain, "_run", side_effect=version):
            return toolchain.preflight_toolchain(self.repo, tool_bin=self.bin)

    def test_missing_tool_fails_before_any_command(self):
        self.project()
        (self.bin / "poetry").unlink()
        with patch.object(toolchain, "_run") as run, self.assertRaises(toolchain.ToolchainError) as error:
            toolchain.preflight_toolchain(self.repo, tool_bin=self.bin)
        self.assertEqual(error.exception.code, "TOOLCHAIN_MISSING")
        run.assert_not_called()

    def test_wrong_tool_version_fails_preflight(self):
        self.project()
        with patch.object(toolchain, "_run", return_value="Poetry (version 2.4.1)"), self.assertRaises(toolchain.ToolchainError) as error:
            toolchain.preflight_toolchain(self.repo, tool_bin=self.bin)
        self.assertEqual(error.exception.code, "TOOLCHAIN_VERSION_MISMATCH")

    def test_unchanged_manifest_and_lock_run_nothing(self):
        self.project()
        receipt = self.preflight()
        with patch.object(toolchain, "_run") as run:
            self.assertEqual(toolchain.finalize_lockfiles(self.repo, receipt), [])
        run.assert_not_called()

    def test_changed_manifests_use_exact_manager_commands_and_clean_env(self):
        self.project("poetry", "poetry-app")
        self.project("uv", "uv-app")
        receipt = self.preflight()
        for project in receipt.projects:
            manifest = self.repo / project.directory / "pyproject.toml"
            manifest.write_text(manifest.read_text() + "# model edit\n")
        calls = []

        def run(argv, **kwargs):
            calls.append((argv, kwargs))
            manager = Path(argv[0]).name
            (kwargs["cwd"] / (manager + ".lock")).write_text("resolved lock\n")
            return ""

        with patch.dict(os.environ, {"RESPAN_API_KEY": "secret-fixture", "ANTHROPIC_API_KEY": "secret-fixture", "GH_TOKEN": "secret-fixture", "PIP_INDEX_URL": "https://private.invalid/", "NETRC": "/private/user.netrc"}), patch.object(toolchain, "_run", side_effect=run):
            result = toolchain.finalize_lockfiles(self.repo, receipt, timeout_seconds=600)
        self.assertEqual(len(result), 2)
        self.assertEqual([call[0][1:] for call in calls], [
            ["--no-plugins", "--no-interaction", "lock"],
            ["--no-plugins", "--no-interaction", "check", "--lock"],
            ["lock", "--no-python-downloads"], ["lock", "--check", "--no-python-downloads"],
        ])
        for _, kwargs in calls:
            env = kwargs["env"]
            self.assertNotIn("RESPAN_API_KEY", env)
            self.assertNotIn("ANTHROPIC_API_KEY", env)
            self.assertNotIn("GH_TOKEN", env)
            self.assertNotIn("PIP_INDEX_URL", env)
            self.assertEqual(env["NETRC"], os.devnull)
            self.assertTrue(env["HOME"].endswith("/home"))
            self.assertEqual(env["UV_PYTHON_DOWNLOADS"], "never")
            self.assertEqual(kwargs["timeout_seconds"], 600)
            self.assertTrue(kwargs["cwd"].is_relative_to(self.repo.resolve()))

    def test_deleted_uv_lock_is_regenerated_from_preflight_record(self):
        project = self.project("uv")
        (project / "pyproject.toml").write_text('[project]\nname="fixture"\nversion="0.0.0"\n')
        receipt = self.preflight()
        (project / "uv.lock").unlink()
        def run(argv, **kwargs):
            (project / "uv.lock").write_text("restored lock\n")
            return ""
        with patch.object(toolchain, "_run", side_effect=run):
            self.assertEqual(len(toolchain.finalize_lockfiles(self.repo, receipt)), 1)

    def test_changed_executable_is_rejected_before_locking(self):
        self.project()
        receipt = self.preflight()
        (self.repo / "pyproject.toml").write_text('[tool.poetry]\nname="edited"\n')
        (self.bin / "poetry").write_text("changed executable\n")
        with patch.object(toolchain, "_run") as run, self.assertRaises(toolchain.ToolchainError) as error:
            toolchain.finalize_lockfiles(self.repo, receipt)
        self.assertEqual(error.exception.code, "TOOLCHAIN_EXECUTABLE_CHANGED")
        run.assert_not_called()

    def test_invalid_timeout_never_starts_command(self):
        self.project()
        receipt = self.preflight()
        for timeout in (0, -1, float("inf"), float("nan")):
            with self.subTest(timeout=timeout), patch.object(toolchain, "_run") as run, self.assertRaises(ValueError):
                toolchain.finalize_lockfiles(self.repo, receipt, timeout_seconds=timeout)
            run.assert_not_called()

    @unittest.skipUnless(os.name == "posix", "POSIX process-group cleanup")
    def test_timeout_terminates_then_kills_owned_group_and_reaps(self):
        process = Mock(pid=424242)
        process.communicate.side_effect = [subprocess.TimeoutExpired("fixture", 0.01), subprocess.TimeoutExpired("fixture", 5), ("", "")]
        with patch.object(subprocess, "Popen", return_value=process) as popen, patch.object(os, "killpg") as kill, self.assertRaises(toolchain.ToolchainError):
            toolchain._run(["fixture"], cwd=self.root, env={}, timeout_seconds=0.01, code="LOCK_FINALIZATION_FAILED")
        self.assertTrue(popen.call_args.kwargs["start_new_session"])
        self.assertEqual(kill.call_args_list[0].args, (424242, signal.SIGTERM))
        self.assertEqual(kill.call_args_list[1].args, (424242, signal.SIGKILL))
        self.assertEqual(process.communicate.call_count, 3)

    def test_bootstrap_preserves_existing_prefix(self):
        existing = self.root / "existing"
        existing.mkdir()
        marker = existing / "user-file"
        marker.write_text("preserve")
        with patch.object(toolchain, "_run") as run, self.assertRaises(toolchain.ToolchainError) as error:
            toolchain.bootstrap_toolchain(existing)
        self.assertEqual(error.exception.code, "TOOLCHAIN_PREFIX_EXISTS")
        self.assertEqual(marker.read_text(), "preserve")
        run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
