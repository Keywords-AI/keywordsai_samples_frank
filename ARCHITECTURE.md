# Respan Agent — Architecture

A first-party onboarding agent that integrates **Respan** (tracing or gateway) into a
user's repository and opens a pull request. It **dogfoods** Respan's own stack: the
agent runs on the Respan **gateway** (cost control), is instrumented with Respan
**tracing** (every session is a trace), and is scored by Respan **evals**.

## Form factor — GitHub App (proactive, not reactive)

Think **Snyk / Dependabot**, not CodeRabbit. CodeRabbit is *reactive* (it reviews a PR
you opened). This agent is *proactive* — **it produces the PR**. So there is no
"PR created" trigger. The entry trigger is a **dashboard action** (the questionnaire
submit); GitHub's only jobs are repo access (clone) and PR creation.

```
1. Install "Respan Onboarding" GitHub App   → installation webhook → store install (repos + token)
2. setup.respan.ai dashboard → pick repo → fill QUESTIONNAIRE → Submit          ← the trigger
3. Session runner: sandbox → clone (installation token) → agent runs per answers
      → commit branch → open PR (GitHub API)
4. Dashboard shows: PR link + "your first trace →"
```

Reactivity has a place too, but **inverted**: comments on the PR *the agent created*
(`issue_comment` / `pull_request_review_comment`) let the agent iterate on its own PR.
That's v2.

## Why "git-cloud" (Model B)

The agent runs server-side, so the code (or the slice it needs) reaches the server.
Rather than tunnel into the user's laptop, the server talks to the **git remote**:
clone → work in an ephemeral sandbox → open a PR. The "how does the server reach the
laptop" problem disappears, and the LLM key never leaves the server.

## Credential / cost control

- The model key lives **only** in the ephemeral sandbox env.
- Every agent LLM call goes through the **Respan gateway** with a **per-user budget** →
  users never hold the key and cannot abuse LLM cost. (This is also the gateway dogfood.)
- The sandbox is torn down after each session; GitHub access is **PR-only** (no force-push).

### Dependency to resolve
The gateway is OpenAI-compatible (`/chat/completions`); the Claude Agent SDK speaks
Anthropic's Messages API. To route the agent through the gateway, the gateway needs an
**Anthropic-compatible endpoint** (`ANTHROPIC_BASE_URL`). Until then, v0 caps cost at the
**orchestrator** (max turns/tokens per session) and adds gateway-Anthropic as a fast-follow.

## The questionnaire (config contract)

The agent implements against a config, not mid-run guesses. A pre-scan pre-fills it
("detected LangChain + OpenAI, Python") so it's confirm-not-fill. See
[`agent/src/respan_integration_agent/config.py`](agent/src/respan_integration_agent/config.py).

- **Scope:** repo + branch · Tracing / Gateway / Both
- **Tracing** (= the Auto-vs-Full skill flow already shipped in the SDK):
  Auto (`Respan()`, flat) or Full (framework instrumentor + optional `@workflow`/`@task`
  decorators; which workflows) · env/service tags · endpoint
- **Gateway** (prep required first, else routed calls fail): funding = **Add credits** or
  **BYOK** · which providers/models · caching / fallbacks · repoint `base_url`

## Reuse (not rebuilt)

| Need | Reuse |
|------|-------|
| Onboarding logic | the **respan skill** (the agent runs it) |
| LLM cost control + routing | the **gateway** (per-user budget) |
| Tracing dogfood | `respan-instrumentation-claude-agent-sdk` |
| Quality signal | the **evals** platform |
| Cloud sandbox | **Railway** (already in use; Railway MCP wired) |

## Components

| Component | Responsibility | Tech |
|-----------|----------------|------|
| `agent/` | The session runner + Claude Agent SDK loop + PR opener (v0 lives here) | Python |
| `web/` | `setup.respan.ai` — auth, credits/BYOK, questionnaire, live progress | Next.js *(v1)* |
| `github-app/` | App manifest + webhook handler (install, PR-comment iterate) | *(v1/v2)* |
| `evals/` | Sample-repo dataset + scorers, run as Respan experiments | Python *(v2)* |

## Phases

- **v0 — prove the loop:** no GitHub App; pass repo URL + token + config JSON. Clone →
  Claude Agent SDK runs the skill (Sonnet-via-gateway, traced) → commit → open PR.
  *Success = a real PR + a real trace from a real agent run.*
- **v1 — the product:** GitHub App, `setup.respan.ai` sign-in + repo picker, the live
  progress UI, per-user gateway budget.
- **v2 — close the dogfood loop:** evals harness feeding back into the skill/prompt;
  comment-to-refine on the agent's PR.
