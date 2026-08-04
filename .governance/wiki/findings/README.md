# Findings directory

Machine-readable knowledge and debt backlog. Schema: `src/sdd/_schemas/finding.schema.yaml`.

Debt triage tags (see [`../debt-backlog.md`](../debt-backlog.md)):

- `tech-debt`
- `vulnerability`
- `code-smell`

```bash
sdd findings add --title "…" --author @you
sdd findings list --tag tech-debt
make debt
```
