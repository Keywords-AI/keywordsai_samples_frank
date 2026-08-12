# github-app (v1 / v2)

GitHub App "Respan Onboarding" — the access + PR-opening mechanism (proactive, like
Snyk/Dependabot; there is no "PR created" trigger).

- **v1:** `installation` webhook (store repos + installation token). The dashboard
  questionnaire-submit is the entry trigger; the app token clones + opens the PR.
- **v2:** `issue_comment` / `pull_request_review_comment` on the agent's OWN PR →
  the agent iterates (the CodeRabbit-style pattern, inverted).

Contains the App manifest + a thin webhook handler that hands sessions to `agent/`.
