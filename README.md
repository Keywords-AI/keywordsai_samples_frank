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

```bash
cd agent && pip install -e .
respan-integration-agent run --repo https://github.com/acme/app --token "$GH_TOKEN" --config config.json
```

`config.json` is an `OnboardingRequest` ([config.py](agent/src/respan_integration_agent/config.py)):

```json
{ "repo_url": "https://github.com/acme/app", "product": "tracing", "tracing": { "mode": "auto" } }
```

### v0 checklist
- [x] Config contract (questionnaire as typed models)
- [x] Session skeleton: preflight → clone → agent → commit → PR
- [ ] Wire `claude_agent_sdk.query` with the `/respan` skill + `ClaudeAgentSDKInstrumentor` (`agent.py`)
- [ ] Route the model through the gateway (`ANTHROPIC_BASE_URL`) — **needs the gateway's Anthropic-compatible endpoint**; until then cap turns/tokens in `runner._preflight`
- [ ] Gateway preflight: verify credits/BYOK before spending a token (`runner._preflight`)
- [ ] `open_pr`: push branch + create PR via REST (`github.py`)
- [ ] Smoke run against a throwaway repo → real PR + real trace

**Success = a real PR opened by the agent + the trace of that very session.**

## Dogfood hooks
- **Tracing:** the agent loop is instrumented (`respan-instrumentation-claude-agent-sdk`).
- **Gateway:** the agent's LLM calls route through the gateway with a per-user budget.
- **Evals:** `evals/` scores onboarding outcomes over a dataset of sample repos.
