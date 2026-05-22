# Research analysis — mutation testing for sdd-plus-plus

> **The question this research answers.** Coverage tells us a line was executed. It does not tell us whether the test would have noticed if that line were wrong. sdd-plus-plus already binds tests to acceptance assertions by `case_id` — does it have a way to verify those tests actually assert what acceptance claims? Not yet. Mutation testing is the gap.

This is a research-grounded analysis, not a marketing document. Where the evidence is thin, it says so. Where the published prior art is adjacent rather than direct, that's flagged.

---

## 1. The gap mutation testing closes

Line and branch coverage prove *execution*. They prove nothing about whether the test would distinguish correct code from incorrect code. The canonical example: a function `is_adult(age) -> bool` returning `age >= 18`, exercised by a test that asserts `is_adult(25) is not None`. Line coverage is 100%. Mutate `>=` to `<` and the assertion still passes — the test is decorative.

A widely-cited 2025 case study reported a Python codebase with 96% line coverage and 93% branch coverage but a **34% mutation score** — meaning two thirds of the surviving production bugs would not have been caught by the existing tests despite "good" coverage [^1].

Mutation testing answers a different question: *if the implementation drifted in some specific syntactic way, would the test suite notice?* The mutation score is:

```
MS = killed_mutants / (total_mutants − equivalent_mutants)
```

A test suite that kills every non-equivalent mutant has mutation score 1.0. Jia & Harman's 2011 IEEE TSE survey is the canonical reference and the source most subsequent work builds on [^2].

For sdd-plus-plus, the relevance is sharper than for a generic codebase. The framework's whole accountability chain is `task → case_id → test`. Mutation testing is the audit that closes that chain — it answers *"does the test bound to this case_id actually exercise the asserted behavior?"*

## 2. Mutation operators and signal-to-noise

The standard operator families, drawn from PIT's industrial taxonomy [^3]:

- **Arithmetic (AOR)** — `+ → -`, `* → /`. High signal on numeric code; noisy on counters.
- **Relational (ROR) / Conditionals Boundary** — `< → <=`, `== → !=`. **Highest signal of any operator class.** Off-by-one bugs map directly here, and acceptance criteria with boundary cases (e.g. "rejects empty input", "accepts maximum length") test exactly this surface.
- **Logical / Conditional (COR, NEG)** — `and ↔ or`, negate conditions. High signal.
- **Return-value replacement** — substitute the return with a default. **Cheap and brutal** — catches missing assertions immediately.
- **Statement deletion (SDL)** — remove a statement. Strong but generates many equivalents on dead code or defensive null-checks.
- **Constant replacement (CRCR)** — `0 → 1`, swap literals. Mixed signal.

PIT explicitly ships a curated **DEFAULTS** group rather than the full operator set because industrial adoption requires a tight signal-to-noise ratio. A capability-spec-driven workflow doesn't need every operator — it needs the operators most likely to expose tests that pass without asserting.

**Practical recommendation for sdd-plus-plus**: start with relational, conditional, negation, and return-value replacement. Defer statement-deletion and constant-replacement to a second-tier opt-in mode for capabilities where authors want maximum rigor.

## 3. Python tooling landscape (2024–2026)

| Tool | Stars | Last activity | Verdict |
|---|---|---|---|
| **mutmut** | ~1.1k | v3.3.0 May 2025, actively maintained | **Recommended default** |
| **cosmic-ray** | ~800 | 1.1.0a1 alpha 2025; distributed mode | Power users / large codebases |
| **MutPy** | ~500 | Sporadic; commits stale 2+ years | Avoid for new work |
| Others (Mutatest, Poodle) | small | Stale (2–6 yr) | Avoid |

**mutmut** is the right pick for sdd-plus-plus. It has the strongest maintenance signal, the simplest pytest integration (zero config in most cases), and a built-in test-mutant mapping that runs only the tests that cover each mutant. v3 rewrote the executor for parallel speed. Pain points are real but bounded: the operator set is less customizable than cosmic-ray's, and HTML reporting is historically thin [^4].

**cosmic-ray** is worth documenting as a power-user option specifically because of its Celery/RabbitMQ-based distributed execution — genuinely unique in the Python landscape and relevant for large codebases where mutmut's per-machine concurrency caps out [^5]. Heavier configuration burden makes it the wrong default.

**MutPy** has the strongest operator catalog academically (the 2024 SBQS comparison study found it still produced the strongest fault model) but maintenance has lapsed [^6]. Not appropriate for a tool that we're recommending to other teams.

Newer entrants worth knowing about but not yet betting on: Trail of Bits published advocacy pieces in 2025 and announced mutation tooling explicitly designed for LLM-driven workflows in 2026 [^7] [^8]; an arXiv preprint explores LLM-guided operator selection in Python [^9].

## 4. The equivalent mutant problem

The largest practical obstacle to mutation testing adoption. An equivalent mutant is semantically identical to the original — `i++` vs `i = i + 1`, a constant whose value is overwritten before use, a `>` vs `>=` on a value that's never at the boundary. No test can ever kill it. Without mitigation, teams spend hours triaging surviving mutants that aren't actually bugs.

Mitigations that work, in order of cost-effectiveness:

1. **Arid-line filtering.** Google's approach: skip lines with no statement coverage, and skip lines deemed "arid" — logging, trivial getters, defensive guards. This alone dropped their false-positive surface materially [^10]. *This is the single biggest win and the cheapest one to ship.*
2. **Trivial Compiler Equivalence (TCE).** Papadakis et al. 2015 — compile mutants and compare machine code; identical bytecode means equivalent. Detects ~30% of equivalents in C, ~54% in Java [^11]. Python's lack of a stable bytecode-optimization layer weakens naive TCE, but AST normalization + `dis` captures a useful subset.
3. **Manual review.** Beller et al.'s Facebook study found developers spent meaningful time triaging but found ~half of surviving mutants were genuinely useful [^12]. Acceptable cost if filtering is doing its job.
4. **LLM-based detection.** Recent arXiv work shows promise but accuracy is below classical TCE for high-precision use [^13]. Worth watching, not worth depending on yet.

**Industry consensus to budget for**: ~20–40% of surviving mutants are equivalent or uninteresting without filtering. With Google-style arid-line filtering, that drops to single digits.

For sdd-plus-plus this maps directly: ship arid-line filtering by default, and provide an inline `# sdd: mutation-equivalent` marker so authors can suppress without editing config.

## 5. Performance and incremental strategies

Naive mutation testing is N × test-suite runtime where N is the mutant count, **typically 10–100× slower than the base test suite** [^14]. Without mitigation, mutation testing in CI is dead on arrival.

Strategies that work:

- **Test-mutant mapping.** Run only the tests whose coverage includes the mutated line. mutmut and PIT both do this. Single biggest speedup.
- **Incremental analysis.** PIT's `withHistory` flag stores hashes and skips unchanged mutants [^15]; mutmut caches results locally between runs.
- **Diff-scoped runs.** Mutate only changed files. PIT's `scmMutationCoverage` with `ADDED,MODIFIED`. **Google runs mutation testing only on the diff of each code review, not the whole codebase** [^10] — at 6,000+ engineers, this is the only model that scales.
- **Parallelization.** cosmic-ray's Celery model; mutmut v3 improved concurrency on a single machine.

The sdd-plus-plus angle that makes this fast is the `case_id` linkage itself. We don't need to mutate the whole codebase. We need to mutate the lines covered by tests bound to the `case_id`s that changed in the diff. That's a much smaller surface than even Google's diff-scoped model, because the scope is already declared in the capability spec.

## 6. CI integration patterns that survive contact with reality

Three established patterns:

1. **PR-incremental, soft gate.** Mutate only changed lines; post the score as a PR comment; don't block. This is the Google model.
2. **Nightly full run, hard gate on regression.** Full mutation suite runs at night; CI fails only if the score *drops* below baseline. Trendyol publishes this approach on the Stryker stack [^16].
3. **Per-PR with budget cap.** Wall-clock budget (e.g. 5 minutes) per run; catches the easy stuff, defers the rest.

**Thresholds people actually use.** Stryker.NET's defaults — `high: 80, low: 60, break: 50` — are widely cited [^17]. **75–80% mutation score is a realistic target for new code; 60% is a sensible floor for legacy.** Chasing 100% wastes time on equivalent mutants. Beller et al.'s strong claim from the Facebook study: dogmatic high thresholds *reduce* adoption — developers disengage when surviving mutants are uninteresting [^12].

For sdd-plus-plus: soft gate per-PR on changed `case_id`s, hard gate only on regression vs baseline. Never block on absolute threshold. The capability spec's `definition_of_done` already supports `verifiable_by: mutation_score` — wire it as guidance, not enforcement.

## 7. Mutation testing in spec-driven workflows — honest prior art

This is where the evidence is **thinnest**, so it's flagged honestly.

Direct prior art on "mutation testing for acceptance-criteria-linked tests" is scarce. The closest published precedents:

- **TDD + Mutation (TDD+M)** — Szlosek et al. showed TDD plus mutation analysis yields tests with higher fault-detection power than TDD alone [^18]. The mechanism is the same one sdd-plus-plus would exploit: the spec tells you *what* to assert; mutation tells you whether you actually did.
- **Property-Based Mutation Testing** — Bartocci et al. 2023 combine properties with mutants and measure whether the property would catch a fault [^19]. Conceptually closest to spec-driven: the property plays the role of the acceptance assertion.
- **BDD/Gherkin + mutation** — no canonical paper. The BDD literature treats acceptance criteria as executable specs but doesn't measure their *adequacy*. An open hole in the literature that sdd-plus-plus partially fills.

**The case_id angle is novel-adjacent, not novel.** The closest published precedent is Google's diff-scoped, productive-mutants approach: scope mutation to the units linked to a change, not the whole codebase. Applied to sdd-plus-plus: scope mutation to the lines covered by tests bound to a given `case_id`. If mutating those lines doesn't break the bound test, the test doesn't actually assert what the acceptance criterion claims.

This is **principled novelty, not invention from scratch**. The framing in the design spec reflects that.

## 8. Where mutation testing genuinely doesn't help

Honest critique, drawn primarily from Beller et al. [^12] and the Trail of Bits 2025 piece [^7]:

- **Orchestration and glue code.** Code that's mostly function calls, DI wiring, route declarations. Mutants are trivially equivalent or don't compile. Low signal-to-noise.
- **Integration and end-to-end tests.** Too slow to mutate at scale; the test-mutant mapping degrades because every test touches everything.
- **Stochastic code.** Anything with randomness, time, network. Flaky tests look like inconsistent mutant kills and poison the score.
- **False confidence from high score with weak operators.** A 95% mutation score with only constant-replacement and statement-deletion operators is worse than 70% with relational and conditional. **The score is only as meaningful as the operator set.**
- **Equivalent mutant treadmill.** Without filtering, the #1 abandonment reason in the Facebook study.

Trail of Bits' argument lands: **use mutation testing as a diagnostic, not a gate**. The framing for sdd-plus-plus follows this — mutation testing surfaces tests that pass without asserting, and prompts the author to strengthen them. The capability does not exist to produce a number for a dashboard.

---

## Synthesis for the design spec

The design that emerges from this research:

- **Tool**: mutmut as the default. Document cosmic-ray as a power-user fallback for distributed CI.
- **Scope**: only mutate lines covered by tests bound to `case_id`s in the changed diff. This is the framework-native acceleration that nothing else has.
- **Operators**: relational, conditional, negation, return-value replacement by default. Statement-deletion and constant-replacement as opt-in.
- **Score target**: 75% per `case_id` as guidance, 60% floor for legacy code. Never an absolute hard gate.
- **CI gating**: soft (warning) per-PR on changed `case_id`s; hard gate only on regression vs baseline.
- **Equivalent mutants**: ship arid-line filtering by default, plus an inline `# sdd: mutation-equivalent` marker. Budget 20–30% suppression on legacy code.
- **Framing**: diagnostic, not score-as-KPI. The capability surfaces weak tests; humans strengthen them.

---

## References

[^1]: ["The AI Reported 93.1% Coverage. It Was 34%," dev.to (2025)](https://dev.to/jghiringhelli/the-ai-reported-931-coverage-it-was-34-290k)
[^2]: [Jia & Harman, "An Analysis and Survey of the Development of Mutation Testing," IEEE TSE 2011](https://mutationtesting.uni.lu/survey.pdf)
[^3]: [PIT Mutation Operators](https://pitest.org/quickstart/mutators/)
[^4]: [mutmut on GitHub](https://github.com/boxed/mutmut)
[^5]: [cosmic-ray docs — Distributed Mutation Testing](https://cosmic-ray.readthedocs.io/en/stable/tutorials/distributed/index.html)
[^6]: [Static and Dynamic Comparison of Mutation Testing Tools for Python, SBQS 2024 (ACM)](https://dl.acm.org/doi/10.1145/3701625.3701659)
[^7]: ["Use mutation testing to find the bugs your tests don't catch," Trail of Bits 2025](https://blog.trailofbits.com/2025/09/18/use-mutation-testing-to-find-the-bugs-your-tests-dont-catch/)
[^8]: ["Mutation testing for the agentic era," Trail of Bits 2026](https://blog.trailofbits.com/2026/04/01/mutation-testing-for-the-agentic-era/)
[^9]: ["Large Language Models for Equivalent Mutant Detection," arXiv:2408.01760](https://arxiv.org/html/2408.01760v1)
[^10]: [Petrović & Ivanković, "State of Mutation Testing at Google"](https://research.google/pubs/state-of-mutation-testing-at-google/)
[^11]: [Papadakis et al., "Trivial Compiler Equivalence," ICSE 2015](http://web4.cs.ucl.ac.uk/staff/Y.Jia/resources/papers/PapadakisJHT2015.pdf)
[^12]: [Beller et al., "What It Would Take to Use Mutation Testing in Industry — A Study at Facebook," ICSE-SEIP 2021](https://arxiv.org/pdf/2010.13464)
[^13]: [Same as ^9]
[^14]: [Frankel, "Faster Mutation Testing"](https://blog.frankel.ch/faster-mutation-testing/)
[^15]: [PIT Incremental Analysis](https://pitest.org/quickstart/incremental_analysis/)
[^16]: [Trendyol — PIT Mutation Testing on CI/CD Pipeline](https://medium.com/trendyol-tech/pit-mutation-testing-on-ci-cd-pipeline-1298f355bae5)
[^17]: [Stryker.NET configuration reference](https://stryker-mutator.io/docs/stryker-net/configuration/)
[^18]: [Szlosek, "TDD with Mutation Testing — An Experimental Study," Software Quality Journal 2020](https://link.springer.com/article/10.1007/s11219-020-09534-x)
[^19]: [Bartocci et al., "Property-Based Mutation Testing," arXiv:2301.13615](https://arxiv.org/pdf/2301.13615)
