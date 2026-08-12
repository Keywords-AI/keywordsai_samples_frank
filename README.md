# Respan Agent

A first-party onboarding agent that integrates **Respan** into a repo and opens a PR —
and **dogfoods** Respan's own stack: it runs on the **gateway** (cost control), is
**traced** (every session is a trace), and is scored by **evals**.

Form factor: a GitHub App (proactive, PR-producing — like Snyk/Dependabot, not CodeRabbit).
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

No GitHub App yet: pass a repo URL + token + config JSON and get a PR.

The **only secret needed is `RESPAN_API_KEY`** — the gateway routes the model (no Anthropic
key), and the same key sends the dogfood trace.

```bash
cd agent && pip install -e .
export RESPAN_API_KEY=...

# v0a — integrate + show the diff + emit a trace (no GitHub needed):
respan-integration-agent run --repo https://github.com/acme/app --config config.json

# v0b — also open a PR:
respan-integration-agent run --repo ... --config config.json --token "$GH_TOKEN"
```

`config.json` is an `OnboardingRequest` ([config.py](agent/src/respan_integration_agent/config.py)):

```json
{ "repo_url": "https://github.com/acme/app", "product": "tracing", "tracing": { "mode": "auto" } }
```

### v0 checklist
- [x] Config contract (questionnaire as typed models)
- [x] Session skeleton: preflight → clone → agent → diff/PR
- [x] Wire `claude_agent_sdk.query` with the `/respan` skill + `ClaudeAgentSDKInstrumentor` (`agent.py`)
- [x] Route the model through the gateway — [already supported](https://respan.ai/docs/integrations/gateway/claude-agent-sdk); `RESPAN_API_KEY` only, `max_turns` caps cost
- [ ] **v0a smoke run** — throwaway repo → real diff + real trace *(needs only `RESPAN_API_KEY`)*
- [ ] Gateway preflight: verify credits/BYOK before spending a turn (`runner._preflight`)
- [ ] `open_pr`: push branch + create PR via REST (`github.py`) — v0b
- [ ] Provision the `/respan` skill in the sandbox image (v1)

**v0a success = the agent integrates Respan + emits its own trace.  v0b adds the PR.**

## Dogfood hooks
- **Tracing:** the agent loop is instrumented (`respan-instrumentation-claude-agent-sdk`).
- **Gateway:** the agent's LLM calls route through the gateway with a per-user budget.
- **Evals:** `evals/` scores onboarding outcomes over a dataset of sample repos.
