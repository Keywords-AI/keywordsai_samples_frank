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
trace. v0b will add automated PR creation; `open_pr` is not implemented yet.

The **only secret needed is `RESPAN_API_KEY`** — the gateway routes the model (no Anthropic
key), and the same key sends the dogfood trace.

```bash
cd agent && pip install -e .
export RESPAN_API_KEY=...

# For Poetry/uv projects, create the lock-tool environment outside the repository:
respan-integration-agent setup --toolchain-dir /path/to/respan-lock-tools
export RESPAN_TOOLCHAIN_BIN=/path/to/respan-lock-tools/bin

# v0a — integrate + show the diff + emit a trace (no GitHub needed):
respan-integration-agent run --repo https://github.com/acme/app --config config.json

# v0b — planned: also open a PR (not implemented yet):
# respan-integration-agent run --repo ... --config config.json --token "$GH_TOKEN"
```

`config.json` is an `OnboardingRequest` ([config.py](agent/src/respan_integration_agent/config.py)):

```json
{ "repo_url": "https://github.com/acme/app", "product": "tracing", "tracing": { "mode": "auto" } }
```

The `/respan` skill is bundled and provisioned in a private per-run configuration. The
controller defaults to `claude-sonnet-5`, with no turn or spending cap; its 600-second
timeout is a hang guard. The runner checks required lock tools before model execution and
returns a partial diff with a nonzero result when dependency finalization fails.

### v0 checklist

- [x] Config contract (questionnaire as typed models)
- [x] Session skeleton: preflight → clone → agent → diff/PR
- [x] Wire `claude_agent_sdk.query` with the `/respan` skill + `ClaudeAgentSDKInstrumentor` (`agent.py`)
- [x] Route the model through the gateway — [already supported](https://respan.ai/docs/integrations/gateway/claude-agent-sdk); `RESPAN_API_KEY` only; turn/spending limits are optional
- [ ] **v0a smoke run** — throwaway repo → real diff + real trace *(needs only `RESPAN_API_KEY`)*
- [ ] Gateway preflight: verify credits/BYOK before spending a turn (`runner._preflight`)
- [ ] `open_pr`: push branch + create PR via REST (`github.py`) — v0b
- [x] Bundle and provision the `/respan` skill for local v0a runs
- [ ] Provision the `/respan` skill in the sandbox image (v1)

**v0a success = the agent integrates Respan + emits its own trace.  v0b adds the PR.**

v0a verification has exercised real controller runs, generated diffs, and dependency
checks. Target application execution and complete semantic trace acceptance remain
outstanding, so the smoke checklist item stays open. Follow the
[trace acceptance guide](INTEGRATION_TRACE_ACCEPTANCE_RULES.md) when judging trace correctness.

## Dogfood hooks

- **Tracing:** the agent loop is instrumented (`respan-instrumentation-claude-agent-sdk`).
- **Gateway:** the agent's LLM calls route through the gateway; controller spending limits are optional.
- **Evals (planned):** `evals/` will score onboarding outcomes over a dataset of sample repos.
