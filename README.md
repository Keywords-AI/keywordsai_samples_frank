# Respan Agent

A first-party onboarding agent designed to integrate **Respan** into a repo and open a PR —
and **dogfoods** Respan's own stack: it runs on the **gateway** (cost control), is
**traced** (every session is a trace), with **evals** planned.

Planned form factor: a GitHub App (proactive, PR-producing — like Snyk/Dependabot, not CodeRabbit).
The full design is in **[ARCHITECTURE.md](ARCHITECTURE.md)**.

```
Install GitHub App → setup.respan.ai → pick repo → questionnaire → Submit
   → sandbox: clone → agent runs the /respan skill (Sonnet via gateway, traced)
   → commit branch → open PR → "your first trace →"
```

## Layout

| Path | What | Status |
|------|------|--------|
| `agent/` | Session runner + Claude Agent SDK loop + PR opener + CLI | **v0 (here now)** |
| `web/` | `setup.respan.ai` — auth, credits/BYOK, questionnaire, live progress | v1 |
| `github-app/` | App manifest + webhook handler | v1 |
| `evals/` | Sample-repo dataset + scorers (Respan experiments) | v2 |

## v0 — prove the loop (this milestone)

No GitHub App yet: v0a takes a repo URL + config JSON and produces a diff and controller
trace. v0b adds a commit, branch push, and draft PR using an explicitly supplied GitHub token.

For v0a, the **only secret needed is `RESPAN_API_KEY`** — the gateway routes the model
(no Anthropic key), and the same key sends the dogfood trace. v0b also needs a GitHub
token with repository contents and pull-request write access.

```bash
cd agent && pip install -e .
export RESPAN_API_KEY=...

# For Poetry/uv projects, create the lock-tool environment outside the repository:
respan-integration-agent setup --toolchain-dir /path/to/respan-lock-tools
export RESPAN_TOOLCHAIN_BIN=/path/to/respan-lock-tools/bin

# v0a — integrate + show the diff + emit a trace (no GitHub needed):
respan-integration-agent run --repo https://github.com/acme/app --config config.json

# v0b — also open a draft PR (set GH_TOKEN in your environment):
respan-integration-agent run --repo https://github.com/acme/app --config config.json --token-env GH_TOKEN
```

`config.json` is an `OnboardingRequest` ([config.py](agent/src/respan_integration_agent/config.py)):

```json
{ "repo_url": "https://github.com/acme/app", "product": "tracing", "tracing": { "mode": "auto" } }
```

The `/respan` skill is bundled and provisioned in a private per-run configuration. The
controller defaults to `claude-sonnet-5`, with no turn or spending cap; its 600-second
timeout is a hang guard. The runner checks required lock tools before model execution and
returns a partial diff with a nonzero result when dependency finalization fails.

v0b keeps GitHub credentials out of the model environment and checkout URLs. It replays
the finalized patch in a fresh checkout at the captured base commit, then creates a unique
branch and draft PR. A moved base or delivery failure returns a nonzero result with the
diff and any known branch/commit identity. It never updates the base or an existing branch.

### v0 checklist

- [x] Config contract (questionnaire as typed models)
- [x] Session skeleton: preflight → clone → agent → diff/PR
- [x] Wire `claude_agent_sdk.query` with the `/respan` skill + `ClaudeAgentSDKInstrumentor` (`agent.py`)
- [x] Route the model through the gateway — [already supported](https://respan.ai/docs/integrations/gateway/claude-agent-sdk); `RESPAN_API_KEY` only; turn/spending limits are optional
- [ ] **v0a smoke run** — throwaway repo → real diff + real trace *(needs only `RESPAN_API_KEY`)*
- [ ] Gateway preflight: verify credits/BYOK before spending a turn (`runner._preflight`)
- [ ] `open_pr`: push branch + create a draft PR via REST (`github.py`) — v0b live verification pending
- [x] Bundle and provision the `/respan` skill for local v0a runs
- [ ] Provision the `/respan` skill in the sandbox image (v1)

**v0a success = the agent integrates Respan + emits its own trace.  v0b adds the PR.**

v0a verification has exercised real controller runs, generated diffs, and dependency
checks. Target application execution and complete semantic trace acceptance remain
outstanding, so the smoke checklist item stays open. Follow the
[trace acceptance guide](INTEGRATION_TRACE_ACCEPTANCE_RULES.md) when judging trace correctness.

The [v0b smoke workflow](.github/workflows/v0b-smoke.yml) runs local regression tests and
an explicitly requested live check (manual dispatch, or a `[v0b-smoke]` commit on
`v0-checklist-implementation`). The live job needs the repository's `RESPAN_API_KEY` secret
and Actions permission to create PRs; it uses the built-in GitHub token. It verifies and
closes one temporary fixture PR, removes its two owned branches, and saves sanitized evidence.

## Dogfood hooks

- **Tracing:** the agent loop is instrumented (`respan-instrumentation-claude-agent-sdk`).
- **Gateway:** the agent's LLM calls route through the gateway; controller spending limits are optional.
- **Evals (planned):** `evals/` will score onboarding outcomes over a dataset of sample repos.
