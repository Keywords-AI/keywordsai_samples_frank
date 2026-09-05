"""The installed agent must supply its own skill, without user-global state."""
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from respan_integration_agent.skill import (
    FILES, bundled_skill_dir, provision_respan_skill, validate_skill_source,
)


class SkillBundleTests(unittest.TestCase):
    def test_clean_home_and_unrelated_claude_config_are_untouched(self):
        with tempfile.TemporaryDirectory() as temp:
            unrelated = Path(temp) / "claude"
            unrelated.mkdir()
            settings = unrelated / "settings.json"
            settings.write_text('{"unrelated":true}')
            with patch.dict("os.environ", {"CLAUDE_CONFIG_DIR": str(unrelated)}):
                with provision_respan_skill() as skill:
                    prepared = skill.config_dir
                    self.assertNotEqual(prepared, unrelated)
                    self.assertEqual(len(list(skill.skill_dir.rglob("*.md"))), 6)
                    self.assertEqual(validate_skill_source(skill.skill_dir), skill.skill_dir)
                    self.assertEqual(skill.receipt()["files"], FILES)
                    self.assertEqual(settings.read_text(), '{"unrelated":true}')
                self.assertFalse(prepared.exists())
            self.assertEqual(list(unrelated.iterdir()), [settings])

    def test_corrupt_bundle_fails_before_creating_a_session(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "skill"
            shutil.copytree(bundled_skill_dir(), source)
            (source / "references/tracing.md").write_text("wrong reference")
            with self.assertRaisesRegex(ValueError, "hash mismatch"):
                with provision_respan_skill(source):
                    self.fail("Corrupt bundle was provisioned")

    def test_reference_symlinks_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "skill"
            shutil.copytree(bundled_skill_dir(), source)
            reference = source / "references/tracing.md"
            reference.unlink()
            reference.symlink_to(bundled_skill_dir() / "references/tracing.md")
            with self.assertRaisesRegex(ValueError, "symlink"):
                validate_skill_source(source)
