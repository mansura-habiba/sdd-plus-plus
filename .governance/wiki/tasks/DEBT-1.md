# Task: DEBT-1 — Enable technical debt backlog tracking

> GitHub issue: **blocked** — `gh` tokens for github.ibm.com and github.com are invalid.
> After `gh auth login -h github.ibm.com`, create the issue and add it to
> [2026 project](https://github.ibm.com/users/MANSURAH/projects/3).

## Goal

Give the team a governed way to track technical debt, vulnerabilities, and rough code
without inventing a second backlog parallel to findings.

## Bigger picture

Findings (`sdd findings`) already store discovered facts with severity and status.
Debt is the same artifact with an explicit tag taxonomy and a list/view surface.
Agents and humans file debt as `suspected` findings; humans confirm; mitigation
moves status to `mitigated` / `archived`.

## Challenge

- **Understood request:** Branch + enable a durable backlog for tech debt, vulns, and bad code.
- **Concern:** A separate `.governance/debt/` schema would duplicate findings and split
  the AI operating surface (`list_findings` vs a second tool). Prefer tags on findings.
- **Concern:** Formal `sdd plan new` needs a capability with `spec.yaml`. AI must not
  author capability specs — so this task enables the wiki/CLI surface first; a human
  can later promote `technical-debt-tracking` to a real capability if needed.
- **Alternative considered:** Track only via GitHub Issues + labels. Rejected —
  principles require embedded governance; findings already feed MCP/`sdd serve`.
- **Alternative considered:** New YAML debt register + schema. Rejected for v1 —
  higher cost, violates “search before you generate,” duplicates finding lifecycle.

## In scope

- [x] Branch `cursor/tech-debt-tracking`
- [x] Task card DEBT-1
- [x] Wiki convention: tag taxonomy + how to file/list debt
- [x] Seed initial suspected debt findings from known repo gaps
- [x] `make debt` / `make debt-open` list targets
- [ ] GitHub issue + project board item (needs human `gh auth login`)
- [ ] Human-authored capability spec if we want formal plans against this work

## Out of scope / non-goals

- New finding schema fields or schema edits (AI must not modify schemas)
- Auto-scanning / Dependabot / SAST integration (future)
- Marking findings `confirmed` (humans only)
- Rewriting example-feature or dogfooding framework capabilities in this PR

## How to use (after merge)

```bash
# List debt by kind
make debt

# File new debt (or vulnerability / code-smell)
sdd findings add --from-task DEBT-1 --title "…" --author @you
# then set tags: [tech-debt] or [vulnerability] or [code-smell]

sdd findings list --tag tech-debt
sdd findings list --tag vulnerability
sdd findings list --status suspected
```

## Decisions

- **Canonical store:** `.governance/wiki/findings/<id>.yaml`
- **Tags:** `tech-debt` | `vulnerability` | `code-smell` (plus optional domain tags)
- **Lifecycle:** same as findings — suspected → confirmed → mitigated | refuted | archived
