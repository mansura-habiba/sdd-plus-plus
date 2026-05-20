---
description: Run the sdd-plus-plus adoption diagnostic and report which milestones are complete vs missing.
allowed-tools:
  - Bash
---

Run `sdd doctor` and produce a short report:

1. The milestones marked complete.
2. The milestones still missing, in priority order.
3. For each missing milestone, the one-line action that would unblock it (e.g. "no capability specs yet — invoke @bob-scaffolder to draft the first one").

Do not run any other commands. Do not write any files.
