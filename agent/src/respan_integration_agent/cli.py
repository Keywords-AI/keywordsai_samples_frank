"""v0 entrypoint — run a session locally, before the platform UI exists.

    export RESPAN_API_KEY=...            # the only secret needed (gateway handles the model)

    # v0a — just integrate + show the diff + emit a trace (no GitHub needed):
    respan-integration-agent run --repo https://github.com/acme/app --config config.json

    # v0b — also open a draft PR, reading the credential from the named environment variable:
    respan-integration-agent run --repo ... --config config.json --token-env GH_TOKEN

`config.json` is an OnboardingRequest (see config.py), e.g.:

    {"repo_url": "https://github.com/acme/app", "product": "tracing", "tracing": {"mode": "auto"}}
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from pydantic import ValidationError

from .config import OnboardingRequest
from .runner import run_session, _redact_secrets
from .toolchain import ToolchainError, bootstrap_toolchain
from .github import GitHubDeliveryError


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="respan-integration-agent")
    sub = parser.add_subparsers(dest="cmd", required=True)
    setup = sub.add_parser("setup", help="install the pinned lock tools in a private environment")
    setup.add_argument("--toolchain-dir", required=True, type=Path,
                       help="new directory for the managed Poetry/uv environment")
    run = sub.add_parser("run", help="onboard a repo (v0a: diff+trace, v0b: +PR)")
    run.add_argument("--repo", help="repo URL (overrides config.repo_url)")
    run.add_argument("--config", required=True, help="path to an OnboardingRequest JSON")
    credential = run.add_mutually_exclusive_group()
    credential.add_argument("--token", help="GitHub token (legacy argument); prefer --token-env to keep it out of argv")
    credential.add_argument("--token-env", metavar="NAME", help="explicit v0b opt-in: read GitHub token from environment variable NAME")
    run.add_argument("--model", help="controller model (default: claude-sonnet-5)")
    run.add_argument("--max-turns", type=int, help="optional positive operator turn limit (default: none)")
    run.add_argument("--max-budget-usd", type=float, help="optional positive SDK budget in USD (default: none)")
    run.add_argument("--timeout-seconds", type=float, help="positive hang timeout (default: 600)")

    args = parser.parse_args(argv)

    if args.cmd == "setup":
        try:
            receipt = bootstrap_toolchain(args.toolchain_dir)
        except (ToolchainError, ValueError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        print(json.dumps(receipt, indent=2))
        print(f"Set RESPAN_TOOLCHAIN_BIN to {receipt['tool_bin']} for subsequent runs.")
        return 0

    respan_api_key = os.environ.get("RESPAN_API_KEY")
    if not respan_api_key:
        print("error: set RESPAN_API_KEY (the gateway handles the model — no Anthropic key needed)",
              file=sys.stderr)
        return 2

    github_token = args.token
    if args.token_env:
        github_token = os.environ.get(args.token_env)
        if not github_token:
            print("error: the selected GitHub token environment variable is unset or empty", file=sys.stderr)
            return 2

    with open(args.config) as config_file:
        data = json.load(config_file)
    if args.repo:
        data["repo_url"] = args.repo
    overrides = {
        key: value
        for key in ("model", "max_turns", "max_budget_usd", "timeout_seconds")
        if (value := getattr(args, key)) is not None
    }
    if overrides:
        controller = data.get("controller", {})
        if not isinstance(controller, dict):
            parser.error("config.controller must be an object")
        data["controller"] = {**controller, **overrides}
    try:
        req = OnboardingRequest.model_validate(data)
    except ValidationError as exc:
        parser.error(str(exc))

    try:
        result = run_session(req, respan_api_key=respan_api_key, github_token=github_token)
    except (ToolchainError, GitHubDeliveryError, ValueError) as exc:
        print("error: " + _redact_secrets(str(exc), respan_api_key, github_token), file=sys.stderr)
        return 2

    print(f"\nchanged {len(result.changed_files)} file(s): {', '.join(result.changed_files)}")
    if result.trace_id:
        print(f"trace:  https://platform.respan.ai  (session {result.trace_id})")
    if result.pr:
        print(f"PR:     {result.pr.url}")
    else:
        print("\n--- diff (v0a; pass --token-env NAME to open a draft PR) ---")
        print(result.diff)
    print("\nsetup verification: " + json.dumps(result.setup_receipt, sort_keys=True))
    if result.delivery_receipt:
        print("\nPR delivery: " + json.dumps(result.delivery_receipt, sort_keys=True))
    if result.validation_errors:
        print("\nPartial integration: validation or PR delivery failed.", file=sys.stderr)
        for error in result.validation_errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(f"\n{result.summary}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
