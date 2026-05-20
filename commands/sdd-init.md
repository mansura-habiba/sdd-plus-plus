---
description: Bootstrap this repo with the sdd-plus-plus governance framework — creates .governance/, AGENTS.md, .github/ templates, and contract tests.
argument-hint: "[--tier solo|team]"
allowed-tools:
  - Bash
---

Run `sdd init` against the current repo, then summarize what was created.

If the user passed `--tier team` (in `$ARGUMENTS`), append it to the command. Otherwise default to the solo tier.

After the command completes:

1. Run `sdd doctor` and surface any milestones not yet complete.
2. List the top-level files and directories created under `.governance/`.
3. Remind the user that the next step is usually to scaffold their first capability — they can invoke `@bob-scaffolder` for that.

Do not modify any existing files yourself — `sdd init` is the only writer in this command.
