---
description: Validate every YAML artifact under .governance/ against its schema and cross-references.
allowed-tools:
  - Bash
  - Read
---

Run `sdd validate` and report the results.

If it passes, say so concisely and stop.

If it fails:

1. List each error with the file path and the schema field that failed.
2. For orphan assertion errors, point to the acceptance file and the `case_id` involved.
3. For broken `acceptance_refs`, point to the task card and the missing `case_id`.
4. Do not attempt to fix the errors yourself — surface them and offer to hand off to `@bob-scaffolder` (for schema/structural fixes) or `@dana-reviewer` (for status/finding issues).
