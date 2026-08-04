# Technical debt backlog

> How this repo tracks tech debt, vulnerabilities, and rough code.
> Canonical store: `.governance/wiki/findings/*.yaml` via `sdd findings`.

## Why findings (not a second backlog)

Findings already have severity, status lifecycle, capability links, evidence, and
MCP/`sdd serve` surfaces. A parallel debt register would split search and dilute
governance. Debt items **are** findings tagged for triage.

## Tag taxonomy

| Tag | Use for |
|-----|---------|
| `tech-debt` | Known shortcuts, missing dogfooding, process/tooling gaps to pay down |
| `vulnerability` | Security defects or exposure (suspected until a human confirms) |
| `code-smell` | Maintainability problems — unclear APIs, duplication, brittle structure |

Add domain tags as needed (`wiki`, `mcp`, `ci`, `docs`). Always include **one** of
the three triage tags above so `make debt` can find the item.

## Lifecycle

1. **File** — `sdd findings add` (AI may leave `status: suspected`).
2. **Confirm** — human sets `status: confirmed` (AI must not).
3. **Pay down** — link a task/PR in `references` / `mitigation`.
4. **Close** — `mitigated` when fixed, `refuted` if wrong, `archived` if obsolete.

## Commands

```bash
make debt              # tech-debt + vulnerability + code-smell
make debt-open         # all suspected + confirmed findings
sdd findings list --tag tech-debt
sdd findings list --tag vulnerability
sdd findings show <id>
```

## Filing checklist

- Title is specific (not “fix stuff”).
- `finding` body ≥ 50 chars with what/where/why it hurts.
- `evidence` points at paths, tests, doctor output, or issues.
- `implications` tells future agents what to avoid or fix first.
- `related_capabilities` when known; otherwise note in `notes`.
- `discovered_during: DEBT-1` (or the current task id).

## What this is not

- Not a substitute for CVE scanners or Dependabot — those can *feed* findings.
- Not a place for feature requests — use tasks / GitHub issues.
- Not confirmed truth until a human changes status from `suspected`.
