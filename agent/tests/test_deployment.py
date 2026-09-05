"""Requirements delivery checks use local synthetic files; never execute scripts."""
from __future__ import annotations

import os
from pathlib import Path
import tempfile
import unittest

from respan_integration_agent.deployment import (
    discover_consumed_requirements,
    repair_consumed_requirements,
)


SDK = "respan-ai==4.2.3; python_version >= '3.11' and python_version < '3.14'"
SETUP = 'import os\nif os.getenv("RESPAN_API_KEY"):\n    from respan import Respan as _Respan\n    _Respan()\n'


class DeploymentTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="deployment-fixture-", dir=os.environ.get("RESPAN_TEST_TMPDIR"))
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()

    def write(self, path, text):
        destination = self.root / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(text)
        return destination

    def setup_component(self, prefix="service"):
        self.write(prefix + "/app/observability.py", SETUP)
        self.write(prefix + "/requirements.txt", SDK + "\n")
        self.write(prefix + "/runtime-requirements.txt", "stdlib-addon==1.0\n")
        return [prefix + "/app/observability.py", prefix + "/requirements.txt"]

    def repair(self, changed):
        catalog = discover_consumed_requirements(self.root)
        return catalog, repair_consumed_requirements(self.root, catalog, changed, SDK)

    def test_pinned_cortex_bundle_command_discovers_and_repairs_missing_delivery(self):
        # Exact command shape from trace-cortex/cortex-app at
        # 1a607cb39c067d8d86744065947cc35f9ce4626d, macos/build.sh:6,264-268.
        changed = self.setup_component("backend")
        source = 'ROOT="$(cd "$(dirname "$0")" && pwd)"\n' + "\n" * 262
        source += '''"$PYTHON_FRAMEWORK_SOURCE/bin/python3.12" -m pip install \\
  --disable-pip-version-check \\
  --only-binary=:all: \\
  --target "$PY_RUNTIME_DEPS" \\
  -r "$ROOT/../backend/runtime-requirements.txt"
'''
        self.write("macos/build.sh", source)
        catalog, result = self.repair(changed)
        self.assertEqual(len(catalog.installations), 1)
        consumer = catalog.installations[0]
        self.assertEqual(consumer.source, "macos/build.sh")
        self.assertEqual(consumer.line, 264)
        self.assertEqual(consumer.manifests, ("backend/runtime-requirements.txt",))
        self.assertEqual(consumer.target, "$PY_RUNTIME_DEPS")
        self.assertIn("macos/build.sh:264", catalog.to_prompt())
        self.assertEqual([item["path"] for item in result["repairs"]], ["backend/runtime-requirements.txt"])
        self.assertEqual(result["issues"], [])
        self.assertIn(SDK, (self.root / "backend/runtime-requirements.txt").read_text())
        # Repeating the deterministic phase must not add duplicate requirements.
        again = repair_consumed_requirements(self.root, catalog, changed, SDK)
        self.assertEqual(again["repairs"], [])

    def test_multiple_r_flags_are_one_install_union(self):
        changed = self.setup_component()
        self.write("deploy.sh", "python -m pip install -r service/requirements.txt --requirement=service/runtime-requirements.txt\n")
        catalog, result = self.repair(changed)
        self.assertEqual(catalog.installations[0].manifests, ("service/requirements.txt", "service/runtime-requirements.txt"))
        self.assertEqual(result["repairs"], [])
        self.assertEqual(len(result["checked_installations"]), 1)

    def test_relative_includes_provide_transitive_sdk_without_duplicate(self):
        changed = self.setup_component()
        self.write("service/runtime-requirements.txt", "-r common.txt\n")
        self.write("service/common.txt", SDK + "\n")
        self.write("deploy.sh", "uv pip install -rservice/runtime-requirements.txt\n")
        _, result = self.repair(changed)
        self.assertEqual(result["repairs"], [])
        self.assertEqual(result["issues"], [])
        self.assertEqual(len(result["checked_installations"]), 1)

    def test_unrelated_component_and_missing_anchor_are_not_modified(self):
        changed = self.setup_component("first")
        second = self.write("second/requirements.txt", "other-package==1\n")
        self.write("deploy.sh", "pip install -r second/requirements.txt\n")
        _, result = self.repair(changed)
        self.assertEqual(result["repairs"], [])
        self.assertEqual(result["issues"], [])
        self.assertEqual(second.read_text(), "other-package==1\n")
        # Setup alone is not authorization to choose an arbitrary base manifest.
        self.write("second/app.py", SETUP)
        _, result = self.repair(["second/app.py"])
        self.assertEqual(result["repairs"], [])
        self.assertIn("no safe repair", str(result["issues"]))
        self.assertEqual(second.read_text(), "other-package==1\n")

    def test_unchanged_same_component_anchor_can_supply_safe_repair(self):
        self.setup_component()
        self.write("deploy.sh", "pip install -r service/runtime-requirements.txt\n")
        _, result = self.repair(["service/app/observability.py"])
        self.assertEqual([item["path"] for item in result["repairs"]], ["service/runtime-requirements.txt"])
        self.assertEqual(result["issues"], [])

    def test_unknown_external_and_symlink_references_are_not_resolved(self):
        changed = self.setup_component()
        self.write("deploy.sh", 'pip install -r "$RELEASE_DIR/service/runtime-requirements.txt"\npip install -r /etc/passwd\npip install -r linked.txt\n')
        (self.root / "linked.txt").symlink_to(self.root / "service/runtime-requirements.txt")
        catalog, result = self.repair(changed)
        self.assertEqual(catalog.installations, [])
        self.assertEqual(len(catalog.issues), 3)
        self.assertEqual(result["repairs"], [])

    def test_cyclic_and_unsafe_includes_block_repair(self):
        changed = self.setup_component()
        self.write("deploy.sh", "pip install -r service/runtime-requirements.txt\n")
        self.write("service/runtime-requirements.txt", "-r common.txt\n")
        self.write("service/common.txt", "-r runtime-requirements.txt\n")
        _, result = self.repair(changed)
        self.assertEqual(result["repairs"], [])
        self.assertIn("cyclic", str(result["issues"]))
        self.write("service/common.txt", "-r ../../outside.txt\n")
        _, result = self.repair(changed)
        self.assertEqual(result["repairs"], [])
        self.assertIn("unsafe", str(result["issues"]))

    def test_existing_conflicting_sdk_is_not_overwritten(self):
        changed = self.setup_component()
        self.write("service/runtime-requirements.txt", "respan-ai==0.1.0\n")
        self.write("deploy.sh", "pip install --target packaged -r service/runtime-requirements.txt\n")
        _, result = self.repair(changed)
        self.assertEqual(result["repairs"], [])
        self.assertIn("conflicting", str(result["issues"]))
        self.assertEqual((self.root / "service/runtime-requirements.txt").read_text(), "respan-ai==0.1.0\n")

    def test_same_version_with_contradictory_or_narrow_marker_is_not_delivery(self):
        changed = self.setup_component()
        self.write("deploy.sh", "pip install -r service/runtime-requirements.txt\n")
        for marker in ["python_version >= '3.14'", "python_version >= '3.12'", "python_version != '3.12'", "sys_platform == 'darwin'", "python_full_version >= '3.11.0'"]:
            with self.subTest(marker=marker):
                original = "respan-ai==4.2.3; " + marker + "\n"
                self.write("service/runtime-requirements.txt", original)
                _, result = self.repair(changed)
                self.assertEqual(result["repairs"], [])
                self.assertIn("conflicting", str(result["issues"]))
                self.assertEqual((self.root / "service/runtime-requirements.txt").read_text(), original)

    def test_unconditional_or_equivalent_sdk_covers_verified_minor_range(self):
        changed = self.setup_component()
        self.write("deploy.sh", "pip install -r service/runtime-requirements.txt\n")
        for requirement in ["respan-ai==4.2.3", "respan-ai==4.2.3; '3.11' <= python_version and python_version <= '3.13'"]:
            with self.subTest(requirement=requirement):
                self.write("service/runtime-requirements.txt", requirement + "\n")
                _, result = self.repair(changed)
                self.assertEqual(result["issues"], [])
                self.assertEqual(result["repairs"], [])
                self.assertEqual(len(result["checked_installations"]), 1)

    def test_poetry_anchor_requires_verified_python_marker_coverage(self):
        self.write("service/app.py", SETUP)
        self.write("service/runtime-requirements.txt", "other==1\n")
        self.write("deploy.sh", "pip install -r service/runtime-requirements.txt\n")
        manifest = '[tool.poetry.dependencies]\nrespan-ai = { version="4.2.3", python=">=3.14" }\n'
        self.write("service/pyproject.toml", manifest)
        changed = ["service/app.py", "service/pyproject.toml"]
        _, result = self.repair(changed)
        self.assertEqual(result["repairs"], [])
        self.assertIn("no safe repair", str(result["issues"]))
        self.write("service/pyproject.toml", manifest.replace('>=3.14', '>=3.11,<3.14'))
        _, result = self.repair(changed)
        self.assertEqual([x["path"] for x in result["repairs"]], ["service/runtime-requirements.txt"])

    def test_poetry_marker_or_platform_restriction_is_not_an_unconditional_anchor(self):
        self.write("service/app.py", SETUP)
        self.write("service/runtime-requirements.txt", "other==1\n")
        self.write("deploy.sh", "pip install -r service/runtime-requirements.txt\n")
        for qualifier in ['markers="python_version >= \'3.14\'"', 'platform="darwin"', 'markers="sys_platform == \'darwin\'"']:
            with self.subTest(qualifier=qualifier):
                self.write("service/pyproject.toml", '[tool.poetry.dependencies]\nrespan-ai = {version="4.2.3", ' + qualifier + '}\n')
                _, result = self.repair(["service/app.py"])
                self.assertEqual(result["repairs"], [])
                self.assertIn("no safe repair", str(result["issues"]))

    def test_ambiguous_multi_manifest_install_is_not_guessed(self):
        changed = self.setup_component()
        self.write("service/extra-requirements.txt", "extra==1\n")
        self.write("deploy.sh", "pip install -r service/runtime-requirements.txt -r service/extra-requirements.txt\n")
        _, result = self.repair(changed)
        self.assertEqual(result["repairs"], [])
        self.assertIn("no unique repair target", str(result["issues"]))

    def test_literal_cd_selects_correct_runtime_and_not_same_named_root_file(self):
        changed = self.setup_component()
        self.write("requirements.txt", "unrelated==1\n")
        self.write("deploy.sh", "cd service && pip install -r runtime-requirements.txt\n")
        catalog, result = self.repair(changed)
        self.assertEqual(catalog.installations[0].manifests, ("service/runtime-requirements.txt",))
        self.assertEqual([x["path"] for x in result["repairs"]], ["service/runtime-requirements.txt"])
        self.assertEqual((self.root / "requirements.txt").read_text(), "unrelated==1\n")

    def test_container_context_is_not_inferred_from_same_named_root_manifest(self):
        changed = self.setup_component()
        self.write("runtime-requirements.txt", "unrelated==1\n")
        self.write("Dockerfile", "COPY service/runtime-requirements.txt /app/runtime-requirements.txt\nRUN pip install -r runtime-requirements.txt\n")
        catalog, result = self.repair(changed)
        self.assertEqual(catalog.installations, [])
        self.assertEqual(len(catalog.issues), 1)
        self.assertEqual(result["repairs"], [])

    def test_make_recipe_directory_does_not_leak_to_another_command(self):
        self.setup_component()
        self.write("requirements.txt", "unrelated==1\n")
        self.write("Makefile", "build:\n\tcd service\n\tpip install -r requirements.txt\n")
        catalog = discover_consumed_requirements(self.root)
        self.assertEqual(catalog.installations[0].manifests, ("requirements.txt",))

    def test_pinned_cortex_readme_install_is_repaired_separately_from_bundle(self):
        # trace-cortex/cortex-app@1a607cb39c067d8d86744065947cc35f9ce4626d
        # backend/README.md:32-38, including the literal checkout-root cd.
        self.write("backend/app/config.py", SETUP)
        self.write("backend/app/main.py", "from .config import load_settings\n")
        self.write("backend/requirements.txt", "fastapi>=0.100.0\n")
        self.write("backend/runtime-requirements.txt", "respan-ai==4.2.3\n")
        self.write("backend/README.md", "\n" * 31 + '''```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8766
```
''')
        catalog, result = self.repair(["backend/app/config.py", "backend/runtime-requirements.txt"])
        self.assertEqual(catalog.installations[0].source, "backend/README.md")
        self.assertEqual(catalog.installations[0].line, 36)
        self.assertEqual(catalog.installations[0].manifests, ("backend/requirements.txt",))
        self.assertEqual([r["path"] for r in result["repairs"]], ["backend/requirements.txt"])
        self.assertEqual(catalog.entrypoints[0].path, "backend/app/main.py")
        self.assertEqual((self.root / "backend/app/config.py").read_text(), SETUP)
        self.assertEqual(result["issues"], [])

    def test_readme_only_shell_fences_and_actual_install_commands_count(self):
        self.setup_component()
        self.write("README.md", '''pip install -r service/runtime-requirements.txt
```python
pip install -r service/runtime-requirements.txt
```
```bash
echo pip install -r service/runtime-requirements.txt
printf python -m pip install -r service/runtime-requirements.txt
```
```console
$ pip install -r service/runtime-requirements.txt
pip install -r service/requirements.txt
```
''')
        catalog = discover_consumed_requirements(self.root)
        self.assertEqual(len(catalog.installations), 1)
        self.assertEqual(catalog.installations[0].manifests, ("service/runtime-requirements.txt",))

    def test_readme_ambiguous_relative_manifest_is_not_guessed(self):
        changed = self.setup_component()
        self.write("runtime-requirements.txt", "unrelated==1\n")
        self.write("service/README.md", "```bash\npip install -r runtime-requirements.txt\n```\n")
        catalog, result = self.repair(changed)
        self.assertEqual(catalog.installations, [])
        self.assertEqual(len(catalog.issues), 1)
        self.assertEqual(result["repairs"], [])

    def test_readme_blocks_do_not_share_directory_state(self):
        self.setup_component()
        self.write("requirements.txt", "unrelated==1\n")
        self.write("README.md", "```bash\ncd service\npip install -r requirements.txt\n```\n```bash\npip install -r requirements.txt\n```\n")
        catalog = discover_consumed_requirements(self.root)
        self.assertEqual([i.manifests for i in catalog.installations], [("service/requirements.txt",), ("requirements.txt",)])

    def test_pinned_cortex_service_and_shell_worker_are_explicit_prompt_facts(self):
        # Exact deployed command shapes from the same pinned Cortex revision:
        # deploy/systemd/cortex-worker.service:10-11, macmini/run-worker.sh:7-9.
        self.write("backend/app/config.py", SETUP)
        worker = self.write("scripts/run_memory_worker.py", "from backend.app.config import load_settings\nsettings = load_settings()\n")
        self.write("deploy/systemd/cortex-worker.service", "[Unit]\n\n\n\n\n[Service]\n\n\n\nWorkingDirectory=/srv/cortex/current\nExecStart=/srv/cortex/venv/bin/python scripts/run_memory_worker.py --iterations 0 --interval-seconds 30\n")
        self.write("deploy/macmini/run-worker.sh", "#!/bin/bash\n\n\n\n\n\ncd \"${CORTEX_REPO_DIR:?CORTEX_REPO_DIR not set}\"\nexec \"${CORTEX_PYTHON:-python3}\" scripts/run_memory_worker.py \\\n  --iterations 0 --interval-seconds \"${CORTEX_WORKER_INTERVAL:-30}\"\n")
        catalog, result = self.repair(["backend/app/config.py"])
        self.assertEqual(len(catalog.entrypoints), 2)
        self.assertEqual({e.candidate_path for e in catalog.entrypoints}, {"scripts/run_memory_worker.py"})
        self.assertTrue(all(e.path is None for e in catalog.entrypoints))
        self.assertEqual({e.line for e in catalog.entrypoints}, {8, 11})
        self.assertIn("scripts/run_memory_worker.py", catalog.to_prompt())
        self.assertIn("reach LLM clients indirectly", catalog.to_prompt())
        self.assertEqual(result["issues"], [])
        self.assertEqual(len(result["entrypoint_coverage_uncertainty"]), 2)
        self.assertTrue(all(e["entrypoint_changed"] is False for e in result["entrypoint_coverage_uncertainty"]))
        self.assertEqual(worker.read_text(), "from backend.app.config import load_settings\nsettings = load_settings()\n")

    def test_literal_service_workdir_and_module_startup_resolve_inside_checkout(self):
        self.write("service/app/main.py", "app = None\n")
        self.write("service/worker.py", "pass\n")
        self.write("deploy/api.service", f"[Service]\nWorkingDirectory={self.root}/service\nExecStart=/opt/python/bin/python3 -m uvicorn app.main:app\n")
        self.write("deploy.sh", "python3 -S -s -m service.worker\n")
        catalog = discover_consumed_requirements(self.root)
        self.assertEqual({e.path for e in catalog.entrypoints}, {"service/app/main.py", "service/worker.py"})

    def test_external_and_symlink_entrypoints_are_not_read_as_repository_code(self):
        self.write("service/worker.py", "pass\n")
        (self.root / "linked.py").symlink_to(self.root / "service/worker.py")
        self.write("deploy.sh", "python3 /etc/outside.py\npython3 linked.py\n")
        catalog = discover_consumed_requirements(self.root)
        self.assertEqual(len(catalog.entrypoints), 2)
        self.assertTrue(all(e.path is None and e.candidate_path is None for e in catalog.entrypoints))


if __name__ == "__main__":
    unittest.main()
