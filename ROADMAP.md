# Roadmap

> The job of this roadmap is to make our priorities legible and our gaps honest. If a release ships without moving us closer to the v0.3 north star, we shipped the wrong release.

---

## North star

**An engineer who uses sdd-plus-plus daily can explain, in their own words and without referring to the spec, the architectural trade-offs of the last feature they shipped.**

This test comes from [Ka Mok's "Future of Software Engineering Part 1"](https://medium.com/@hey.kamok/future-of-software-engineering-part-1-the-individual-ebe1eb9357a6). It is the single most important measure of whether the framework is doing its job or quietly automating engineering judgment away.

If yes: the framework is making senior thinking *visible*, juniors are absorbing it, and judgment is compounding across the team.

If no: the framework has become an excuse. Engineers ship correct code without understanding why it's correct. That is exactly the failure mode the framework was built to prevent — and the one it could accidentally accelerate if we don't build toward this test.

---

## Where we are — v0.1 (current)

Shipped:

- `sdd init` — bootstrap any repo with `.governance/`, `AGENTS.md`, `.github/` templates, and contract tests in ~60 seconds
- `sdd validate` — schema + cross-reference validation across the framework
- `sdd generate-acceptance --from-tests` — produce a starter acceptance spec from existing pytest tests
- `sdd doctor` — 8-milestone adoption diagnostic
- Three schemas (task-card, capability-spec, acceptance) battle-tested in bee-skill-registry
- AI-resistance: `authored_by.ai_assistance: forbidden` defaults; case_id linkage required; orphan-assertion lint

What v0.1 solves: team coordination — junior ignores docs, senior overbuilds, AI tests please code, review burden.

What v0.1 does NOT solve: individual engineering judgment development. The framework externalizes the senior's thinking into the spec so juniors get correct *outputs*. The risk is that they never develop their own thinking.

---

## v0.2 — Infrastructure depth

The plumbing that makes v0.1 more robust. Priority-ordered.

### 1. `contracts.lock` — drift detection on public interfaces

Content-hashed snapshot of every function signature, schema, and exported type. A PR that changes a public surface fails CI unless the lock is explicitly approved (`sdd contracts approve`). Pays back the first time a junior changes a signature without realizing.

Estimated effort: ~300 LOC + CI step.

### 2. `sdd inject-context` — AI context auto-loading

Update `.cursorrules` / `AGENTS.md` / `.github/copilot-instructions.md` with the active branch's task card. Closes the "AI ignores the spec" loop mechanically — the spec is in the AI's context window before the engineer types the first prompt.

Estimated effort: ~150 LOC.

### 3. `sdd test --mutation` — mutation testing wrapper

Wrap `mutmut` (Python) / `Stryker` (JS) with per-capability mutation score thresholds defined in `acceptance.yaml`. Surfaces AI-generated tests that please the code, mechanically. Highest-leverage defense against the "tests pass, behavior wrong" anti-pattern.

Estimated effort: ~200 LOC + per-language adapter.

### 4. `signals.json` — provenance time-series

Every PR emits a structured record: which intent it satisfied, which cases it covered, mutation score delta, drift detected, AI assistance disclosed. Goes into a per-repo time-series store. The data layer that lets you answer "is SDD++ working in this repo?" mechanically.

Estimated effort: ~250 LOC + aggregation script.

### 5. IDE extension (Cursor / VS Code)

Hover-over-test shows the case_id it satisfies. Autocomplete in `acceptance.yaml`. Live schema validation. Drift warnings inline. The biggest investment in this release line — defers until v0.4 unless an external contributor takes it.

Estimated effort: 30–50 engineer-weeks. Likely an external contribution.

---

## v0.3 — Judgment Development (the north star release)

The release that targets the Ka Mok test directly. This is the hardest item on the roadmap because it asks a *tool* to do something tools usually fail at: develop the *thinking* of the humans using it.

The principle: a tool can't teach judgment. But it can structurally *force articulation*, *invert authorship*, and *track comprehension persistence*. Those three together create the conditions under which judgment develops — even if the framework itself is never the teacher.

### 1. `sdd intent` — pre-implementation intent capture

Before AI generates code on a branch, the engineer writes a 50–200-word *intent statement*:

```
What I think this code should do: ...
Why this approach (not alternatives): ...
What could go wrong: ...
What I'd do differently if X were not a constraint: ...
```

The intent is saved to `.governance/intents/<task-id>.intent.yaml` and signed by the author. AI sees the intent in its context. Critically: the intent is captured *before* the AI overwrites the engineer's thinking with code.

After implementation, the engineer reviews their own intent against what shipped. The framework saves the diff. Patterns of "intent ≠ shipped" are tracked over time — they're the canary for "AI is making the decisions, I'm just clicking accept."

This is also Ka Mok's rule #1 ("solve the problem yourself first") made mechanical. The engineer doesn't have to solve the *whole* problem first — but they have to think hard enough to write the intent.

### 2. `sdd reflect` — post-merge reflection

Within 48 hours of a merge, the framework prompts the author for a short reflection:

```
In your own words, why did this design work?
What trade-off did you make that someone reviewing the spec wouldn't see?
What would you do differently next time?
```

No grading. No public exposure. Just structured forced articulation. The reflections are stored as part of the provenance chain. Over time, the team can see whether reflections are getting more sophisticated — that's the signal that judgment is developing.

The framework *cannot* read the reflection content to grade it. But it can detect empty/template/AI-generated reflections (zero or boilerplate content) and flag them. The point isn't to surveil — it's to make articulation a habit.

### 3. `sdd defend` — inverted authorship for juniors

For tasks tier `team` or higher, juniors can opt into *inverted authorship mode*: before they read the senior's spec, they author their own version. The framework diffs the two — junior's spec vs. senior's spec — and surfaces it as a *conversation*, not a handoff.

This is the practice "juniors author spec drafts, seniors critique" operationalized. The framework cannot make seniors critique well, but it can put the diff in front of them at the right time.

A team can configure: "every junior PR in their first 6 months uses inverted authorship mode by default." Optional, recommended, configurable.

### 4. `# why:` annotations on contract tests

Every contract test gets a `# why:` comment from the author explaining their understanding of why the test matters:

```python
def test_minimum_valid_skill_accepted():
    # case_id: minimum-valid-skill-accepted
    # why: This is the canonical positive path. If this fails, no skill can register.
    #      The agentskills.io public spec hinges on this — every downstream check assumes it.
    ...
```

`sdd validate` checks that every test has a non-empty, non-template `# why:`. Empty or generic ("# why: covers the spec") fails the gate. This is light enforcement of "you cannot ship code you cannot explain."

For AI-generated tests: the human author owns the `# why:` line. AI is forbidden from generating it. (Schema field: `test_quality_gates.why_comment_is_human_authored: true`.)

### 5. `sdd probe` — periodic comprehension spot-checks

Once a quarter (or on demand), the framework picks a random feature the engineer shipped 30+ days ago and asks them to answer one question about a specific design choice:

```
On 2026-04-12 you shipped BBS-127. The task card listed
`non_goals: ["Do not refactor auth_middleware"]`.

In your own words: why was that non-goal there?
```

Answer goes into a private record. Over time, the team can see whether comprehension persists past the shipping moment. If the engineer answers "I don't know, the senior wrote that" — that's *useful information*, not a punishment. It tells the team that the spec succeeded in shipping but failed in teaching.

Not graded. Not exposed. Diagnostic only.

### 6. Authorship balance metric

`sdd doctor` adds a new milestone: "spec authorship balance — every engineer over the last quarter authored at least one capability or acceptance spec, not just consumed."

The framework can't enforce this — but it can surface it. A team where one senior authors 100% of the specs and three juniors author 0% is a team where the framework is preventing junior judgment from developing. That's worth seeing.

### Cultural practices v0.3 documents but cannot enforce

Some things tooling cannot do. The release includes a `judgment-practices.md` doc that codifies:

- Code review asks "would you have made this decision without the spec?" — every time, for every junior PR
- Juniors author spec drafts; seniors critique rather than hand specs down
- Reviewers grade `# why:` comments harder than they grade code
- Quarterly retrospective: pick three recent features; ask the authors to explain trade-offs from memory; compare to written specs

The framework provides the substrate. The team builds the practice. We say so explicitly.

---

## v0.4 — Crew Resource Management (the long horizon)

Drawn from aviation safety culture, applied to AI-assisted teams. Speculative — buildable but expensive. Items here are intentions, not commitments.

- **Graduated autonomy by action class** — per-domain, per-action-class trust scores for each AI assistant. Read-only is free; commit-and-execute requires recent track record.
- **Calibrated confidence on every AI claim** — AI emits probability, framework measures calibration over time and degrades overconfident models.
- **Mandatory callouts for critical action classes** — schema changes, data migrations, security-sensitive code require structured pre-action artifacts.
- **Two-AI structural separation** — author-AI and reviewer-AI cannot share memory; disagreement is the gate to merge.
- **Blameless post-incident review** — when something breaks, the framework reconstructs the decision chain and auto-updates memory / policy / contracts.
- **Recurrency requirements** — periodic re-qualification of AI trust grants against evolving codebases.

The deeper question this release line is heading toward: software engineering safety culture is at the equivalent of aviation in 1955. Cofly is what 1980s aviation looks like. We don't have to build it all, but we should be pointed at it.

---

## How to track this

Each release line has acceptance criteria in `.governance/acceptance/` (in the sdd-plus-plus repo itself — we dogfood). The Ka Mok test is the highest-priority case in `judgment-development.acceptance.yaml`:

```yaml
id: north-star-test
kind: invariant
description: |
  Sample five engineers using sdd-plus-plus for 90+ days.
  Ask them to explain trade-offs of their most recent feature without spec access.
  At least 4 of 5 give substantive, accurate answers.
priority: critical
```

We measure this. If we ship features but the test gets worse, we shipped the wrong features.

---

## Non-goals (this roadmap)

To prevent scope drift, we are explicit about what we will NOT do:

- **Replace TDD.** sdd-plus-plus elevates and structures TDD. It does not replace pytest, Jest, Hypothesis, fast-check, mutmut, Stryker — those stay native.
- **Build a proprietary AI assistant.** The framework is AI-tool-agnostic. AGENTS.md works for Cursor, Claude Code, Copilot, Aider, and any future entrant.
- **Build a CI/CD platform.** We ship GitHub Actions workflows because that's where most teams are. GitLab/Jenkins/CircleCI versions are welcomed as community contributions, not core scope.
- **Build an IDE.** The IDE extension is a thin layer on existing IDEs. We don't compete with Cursor/VS Code/JetBrains.
- **Solve the AGI question.** Per Ka Mok: human steering is permanent, not temporary. The framework's design assumes that's true. If LLMs reach AGI, this framework is obsolete — and that's fine.

---

## Contributing

Roadmap items move based on:

1. **The Ka Mok test trajectory.** Features that move the test answer toward "yes" get priority over features that just add capability.
2. **Adoption data.** When we have `signals.json` running across multiple repos, we'll prioritize based on what's actually friction in real teams.
3. **Community contributions.** Items marked "estimated effort" or "external contribution welcome" are explicit invitations.

File an issue with `enhancement` label to propose a roadmap addition. Include: which release line, what problem it solves, why now.
