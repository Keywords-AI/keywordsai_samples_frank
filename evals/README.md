# evals (v2) — close the dogfood loop

A dataset of sample repos (py/ts × direct-SDK / LangChain / agents / etc.) and scorers,
run as Respan **experiments**:
- integration applied correctly (build/typecheck passes)?
- did a real trace / gateway log actually appear in the account?
- time-to-first-signal
- PR quality (diff minimal, description accurate)

Results feed back into the skill/prompt. Uses the Respan evals platform + MCP tools.
