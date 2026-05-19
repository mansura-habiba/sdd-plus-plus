# Coding standards

> The team's tribal knowledge made explicit. Captures everything beyond what lint, type-check, and the schema enforce — things that look right to lint but wrong to a senior reviewer.
>
> This file is loaded by every AI session (referenced from `.governance/instructions.md`). Edit it when you correct a pattern more than twice — that's a signal the convention should be documented, not re-explained.

---

## How to use this doc

- **Junior engineer:** read once. Don't memorize — the patterns will become muscle.
- **Senior engineer:** when you correct the same thing across multiple PRs, add it here. The framework's job is to externalize what you keep saying.
- **AI assistant:** treat this as binding. When generating code, conform to these patterns. Failure to follow them is a code-quality regression even if lint passes.

---

## Naming

- **TODO** — variable naming style for the team
- **TODO** — function naming patterns (verb_noun? present-tense? imperative?)
- **TODO** — file naming conventions
- **TODO** — test naming conventions (e.g. `test_<unit>_<behavior>_<expected>`)

## Error handling

- **TODO** — what gets raised vs. returned?
- **TODO** — what's the team's exception hierarchy?
- **TODO** — when do we catch vs. let propagate?
- **TODO** — never swallow exceptions without an explicit `# rationale:` comment

## Logging

- **TODO** — structured log fields (e.g. `trace_id`, `capability_id`, `outcome`)
- **TODO** — log levels (when to use info vs. debug vs. warning vs. error)
- **TODO** — never log secrets, PII, or full payloads

## Type discipline

- **TODO** — required type hints on public functions; optional on internal helpers
- **TODO** — when `Any` is acceptable (rare — explain in comment)
- **TODO** — preferred patterns for generics

## Comments

- **TODO** — comments explain *why*, not *what*
- **TODO** — a comment that paraphrases the line below is noise
- **TODO** — TODO comments must have a date and an issue reference

## Imports

- **TODO** — import ordering (stdlib, third-party, local)
- **TODO** — banned imports (e.g. wildcard imports, deprecated libraries)
- **TODO** — preferred libraries for common tasks

## Functions

- **TODO** — max function length before it should be split
- **TODO** — max parameter count
- **TODO** — preferred patterns for default arguments

## Classes

- **TODO** — when to use dataclasses vs. attrs vs. plain classes
- **TODO** — preferred patterns for builders, factories, abstract base classes

## Tests

- **TODO** — test independence (no shared state between tests)
- **TODO** — fixtures vs. setup/teardown
- **TODO** — never mock the unit under test
- **TODO** — every assertion has a clear failure message OR matches a named case_id

## Performance

- **TODO** — known performance hotspots (which code paths matter)
- **TODO** — patterns that look correct but are slow (e.g. repeated dict lookups, naive list ops)
- **TODO** — when caching is appropriate; when it's premature

## Security

- **TODO** — input validation: where does sanitization happen?
- **TODO** — secret management: never in code, never in logs
- **TODO** — known attack surfaces specific to this codebase

## Concurrency

- **TODO** — what's safe to run in parallel?
- **TODO** — locking discipline (always acquire X before Y)
- **TODO** — async/await conventions

## Refactoring

- **TODO** — when to refactor vs. when to ship and file a follow-up
- **TODO** — patterns that should be extracted (DRY) vs. duplicated for clarity
- **TODO** — never introduce abstraction with fewer than 2 real consumers

## What "good code" means here (beyond lint)

- A senior could read this diff and identify the *intent* without running the code.
- A junior could read it in 6 months and not need to ask why.
- It does one thing well; it does not optimize for the case nobody asked for.
- It fails loudly in the cases we said it should fail; it does not silently degrade.
- It survives mutation testing (the test suite catches small intentional regressions).

---

## Anti-patterns we have hit before

These come from findings. When you spot a new one, file a `wiki/findings/<id>.md` entry, then promote the durable lesson here.

- **TODO** — pattern that looked correct but caused issue X (linked finding)
- **TODO** — convention that diverged across the codebase, costing review time

---

## How AI assistants should behave

(Mirror of the relevant clauses in `.governance/instructions.md`.)

- When generating code, conform to every pattern above.
- When a pattern is ambiguous, **ask** before assuming. Don't pick the "popular" answer from training data — pick what fits this codebase.
- When you notice a pattern this doc doesn't cover, surface it to the human ("I noticed convention X — should we document it in coding-standards.md?"). Findings about good-code patterns become rules over time.
- When the schema permits something but this doc forbids it, this doc wins.
