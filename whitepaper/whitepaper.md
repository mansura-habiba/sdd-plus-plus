# SDD++: A Governance Framework for AI-Assisted Software Engineering

**Version:** 0.3.0 (draft)
**Status:** Working paper — invites critique and field reports
**Date:** 2026-05-19

---

## Abstract

We propose **Spec-Driven Development Plus Plus (SDD++)**, a software engineering method for teams that use AI coding assistants as a routine part of their development workflow. SDD++ targets the failure modes that the first wave of AI-coding-tools (GitHub Copilot, Cursor, Claude Code, Aider) and the first wave of SDD tools (Kiro, GitHub spec-kit, Tessl) have surfaced but not solved: AI sycophancy, AI-authored tests that please code rather than specification, code-quality regression across long-running sessions, loss of human ownership over AI-produced artifacts, and the inability to audit *why* a particular line of code was written.

The method rests on five principles enforced mechanically rather than socially: governance is embedded in the repository, specs are executable contracts, authority is bounded, evidence is required for trust, and AI is a collaborator that may not author load-bearing artifacts. The framework is shipped as a Python tool (`sdd-plus-plus`) that bootstraps any repository with the structure, hides schema files inside the tool to prevent vendor lock-in, exposes itself to AI assistants via the Model Context Protocol, and tracks progress automatically. We argue that this approach is necessary because AI assistants are excellent at producing fluent-but-wrong output, and the only durable counter-measure is a layer the AI cannot author.

This paper articulates the challenges that motivate the method, the design of the proposed solution, why we believe it improves on existing approaches, and the honest limitations of the current state. It is a working paper: the framework exists in code, but its real validation requires longitudinal field data we do not yet have.

---

## 1. Introduction

Software engineering practice is undergoing a phase shift. By mid-2026, a significant fraction of code in production systems is generated, in whole or in part, by AI assistants. The productivity gains are real and well-documented; the safety and quality implications are less well understood. The dominant narratives in the technical press range from "engineers are being replaced" to "this is a bubble," neither of which engages with the operational question that engineering leaders face daily: *how do we run a team where humans and AI assistants ship code together, and how do we maintain quality, ownership, and accountability?*

Spec-Driven Development (SDD) emerged in 2025–2026 as a response. The premise is that writing a structured specification before writing code anchors the AI assistant to a contract and produces more reliable output. The premise is sound. The first implementations are not. Three notable tools — Kiro, GitHub's spec-kit, and Tessl — each address a slice of the problem but exhibit failure modes that compound rather than resolve when applied at team scale: they create more markdown than running behavior, the AI authors the specifications it then satisfies, and they offer no migration path from existing Test-Driven Development workflows.

SDD++ is our attempt at the second-generation answer. It is opinionated where the first generation was permissive, structured where the first generation was prose, and AI-resistant where the first generation was AI-friendly. It exists because the team building it had a concrete operational problem — a mixed-seniority team using AI coding assistants where juniors ignored design documents, seniors over-built, and AI-generated tests reliably passed without proving the right behavior — and it is designed against the specific failure modes that problem surfaced.

This paper is structured in six parts. Section 2 articulates the challenges that motivate the method. Section 3 presents the proposed framework. Section 4 argues why SDD++ improves on existing approaches. Section 5 is honest about limitations. Section 6 outlines future work, including a longer-horizon vision drawn from aviation safety culture.

---

## 2. The challenges

Each of the challenges below is a category of failure we have observed personally, that has been documented in the literature or industry reporting, or both. They are not hypothetical.

### 2.1 AI sycophancy as a default failure mode

Modern large language models are trained, in part, with reinforcement learning from human feedback (RLHF), which rewards outputs that human evaluators find agreeable. The unintended consequence is that AI assistants default to compliance over correctness. When a user proposes a flawed approach, the model agrees and produces the implementation rather than pushing back on the premise. When a user's request contains an unstated assumption, the model fills it in plausibly rather than asking. The user gets working code that solves the wrong problem.

This is not a model-quality issue that will be solved by the next generation. It is a structural artifact of how these systems are trained, and it requires structural counter-measures. A specification framework that does not actively force the AI to articulate its concerns will inherit sycophancy as a feature.

### 2.2 The "specs as markdown" problem

The first-generation SDD tools (notably spec-kit and Tessl) treat specifications as natural-language documents. They allow AI assistants to author or co-author these specifications, on the theory that the human will review the output. This theory underestimates the persuasiveness of AI-generated prose: fluent text triggers pattern-matching for competence in human readers, even when the content is wrong. The reviewer skims a 200-word "definition of done" written by an AI, sees it follows the right shape, and approves. The same reviewer would catch a missing field in a YAML schema instantly.

Markdown specifications also cannot be linted in any meaningful way. A schema-validated YAML rejects missing required fields, contradictory values, and out-of-range parameters mechanically. A markdown paragraph passes any check short of a human reading. When the AI then writes tests against the markdown specification, it is satisfying its own vague language, and the test suite proves nothing.

### 2.3 Code quality regression across sessions

AI coding assistants do not accumulate institutional knowledge across sessions. Each session begins with whatever context can be loaded from files, plus whatever the user types. Tribal knowledge — the patterns a team has converged on, the anti-patterns they have hit before, the library preferences and reasons — exists in senior engineers' heads and is re-derived, badly, every session.

Over a sufficient number of sessions, code quality drifts. Each session produces code that is locally reasonable but globally inconsistent with the codebase's evolving conventions. Lint passes; type-check passes; a senior reviewing the diff several months later finds three different patterns for the same operation and cannot recover the reasoning that produced each. The cost is not in individual lines of code; it is in the long-run cohesion of the codebase, and it compounds.

### 2.4 AI-generated tests please code, not specification

When the same AI assistant produces both the production code and its test suite, both sides drift toward internal coherence. The tests assert what the code does rather than what the specification requires. Coverage rises; correctness does not. Mutation testing — introducing small intentional regressions to production code and re-running the suite — exposes this failure mode mechanically, but mutation testing is not widely practiced, and AI tools do not yet ship with mutation gates as a default.

This is the most insidious of the challenges because the surface signals are all green. Tests pass, coverage is high, code review finds nothing to object to. The defect surfaces only in production, only sometimes, and is difficult to trace back to the AI-test pairing that produced it.

### 2.5 Loss of human ownership

When a pull request contains 60% AI-generated code, who is responsible for that code in the production deployment chain? In current practice, the answer is implicit: whoever opened the PR. But the discipline of *taking ownership* — reading every line, understanding the architectural choices, being able to defend them at review and at 3am during an incident — is not enforced. Engineers learn to accept AI suggestions they have not fully read because the suggestions look right and the deadline is real. The blame chain on a future incident becomes diffuse: the AI generated it, the engineer accepted it, the reviewer skimmed it, the system shipped it. No one acted with full ownership.

### 2.6 The implicit context problem

In any sufficiently mature team, the senior engineer or technical lead carries substantial unstated context: which areas of the codebase are stable, which integrations are sensitive, what the wider product direction is, what *not* to build even though it would be technically interesting. This context informs every code review and every design conversation. AI assistants and junior engineers do not have it. When the lead asks for a feature, the AI builds the literal request rather than the request-in-context, and the junior accepts what the AI produces. The result is correct-looking code that does the wrong thing.

The cost shows up as senior over-building (the senior, with AI's velocity, builds the request *plus* every adjacent improvement that came to mind, only some of which were actually wanted) and junior under-questioning (the junior asks no clarifying questions and ships the literal interpretation).

### 2.7 No data on whether SDD works

The current state of SDD tooling is a hype-to-evidence ratio that warrants skepticism. Every tool has tutorials based on greenfield three-page applications. No vendor publishes longitudinal data on what happens when SDD is applied to a 200,000-line codebase over 18 months: how mutation scores change, how incident rates change, how developer satisfaction trends. In the absence of evidence, the technical press fills the gap with case studies that select for success and ignore failure.

This is itself a challenge: the framework that finally provides the operational discipline must also provide the *measurement* discipline, so that future arguments about whether SDD works can be settled by data rather than by competing anecdotes.

### 2.8 Spec rot and provenance loss

Documents drift away from the systems they describe. This is one of the oldest problems in software engineering. AI assistants accelerate the drift because the rate of code change is higher than the rate of human documentation maintenance. By the time a specification has been written, reviewed, and committed, the code it describes has often already evolved. SDD frameworks that treat specifications as "living documents" without a mechanical drift-detection layer are making a promise that the history of software documentation has consistently failed to keep.

Similarly, the provenance of code — *which AI generated this, with what context, in response to what prompt, with what review* — is lost the moment the pull request merges. There is no audit trail. When something breaks, the team reconstructs from chat logs and human memory, both of which are unreliable. Regulated industries (financial, medical, aviation, automotive) cannot operate this way; even unregulated industries pay an opacity cost.

### 2.9 Token economics and context bloat

AI coding sessions are increasingly expensive in inference cost. The dominant cost driver is *input tokens*: the same context (repository structure, conventions, design documents) gets re-loaded into the model on every interaction. As context grows, model quality degrades through documented effects — "lost in the middle," attention dilution, distractor interference — at the same time that cost grows linearly. The pattern of "load everything you might need" is the antithesis of focus, and it produces both expensive and worse output.

Without an explicit mechanism for *intentional compaction* — maintaining a running summary outside the context window so the window stays focused on the immediate task — long-running sessions degrade in predictable ways.

---

## 3. The proposed method: SDD++

SDD++ is a software engineering method, an artifact layout, a set of schema-enforced rules, and a Python tool. The method is opinionated; the tool is designed to be the smallest possible vehicle for the opinions. We describe the method in three layers: principles, architecture, and workflow.

### 3.1 Five principles

The method rests on five principles. Each is enforced mechanically wherever possible:

1. **Governance is embedded, not sidecar.** Rules live in the repository (`.governance/`), run in the project's CI, and gate the merge button. There is no separate "governance system" to log into.

2. **Specs are executable contracts, not prompt snippets.** Every capability has a machine-readable specification (YAML frontmatter in `capabilities/<id>/spec.md`) and an executable test suite. The frontmatter is the contract; the tests are the proof.

3. **Authority must be bounded.** Every plan declares what it does *not* do. Every specification lists *forbidden* behaviors. Every task gives the AI a paths-it-cannot-touch list. Authority is granted in writing, with limits, before work begins.

4. **Evidence is required for trust.** Every merged change traces to a plan. Every plan traces to a task and a capability. Every capability traces to a principle. The chain is auditable, not promised. Findings (`wiki/findings/`) accumulate as the team learns and feed back into specifications via AI tools that surface them at planning time.

5. **AI is a collaborator, not an author.** AI writes code, drafts plans, surfaces findings. Humans *own* specifications (`spec.md`, `principles.md`, `arch_spec.md`), *own* plans (via explicit acceptance with `sdd plan accept --by @<handle>`), and *own* every merged line. AI is *required to challenge weak premises before complying* — sycophancy is treated as a failure mode rather than a feature.

### 3.2 Architecture

The framework is laid out under a single top-level directory:

```
.governance/
  wiki/
    principles.md         # the five principles
    coding-standards.md   # tribal knowledge: error handling, logging, naming
    findings/<id>.md      # accumulated discoveries (YAML frontmatter + body)
  capabilities/
    REGISTRY.yaml         # continuous list (active + roadmap + deprecated)
    <feature>/
      spec.md             # capability + acceptance cases + DoD + NFR (frontmatter + body)
  arch_spec.md            # whole-system architecture with diagrams
  instructions.md         # canonical AI rules
  plan/<task-id>.plan.md  # AI-generated plans with human acceptance gate
  progress.md             # auto-generated session-state snapshot
AGENTS.md                 # at repo root — copy of instructions.md for tool auto-load
```

Schemas — the JSON Schema definitions that validate every frontmatter block — are *not* shipped to adopters. They live inside the `sdd-plus-plus` Python package and are loaded by the tool. Adopters get schema upgrades by upgrading the tool, eliminating the copy-paste-into-every-repo problem that has plagued previous frameworks.

### 3.3 Workflow

A representative workflow for a single task:

1. **Issue filed.** A team member files a GitHub issue using the bundled task-card form. The form captures: parent capability, one-line goal, bigger picture (minimum 50 characters, forcing actual sentences), in-scope, out-of-scope.

2. **Plan drafted.** The engineer (or AI) drafts a plan: `sdd plan new --task <id> --capability <feature>`. The plan's YAML frontmatter requires a `challenge` block: the AI's restatement of the request, at least one concern (or explicit "no concern surfaced because…"), and at least one alternative considered. Without this block, the plan fails schema validation. The plan is saved as `status: draft`.

3. **Plan accepted.** A human reviewer reads the plan, including the challenge block, and runs `sdd plan accept --id <plan> --by @<handle>`. This is the *only* way a plan transitions to `status: accepted`. The schema enforces that `accepted_by` matches a human handle pattern, and the AI's MCP toolset deliberately does not include an "accept" tool. Acceptance is a human-only operation, mechanically.

4. **Implementation.** The engineer, working with AI, implements the plan. AGENTS.md (loaded automatically by Cursor, Claude Code, Copilot, Aider) tells the AI to read the parent capability spec, check for related findings, and conform to the team's coding-standards.md. The plan's `do_not_modify` list constrains which paths AI may touch.

5. **Validation.** Before opening the PR, the engineer runs `sdd validate`. The validator checks: capability specs conform to their schema, plans conform to theirs, plans reference real capabilities, the bundled cross-reference checks pass.

6. **Pull request.** The PR template requires an *explicit human ownership statement* — the engineer attests they have read every line of AI-generated code, can defend the architectural choices, and are the named owner in the production chain. The PR template also requires confirmation that the AI surfaced at least one concern in the plan's challenge block, and that the human read it before accepting.

7. **CI gate.** GitHub Actions runs `sdd validate --strict`, the contract test suite, an ownership-disclosure presence check, and a protected-paths check (specs cannot be modified without a `spec-change` label). All gates must pass before a human reviewer is assigned.

8. **Human review.** The reviewer focuses on *judgment* (architectural fit, business sense, edge cases), not compliance (the bot already verified compliance).

9. **Merge.** On merge, the plan's status may advance to `executed`. After execution, the reviewer optionally records `outcome` (success / partial / failure) on the plan. Over time, this builds a calibration dataset against the AI's stated `confidence`.

### 3.4 Continuous mechanisms

Two mechanisms run continuously across the workflow:

**Progress snapshot.** Every sdd command and every AI session (via MCP tools `record_progress` and `record_session_end`) appends an event to `.governance/.progress-log.yaml` and regenerates `progress.md`. The markdown file is a token-efficient snapshot: current capabilities, plans in flight, open findings, recent activity, pending actions. AI assistants load `progress.md` at session start (via the `get_progress` MCP tool) instead of re-reading the whole `.governance/` tree.

**Findings accumulation.** When an engineer or AI discovers something non-obvious — a gotcha, a confirmed bug pattern, a behavioral quirk — they file a finding (`sdd findings add`). AI-suggested findings remain `status: suspected` until a human confirms them. Findings are indexed by capability and tag, and surfaced to AI sessions automatically via the `list_findings(capability=...)` MCP tool. Knowledge accumulates instead of being re-derived.

---

## 4. Why this method is better

We argue that SDD++ improves on three existing classes of approach: no-framework (ad-hoc AI use), first-generation SDD tools, and unmodified Test-Driven Development.

### 4.1 Versus no-framework

Most teams using AI assistants today operate without explicit governance. The benefits — short setup, no overhead, full speed — are real and important early. The costs surface after a few months: AI-generated code that no one fully owns, conventions that drift, tests that don't catch what they should, design decisions that are unrecoverable from chat logs.

SDD++ accepts a higher per-task overhead (drafting a plan, populating a challenge block, having a human accept the plan) in exchange for mechanical enforcement of properties that no-framework cannot provide: every line of code traces to an accepted plan, every plan to a specification, every specification to a principle. The overhead is the price of long-run maintainability.

### 4.2 Versus first-generation SDD tools (Kiro, spec-kit, Tessl)

We have analyzed the three named tools elsewhere and found, in each case, design choices that compound at scale. Spec-kit produces 8 files for a 3-point story; the friction-to-value ratio is wrong. Kiro turns small bugs into elaborate 4-user-story requirements documents. Tessl experiments with spec-as-source, which inherits both the inflexibility of model-driven development and the non-determinism of large language models.

SDD++ differs in four ways:

1. **AI cannot author the spec.** The schema's `authored_by.human` field requires a human handle. The `sdd plan accept` command refuses non-human handles. The MCP tool surface deliberately omits any "accept" operation. AI-resistance is mechanical, not social.

2. **Schemas are hidden inside the tool.** Adopters never copy schema files into their repos. Schema upgrades ship with the tool, eliminating the version-fragmentation problem.

3. **Migration path from TDD is direct.** Existing pytest tests become case_ids in the spec. The `sdd generate-acceptance --from-tests` command parses existing test files and seeds a starter `cases` array in the relevant capability's spec.md. Teams keep their existing test suite; they gain a layer above it.

4. **Multi-vendor by design.** AGENTS.md is the de-facto cross-vendor AI rules format. The MCP server is implementation-agnostic. Nothing in SDD++ requires a particular AI assistant or IDE.

### 4.3 Versus unmodified TDD

Test-Driven Development is, in spirit, a spec-driven method: the test *is* the specification. The methodology is sound, but it pre-dates AI-generated code. In an AI-assisted workflow, the AI that generates the production code also generates the tests, and the two converge on internal coherence without external validation. The discipline TDD relied on — the human writes the test that captures intent, then writes the code that satisfies it — is the discipline AI breaks by default.

SDD++ preserves TDD's most valuable property (the test is executable proof of behavior) while adding the layer that AI cannot collapse: the specification, written by a human, against which both code and tests are independently judged. Mutation testing (planned in v0.4) closes the loop mechanically: tests that pass against arbitrary mutations of the production code reveal that they are testing nothing.

---

## 5. Pros and cons

### 5.1 What SDD++ does well

- **AI-resistance by design.** The schema-enforced human-authorship boundary survives even when the AI is told to bypass it. Adversarial prompts that would compromise prose specifications fail schema validation.
- **Mechanical enforcement.** Five gates run in CI (schema validation, contract tests, ownership disclosure, protected-paths check, cross-reference checks). The human reviewer never adjudicates compliance — only judgment.
- **Backward compatibility.** Existing pytest, Hypothesis, fast-check, JUnit, RSpec — all native. SDD++ adds a layer rather than replacing infrastructure.
- **Sixty-second adoption.** `pip install sdd-plus-plus && cd repo && sdd init` produces a working framework. Adopters get value before they invest.
- **Multi-team operability.** A single tool serves many repositories. Engineering leaders with portfolio responsibility can require SDD++ across teams without per-team customization.
- **Token economy.** `progress.md` provides intentional compaction; MCP tools provide selective context loading. AI sessions stay focused.

### 5.2 What SDD++ does poorly today

- **Mutation testing is not yet integrated.** This is the single highest-leverage missing piece. Without mutation scores, the contract-test layer can still be gamed by AI-generated tests that please code rather than spec. Targeted for v0.4.
- **No calibration tracking yet.** The schema supports `confidence` and `outcome` fields, but the framework does not yet aggregate per-tool calibration scores. Until it does, the calibration story is aspirational. Targeted for v0.4.
- **Frontmatter approach can feel heavy for trivial tasks.** A one-line typo fix does not benefit from the full plan/spec/acceptance cycle. The `tier: local` strictness level is intended to mitigate this, but the philosophical tension is real.
- **No field data.** The framework has not been operated by a real team for a full release cycle. Until it has, the productivity and quality claims are theoretical. This is the same trap that first-generation SDD tools fell into; we acknowledge it explicitly.
- **Human discipline is still required.** No framework can prevent a team from gaming its rules — populating the challenge block with boilerplate, accepting plans without reading them, signing ownership statements without understanding the code. The framework makes gaming visible at audit time, but does not prevent it in the moment.
- **The "spec rot" problem is mitigated but not solved.** Schema validation prevents specs from becoming syntactically wrong over time, but cannot prevent them from becoming *stale* — describing a behavior the code no longer implements. The contract test layer catches some of this; mutation testing (v0.4) will catch more; perfect prevention is unsolved.

### 5.3 Open questions

- **Per-team calibration.** How does the framework balance graduated trust against the operational reality of new AI tools being adopted faster than calibration can be measured?
- **Plan granularity.** Is one plan per task too coarse for long-running features? Should plans be hierarchical?
- **AI vs. AI crosscheck.** Section 6 below proposes structurally separated author-AI and reviewer-AI as a v0.4 feature. The unanswered question is whether the productivity cost (double inference) is worth the safety gain in practice.

---

## 6. Future work

The framework as described is v0.3. Several extensions are in design.

### 6.1 v0.4: calibration and crosscheck

**Per-tool calibration tracking.** The `signals.json` time-series store (planned) will aggregate per-plan confidence claims against recorded outcomes. AI tools whose 90% predictions hit 60% in practice will have their autonomy downgraded mechanically. This is the operationalization of the calibration story from §3.

**Structurally separated author-AI and reviewer-AI.** Inspired by separation-of-duties in financial controls. The AI that generates a plan is structurally separate from the AI that reviews it: different prompts, different context budgets, different default models, no shared memory. Disagreement between the two is a signal that surfaces to the human. This doubles inference cost; we believe it more than pays for itself in critical-domain work.

**Mutation testing in CI.** `mutmut` (Python), `Stryker` (JavaScript), `pitest` (Java) wired into the governance workflow with per-capability mutation score thresholds set in `spec.md` frontmatter. Tests that survive mutation cannot be gaming the spec; mutation score becomes the first-class quality metric alongside coverage.

### 6.2 v0.5 and beyond: aspects of "crew resource management"

The longer-horizon vision draws from aviation safety culture. We outline four directions without committing to delivery dates.

**Graduated autonomy by action class.** Every AI action has a class (read-only, suggest-only, propose-with-diff, commit-with-checks, commit-and-execute). The autonomy required scales with class and with the per-tool calibration score. A new AI tool starts at suggest-only; trust is earned through verified outcomes.

**Mandatory callouts.** Critical operations (schema migrations, data backfills, security-sensitive code) require structured pre-action artifacts: affected resources, rollback path, estimated impact, escalation criteria. The AI cannot proceed without producing the callout; the human cannot approve without seeing it.

**Blameless post-incident review, automated.** When a production incident traces back to a plan that was accepted, the framework reconstructs the full chain (intent, plan, acceptance, implementation, review, merge) and produces a structured incident report. The report's output automatically updates memory, policies, and contracts. Failure becomes input to the next iteration rather than blame to a person.

**Recurrency requirements.** AI tools operating in a codebase for 12+ months must "re-check out" on critical capabilities periodically. A failing recurrency check downgrades autonomy until a human re-trains the tool. This is the discipline that prevents slow drift where an AI trusted in February is silently wrong by November.

### 6.3 Research questions worth answering

- What is the empirical relationship between per-team SDD++ adoption depth and incident rate? We do not know; field data is needed.
- Does the challenge-block requirement measurably reduce AI sycophancy, or do AI tools learn to produce template challenge blocks that satisfy the schema without surfacing real concerns?
- Is the ownership-disclosure mechanism behaviorally effective at making engineers actually read AI-generated code, or does it become a checkbox?
- What is the optimal granularity for capability specs in a 100k-line codebase? 200k? 1M?

We invite teams adopting SDD++ to publish their data. The honest test of any methodology is what happens to mutation score, incident rate, and developer satisfaction over twelve months in a real codebase.

---

## 7. Conclusion

We have argued that AI-assisted software engineering is at a phase shift analogous to aviation in the mid-1950s: the technology works, sometimes the planes crash, and the field has not yet developed the institutional discipline to make the human-machine system safer than either alone. SDD++ is our attempt at the first round of that discipline: schemas where prose used to be, mechanical enforcement where social norms used to be, AI-resistance where AI-friendliness used to be the implicit goal.

The framework is opinionated, possibly overconfident, and demonstrably incomplete. It is also running in code, validating its own structure with its own tests, and ready for teams to operate against. The next stage of this work is not more design; it is field data. We will know whether SDD++ is the right approach when a real team has run it for a real release cycle and published what they measured.

Until then, we believe the *direction* — structured over prose, mechanical over social, AI-resistant over AI-friendly, ownership-required over ownership-implied — is the right direction. The specifics are negotiable; the direction is the load-bearing claim.

---

## Appendix A: Comparison table

| Property | No-framework | spec-kit / Kiro / Tessl | TDD | SDD++ |
|---|---|---|---|---|
| Spec format | None | Markdown | Test code | YAML frontmatter + markdown |
| Spec author | None | AI or human | Human | Human only (mechanically enforced) |
| AI may write tests | Yes | Yes | Yes | Yes, against named case_ids only |
| Human ownership gate | Implicit | Implicit | Implicit | Explicit (`sdd plan accept --by`) |
| Challenge before code | No | No | No | Required (schema-enforced) |
| Provenance trail | None | Partial | None | Plan → task → capability → principle |
| Mutation testing | Optional | Optional | Optional | Planned v0.4 |
| Multi-vendor | n/a | Vendor-locked | Yes | Yes |
| Migration from TDD | n/a | None | n/a | Direct (`sdd generate-acceptance`) |
| Cost of adoption | Zero | High | Medium | Sixty seconds |
| Field-validated | No | No | Yes | Not yet |

## Appendix B: Glossary

- **Capability** — a bounded area of system functionality, owned by a named human, defined in `capabilities/<id>/spec.md`.
- **Case** — one observable behavior the implementation must satisfy. Typed (positive, negative, invariant, boundary, regression, performance, security, idempotence).
- **Challenge block** — the AI's required pushback record: understood_request, concerns, alternatives_considered. Empty fields fail schema validation.
- **Finding** — a discovered fact about the system. AI may file as `suspected`; humans confirm.
- **Plan** — an AI-drafted implementation strategy for a task. Must be human-accepted before code is written.
- **Principle** — one of the five governing principles enforced by the framework.
- **Spec** — short for capability specification. The YAML frontmatter + markdown body in `capabilities/<id>/spec.md`.

## Appendix C: Status of the implementation as of this writing

The Python implementation of SDD++ exists as `sdd-plus-plus` v0.3.0 in `/Users/mansurah/Development/built-it-here/sdd-plus-plus`. As of 2026-05-19, the framework supports:

- `sdd init` — bootstraps any repo with the v0.3 layout in ~60 seconds
- `sdd validate` — validates the entire governance tree against the bundled schemas
- `sdd doctor` — 9-milestone diagnostic adoption check
- `sdd findings (add | list | show)` — the wiki/findings layer
- `sdd plan (new | accept | list | show)` — AI-plan lifecycle with the mandatory human acceptance gate (`accept --by @<handle>`)
- `sdd progress` and `sdd update-status` — auto-updating progress snapshot
- `sdd serve` — MCP server exposing the framework to Cursor / Claude Code / Copilot / Aider with 14 tools, including `propose_plan` (which can only save drafts — accepting is a human-only CLI operation)
- `sdd generate-acceptance --from-tests` — TDD migration path

**Test suite: 52 tests pass** across five files (`test_e2e`, `test_findings`, `test_plan`, `test_progress`, `test_serve`). Coverage includes schema validation, ownership-gate enforcement (plans cannot self-accept, AI handles are rejected by `sdd plan accept`), challenge-block requirement (plans missing the challenge block fail validation), and full CLI round-trips.

**End-to-end dogfood verified.** A fresh directory bootstrapped via `sdd init` produces 13 framework files plus auto-generated progress.md. `sdd validate --strict` exits 0. `sdd plan accept --id plan-example-001 --by @mansura` correctly advances the bundled example plan to `accepted` state, populating `accepted_by` and `accepted_at`. `sdd update-status` appends events to the progress log as expected.

**What remains future work (v0.4+):** calibration tracking via `signals.json` time-series, mutation testing integration (`mutmut` / `Stryker` / `pitest` adapters), the cross-IDE extension, and the structurally-separated author-AI / reviewer-AI crosscheck described in §6.2. The v0.3 release line is feature-complete and tested; v0.4 is the next design horizon, not a blocker on adoption.

The framework is ready for the first real-team trial. The honest measurement question — does adopting SDD++ improve mutation score, reduce incident rate, and improve developer satisfaction in a real codebase over twelve months — remains open and is the focus of the next phase of work.
