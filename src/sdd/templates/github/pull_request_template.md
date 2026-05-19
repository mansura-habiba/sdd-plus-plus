<!--
PR template — sdd-plus-plus v0.3.
CI workflow .github/workflows/governance.yml validates that every section below is populated.
-->

## Task and plan

**Closes** # <!-- Issue / task id; required -->

**Plan:** <!-- e.g. .governance/plan/BBS-127-plan-001.plan.yaml; required -->

**Parent capability:** <!-- e.g. .governance/capabilities/skill-validation/spec.yaml; required -->

## What changed (one line)

<!-- The plan's goal.one_liner. If this PR diverges from that, update the plan first. -->

## Compliance checklist

Run before requesting review. CI will re-run these — the human reviewer focuses on judgment, not compliance.

- [ ] The plan is `status: accepted` and `accepted_by` is set to my handle.
- [ ] Every case_id from the capability's `spec.md` that this PR touches has a passing test locally. Paste output below.
- [ ] Diff touches **no path** in `plan.ai_context.do_not_modify`.
- [ ] No code in this PR implements anything listed in `plan.scope.non_goals` or `spec.forbidden`.
- [ ] No dependency added that's in `spec.tasks_must.avoid_dependencies`.
- [ ] The plan's `challenge` block was populated honestly when drafted (concerns + alternatives_considered).
- [ ] `sdd validate` exits 0 locally.

### Contract test output

```
$ pytest tests/contract/ -k <case_id>
<paste here>
```

## Scope check

**Did the diff stay within `plan.scope.in_scope`?**

- [ ] Yes — every changed file maps to an `in_scope` entry.
- [ ] No — see explanation below and link to the follow-up issue. Do **not** expand this PR.

If "no," explain and link the follow-up: <!-- e.g. "Spotted a typo in adjacent file; filed BBS-128, will fix there" -->

## Human ownership disclosure

By merging this PR, I, **@<handle>**, take full ownership of every line in the diff — including AI-generated portions. I affirm:

- [ ] I have read every line of code in this PR, including AI-generated portions.
- [ ] I understand the architectural choices and can defend them in review.
- [ ] I am the named owner for this work in the production deployment chain.
- [ ] No code in this PR is shipping purely because "the AI said so." Where I disagreed with AI suggestions, I overrode them; where I accepted them, I understood them.

**Owner handle:** @<your-handle> <!-- required -->
**AI tools used:** <!-- e.g. Claude Code, Cursor, Copilot, none -->
**Approximate % of lines AI-generated:** <!-- e.g. 60% -->
**Approximate % of lines authored by me:** <!-- e.g. 40% -->

## AI pushback record

The plan's `challenge` block recorded the AI's concerns and alternatives before code was generated. As the human owner, I confirm:

- [ ] **The AI surfaced at least one concern** (in `plan.challenge.concerns`), OR explicitly stated "no concern surfaced" with evidence. If the AI complied without thinking, this PR should not exist.
- [ ] **The AI considered at least one alternative** (in `plan.challenge.alternatives_considered`), OR explicitly stated "no alternative came to mind."
- [ ] **I read the challenge block before accepting the plan.** If the AI's concerns identified a real issue I dismissed, I noted my reasoning here:

<!-- If you dismissed AI concerns, say why. This is the audit trail that protects future you. -->

## Notes for the reviewer

<!--
What you'd like the human reviewer to focus on. Things compliance gates can't catch:
- Is the architecture choice right for the area?
- Are there edge cases the contract tests don't exercise?
- Does this fit the wider direction in plan.goal.bigger_picture?
-->
