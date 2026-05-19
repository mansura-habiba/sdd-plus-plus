---
id: example-feature
name: "Example Feature"
purpose: |
  This is a starter capability. Rename the folder to your real capability id, then edit
  every field. The purpose field must be at least 100 characters of real content —
  no "TBD", no "see X", no placeholder. Describe what would break in your product if
  this capability stopped working.
status: active
tier: team

owner:
  human: "@TODO-your-handle"

contract:
  inputs:
    - name: example_request
      shape: "TODO — type name or schema reference"
      description: "What this capability accepts."
  outputs:
    - name: example_result
      shape: "TODO — type name or schema reference"
      description: "What this capability returns."
  invariants:
    - "TODO — a property that holds across all executions of this capability."

cases:
  - id: positive-happy-path
    kind: positive
    priority: critical
    description: "TODO — the canonical happy-path test."
    test_id: "tests/contract/test_example_feature.py::test_happy_path"
  - id: rejects-invalid-input
    kind: negative
    priority: high
    description: "TODO — invalid input is rejected, not crashed on."
    test_id: "tests/contract/test_example_feature.py::test_rejects_invalid_input"

definition_of_done:
  conditions:
    - id: all-cases-pass
      statement: "Every case above has a passing test."
      verifiable_by: contract_test
      evidence_ref: "tests/contract/test_example_feature.py"
    - id: schema-valid
      statement: "This spec.md frontmatter validates against the capability_spec schema."
      verifiable_by: schema_validation

non_functional:
  performance: "TODO — e.g. p95 < 200ms"
  security: "TODO — e.g. inputs sanitized, no eval"

tasks_must:
  use_patterns:
    - "TODO — design patterns required for tasks in this capability area"
  avoid_dependencies:
    - "TODO — libraries tasks must not introduce"

forbidden:
  - "TODO — at least one behavior NO task within this capability does, ever."
---

# Example Feature

> Replace this entire file with your real capability. Below is what each section is for.

## Purpose

The frontmatter's `purpose` is the one-paragraph machine-readable summary. Use *this* section for the longer human-readable narrative: why this capability exists, who it serves, what would break without it. Keep it tight — the contract is in the frontmatter.

## Design notes

Architectural choices that don't fit in frontmatter — why we chose pattern X over Y, why a particular library, what the tradeoffs are. This is the section where someone joining the team in six months catches up.

## Open questions

Things you're not yet sure about. Pin them here so they don't get lost.

## Related findings

When a finding in `wiki/findings/` is highly relevant to this capability, link it here. The framework also surfaces these automatically via `sdd serve list_findings(capability=this_id)`.
