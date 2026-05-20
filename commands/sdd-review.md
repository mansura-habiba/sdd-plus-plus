---
description: Run a structured peer review on a task card against the framework's contracts — hands off to Dana the Reviewer.
argument-hint: "<task-id>"
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash
---

Open a review session for the task card referenced in `$ARGUMENTS`.

1. Verify the task card exists under `.governance/tasks/` or as an issue body. If `$ARGUMENTS` is empty, list task cards currently in `review` status and ask which to open.

2. Hand off to `@dana-reviewer` with the task ID. Dana will read the full chain (task card → acceptance → tests → capability spec → diff → findings) and produce a structured review with acceptance coverage, schema validation, AI-resistance check, capability fit, finding gaps, and a status recommendation.

3. Do not approve or reject the task card yourself. Surface Dana's recommendation and wait for the user's call.
