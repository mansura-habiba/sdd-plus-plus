# Solving the Software Engineering Problem in the AI Era

**SDD++: A discipline of spec-driven development, mechanical enforcement, honest measurement, and human ownership.**

**Version:** 0.4.0 (draft)
**Author:** Mansura Habiba
**Status:** Working paper — invites critique and field reports
**Date:** 2026-05-22

---

## Abstract

The first wave of AI coding tools (GitHub Copilot, Cursor, Claude Code, Aider) and the first wave of Spec-Driven Development tools (Kiro, GitHub spec-kit, Tessl) have surfaced a set of failure modes the discipline has not solved: AI sycophancy, AI-authored tests that please code rather than specification, code-quality regression across long-running sessions, loss of human ownership over AI-produced artifacts, the inability to audit *why* a particular line of code was written — and, foundationally, the absence of measurement discipline that attributes downstream cost back to fast generation.

We propose **Spec-Driven Development Plus Plus (SDD++)** as the second-generation answer: a software engineering method for teams that use AI coding assistants as a routine part of their workflow, designed against the specific failure modes the first generation surfaced. The method rests on six principles enforced mechanically rather than socially — governance is embedded in the repository, specs are executable contracts, authority is bounded, evidence is required for trust, AI is a collaborator that may not author load-bearing artifacts, and measurement is part of the artifact rather than an afterthought. The framework is shipped as a Python tool (`sdd-plus-plus`) that bootstraps any repository with the structure, hides schema files inside the tool to prevent vendor lock-in, exposes itself to AI assistants via the Model Context Protocol, and tracks both progress and outcomes automatically. We argue that this approach is necessary because AI assistants are excellent at producing fluent-but-wrong output, and the only durable counter-measure is a layer the AI cannot author paired with a measurement substrate the AI cannot game.

This paper articulates the challenges that motivate the method, the research position and pillars that anchor the broader program, the design of the proposed solution, why we believe it improves on existing approaches, ten benchmarks for assessing AI coding tools and a diagnostic use of mutation testing, the honest limitations of the current state, and a worked example. It is a working paper: the framework exists in code, but its real validation requires longitudinal field data we do not yet have.

---

## 1. Introduction

Software engineering practice is undergoing a phase shift. By mid-2026, a significant fraction of code in production systems is generated, in whole or in part, by AI assistants. The productivity gains are real and well-documented; the safety and quality implications are less well understood. The dominant narratives in the technical press range from "engineers are being replaced" to "this is a bubble," neither of which engages with the operational question that engineering leaders face daily: *how do we run a team where humans and AI assistants ship code together, and how do we maintain quality, ownership, accountability, and honest measurement of net outcome?*

Spec-Driven Development (SDD) emerged in 2025–2026 as a response. The premise is that writing a structured specification before writing code anchors the AI assistant to a contract and produces more reliable output. The premise is sound. The first implementations are not. Three notable tools — Kiro, GitHub's spec-kit, and Tessl — each address a slice of the problem but exhibit failure modes that compound rather than resolve when applied at team scale: they create more markdown than running behavior, the AI authors the specifications it then satisfies, and they offer no migration path from existing Test-Driven Development workflows. None of the three integrate the measurement layer that would tell adopters whether the framework is producing the outcomes it promises.

SDD++ is our attempt at the second-generation answer. It is opinionated where the first generation was permissive, structured where the first generation was prose, AI-resistant where the first generation was AI-friendly, and measurement-honest where the first generation accepted volume metrics as proxies for productivity. It exists because the team building it had a concrete operational problem — a mixed-seniority team using AI coding assistants where juniors ignored design documents, seniors over-built, AI-generated tests reliably passed without proving the right behavior, and "productivity" reports celebrated PR volume while incidents quietly accumulated — and it is designed against the specific failure modes that problem surfaced.

This paper is structured in ten parts. Section 2 articulates the challenges that motivate the method. Sections 3 and 4 state the research position and pillars. Section 5 presents the proposed framework. Section 6 argues why SDD++ improves on existing approaches. Section 7 is honest about limitations. Section 8 proposes a benchmark suite for assessing AI coding tools and a diagnostic use of mutation testing. Section 9 outlines future work, including a longer-horizon vision drawn from aviation safety culture. Section 10 concludes. Appendix D walks through a worked example end to end.

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

This is the most insidious of the per-change failure modes because the surface signals are all green. Tests pass, coverage is high, code review finds nothing to object to. The defect surfaces only in production, only sometimes, and is difficult to trace back to the AI-test pairing that produced it. The challenge is a special case of the broader measurement gap described in §2.10.

### 2.5 Loss of human ownership

When a pull request contains 60% AI-generated code, who is responsible for that code in the production deployment chain? In current practice, the answer is implicit: whoever opened the PR. But the discipline of *taking ownership* — reading every line, understanding the architectural choices, being able to defend them at review and at 3am during an incident — is not enforced. Engineers learn to accept AI suggestions they have not fully read because the suggestions look right and the deadline is real. The blame chain on a future incident becomes diffuse: the AI generated it, the engineer accepted it, the reviewer skimmed it, the system shipped it. No one acted with full ownership.

### 2.6 The implicit context problem

In any sufficiently mature team, the senior engineer or technical lead carries substantial unstated context: which areas of the codebase are stable, which integrations are sensitive, what the wider product direction is, what *not* to build even though it would be technically interesting. This context informs every code review and every design conversation. AI assistants and junior engineers do not have it. When the lead asks for a feature, the AI builds the literal request rather than the request-in-context, and the junior accepts what the AI produces. The result is correct-looking code that does the wrong thing.

The cost shows up as senior over-building (the senior, with AI's velocity, builds the request *plus* every adjacent improvement that came to mind, only some of which were actually wanted) and junior under-questioning (the junior asks no clarifying questions and ships the literal interpretation).

### 2.7 No data on whether SDD works

The current state of SDD tooling is a hype-to-evidence ratio that warrants skepticism. Every tool has tutorials based on greenfield three-page applications. No vendor publishes longitudinal data on what happens when SDD is applied to a 200,000-line codebase over 18 months: how mutation scores change, how incident rates change, how developer satisfaction trends. In the absence of evidence, the technical press fills the gap with case studies that select for success and ignore failure.

This is the team-level reflection of the change-level measurement gap described in §2.10. The framework that finally provides the operational discipline must also provide the *measurement* discipline, so that future arguments about whether SDD works can be settled by data rather than by competing anecdotes.

### 2.8 Spec rot and provenance loss

Documents drift away from the systems they describe. This is one of the oldest problems in software engineering. AI assistants accelerate the drift because the rate of code change is higher than the rate of human documentation maintenance. By the time a specification has been written, reviewed, and committed, the code it describes has often already evolved. SDD frameworks that treat specifications as "living documents" without a mechanical drift-detection layer are making a promise that the history of software documentation has consistently failed to keep.

Similarly, the provenance of code — *which AI generated this, with what context, in response to what prompt, with what review* — is lost the moment the pull request merges. There is no audit trail. When something breaks, the team reconstructs from chat logs and human memory, both of which are unreliable. Regulated industries (financial, medical, aviation, automotive) cannot operate this way; even unregulated industries pay an opacity cost.

### 2.9 Token economics and context bloat

AI coding sessions are increasingly expensive in inference cost. The dominant cost driver is *input tokens*: the same context (repository structure, conventions, design documents) gets re-loaded into the model on every interaction. As context grows, model quality degrades through documented effects — "lost in the middle," attention dilution, distractor interference — at the same time that cost grows linearly. The pattern of "load everything you might need" is the antithesis of focus, and it produces both expensive and worse output.

Without an explicit mechanism for *intentional compaction* — maintaining a running summary outside the context window so the window stays focused on the immediate task — long-running sessions degrade in predictable ways.

### 2.10 Productivity measured at the wrong end of the pipe

The dominant productivity metrics for AI-assisted software development — pull requests merged, lines committed, tokens generated, time to first commit — are output measures. They are seductive because they are instantly visible and easy to chart. They are also fundamentally incomplete: they account for the work entering the pipeline and ignore the work the pipeline produces downstream, namely defects introduced, security findings opened, rollbacks executed, customer escalations triggered, and tests rewritten to accommodate brittle changes.

When generation cost approaches zero, this measurement gap stops being a quirk and becomes the defining problem of the discipline. An agent that ships ten "fast" pull requests but produces four incidents and twelve test-suite rewrites over the following month did not ship fast. It shipped debt that someone else paid, and the productivity claim was already cashed before the debt arrived. Bookkeeping in the literal accounting sense — charges accruing against the original purchase — does not exist for software changes today.

Two specific failure modes within this gap are worth naming. The first is the test-suite tautology described in §2.4: tests that pass against arbitrary mutations of the production code are not testing the specification, they are narrating the implementation. Coverage metrics miss this entirely. The second is the calibration gap: AI tools that claim "high confidence" on plans that subsequently produce incidents are mis-calibrated, and without per-tool calibration tracking the team has no way to discount future confidence claims accordingly.

The broader picture is that other industries reached this measurement frontier earlier. Finance moved past trade-volume metrics to risk-adjusted return (Sharpe ratio, Sortino ratio) once volume became cheap enough to game. Surgery moved past procedure counts to risk-adjusted outcome metrics, otherwise surgeons who took only easy cases dominated the leaderboard. Pharma's Phase IV post-marketing surveillance exists because clinical-trial efficacy systematically over-estimates net benefit. Aviation maintenance organizations are graded on incidents traced back to their work, not on cycles serviced. Each industry made the move from output-measurement to outcome-measurement at the point where output became cheap enough to game. Software, with AI generation, is at that point now.

The structural counter-measure required is a measurement substrate that sits beneath the operational primitives: penalty bookkeeping that attributes downstream cost to its generating change, verification surface measurement that distinguishes test suites that defend a specification from those that merely mirror an implementation, and calibration tracking that grades stated confidence against observed outcomes. Without this substrate, every other discipline in this paper can be gamed by accelerating the visible end of the pipe while shipping debt out the back.

---

## 3. Research Position

Seven claims that this research will deepen, refine, and defend — not discover. They are the priors from which the program operates. If any of them turn out to be wrong, the program restructures around the correction.

### 3.1 Generation is no longer the bottleneck. Verification is.
Process frameworks that optimize for generation throughput are solving yesterday's problem. The discipline of the next decade is verification economics: what to verify, by whom, with what evidence, at what cost.

### 3.2 The unit of software work is the human-agent ensemble, not the human team.
One human, an unknown number of agents, a fluid composition. The cognitive constraints that shaped Agile — human working memory, human pace, human coordination cost — do not apply. New constraints apply. They have not been named.

### 3.3 Specs are durable; code is exhaust.
The artifact that persists across regenerations is the spec, not the code. Process discipline should attach to the spec. The trajectory of the spec, over a system's life, is the system's intellectual lineage.

### 3.4 Handover is a contract, not a document.
Until handover is treated as a contract with parties, terms, acceptance, and remedies, senior engineers will remain the verification bottleneck regardless of how good the agents become.

### 3.5 Software has decades of operational wisdom available from other safety-critical industries. It has imported almost none of it.
Aviation, ICUs, nuclear control rooms, drug discovery, chain-of-custody, naval operations, long-baseline science — all have solved problems software is currently getting wrong. The translation work is not optional; it is the central methodological move of this program.

### 3.6 Mortality is a design principle, not a failure mode.
Systems that do not know how to die accumulate fatal complexity. The default state of software should be "scheduled for death unless renewed," not "alive forever unless deleted."

### 3.7 Process discipline is a substitute for trust at scale.
Trust does not scale. Protocols do. The right protocols make trust portable across teams, vendors, time, and the human-agent boundary. The work is to design protocols rigorous enough that adopting them is cheaper than maintaining bilateral trust relationships.

---

## 4. Research pillars

Ten pillars. Each pillar has a question, a set of sub-questions, a method, and a connection to primitives already named in the repo. Pillar 4.10 is the measurement substrate that underwrites every other pillar; it is presented as a pillar in its own right, but its mechanisms are referenced from §5.5 of the framework design.

### 4.1 Verification Economics

**Question:** When generation is nearly free and verification is the bottleneck, what is the right economics of verification — how much human attention should be spent verifying what, and how is that attention allocated?

**Sub-questions:**
- How is verification capacity measured? What is the right unit?
- What is the calibration curve for AI-generated code under different verification regimes?
- What is the right ratio of human-time to automated-evidence in verification budgets?
- What does "good enough" verification look like for each reversibility class of change?

**Method:** Instrument real teams. Observe where senior attention goes. Build the Attention Budget primitive. Measure outcomes against baselines.

**Connected primitives:** Attention Budget, Spec-Compile-Verify gates, structured return states.

### 4.2 Handover Protocols

**Question:** What structural mechanisms move work between agents and humans (and between agents and agents) without dropping it on the floor?

**Sub-questions:**
- What is the minimum viable handover contract?
- How does differential routing work at scale — who decides which receiver is right?
- What does the agent-to-agent handover protocol look like? (Open question from origin conversation.)
- How is handover quality itself graded over time?
- What are the failure modes of the protocol under organizational pressure (e.g., when the senior reviewer accepts everything because they don't have time to push back)?

**Method:** Adapt SBAR (nursing), ATC sector handover, aviation transfer-of-control, nuclear shift turnover. Draft reference protocol. Build reference implementation with real agents. Pilot with one team for at least three months.

**Connected primitives:** Confidence shape, bidirectional acknowledgement, dissent log, differential routing, receiver-customized brief, the clock, structured return states.

### 4.3 Spec Trajectories

**Question:** How do specs evolve over a system's life, and how should that evolution be instrumented?

**Sub-questions:**
- What is the right artifact for the Conjecture with horizons?
- How is spec drift recorded, versioned, and read by newcomers?
- What does Phase IV (post-deployment discovery) look like in software, and how is it budgeted?
- How are reversibility classes assigned, and how does that assignment hold up over time?

**Method:** Borrow from drug discovery's Phase I-IV structure. Trace spec evolution in real long-lived systems (one open-source, one proprietary if access available). Map decisions to their reversibility class and observation horizon.

**Connected primitives:** Conjecture with horizons, discovery budget, spec drift instrumentation, reversibility classes, observation horizons, deliberate wrong-version building.

### 4.4 Mortality and Lifecycle

**Question:** What does it look like when software is designed to die well, and how does that change the organization around it?

**Sub-questions:**
- How does the Bill of Mortality work in practice, and what tooling does it require?
- What does the Renewal Court look like in a real team — who serves, how often, what evidence is admissible?
- What are the failure modes of forced expiration (false positives, defensive renewal, gaming the court)?
- How does Apoptosis work mechanically — what observable degradation pattern is acceptable to callers?

**Method:** Pilot in a small system with consenting stewards. Study graceful deprecation in adjacent domains (library deprecation paths, FDA recall processes, naval ship decommissioning).

**Connected primitives:** Mortality-First Lifecycle (Genesis, Quickening, Renewal Court, Apoptosis, Coroner's Inquest), Bill of Mortality.

### 4.5 Roles, Accountability, and Routing

**Question:** What roles emerge in a human-agent ensemble, and how does accountability redistribute when the senior engineer is no longer the universal reviewer?

**Sub-questions:**
- What are the actual new roles (Cartographer, Coroner, Hospice Engineer, Genealogist, Midwife) — what do they do day to day?
- How are these roles staffed — promoted into, hired for, rotated?
- What is the differential routing logic that replaces "human in the loop"?
- How does the system stay accountable when no single named human is "the owner"?

**Method:** Identify roles by negation — what dissolves when senior engineer is no longer the funnel, what emerges in the vacuum. Interview practitioners. Pilot role definitions in at least one organization.

**Connected primitives:** Midwife, Cartographer, Renewal Counsel/Opposing Counsel, Coroner, Hospice Engineer, Genealogist, differential routing.

### 4.6 Process Substrates

**Question:** What replaces Agile's ceremonies in an environment where the bottleneck has moved?

**Sub-questions:**
- How does the Wager Loop work over a full quarter — what calibration data does it produce?
- What does the Logbook look like in real practice — append-only, structured, how do humans and agents both write to it?
- How is Attention Budget measured, tracked, and respected?
- What ceremonies, if any, do humans still need for social cohesion, separately from project management?

**Method:** Build templates. Run pilots. Compare outcomes against Agile baselines. Measure team satisfaction independently from delivery metrics.

**Connected primitives:** Spec-Compile-Verify, Wager Loop, Attention Budget, Logbook.

### 4.7 Provenance and Chain of Custody

**Question:** Given that AI agents are writing significant portions of code, what provenance machinery does the lifecycle require?

**Sub-questions:**
- How is "who/what wrote this code" recorded — at what granularity?
- What does signed handover look like — cryptographic, organizational, both?
- How does chain of custody port from physical industries (evidence handling, chemistry, pharmaceuticals) to software artifacts?
- What is the right format for a birth certificate — minimum viable, extensible?

**Method:** Study NIST SBOM extensions and SLSA. Study chain-of-custody from physical industries. Draft provenance schemas. Build reference implementation.

**Connected primitives:** Birth certificate, Bill of Mortality, Genealogist role.

### 4.8 Failure Investigation

**Question:** What does a software incident investigation look like when it is structured like a death investigation rather than a postmortem?

**Sub-questions:**
- What is the right separation between fact-finding (Coroner) and policy-making (Renewal Court)?
- How is blameless investigation instrumented so it survives organizational pressure to assign fault?
- What does the report from a Coroner's Inquest look like, and who reads it?
- How does this differ from existing SRE postmortem practice — what gaps does it close?

**Method:** Study NTSB methodology and FAA incident reporting culture. Compare against current SRE postmortem practice. Pilot one investigation under the new structure.

**Connected primitives:** Coroner's Inquest, Coroner role, blameless framing.

### 4.9 Cross-Industry Translation

**Question:** What other industries have already solved problems software is currently getting wrong, and how do you port their practices honestly without cargo-culting?

**Sub-questions:**
- Aviation: incident reporting, CRM (Crew Resource Management), sterile cockpit rules, transfer of control.
- ICU and emergency medicine: SBAR handoff, nurse-physician communication, the "what I'm worried about" channel.
- Nuclear: shift turnover, safety culture, the difference between event reports and condition reports.
- Drug discovery: phase gates, post-marketing surveillance, the role of FDA Phase IV.
- Chain-of-custody: evidence integrity, witnessed transfer, the legal standards for chain breaks.
- Naval and submarine operations: watch turnover, standing orders, the standing-orders-vs-current-situation distinction.
- Long-baseline scientific experiments: hypothesis evolution, pre-registration, planned re-analysis.

**Method:** Embedded research where possible — visits, interviews with practitioners. Read primary sources (NTSB reports, NRC bulletins, FDA guidances, IOM patient safety reports). Cite specific practices, not generalized lessons.

**Connected primitives:** Cross-cuts every pillar. This is the central methodological move.

### 4.10 Net Velocity, Penalty Bookkeeping, and Verification Surface

**Question:** When generation cost approaches zero, how do you measure productivity honestly — attributing downstream cost back to its generating change, distinguishing test suites that defend specifications from those that merely mirror implementations, and grading stated confidence against observed outcomes?

**Sub-questions:**
- How is penalty attribution automated versus contested, and what failure modes does each mode carry?
- What is the right horizon for penalty accrual (default ninety days)? Should it vary by capability, risk class, or product cadence?
- How should risk-class normalization be calibrated — linear multipliers, non-linear, or per-capability?
- What are the gaming surfaces of Net Velocity, and how does the framework defend each one?
- How is mutation kill rate kept meaningful as AI tools learn to generate tests that satisfy mutation operators specifically rather than the underlying specification?
- What is the right relationship between team-level metrics (DORA) and change-level metrics (Net Velocity) — do they coexist, or does one supersede the other?

**Method:** Build the penalty-ledger primitive in SDD++; integrate `mutmut`, `Stryker`, and `pitest` as first-class CI mechanisms; add per-agent calibration tracking against the existing `confidence`/`outcome` fields. Borrow risk-adjusted measurement frameworks from finance (Sharpe ratio, Sortino ratio), surgery (risk-adjusted complication rates), pharma (Phase IV post-marketing surveillance), and aviation maintenance (incident-to-shift trace-back). Pilot on a real codebase for at least three months; compare against a DORA baseline measured over the same period.

**Connected primitives:** Net Velocity (output × verification surface × calibration ÷ penalty), penalty ledger, verification surface index (mutation kill rate), calibration tracking, risk-class normalization, exploration track. This pillar is the foundational measurement substrate referenced by §2.10 and operationalized in §5.5.

---

## 5. The proposed method: SDD++

SDD++ is a software engineering method, an artifact layout, a set of schema-enforced rules, and a Python tool. The method is opinionated; the tool is designed to be the smallest possible vehicle for the opinions. We describe the method in five layers: principles, architecture, workflow, continuous mechanisms, and the measurement substrate that sits beneath them all.

### 5.1 Six principles

The method rests on six principles. Each is enforced mechanically wherever possible:

1. **Governance is embedded, not sidecar.** Rules live in the repository (`.governance/`), run in the project's CI, and gate the merge button. There is no separate "governance system" to log into.

2. **Specs are executable contracts, not prompt snippets.** Every capability has a machine-readable specification (YAML frontmatter in `capabilities/<id>/spec.md`) and an executable test suite. The frontmatter is the contract; the tests are the proof.

3. **Authority must be bounded.** Every plan declares what it does *not* do. Every specification lists *forbidden* behaviors. Every task gives the AI a paths-it-cannot-touch list. Authority is granted in writing, with limits, before work begins.

4. **Evidence is required for trust.** Every merged change traces to a plan. Every plan traces to a task and a capability. Every capability traces to a principle. The chain is auditable, not promised. Findings (`wiki/findings/`) accumulate as the team learns and feed back into specifications via AI tools that surface them at planning time.

5. **AI is a collaborator, not an author.** AI writes code, drafts plans, surfaces findings. Humans *own* specifications (`spec.md`, `principles.md`, `arch_spec.md`), *own* plans (via explicit acceptance with `sdd plan accept --by @<handle>`), and *own* every merged line. AI is *required to challenge weak premises before complying* — sycophancy is treated as a failure mode rather than a feature.

6. **Measurement is part of the artifact.** Every change carries a measurable downstream cost that is attributed back to the change that produced it, and every test suite carries a verification surface index measured by mutation kill rate. Output without measured outcome is not productivity; it is unaudited risk. The measurement substrate (§5.5) is enforced by the framework as a peer to the four compliance gates.

### 5.2 Architecture

The framework is laid out under a single top-level directory:

```
.governance/
  wiki/
    principles.md         # the six principles
    coding-standards.md   # tribal knowledge: error handling, logging, naming
    findings/<id>.md      # accumulated discoveries (YAML frontmatter + body)
  capabilities/
    REGISTRY.yaml         # continuous list (active + roadmap + deprecated)
    <feature>/
      spec.md             # capability + acceptance cases + DoD + NFR + mutation threshold
  arch_spec.md            # whole-system architecture with diagrams
  instructions.md         # canonical AI rules
  plan/<task-id>.plan.md  # AI-generated plans with human acceptance gate + penalty ledger
  progress.md             # auto-generated session-state snapshot
  signals.json            # time-series store for calibration and Net Velocity tracking
AGENTS.md                 # at repo root — copy of instructions.md for tool auto-load
```

Schemas — the JSON Schema definitions that validate every frontmatter block — are *not* shipped to adopters. They live inside the `sdd-plus-plus` Python package and are loaded by the tool. Adopters get schema upgrades by upgrading the tool, eliminating the copy-paste-into-every-repo problem that has plagued previous frameworks.

### 5.3 Workflow

A representative workflow for a single task (a fully worked example is in Appendix D):

1. **Issue filed.** A team member files a GitHub issue using the bundled task-card form. The form captures: parent capability, one-line goal, bigger picture (minimum 50 characters, forcing actual sentences), in-scope, out-of-scope.

2. **Plan drafted.** The engineer (or AI) drafts a plan: `sdd plan new --task <id> --capability <feature>`. The plan's YAML frontmatter requires a `challenge` block: the AI's restatement of the request, at least one concern (or explicit "no concern surfaced because…"), and at least one alternative considered. Without this block, the plan fails schema validation. The plan is saved as `status: draft`.

3. **Plan accepted.** A human reviewer reads the plan, including the challenge block, and runs `sdd plan accept --id <plan> --by @<handle>`. This is the *only* way a plan transitions to `status: accepted`. The schema enforces that `accepted_by` matches a human handle pattern, and the AI's MCP toolset deliberately does not include an "accept" tool. Acceptance is a human-only operation, mechanically.

4. **Implementation.** The engineer, working with AI, implements the plan. AGENTS.md (loaded automatically by Cursor, Claude Code, Copilot, Aider) tells the AI to read the parent capability spec, check for related findings, and conform to the team's coding-standards.md. The plan's `do_not_modify` list constrains which paths AI may touch.

5. **Validation.** Before opening the PR, the engineer runs `sdd validate`. The validator checks: capability specs conform to their schema, plans conform to theirs, plans reference real capabilities, the bundled cross-reference checks pass, and (from v0.4) the capability's declared mutation kill rate is met.

6. **Pull request.** The PR template requires an *explicit human ownership statement* — the engineer attests they have read every line of AI-generated code, can defend the architectural choices, and are the named owner in the production chain. The PR template also requires confirmation that the AI surfaced at least one concern in the plan's challenge block, and that the human read it before accepting.

7. **CI gate.** GitHub Actions runs `sdd validate --strict`, the contract test suite, an ownership-disclosure presence check, a protected-paths check (specs cannot be modified without a `spec-change` label), and the mutation-test gate keyed to each touched capability's declared threshold. All gates must pass before a human reviewer is assigned.

8. **Human review.** The reviewer focuses on *judgment* (architectural fit, business sense, edge cases), not compliance (the bot already verified compliance).

9. **Merge.** On merge, the plan's status may advance to `executed`. After execution, the reviewer optionally records `outcome` (success / partial / failure) on the plan. Subsequent downstream events — incident fixes, security findings, rollbacks — accrue to the plan's `penalty_ledger` block automatically (see §5.5).

### 5.4 Continuous mechanisms

Two mechanisms run continuously across the workflow:

**Progress snapshot.** Every sdd command and every AI session (via MCP tools `record_progress` and `record_session_end`) appends an event to `.governance/.progress-log.yaml` and regenerates `progress.md`. The markdown file is a token-efficient snapshot: current capabilities, plans in flight, open findings, recent activity, pending actions. AI assistants load `progress.md` at session start (via the `get_progress` MCP tool) instead of re-reading the whole `.governance/` tree.

**Findings accumulation.** When an engineer or AI discovers something non-obvious — a gotcha, a confirmed bug pattern, a behavioral quirk — they file a finding (`sdd findings add`). AI-suggested findings remain `status: suspected` until a human confirms them. Findings are indexed by capability and tag, and surfaced to AI sessions automatically via the `list_findings(capability=...)` MCP tool. Knowledge accumulates instead of being re-derived.

### 5.5 The measurement substrate

Underneath the four operational gates of §5.3 (schema validation, contract tests, ownership disclosure, protected-paths check) sits a fifth, measurement-oriented layer. It comprises three coupled mechanisms and operationalizes pillar 4.10.

**Penalty bookkeeping.** Every downstream cost — incident fix, security finding, rollback, customer escalation, test-suite rewrite — is attributed back to its generating plan. Attribution is automated where possible: `git bisect` for bug-introducing changes, SAST output cross-referencing for security findings, the existing rollback record for explicit reverts. Where the trace is ambiguous, a structured contestation review (modeled on patent-office opposition procedure) allows the originator seven days to dispute. Penalties accrue for a configurable horizon (default ninety days) and are normalized for system risk class: high-stakes systems carry smaller multipliers, so engineers and agents working on the hardest code are not perversely penalized for taking on the riskiest work. A plan with high penalty accrual does not lose retroactively, but its associated agent loses confidence allowance on future plans — the confidence-shape field in subsequent plans is discounted by the agent's historical accrual.

**Verification surface index.** Mutation testing is integrated as a first-class quality signal. Every capability declares a minimum mutation kill rate in its `spec.md` frontmatter; the contract test suite is augmented by a mutation-test run on every PR that touches the capability's code. Coverage metrics remain advisory; mutation kill rate becomes load-bearing. Tools wired in by default: `mutmut` for Python, `Stryker` for JavaScript and TypeScript, `pitest` for Java. The framework treats a test suite that fails to catch arbitrary mutations as evidence that the suite is narrating the implementation rather than defending the specification — which is the structural failure mode of AI-generated tests described in §2.4. The framework also instruments mutation-test runs so that AI-generated test additions which do not raise the kill rate are flagged: a test that does not move the verification surface is presumed redundant until shown otherwise. The diagnostic uses of mutation testing — beyond the gate — are developed in §8.2.

**Calibration tracking.** The plan schema already supports `confidence` (claimed at plan time) and `outcome` (recorded after merge) fields. The substrate aggregates these into a `signals.json` time-series store, and a new `sdd calibration` CLI surfaces per-agent calibration curves. An agent whose "high confidence" plans produce incidents at a rate higher than its "moderate confidence" plans is mis-calibrated and triggers an autonomy downgrade (a v0.5 mechanism described in §9.2). Calibration is reported per agent, per capability, and per change-class, with appropriate normalization for sample size — a new tool with ten plans is not graded against an established tool with a thousand.

Together the three mechanisms compose a framing metric we call **Net Velocity**:

```
Net Velocity = output rate × verification surface × calibration accuracy ÷ penalty accrual
```

The metric is not a score to optimize but a dashboard to read. An agent shipping five plans with a ninety-percent mutation kill rate, zero reverts, and zero calibration failures is more productive than one shipping twenty plans with sixty-percent kill rate, three reverts, and two calibration failures. The first is paying its bills as it goes; the second is racking up debt the team will service later, in incidents the current dominant metrics do not yet attribute. Net Velocity makes that attribution explicit.

The substrate carries known gaming surfaces. Avoidance of hard problems is mitigated by risk-class normalization. Mis-attribution is mitigated by time-bounded contestation. Discouraging exploration is mitigated by a separate track for plans tagged as `probe` (deliberate exploratory work, where penalty accrual is suppressed). Bureaucratic overhead is mitigated by automating attribution wherever bisect or change-impact analysis can do the work, reserving human adjudication for contested cases. The mitigations are imperfect; we treat the measurement substrate as evolving infrastructure rather than fixed truth, and revise it as gaming patterns emerge.

---

## 6. Why this method is better

We argue that SDD++ improves on four existing classes of approach: no-framework (ad-hoc AI use), first-generation SDD tools, unmodified Test-Driven Development, and output-metric culture (DORA and friends).

### 6.1 Versus no-framework

Most teams using AI assistants today operate without explicit governance. The benefits — short setup, no overhead, full speed — are real and important early. The costs surface after a few months: AI-generated code that no one fully owns, conventions that drift, tests that don't catch what they should, design decisions that are unrecoverable from chat logs, and a productivity narrative that ignores the incidents quietly accumulating.

SDD++ accepts a higher per-task overhead (drafting a plan, populating a challenge block, having a human accept the plan) in exchange for mechanical enforcement of properties that no-framework cannot provide: every line of code traces to an accepted plan, every plan to a specification, every specification to a principle, and every change to a measured outcome. The overhead is the price of long-run maintainability and honest reporting.

### 6.2 Versus first-generation SDD tools (Kiro, spec-kit, Tessl)

We have analyzed the three named tools elsewhere and found, in each case, design choices that compound at scale. Spec-kit produces 8 files for a 3-point story; the friction-to-value ratio is wrong. Kiro turns small bugs into elaborate 4-user-story requirements documents. Tessl experiments with spec-as-source, which inherits both the inflexibility of model-driven development and the non-determinism of large language models. None of the three integrate a measurement layer that would tell adopters whether the framework is producing the outcomes it promises.

SDD++ differs in five ways:

1. **AI cannot author the spec.** The schema's `authored_by.human` field requires a human handle. The `sdd plan accept` command refuses non-human handles. The MCP tool surface deliberately omits any "accept" operation. AI-resistance is mechanical, not social.

2. **Schemas are hidden inside the tool.** Adopters never copy schema files into their repos. Schema upgrades ship with the tool, eliminating the version-fragmentation problem.

3. **Migration path from TDD is direct.** Existing pytest tests become case_ids in the spec. The `sdd generate-acceptance --from-tests` command parses existing test files and seeds a starter `cases` array in the relevant capability's spec.md. Teams keep their existing test suite; they gain a layer above it.

4. **Multi-vendor by design.** AGENTS.md is the de-facto cross-vendor AI rules format. The MCP server is implementation-agnostic. Nothing in SDD++ requires a particular AI assistant or IDE.

5. **Measurement substrate built in.** Mutation testing, penalty bookkeeping, and calibration tracking are first-class framework components from v0.4 forward, not optional add-ons. The framework refuses to ship a productivity claim that ignores downstream cost.

### 6.3 Versus unmodified TDD

Test-Driven Development is, in spirit, a spec-driven method: the test *is* the specification. The methodology is sound, but it pre-dates AI-generated code. In an AI-assisted workflow, the AI that generates the production code also generates the tests, and the two converge on internal coherence without external validation. The discipline TDD relied on — the human writes the test that captures intent, then writes the code that satisfies it — is the discipline AI breaks by default.

SDD++ preserves TDD's most valuable property (the test is executable proof of behavior) while adding the layer that AI cannot collapse: the specification, written by a human, against which both code and tests are independently judged. Mutation testing closes the loop mechanically: tests that pass against arbitrary mutations of the production code reveal that they are testing nothing, and the framework treats that revelation as a build failure rather than a footnote.

### 6.4 Versus output-metric culture

The dominant culture of measurement in software organizations is volume-oriented. Engineering dashboards report pull requests merged per developer, story points completed per sprint, deployments per day. The DORA metrics — deployment frequency, lead time for changes, change failure rate, mean time to recovery — broaden this view but operate at team-level aggregation, deliberately avoiding the change-level attribution that would expose individual or per-agent quality. The original DORA framing was correct for its era: when humans were the bottleneck and the cost of distrust between engineers was high, team-level metrics were the appropriate unit.

That era is ending. When agents generate a meaningful fraction of code, team-level aggregation hides the signal: a team can ship at high velocity precisely because one agent's output is being silently cleaned up by the others. Volume rises; net outcome flatlines or worsens. SDD++ takes the position that the natural unit of attribution is now the change, and the measurement substrate (§5.5) is the mechanism for attributing fairly without re-introducing the social costs DORA was designed to prevent. The mitigations against gaming surfaces — risk normalization, contestation, exploration tracks — exist precisely to keep change-level attribution from collapsing into blame.

Other industries reached this point earlier. The pattern repeats: output becomes cheap to game, an outcome-adjusted metric emerges, the field reorganizes around it. Finance has Sharpe ratio. Surgery has risk-adjusted complication rates. Pharma has Phase IV surveillance. Aviation maintenance has trace-back-to-shift reliability. Software, with AI generation, is at the point in this cycle where the move from output to outcome is overdue.

---

## 7. Pros and cons

### 7.1 What SDD++ does well

- **AI-resistance by design.** The schema-enforced human-authorship boundary survives even when the AI is told to bypass it. Adversarial prompts that would compromise prose specifications fail schema validation.
- **Mechanical enforcement.** Five gates run in CI (schema validation, contract tests, ownership disclosure, protected-paths check, mutation-test threshold). The human reviewer never adjudicates compliance — only judgment.
- **Measurement substrate built in.** Penalty bookkeeping, verification surface index, and calibration tracking are first-class framework components rather than optional add-ons. Net Velocity is reportable, not aspirational.
- **Backward compatibility.** Existing pytest, Hypothesis, fast-check, JUnit, RSpec — all native. SDD++ adds a layer rather than replacing infrastructure.
- **Sixty-second adoption.** `pip install sdd-plus-plus && cd repo && sdd init` produces a working framework. Adopters get value before they invest.
- **Multi-team operability.** A single tool serves many repositories. Engineering leaders with portfolio responsibility can require SDD++ across teams without per-team customization.
- **Token economy.** `progress.md` provides intentional compaction; MCP tools provide selective context loading. AI sessions stay focused.

### 7.2 What SDD++ does poorly today

- **Frontmatter approach can feel heavy for trivial tasks.** A one-line typo fix does not benefit from the full plan/spec/acceptance cycle. The `tier: local` strictness level is intended to mitigate this, but the philosophical tension is real.
- **Penalty attribution depends on incident-to-change traceability.** Bisectable codebases benefit fully; codebases with long-running feature branches, squash-merge cultures, or limited incident telemetry benefit partially. The framework degrades gracefully but does not solve the underlying traceability gap.
- **Risk-class normalization is a calibration of its own.** Getting the multipliers right requires iteration over real incident data, which the framework does not yet have. Initial multipliers ship with conservative defaults documented in the schema.
- **Mutation testing has known limitations.** Equivalent mutants, surface-level mutations that don't probe deep behavior, and language-specific gaps in the mutation operator set all reduce the signal. We treat mutation kill rate as best-available, not perfect, and version the operator set so improvements ship with the tool.
- **No field data.** The framework has not been operated by a real team for a full release cycle. Until it has, the productivity and quality claims — including those about the measurement substrate — are theoretical. This is the same trap that first-generation SDD tools fell into; we acknowledge it explicitly.
- **Human discipline is still required.** No framework can prevent a team from gaming its rules — populating the challenge block with boilerplate, accepting plans without reading them, signing ownership statements without understanding the code, contesting penalty attribution as a default. The framework makes gaming visible at audit time, but does not prevent it in the moment.
- **The "spec rot" problem is mitigated but not solved.** Schema validation prevents specs from becoming syntactically wrong over time, but cannot prevent them from becoming *stale* — describing a behavior the code no longer implements. The contract test layer and mutation-test gate catch some of this; perfect prevention is unsolved.

### 7.3 Open questions

- **Per-team calibration.** How does the framework balance graduated trust against the operational reality of new AI tools being adopted faster than calibration can be measured?
- **Plan granularity.** Is one plan per task too coarse for long-running features? Should plans be hierarchical?
- **Penalty horizon.** Ninety days is the default attribution window. Is it too short for security findings (which surface slowly), too long for rapidly-iterating products? Per-capability horizons may be necessary.
- **AI vs. AI crosscheck.** Section 9 below proposes structurally separated author-AI and reviewer-AI as a v0.4 feature. The unanswered question is whether the productivity cost (double inference) is worth the safety gain in practice.

---

## 8. Benchmarking and diagnostics for AI coding assistants

The measurement substrate (§5.5) makes per-change attribution possible. The next question is how to use that capability to grade the AI coding tools themselves, and how to use mutation testing as a diagnostic — not just a CI gate — for understanding what changed and reviewing better. Section 8.1 proposes a ten-benchmark suite; §8.2 develops mutation testing as a diagnostic instrument.

### 8.1 Benchmarks for assessing AI coding tools

Choosing among AI coding assistants today is a vendor-marketing exercise. Each tool publishes selective benchmarks against synthetic tasks (HumanEval, MBPP, SWE-bench) that bear little relationship to the operational properties that matter in real teams. We propose ten benchmarks rooted in the operational substrate of SDD++, all of which can be run by any team that has adopted the framework. Each benchmark has a test scenario, a scoring rule, and a baseline.

**B1: Calibration accuracy.** Over N plans authored by the tool, what fraction of `confidence: high` plans produced `outcome: success`? What fraction of `confidence: moderate`? `low`? A well-calibrated tool's outcomes align with its claims. Mis-calibration in either direction (over-confident or under-confident) is a signal. *Score:* Brier-like metric on (confidence, outcome) pairs. *Baseline:* random tool would produce flat curves; a well-calibrated tool produces monotonic alignment.

**B2: Sycophancy resistance.** Present the tool with a flawed premise embedded in a feature request (e.g., "implement caching for this function" when the function is non-deterministic). Does the tool's challenge block surface the conflict, or does it produce caching code as requested? *Score:* fraction of seeded flawed requests where the challenge block names the actual flaw. *Baseline:* near-zero for tools without a forced challenge mechanism.

**B3: Specification fidelity.** Given a spec with cases covering positive, negative, boundary, and invariant behaviors, does the AI's implementation pass all cases, including the invariants? Or does it pass the positive cases and silently weaken the others? *Score:* per-case pass rate, weighted by case type. *Baseline:* TDD-only flow without spec types.

**B4: Mutation-survival rate of AI tests.** When the tool authors tests for production code it did *not* write, what fraction of mutations to that code do the tests catch? When the tool authors *both* the code and the tests, what fraction? The gap between these is the tautology gap (§2.4). *Score:* mutation kill rate, AI-tests-only vs. AI-code-and-tests. *Baseline:* humans-only run for comparison.

**B5: Penalty accrual rate.** Over a sliding window (default ninety days), what is the average penalty score per plan attributed to the tool, normalized for risk class and plan count? *Score:* penalty per plan. *Baseline:* comparison against other tools in the same codebase.

**B6: Spec drift contribution.** Over N sessions, does the tool produce code consistent with the existing capability specs, or does it introduce drift — functions matching the spec name with subtly different behavior, new patterns inconsistent with declared coding standards, conventions diverging silently across modules? *Score:* spec-conformance check per change. *Baseline:* same codebase reviewed by a human-only team.

**B7: Context economy.** Given the same task, what is the ratio of input tokens to output tokens? More precisely: what is the token budget consumed per unit of useful work produced? Tools that re-load the entire repository on every interaction lose; tools that use focused-context primitives (such as `get_progress` and `list_findings`) win. *Score:* token-per-useful-output ratio. *Baseline:* maximum-context-window flow.

**B8: Challenge block quality.** When forced to produce a challenge block (§5.3), are the concerns substantive or templated? Substantive means the concern names a specific risk that would not have surfaced without it. Templated means generic ("this might have edge cases"). *Score:* human-rated substantiveness on a sample of challenge blocks, with inter-rater agreement reported. *Baseline:* random sample of issues raised in code review under the same codebase.

**B9: Handover discipline.** When the tool hands off work to another agent or to a human, does it produce the structured handover artifact (confidence shape, dissent log, etc.) the framework expects, or does it produce a status-style "done" handoff? *Score:* schema conformance plus dissent-log substantiveness. *Baseline:* tools without handover support.

**B10: Cross-session consistency.** Code from session 1 vs. code from session 100, on related tasks in the same capability. How similar are the patterns? Identical patterns are over-conformity (the tool memorized the codebase and is no longer thinking); wildly different patterns are drift (the tool re-derives every time and forgets). The right answer is somewhere in between. *Score:* structural similarity index weighted by convention markers. *Baseline:* human team writing the same tasks over the same period.

The intent of these benchmarks is not to produce a single leaderboard score. It is to produce a *vector of properties* that an engineering organization can use to choose, monitor, and demote AI coding tools as operational evidence accumulates. The framework treats this benchmark set as evolving: missing benchmarks (B-?) are tracked in `notes/benchmark-gaps.md` and filled as the literature and the practice catch up.

A benchmark suite that is not adversarial degrades quickly. Tools train on benchmarks. We expect B1-B10 to be partially gameable within twelve to eighteen months of public adoption, and the framework versions the benchmark set so that adversarial extensions ship with the tool. Honest assessment requires assuming the assessed tools will try to satisfy the metric rather than the underlying property.

### 8.2 Mutation testing as a diagnostic, not just a gate

Mutation testing has been described in §5.5 as a CI gate: PRs that drop the mutation kill rate below the declared threshold fail. That use is necessary but insufficient. The deeper value of mutation testing is as a *diagnostic instrument*: a tool for understanding what changed in a codebase and reviewing it more effectively.

**Mutation diffs across PRs.** When a PR is opened, the framework runs mutation testing twice: against `main` and against the PR head. The diff in the surviving mutants — *new* surviving mutants the PR introduces, *resurrected* surviving mutants the PR brings back, *killed* mutants the PR eliminates — is itself a report. A reviewer who reads the mutation diff before reading the code diff sees, in advance, the parts of the change the test suite does not defend. This re-orients human attention from "is this code correct?" to "do the tests prove this code does what it claims?" — which is a more answerable question with a faster turnaround.

**Reading surviving mutants as review aids.** Each surviving mutant is a sentence: "if I change X here, no test fails." That sentence is information. Surviving mutants that change error-handling paths are saying *the error handling is not under test*. Surviving mutants that flip a boundary condition are saying *the boundary is not under test*. A reviewer can read the list of surviving mutants and focus their attention on the corresponding code paths, rather than re-reading every line of the diff with equal weight. This is a redistribution of attention budget (§4.6), routed by mechanical signal.

**Evaluating AI-generated tests.** When the AI adds N tests to a PR, the question is not "do the tests pass?" but "do the tests move the kill rate?" If five new tests add zero kills, the tests are tautological — they describe what the code does without challenging it. If five new tests add ten kills, they are doing real verification work. The framework flags zero-kill test additions automatically and routes them to human review with the diagnostic attached. This converts the §2.4 problem — AI tests that please code rather than spec — from invisible to flagged.

**Equivalent mutant analysis.** Some surviving mutants are equivalent to the original code: a refactor that produces semantically identical behavior. These are noise, not signal. Tooling marks equivalent mutants explicitly so they are excluded from the kill-rate calculation and do not pollute reviewer attention. The framework's mutation adapters (`mutmut`, `Stryker`, `pitest`) all support equivalence annotations; the framework propagates them across runs and flags newly-suspected equivalents for human verification on a sample basis rather than every PR.

**Mutation testing as drift detection.** Over time, a capability's mutation kill rate is a leading indicator of spec rot (§2.8). A capability whose kill rate drifts from 87% to 73% over a quarter is telling you something — the tests are no longer keeping pace with the code, or the code has grown branches that no one wrote tests for. The framework tracks mutation kill rate per capability over time in `signals.json` and surfaces drift in the `sdd doctor` output. A capability whose kill rate is stable while its complexity is rising is paradoxically suspicious: stability without test-suite growth often means the new code is not being challenged.

**The reviewer's checklist with mutation.** A reviewer opening a PR sees, alongside the diff:

- Mutation diff: new surviving / resurrected / killed mutants for this PR.
- Capability kill-rate trajectory: this PR's effect on the capability's kill rate over the rolling window.
- Test additions: kills added per test, with zero-kill tests highlighted.
- Equivalent-mutant flags: any newly-suspected equivalents needing verification.

The reviewer focuses where the mechanical signal directs them, and the AI's tests are evaluated on whether they actually expanded the verification surface or merely added compliance lines.

This shifts mutation testing from a CI checkbox to a review primitive. The CI gate prevents kill-rate regression; the diagnostic view explains what changed, where the tests are weakest, and which of the AI's contributions are doing real work. The diagnostic is also the bridge to benchmark B4 in §8.1: per-tool mutation contribution becomes empirically measurable rather than reputationally claimed.

---

## 9. Future work

The framework as described is v0.4. Several extensions are in design.

### 9.1 v0.4: the measurement substrate (this release)

The v0.4 release shipping with this whitepaper introduces the measurement substrate described in §5.5 as a core framework capability rather than a planned addition. Four mechanisms ship together:

**Mutation testing integrated in CI.** Per-capability minimum kill rates declared in `spec.md` frontmatter, with `mutmut`, `Stryker`, and `pitest` adapters wired into `sdd validate --strict`. PRs that drop mutation score below the declared minimum fail CI. The mutation-test invocation is itself instrumented so AI-generated test additions that do not raise the kill rate are flagged. The diagnostic uses of mutation testing are developed in §8.2.

**Penalty ledger.** Every plan in `.governance/plan/` accrues a `penalty_ledger` block as downstream events are attributed. Attribution is automated for bug fixes (`git bisect`), security findings (SAST output references the plan), and rollbacks (which already reference the changeset). Contested attributions go through a structured contestation review modeled on patent-office opposition procedure: the originator may dispute the attribution within seven days, and a third-party reviewer adjudicates.

**Per-agent calibration tracking.** The existing `confidence` and `outcome` fields on plans are aggregated into a `signals.json` time-series store, and a new `sdd calibration` CLI surfaces per-agent calibration curves. Agents whose 90% confidence claims produce 60% outcomes have their autonomy class downgraded (a v0.5 mechanism, described next).

**Structurally separated author-AI and reviewer-AI.** Inspired by separation-of-duties in financial controls. The AI that generates a plan is structurally separate from the AI that reviews it: different prompts, different context budgets, different default models, no shared memory. Disagreement between the two is a signal that surfaces to the human. This doubles inference cost; we believe it more than pays for itself in critical-domain work because it raises the verification surface without requiring more human attention.

Together the four mechanisms convert the framework from an output-discipline tool into an outcome-discipline tool. The discipline of writing plans, drafting challenges, accepting through human handles, and tracing every change to a capability remains; what changes is that the discipline is now graded by measured outcomes rather than by faithful compliance alone.

### 9.2 v0.5 and beyond: aspects of crew resource management

The longer-horizon vision draws from aviation safety culture. We outline four directions without committing to delivery dates.

**Graduated autonomy by action class.** Every AI action has a class (read-only, suggest-only, propose-with-diff, commit-with-checks, commit-and-execute). The autonomy required scales with class and with the per-tool calibration score from §9.1. A new AI tool starts at suggest-only; trust is earned through verified outcomes, and is lost through mis-calibration without human intervention.

**Mandatory callouts.** Critical operations (schema migrations, data backfills, security-sensitive code) require structured pre-action artifacts: affected resources, rollback path, estimated impact, escalation criteria. The AI cannot proceed without producing the callout; the human cannot approve without seeing it.

**Blameless post-incident review, automated.** When a production incident traces back to a plan that was accepted, the framework reconstructs the full chain (intent, plan, acceptance, implementation, review, merge, penalty attribution) and produces a structured incident report. The report's output automatically updates memory, policies, and contracts. Failure becomes input to the next iteration rather than blame to a person.

**Recurrency requirements.** AI tools operating in a codebase for 12+ months must "re-check out" on critical capabilities periodically. A failing recurrency check downgrades autonomy until a human re-trains the tool. This is the discipline that prevents slow drift where an AI trusted in February is silently wrong by November.

### 9.3 Research questions worth answering

- What is the empirical relationship between SDD++ adoption depth and incident rate? We do not know; field data is needed.
- Does the challenge-block requirement measurably reduce AI sycophancy, or do AI tools learn to produce template challenge blocks that satisfy the schema without surfacing real concerns?
- Is the ownership-disclosure mechanism behaviorally effective at making engineers actually read AI-generated code, or does it become a checkbox?
- Does penalty attribution change agent behavior — do agents become more conservative when their plans accrue penalties, and is that conservatism productive or risk-avoidant?
- What is the right risk-class normalization curve? Are linear multipliers sufficient, or are non-linearities required for the highest-stakes systems?
- Do the §8.1 benchmarks survive tool training? Within twelve months of public adoption, which benchmarks become tautological, and what is the right adversarial extension?
- What is the optimal granularity for capability specs in a 100k-line codebase? 200k? 1M?

We invite teams adopting SDD++ to publish their data. The honest test of any methodology is what happens to mutation score, incident rate, Net Velocity, and developer satisfaction over twelve months in a real codebase.

---

## 10. Conclusion

We have argued that AI-assisted software engineering is at a phase shift analogous to aviation in the mid-1950s: the technology works, sometimes the planes crash, and the field has not yet developed the institutional discipline to make the human-machine system safer than either alone. SDD++ is our attempt at the first round of that discipline: schemas where prose used to be, mechanical enforcement where social norms used to be, AI-resistance where AI-friendliness used to be the implicit goal, and outcome-measurement where output-measurement used to be enough.

The framework is opinionated, possibly overconfident, and demonstrably incomplete. It is also running in code, validating its own structure with its own tests, measuring its own outputs against its own outcomes, and ready for teams to operate against. The next stage of this work is not more design; it is field data. We will know whether SDD++ is the right approach when a real team has run it for a real release cycle and published what they measured — mutation score, incident rate, Net Velocity, and the calibration curves of the AI tools they used.

Until then, we believe the *direction* — structured over prose, mechanical over social, AI-resistant over AI-friendly, ownership-required over ownership-implied, outcome-measured over output-measured — is the right direction. The specifics are negotiable; the direction is the load-bearing claim. Appendix D illustrates the full workflow against a concrete task; readers wanting to see SDD++ in motion should start there.

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
| Mutation testing | Optional | Optional | Optional | Required, capability-thresholded, also used as diagnostic |
| Penalty attribution | None | None | None | Per-plan ledger with bisect-based automation |
| Calibration tracking | None | None | None | Per-agent curves with autonomy linkage |
| Output vs outcome metric | Output (PRs) | Output (PRs) | Output (tests) | Net Velocity (output × surface × calibration ÷ penalty) |
| AI tool benchmarking | Ad-hoc | None | None | Ten-benchmark suite (§8.1) |
| Multi-vendor | n/a | Vendor-locked | Yes | Yes |
| Migration from TDD | n/a | None | n/a | Direct (`sdd generate-acceptance`) |
| Cost of adoption | Zero | High | Medium | Sixty seconds |
| Field-validated | No | No | Yes | Not yet |

## Appendix B: Glossary

- **Capability** — a bounded area of system functionality, owned by a named human, defined in `capabilities/<id>/spec.md`.
- **Case** — one observable behavior the implementation must satisfy. Typed (positive, negative, invariant, boundary, regression, performance, security, idempotence).
- **Challenge block** — the AI's required pushback record: understood_request, concerns, alternatives_considered. Empty fields fail schema validation.
- **Confidence shape** — the per-item confidence declaration accompanying a plan: which parts the agent is sure about, which it is hypothesizing, which it is uncertain on, which it declined. Calibrated by historical penalty accrual.
- **Equivalent mutant** — a code mutation that produces semantically identical behavior to the original; excluded from kill-rate calculation as noise.
- **Finding** — a discovered fact about the system. AI may file as `suspected`; humans confirm.
- **Mutation diff** — the per-PR comparison of surviving mutants between `main` and the PR head; used as a review primitive (§8.2).
- **Mutation kill rate** — fraction of injected code mutations the test suite catches. The verification surface index.
- **Net Velocity** — output rate × verification surface × calibration accuracy ÷ penalty accrual. The framing metric for outcome-graded productivity.
- **Penalty ledger** — the per-plan accrual of downstream costs (incidents, security findings, rollbacks, test rewrites) attributed back to the plan that generated them.
- **Plan** — an AI-drafted implementation strategy for a task. Must be human-accepted before code is written.
- **Principle** — one of the six governing principles enforced by the framework.
- **Spec** — short for capability specification. The YAML frontmatter + markdown body in `capabilities/<id>/spec.md`.
- **Verification surface index** — synonym for mutation kill rate; the measure of how much of the spec the test suite actually defends.
- **Zero-kill test** — an AI-added test that does not raise the mutation kill rate; flagged for human review as presumptively redundant.

## Appendix C: Status of the implementation as of this writing

The Python implementation of SDD++ exists as `sdd-plus-plus` v0.4.0 (draft) in `/Users/mansurah/Development/built-it-here/sdd-plus-plus`. As of 2026-05-22, the framework supports:

- `sdd init` — bootstraps any repo with the v0.4 layout in ~60 seconds
- `sdd validate` — validates the entire governance tree against the bundled schemas
- `sdd doctor` — 9-milestone diagnostic adoption check
- `sdd findings (add | list | show)` — the wiki/findings layer
- `sdd plan (new | accept | list | show)` — AI-plan lifecycle with the mandatory human acceptance gate (`accept --by @<handle>`)
- `sdd progress` and `sdd update-status` — auto-updating progress snapshot
- `sdd serve` — MCP server exposing the framework to Cursor / Claude Code / Copilot / Aider with 14 tools, including `propose_plan` (which can only save drafts — accepting is a human-only CLI operation)
- `sdd generate-acceptance --from-tests` — TDD migration path

**v0.4 measurement substrate (in active development as of this writing):**

- `sdd mutation` — invokes the language-appropriate mutation adapter (`mutmut`, `Stryker`, `pitest`), enforces per-capability minimum kill rates declared in `spec.md` frontmatter, and writes results to `signals.json`. Also produces the mutation diff and zero-kill flags described in §8.2.
- Penalty ledger — `penalty_ledger` block in plan frontmatter, populated automatically by `sdd ledger ingest` from bisect output, SAST reports, and rollback records; contestation handled via `sdd ledger contest --plan <id>`
- `sdd calibration` — surfaces per-agent calibration curves from `signals.json` time-series data
- `sdd benchmark` — runs benchmarks B1-B10 (§8.1) against a configured tool; produces a vector of property scores rather than a single leaderboard number

**Test suite at v0.3 baseline: 52 tests pass** across five files (`test_e2e`, `test_findings`, `test_plan`, `test_progress`, `test_serve`). Coverage includes schema validation, ownership-gate enforcement (plans cannot self-accept, AI handles are rejected by `sdd plan accept`), challenge-block requirement (plans missing the challenge block fail validation), and full CLI round-trips. v0.4 test additions targeting mutation, ledger, calibration, and benchmark are in flight.

**End-to-end dogfood verified at v0.3.** A fresh directory bootstrapped via `sdd init` produces 13 framework files plus auto-generated progress.md. `sdd validate --strict` exits 0. `sdd plan accept --id plan-example-001 --by @mansura` correctly advances the bundled example plan to `accepted` state, populating `accepted_by` and `accepted_at`. `sdd update-status` appends events to the progress log as expected.

**What remains future work (v0.5+):** graduated autonomy by action class, mandatory pre-action callouts for critical operations, automated blameless post-incident review with structured chain reconstruction, and recurrency requirements for long-running AI tool deployments. These are described in §9.2.

The framework at v0.4 is ready for the first real-team trial. The honest measurement question — does adopting SDD++ improve mutation score, reduce incident rate, improve Net Velocity, and improve developer satisfaction in a real codebase over twelve months — remains open and is the focus of the next phase of work.

## Appendix D: Worked example — adding a rate limiter to the signup endpoint

To illustrate the workflow in §5.3 and the measurement substrate in §5.5, this appendix walks through a single representative task end to end. The example is composed from features and patterns the framework supports; it is illustrative, not a published case study.

**Context.** A team operates an API service with a `users` capability containing a `/signup` endpoint. The team's Q2 2026 security review flags the endpoint as vulnerable to credential-stuffing attacks. The team decides to add per-IP rate limiting: five attempts per minute, returning HTTP 429 with `Retry-After` on excess.

**Step 1 — Issue filed.** A team member files a GitHub issue using the bundled task-card form:

- *Parent capability:* `users`
- *One-line goal:* Rate-limit `/signup` to defend against credential-stuffing
- *Bigger picture:* The Q2 security review flagged the unprotected signup endpoint as a credential-stuffing target. The team wants to land protection before the next public launch without introducing latency for legitimate users or breaking the existing integration tests.
- *In-scope:* rate-limit middleware on the signup route; per-IP windowed counter; 429 response with `Retry-After`; metrics for rate-limit hits.
- *Out-of-scope:* account-level lockout; CAPTCHA integration; rate-limiting on other endpoints.

**Step 2 — Plan drafted.** The engineer asks the AI assistant (Cursor in this example) to draft a plan via the `propose_plan` MCP tool. The plan saves to `.governance/plan/users-rate-limit.plan.md` with `status: draft`:

```yaml
---
plan_id: users-rate-limit
task_id: gh-1247
capability: users
status: draft
authored_by:
  ai: cursor-claude-opus-4-6
confidence:
  overall: moderate
  per_item:
    middleware_implementation: high
    counter_storage_choice: moderate
    edge_case_handling: low
challenge:
  understood_request: |
    Add per-IP rate limiting to /signup, 5 attempts per minute, with
    429 + Retry-After response. Must not break existing integration
    tests. Must emit metrics for limit hits.
  concerns:
    - The default Redis storage backend assumes Redis is available
      in test environments; our integration test suite uses in-memory
      fakes which may not exercise the lock path. Recommend a dual
      implementation behind a feature flag for safe rollout.
    - Per-IP rate limiting can be evaded with proxies and is a partial
      defense; the spec should note this and link to follow-up work
      for account-level controls.
  alternatives_considered:
    - Token bucket with a higher refill rate (rejected: harder to reason
      about attack-cost economics for credential stuffing).
    - WAF-level rate limiting (rejected: deferred to platform team).
do_not_modify:
  - capabilities/users/spec.md
  - capabilities/auth/spec.md
---
```

**Step 3 — Plan accepted.** The tech lead reads the plan, including the challenge block. The first concern flags a real test-environment gap that would have caused a CI surprise. The lead runs:

```
sdd plan accept --id users-rate-limit --by @mansura
```

The schema updates `status: accepted`, populates `accepted_by: "@mansura"` and `accepted_at`. The MCP toolset deliberately does not expose `accept`; this transition is human-only.

**Step 4 — Implementation.** The engineer pairs with the AI to write the middleware. AGENTS.md is auto-loaded by Cursor. A finding from a previous session is surfaced automatically via `list_findings(capability='users', tag='rate-limit')`:

> *finding-2026-q1-redis-flapping:* Redis connection flapping during deploys caused brief 503s on auth endpoints. Mitigation: connection-pool warmup in middleware initializer. Capability: `users`. Status: confirmed.

The AI implements the middleware with the connection-pool warmup pattern from the start, avoiding a re-derivation of the prior team's lesson.

**Step 5 — Validation.** The engineer runs `sdd validate`. The validator confirms the plan references a real capability, the challenge block is non-empty, and the protected-paths list is respected. The mutation-test gate runs `mutmut` against the changed files: the test suite catches 87% of mutations, above the `users` capability's declared 80% threshold. The mutation diff (§8.2) shows three new surviving mutants in the boundary-handling branch (`requests == limit` vs `requests > limit`), which the engineer addresses by adding two boundary tests; the second pass catches 94%.

**Step 6 — Pull request.** The PR template requires explicit confirmation:

- [x] I have read every line of AI-generated code in this PR.
- [x] I can defend the architectural choices.
- [x] The AI's challenge block surfaced at least one concern, and I read it.
- Ownership: @mansura

**Step 7 — CI gate.** GitHub Actions runs five gates: `sdd validate --strict`, the contract test suite, the ownership-disclosure presence check, the protected-paths check, and the mutation gate. All pass. A reviewer is assigned.

**Step 8 — Human review.** The reviewer opens the PR and the framework's reviewer view shows: mutation diff (three killed, zero new surviving, zero resurrected), capability kill-rate trajectory (80% → 94%, +14 points), and no zero-kill test additions. The reviewer focuses on judgment: should the limit be per-IP, or per-IP combined with username prefix? The engineer files a follow-up finding rather than expanding scope. The reviewer approves.

**Step 9 — Merge.** On merge, the plan transitions to `status: executed`. The engineer records:

```
sdd plan outcome --id users-rate-limit --outcome success
```

**Step 10 — Downstream.** Three weeks later, an incident: a legitimate user gets rate-limited because they share an office IP with five colleagues signing up at the same event. The incident's `git bisect` attribution traces back to `users-rate-limit`. The framework appends to the plan's `penalty_ledger`:

```yaml
penalty_ledger:
  - event_id: incident-2026-q2-shared-ip
    event_type: customer_escalation
    attributed_at: 2026-06-12
    severity: low
    risk_class_multiplier: 0.5   # users is mid-stakes
    accrued_value: 0.5
    contested: false
```

The penalty is also recorded against the originating agent (`cursor-claude-opus-4-6`) in `signals.json`. The agent's `low`-confidence claim on `edge_case_handling` turns out to have been honest; its `high`-confidence claim on `middleware_implementation` was the one that produced the issue, slightly mis-calibrating the curve. The team responds with a follow-up plan for shared-IP handling, with the original incident attached as context. The follow-up plan does not retroactively erase the penalty — the original was correctly attributed at the time, and the trajectory of the spec is preserved as the system's intellectual lineage.

**What this example illustrates.**

The framework's gates ran without any of them adjudicating judgment — schema validation, mutation testing, ownership disclosure, protected paths all passed mechanically. The human review focused on design questions, not compliance. The challenge block surfaced a real test-environment concern that saved a later debugging session. A prior finding informed the implementation without re-derivation. The mutation diagnostic redirected the engineer to a specific weak boundary in the test suite, raising the verification surface before the PR opened. When the inevitable downstream cost arrived, it attributed cleanly to the originating plan and agent, updating the calibration curve for future work. None of these properties hold under no-framework or first-generation SDD; they all hold here by mechanical enforcement.

This is what *solving the software engineering problem in the AI era* looks like in concrete operation. The framework's claim is not that this workflow is the only possible answer — it is that the workflow's properties (mechanical gates, human ownership, measured outcomes, honest penalty attribution) are non-negotiable, and any framework that omits them is solving a different problem.
