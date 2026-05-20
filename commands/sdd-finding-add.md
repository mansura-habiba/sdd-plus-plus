---
description: Record a new finding — the reusable judgment-call layer in sdd-plus-plus.
argument-hint: "[--from-task TASK-ID] [--capability CAPABILITY-NAME]"
allowed-tools:
  - Bash
  - Read
  - Write
---

Help the user record a finding. Findings are the LLM-wiki layer — they capture decisions and trade-offs that future task cards and AI assistants should respect.

Workflow:

1. Ask the user for the finding's `title`, `context` (what situation prompted it), `decision` (what was decided), and `consequences` (what this means for future work). A finding without consequences is a comment, not a finding — push back if consequences are vague.

2. If `$ARGUMENTS` contains `--from-task`, run `sdd findings add --from-task <id>` to pre-fill from task context. If `--capability` was passed, ensure the resulting finding links to that capability.

3. Before writing, check for duplicates: `sdd findings list --capability <name>` and surface any finding that overlaps. If overlap exists, ask whether to merge or proceed with a new finding.

4. Hand off to `@dana-reviewer` for ingestion (cross-referencing, validation, capability spec updates).

Do not write findings without all four fields populated.
