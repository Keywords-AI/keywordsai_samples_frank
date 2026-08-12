"""v0 entrypoint — run a session locally, before the platform UI exists.

    export RESPAN_API_KEY=...            # the only secret needed (gateway handles the model)

    # v0a — just integrate + show the diff + emit a trace (no GitHub needed):
    respan-integration-agent run --repo https://github.com/acme/app --config config.json

    # v0b — also open a PR:
    respan-integration-agent run --repo ... --config config.json --token $GH_TOKEN

`config.json` is an OnboardingRequest (see config.py), e.g.:

    {"repo_url": "https://github.com/acme/app", "product": "tracing", "tracing": {"mode": "auto"}}
"""

from __future__ import annotations

import argparse
import json
import os
import sys

from .config import OnboardingRequest
from .runner import run_session


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="respan-integration-agent")
    sub = parser.add_subparsers(dest="cmd", required=True)
    run = sub.add_parser("run", help="onboard a repo (v0a: diff+trace, v0b: +PR)")
    run.add_argument("--repo", help="repo URL (overrides config.repo_url)")
    run.add_argument("--config", required=True, help="path to an OnboardingRequest JSON")
    run.add_argument("--token", help="GitHub token (PR scope) — omit for v0a (diff only)")

    args = parser.parse_args(argv)

    respan_api_key = os.environ.get("RESPAN_API_KEY")
    if not respan_api_key:
        print("error: set RESPAN_API_KEY (the gateway handles the model — no Anthropic key needed)",
              file=sys.stderr)
        return 2

    data = json.loads(open(args.config).read())
    if args.repo:
        data["repo_url"] = args.repo
    req = OnboardingRequest.model_validate(data)

    result = run_session(req, respan_api_key=respan_api_key, github_token=args.token)

    print(f"\nchanged {len(result.changed_files)} file(s): {', '.join(result.changed_files)}")
    if result.trace_id:
        print(f"trace:  https://platform.respan.ai  (session {result.trace_id})")
    if result.pr:
        print(f"PR:     {result.pr.url}")
    else:
        print("\n--- diff (v0a; pass --token to open a PR) ---")
        print(result.diff)
    print(f"\n{result.summary}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
