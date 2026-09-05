"""Check delivered patches with synthetic local Git repositories only."""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from respan_integration_agent.runner import _git_diff


class DiffDeliveryTests(unittest.TestCase):
    def test_complete_patch_applies_without_changing_real_index(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {
            "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1",
        }):
            root = Path(tmp)
            repo = root / "source"
            repo.mkdir()

            def git(*args, cwd=repo, input=None):
                return subprocess.run(
                    ["git", "-C", str(cwd), *args], input=input,
                    check=True, capture_output=True,
                ).stdout

            git("init", "--quiet", "--template=", "--initial-branch=main")
            (repo / "tracked.py").write_text("original\n")
            (repo / "deleted.py").write_text("delete me\n")
            (repo / ".gitignore").write_text("ignored.txt\n")
            git("add", "--all")
            git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                "-c", "commit.gpgsign=false", "commit", "--quiet", "-m", "fixture baseline")
            (repo / "tracked.py").write_text("staged\n")
            git("add", "--", "tracked.py")
            (repo / "tracked.py").write_text("final worktree content\n")
            (repo / "deleted.py").unlink()
            new_files = {
                "setup_tracing.py": b"def setup():\n    return True\n",
                "space name.py": b"space\n", "-leading.py": b"dash\n",
                "café.py": b"unicode name\n", "line\nbreak.py": b"newline name\n",
                "binary.bin": b"\x00\x01\xfffixture\x00",
            }
            for name, content in new_files.items():
                (repo / name).write_bytes(content)
            (repo / "ignored.txt").write_text("fixture-only ignored content\n")
            before_index = (repo / ".git/index").read_bytes()
            before_status = git("status", "--porcelain", "-z")

            delivered = _git_diff(repo)

            self.assertEqual((repo / ".git/index").read_bytes(), before_index)
            self.assertEqual(git("status", "--porcelain", "-z"), before_status)
            self.assertNotIn("fixture-only ignored content", delivered)
            self.assertIn("GIT binary patch", delivered)
            fresh = root / "fresh"
            git("clone", "--quiet", str(repo), str(fresh))
            git("apply", "--binary", "-", cwd=fresh, input=delivered.encode())
            self.assertEqual((fresh / "tracked.py").read_text(), "final worktree content\n")
            self.assertFalse((fresh / "deleted.py").exists())
            for name, content in new_files.items():
                self.assertEqual((fresh / name).read_bytes(), content)


if __name__ == "__main__":
    unittest.main()
