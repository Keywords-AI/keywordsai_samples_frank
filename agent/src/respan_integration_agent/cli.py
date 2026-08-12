"""v0 entrypoint — run a session locally, before the GitHub App / dashboard exist.

    respan-integration-agent run --repo https://github.com/acme/app --token $GH_TOKEN --config config.json

`config.json` is an OnboardingRequest (see config.py). Example:

    {"repo_url": "https://github.com/acme/app", "product": "tracing",
     "tracing": {"mode": "auto"}}
"""

from __future__ import annotations

import argparse
import json
import sys

from .config import OnboardingRequest
from .runner import run_session


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="respan-integration-agent")
    sub = parser.add_subparsers(dest="cmd", required=True)
    run = sub.add_parser("run", help="onboard a repo and open a PR")
    run.add_argument("--repo", help="repo URL (overrides config.repo_url)")
    run.add_argument("--token", required=True, help="GitHub token with PR scope")
    run.add_argument("--config", required=True, help="path to an OnboardingRequest JSON")

    args = parser.parse_args(argv)
    data = json.loads(open(args.config).read())
    if args.repo:
        data["repo_url"] = args.repo
    req = OnboardingRequest.model_validate(data)

    result = run_session(req, github_token=args.token)
    print(f"PR:    {result.pr.url}")
    if result.trace_id:
        print(f"Trace: https://platform.respan.ai (session {result.trace_id})")
    print(result.summary)
    return 0


if __name__ == "__main__":
    sys.exit(main())
