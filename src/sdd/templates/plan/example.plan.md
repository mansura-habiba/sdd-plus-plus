---
plan_id: plan-example-001
task_id: EXAMPLE-1
capability: example-feature

generated_by:
  tool: human
  generated_at: "2026-05-19T10:00:00Z"

status: draft
accepted_by: ""
accepted_at: ""

# REQUIRED — the AI's pushback record. Populated BEFORE the plan is saved.
# Empty fields here mean the AI complied without thinking, which is a failure mode.
challenge:
  understood_request: |
    The user wants a working example plan file in the templates folder so adopters
    can see the expected shape. This is an artifact for new users, not a real
    implementation plan.
  concerns:
    - "If readers treat this as the canonical plan format and copy-paste it without editing, the framework will fill with stale example data. Mitigation: TODO sentinels in the body force editing."
    - "An example plan with status: draft and empty accepted_by may confuse the validator. We confirm: schema permits accepted_by='' when status=draft."
  alternatives_considered:
    - "Could omit the example plan entirely and only document the format in instructions.md — rejected because adopters learn faster from a worked example than from prose."

scope:
  in_scope:
    - "Ship a worked example of plan.md so adopters know what fields look like populated."
    - "Demonstrate the challenge block populated honestly."
  non_goals:
    - "This is a template — not a real plan against a real task."
    - "Do not implement anything from this plan; it is illustrative."

ai_context:
  required_reading:
    - .governance/wiki/principles.md
    - .governance/instructions.md
    - .governance/capabilities/example-feature/spec.md
  do_not_modify:
    - .governance/_schemas/
    - .governance/wiki/principles.md
  preferred_patterns:
    - "Use the YAML frontmatter format demonstrated by this file."
    - "Populate every required field honestly; AI may not skip the challenge block."
---

# Plan: example task

> This is an example plan to show the expected shape. Replace with a real plan when working a real task. Run `sdd plan new --task <task-id>` to scaffold a new one.

## What I'll do

A plan written by an AI assistant lays out concrete steps here:

1. Step one — files I'll create or change, with paths.
2. Step two — tests I'll write or satisfy, by case_id.
3. Step three — validations I'll run before claiming done.

## Files I'll touch

- `path/to/file_one.py` — what changes and why
- `path/to/file_two.py` — what changes and why

## Tests I'll satisfy

- `tests/contract/test_example_feature.py::test_happy_path` (case_id: positive-happy-path)
- `tests/contract/test_example_feature.py::test_rejects_invalid_input` (case_id: rejects-invalid-input)

## Risks I see

- TODO — risks the AI identifies. If the AI says "no risks," that's itself a signal worth questioning.

## Things I will NOT do (reinforcing non_goals)

- Will not touch paths listed in `ai_context.do_not_modify`.
- Will not implement anything that satisfies `non_goals` instead of `in_scope`.
- Will not mark this plan as `accepted` myself — that is the human's job via `sdd plan accept --id <plan_id> --by @<human>`.

## How to accept this plan

A human reviewer reads the challenge block, the scope, and the file list. If acceptable:

```bash
sdd plan accept --id plan-example-001 --by @your-handle
```

That command sets `accepted_by` and `accepted_at` in the frontmatter, advancing status to `accepted`. Only then may implementation start.
