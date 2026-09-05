"""Exercise controller limits without making model calls or cloning a target."""
from __future__ import annotations

import asyncio
import ast
import base64
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from dataclasses import dataclass
import io
import importlib.util
from importlib.metadata import metadata
import os
from pathlib import Path
import tempfile
import sys
import textwrap
import tomllib
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from urllib.parse import quote

from pydantic import ValidationError
from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet

from respan_integration_agent import agent, cli, runner
from respan_integration_agent.config import ControllerConfig, OnboardingRequest
from respan_integration_agent.deployment import DeploymentCatalog
from respan_integration_agent.toolchain import ToolchainReceipt


def request(**controller):
    return OnboardingRequest(
        repo_url="https://example.invalid/repo", product="tracing",
        tracing={"mode": "auto", "service_name": "test-service", "environment": "test"},
        controller=controller,
    )


@dataclass
class Result:
    result: str = "Applied tracing"
    is_error: bool = False
    subtype: str = "success"
    errors: list[str] | None = None
    api_error_status: int | None = None


class ControllerConfigTests(unittest.TestCase):
    def test_defaults_do_not_hide_turn_or_cost_regressions(self):
        self.assertEqual(request().controller.model_dump(), {
            "model": "claude-sonnet-5", "max_turns": None,
            "max_budget_usd": None, "timeout_seconds": 600,
        })

    def test_invalid_config_is_rejected(self):
        for limits in (
            {"model": ""}, {"model": " sonnet"}, {"max_turns": 0},
            {"max_turns": -1}, {"max_turns": 1.5}, {"max_turns": True},
            {"max_budget_usd": 0}, {"max_budget_usd": float("inf")},
            {"max_budget_usd": float("nan")}, {"max_budget_usd": True},
            {"timeout_seconds": -1}, {"timeout_seconds": True},
            {"timeout_seconds": float("inf")}, {"fallback_model": "sonnet"},
        ):
            with self.subTest(limits=limits), self.assertRaises(ValidationError):
                ControllerConfig(**limits)

    def test_cli_overrides_config_without_losing_other_limits(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / "config.json"
            config.write_text(request(max_turns=7, timeout_seconds=123).model_dump_json())
            result = runner.SessionResult("done", None, ["main.py"], "diff", None)
            with patch.dict(os.environ, {"RESPAN_API_KEY": "unit-test-placeholder"}), \
                    patch.object(cli, "run_session", return_value=result) as run, \
                    redirect_stdout(io.StringIO()):
                code = cli.main([
                    "run", "--config", str(config), "--model", "claude-haiku-4-5-20251001",
                    "--max-budget-usd", "0.12",
                ])
            self.assertEqual(code, 0)
            self.assertEqual(run.call_args.args[0].controller.model_dump(), {
                "model": "claude-haiku-4-5-20251001", "max_turns": 7,
                "max_budget_usd": 0.12, "timeout_seconds": 123,
            })

    def test_invalid_cli_limits_fail_before_session(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / "config.json"
            config.write_text(request().model_dump_json())
            for args in (
                ["--max-turns", "0"], ["--max-turns", "1.5"],
                ["--max-budget-usd", "nan"], ["--max-budget-usd", "-1"],
                ["--timeout-seconds", "inf"], ["--timeout-seconds", "0"],
                ["--model", ""],
            ):
                with self.subTest(args=args), \
                        patch.dict(os.environ, {"RESPAN_API_KEY": "unit-test-placeholder"}), \
                        patch.object(cli, "run_session") as run, \
                        redirect_stderr(io.StringIO()), \
                        self.assertRaises(SystemExit) as raised:
                    cli.main(["run", "--config", str(config), *args])
                self.assertEqual(raised.exception.code, 2)
                run.assert_not_called()

    def test_session_passes_every_limit_to_agent(self):
        req = request(model="haiku", max_turns=9, max_budget_usd=0.11, timeout_seconds=45)

        @contextmanager
        def checkout(*args, **kwargs):
            yield Path("/unused-unit-test-checkout")

        with patch.object(runner, "validate_skill_source"), \
                patch.object(runner, "checkout", checkout), \
                patch.object(runner, "preflight_toolchain", return_value=ToolchainReceipt("/unused-unit-test-checkout", (), {}, {}, {})), \
                patch.object(runner, "discover_consumed_requirements", return_value=DeploymentCatalog()), \
                patch.object(runner, "repair_consumed_requirements", return_value={"issues": [], "repairs": []}), \
                patch.object(runner, "finalize_lockfiles", return_value=[]), \
                patch.object(runner, "_git_changed", return_value=["main.py"]), \
                patch.object(runner, "_git_diff", return_value="diff"), \
                patch.object(runner, "run_agent", return_value=agent.AgentResult("done", ["main.py"], None)) as run:
            runner.run_session(req, respan_api_key="unit-test-placeholder")
        self.assertEqual({k: v for k, v in run.call_args.kwargs.items() if k != "setup_context"}, {
            "respan_api_key": "unit-test-placeholder", **req.controller.model_dump(),
        })
        self.assertIn("Lock tools verified by the runner", run.call_args.kwargs["setup_context"])

    def test_corrupt_bundled_skill_stops_before_clone(self):
        with patch.object(runner, "validate_skill_source", side_effect=ValueError("Bundled skill hash mismatch")), \
                patch.object(runner, "checkout") as clone, patch.object(runner, "run_agent") as model:
            with self.assertRaisesRegex(ValueError, "Bundled skill hash mismatch"):
                runner.run_session(request(), respan_api_key="unit-test-placeholder")
        clone.assert_not_called()
        model.assert_not_called()

    def test_default_skill_directory_matches_provisioner_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill = Path(tmp) / ".claude" / "skills" / "respan"
            (skill / "references").mkdir(parents=True)
            (skill / "SKILL.md").write_text("fixture")
            (skill / "references/tracing.md").write_text("fixture")
            with patch.object(Path, "home", return_value=Path(tmp)), patch.dict(os.environ, {}, clear=True):
                self.assertEqual(agent.validate_skill_directory(), skill.resolve())

    def test_direct_agent_invalid_limits_stop_before_instrumentation(self):
        with patch.dict("sys.modules", {"respan": SimpleNamespace(Respan=None)}), \
                self.assertRaises(ValidationError):
            agent.run_agent(Path("/unused"), request(), respan_api_key="unit-test-placeholder", max_turns=0)

    def test_supplied_initializer_keys_match_installed_sdk_signatures(self):
        # Inspect source without importing or initializing telemetry.
        def constructor_keys(package, filename, class_name):
            spec = importlib.util.find_spec(package)
            self.assertIsNotNone(spec, f"Install the declared dependency {package}")
            source = Path(spec.origin).parent / filename
            module = ast.parse(source.read_text())
            cls = next(node for node in module.body if isinstance(node, ast.ClassDef) and node.name == class_name)
            ctor = next(node for node in cls.body if isinstance(node, ast.FunctionDef) and node.name == "__init__")
            return {argument.arg for argument in ctor.args.args + ctor.args.kwonlyargs}

        facade = constructor_keys("respan", "_core.py", "Respan")
        telemetry = constructor_keys("respan_tracing", "main.py", "RespanTelemetry")
        self.assertTrue({"api_key", "base_url", "app_name", "environment"} <= facade)
        self.assertTrue({"tags", "endpoint", "service_name"}.isdisjoint(facade | telemetry))

    def test_prompt_initializer_is_opt_in_and_does_not_hide_missing_dependency(self):
        snippet = agent.PYTHON_AUTO_CONTRACT.split("```python\n", 1)[1].split("```", 1)[0]
        code = compile(snippet, "<supplied-python-initializer>", "exec")
        with patch.dict(os.environ, {}, clear=True), patch.dict("sys.modules", {"respan": None}):
            exec(code, {})  # No key must not attempt the unavailable SDK import.
        calls = []

        def respan(*, api_key):
            calls.append(api_key)

        with patch.dict(os.environ, {"RESPAN_API_KEY": "unit-test-placeholder"}, clear=True), \
                patch.dict("sys.modules", {"respan": SimpleNamespace(Respan=respan)}):
            exec(code, {})
        self.assertEqual(calls, ["unit-test-placeholder"])
        with patch.dict(os.environ, {"RESPAN_API_KEY": "unit-test-placeholder"}, clear=True), \
                patch.dict("sys.modules", {"respan": None}), \
                self.assertRaises(ModuleNotFoundError):
            exec(code, {})

    def test_conditional_dependency_matches_sdk_python_metadata(self):
        supported = SpecifierSet(metadata("respan-ai")["Requires-Python"])
        self.assertEqual(supported, SpecifierSet(agent.PYTHON_SDK_REQUIRES))
        dependency = Requirement(agent.PYTHON_SDK_CONDITIONAL_DEPENDENCY)
        self.assertEqual(dependency.name, "respan-ai")
        self.assertEqual(str(dependency.specifier), "==4.2.3")
        self.assertIsNotNone(dependency.marker)
        # The dependency marker preserves a target's broader >=3.10,<4.0 declaration
        # while installing this SDK only on versions accepted by its own metadata.
        for version in ("3.9", "3.10", "3.11", "3.12", "3.13", "3.14", "3.15", "4.0"):
            with self.subTest(version=version):
                self.assertEqual(dependency.marker.evaluate({"python_version": version}), supported.contains(version + ".0"))
        poetry = tomllib.loads(agent.PYTHON_SDK_POETRY_DEPENDENCY)["respan-ai"]
        self.assertEqual(poetry["version"], "4.2.3")
        self.assertEqual(SpecifierSet(poetry["python"]), supported)

    def test_prompt_initializer_does_not_shadow_enclosing_function_names(self):
        snippet = agent.PYTHON_AUTO_CONTRACT.split("```python\n", 1)[1].split("```", 1)[0]
        source = (
            "def startup():\n"
            "    before = (os, sys, Respan)\n"
            + textwrap.indent(snippet, "    ")
            + "    after = (os, sys, Respan)\n"
            "    return before, after\n"
        )
        existing_respan = object()
        for enabled in (False, True):
            with self.subTest(enabled=enabled):
                calls = []
                namespace = {"os": os, "sys": sys, "Respan": existing_respan}
                sdk = SimpleNamespace(Respan=lambda **kwargs: calls.append(kwargs)) if enabled else None
                environment = {"RESPAN_API_KEY": "unit-test-placeholder"} if enabled else {}
                with patch.dict(os.environ, environment, clear=True), patch.dict("sys.modules", {"respan": sdk}):
                    exec(compile(source, "<initializer-in-existing-function>", "exec"), namespace)
                    before, after = namespace["startup"]()
                self.assertEqual(before, (os, sys, existing_respan))
                self.assertEqual(after, before)
                self.assertEqual(len(calls), int(enabled))

    def test_prompt_initializer_preserves_unsupported_runtime_without_key(self):
        snippet = agent.PYTHON_AUTO_CONTRACT.split("```python\n", 1)[1].split("```", 1)[0]
        code = compile(snippet, "<supplied-python-initializer>", "exec")
        for version in ((3, 10), (3, 11), (3, 12), (3, 13), (3, 14), (3, 15)):
            with self.subTest(version=version):
                with patch.object(sys, "version_info", version), \
                        patch.dict(os.environ, {}, clear=True), \
                        patch.dict("sys.modules", {"respan": None}):
                    exec(code, {})
                calls = []
                sdk = SimpleNamespace(Respan=lambda **kwargs: calls.append(kwargs))
                with patch.object(sys, "version_info", version), \
                        patch.dict(os.environ, {"RESPAN_API_KEY": "unit-test-placeholder"}, clear=True), \
                        patch.dict("sys.modules", {"respan": sdk}):
                    if (3, 11) <= version < (3, 14):
                        exec(code, {})
                        self.assertEqual(len(calls), 1)
                    else:
                        with self.assertRaisesRegex(RuntimeError, "requires Python >=3.11,<3.14"):
                            exec(code, {})
                        self.assertEqual(calls, [])
class SDKControlTests(unittest.IsolatedAsyncioTestCase):
    async def test_relative_skill_directory_is_absolute_in_sdk_and_prompt(self):
        captured = {}

        async def query(**kwargs):
            captured.update(kwargs)
            yield Result()

        module = SimpleNamespace(query=query, ClaudeAgentOptions=SimpleNamespace, ResultMessage=Result)
        respan = SimpleNamespace(get_client=lambda: SimpleNamespace(get_current_trace_id=lambda: None))
        expected = (Path.cwd() / "relative-config").resolve()
        with patch.dict("sys.modules", {"claude_agent_sdk": module, "respan": respan}), \
                patch.dict(os.environ, {"CLAUDE_CONFIG_DIR": "relative-config"}), \
                patch.object(agent, "_git_changed", return_value=["main.py"]):
            await agent._run(Path("/different-target-cwd"), request(), "unit-test-placeholder", ControllerConfig())
        self.assertEqual(captured["options"].env["CLAUDE_CONFIG_DIR"], str(expected))
        self.assertEqual(captured["options"].add_dirs, [str(expected / "skills/respan")])
        self.assertIn(str(expected / "skills/respan/references/tracing.md"), captured["prompt"])

    async def test_error_result_drains_query_and_redacts_failure_details(self):
        events = []
        key = "unit/test+key"
        encoded = base64.b64encode(key.encode()).decode()

        async def query(**kwargs):
            try:
                yield Result(
                    result=f"Connection failed for {key}", is_error=True, subtype="success",
                    errors=[f"Retry failed {quote(key, safe='')} {encoded}"], api_error_status=503,
                )
                events.append("drained")
            finally:
                events.append("closed")

        module = SimpleNamespace(query=query, ClaudeAgentOptions=SimpleNamespace, ResultMessage=Result)
        with patch.dict("sys.modules", {"claude_agent_sdk": module}), \
                patch.dict(os.environ, {"CLAUDE_CONFIG_DIR": "/isolated/claude"}), \
                patch.object(agent, "_git_changed") as changes:
            with self.assertRaises(RuntimeError) as raised:
                await agent._run(Path("/unused"), request(), key, ControllerConfig())
        self.assertEqual(events, ["drained", "closed"])
        message = str(raised.exception)
        self.assertIn("Controller failed [HTTP 503]: Connection failed", message)
        self.assertNotIn("Controller stopped: success", message)
        for value in (key, quote(key, safe=""), encoded):
            self.assertNotIn(value, message)
        changes.assert_not_called()

    async def test_default_sdk_run_has_no_turn_or_budget_cap(self):
        captured = {}

        async def query(**kwargs):
            captured.update(kwargs)
            yield Result()

        module = SimpleNamespace(query=query, ClaudeAgentOptions=SimpleNamespace, ResultMessage=Result)
        respan = SimpleNamespace(get_client=lambda: SimpleNamespace(get_current_trace_id=lambda: None))
        with patch.dict("sys.modules", {"claude_agent_sdk": module, "respan": respan}), \
                patch.dict(os.environ, {"CLAUDE_CONFIG_DIR": "/isolated/claude"}), \
                patch.object(agent, "_git_changed", return_value=["main.py"]):
            await agent._run(Path("/unused"), request(), "unit-test-placeholder", ControllerConfig())
        self.assertIsNone(captured["options"].max_turns)
        self.assertIsNone(captured["options"].max_budget_usd)
        self.assertEqual(captured["options"].model, "claude-sonnet-5")

    async def test_sdk_receives_model_budget_turns_skill_access_and_tool_profile(self):
        captured = {}

        async def query(**kwargs):
            captured.update(kwargs)
            yield Result()

        module = SimpleNamespace(query=query, ClaudeAgentOptions=SimpleNamespace, ResultMessage=Result)
        limits = ControllerConfig(model="claude-sonnet-5", max_turns=5, max_budget_usd=0.09, timeout_seconds=2)
        respan = SimpleNamespace(get_client=lambda: SimpleNamespace(get_current_trace_id=lambda: None))
        with patch.dict("sys.modules", {"claude_agent_sdk": module, "respan": respan}), \
                patch.dict(os.environ, {"CLAUDE_CONFIG_DIR": "/isolated/claude"}), \
                patch.object(agent, "_git_changed", return_value=["main.py"]):
            result = await agent._run(Path("/unused"), request(), "unit-test-placeholder", limits)
        options = captured["options"]
        self.assertEqual(options.model, "claude-sonnet-5")
        self.assertEqual(options.max_turns, 5)
        self.assertEqual(options.max_budget_usd, 0.09)
        self.assertEqual(options.add_dirs, ["/isolated/claude/skills/respan"])
        self.assertEqual(options.tools, ["Skill", "Read", "Glob", "Grep", "Edit", "Write", "Bash"])
        self.assertFalse(hasattr(options, "disallowed_tools"))
        self.assertFalse(hasattr(options, "fallback_model"))
        self.assertFalse(hasattr(options, "effort"))
        self.assertEqual(options.permission_mode, "acceptEdits")
        self.assertEqual(options.env["ANTHROPIC_BASE_URL"], f"{agent.RESPAN_BASE_URL}/anthropic/")
        self.assertIn("Target repository root: /unused.", captured["prompt"])
        self.assertIn("Skill documentation directory: /isolated/claude/skills/respan.", captured["prompt"])
        self.assertIn("/isolated/claude/skills/respan/references/tracing.md", captured["prompt"])
        self.assertEqual(result.summary, "Applied tracing")

    async def test_timeout_closes_query_and_reports_failure(self):
        closed = []

        async def query(**kwargs):
            try:
                await asyncio.sleep(1)
                yield Result()
            finally:
                closed.append(True)

        module = SimpleNamespace(query=query, ClaudeAgentOptions=SimpleNamespace, ResultMessage=Result)
        with patch.dict("sys.modules", {"claude_agent_sdk": module}), \
                patch.dict(os.environ, {"CLAUDE_CONFIG_DIR": "/isolated/claude"}), \
                patch.object(agent, "_git_changed") as changes:
            with self.assertRaisesRegex(TimeoutError, "exceeded 0.01 second"):
                await agent._run(Path("/unused"), request(), "unit-test-placeholder", ControllerConfig(timeout_seconds=0.01))
        self.assertEqual(closed, [True])
        changes.assert_not_called()

    async def test_budget_error_does_not_return_success_or_retry(self):
        calls = []

        async def query(**kwargs):
            calls.append(kwargs)
            yield Result(result="", is_error=True, subtype="error_max_budget_usd")

        module = SimpleNamespace(query=query, ClaudeAgentOptions=SimpleNamespace, ResultMessage=Result)
        with patch.dict("sys.modules", {"claude_agent_sdk": module}), \
                patch.dict(os.environ, {"CLAUDE_CONFIG_DIR": "/isolated/claude"}), \
                patch.object(agent, "_git_changed") as changes:
            with self.assertRaisesRegex(RuntimeError, "error_max_budget_usd"):
                await agent._run(Path("/unused"), request(), "unit-test-placeholder", ControllerConfig(max_budget_usd=0.09))
        self.assertEqual(len(calls), 1)
        changes.assert_not_called()


if __name__ == "__main__":
    unittest.main()
