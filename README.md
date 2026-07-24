# sdd-plus-plus

> **Spec-Driven Development that ships.** A Python tool that bootstraps any repo with executable specs, structured acceptance criteria, AI assistant rules, and CI gates — designed for AI-assisted teams where juniors, seniors, and AI coding assistants all need to coordinate without losing each other.

```bash
pip install sdd-plus-plus
cd your-repo
sdd init
```

That's it. 60 seconds from install to a working `.governance/` framework in your repo.

### Or install as a Claude Code plugin

`sdd-plus-plus` ships as a Claude Code plugin too — bundling the `sdd serve` MCP server, the **Bob** (scaffolder) and **Dana** (reviewer) agents, and slash commands for the full CLI.

```text
/plugin marketplace add built-it-here/sdd-plus-plus
/plugin install sdd-plus-plus@sdd-plus-plus-marketplace
```

After install you get:

- **`@bob-scaffolder`** — drafts capability specs, acceptance YAML, and task cards in one pass
- **`@dana-reviewer`** — peer-reviews task cards against the contracts, ingests findings, updates status
- **`/sdd-init`**, **`/sdd-validate`**, **`/sdd-doctor`**, **`/sdd-finding-add`**, **`/sdd-review`** — slash commands wrapping the CLI
- An MCP server (`sdd-governance`) that exposes `list_capabilities`, `get_task`, `get_acceptance`, `search_findings`, `validate`, and more as native Claude tools, scoped to the current repo via `${CLAUDE_PROJECT_DIR}`

The plugin requires `pip install 'sdd-plus-plus[serve]'` so the `sdd` binary is on `$PATH` for the MCP server.

**Optional but powerful: a shared findings wiki.** Point `wiki.repo` in your config at a git repo and findings stop being trapped per-codebase — they become an org-wide knowledge layer that Bob reads before scaffolding and Dana publishes to after review. See [`CONFIG.md`](./CONFIG.md) and [`examples/sdd-config.example.yaml`](./examples/sdd-config.example.yaml).

---

## What you get from `sdd init`

```
your-repo/
├── .governance/
│   ├── philosophy.md                # 4 principles + violation examples
│   ├── README.md                    # junior quickstart with diagrams
│   ├── diagrams.md                  # 6 Mermaid diagrams of the framework
│   ├── testing-philosophy.md        # the AI-era testing position
│   ├── task-card.schema.yaml        # per-issue contract schema
│   ├── capability-spec.schema.yaml  # per-feature contract schema
│   ├── acceptance.schema.yaml       # structured acceptance schema
│   ├── capabilities/                # your team writes one .yaml per feature area
│   ├── acceptance/                  # one .acceptance.yaml per capability
│   ├── examples/                    # worked examples of each artifact
│   └── tests/contract/              # executable schema-validation tests
├── AGENTS.md                        # AI assistant rules (Cursor / Claude Code / Copilot)
├── .github/
│   ├── ISSUE_TEMPLATE/task-card.yml
│   ├── pull_request_template.md
│   └── workflows/governance.yml
└── tests/contract/                  # test_task_card_validates.py + test_acceptance_validates.py
```

Every artifact is schema-validated. AI assistants automatically load the active task card and capability spec before generating code. CI rejects PRs that violate the spec.

---

## Commands

```bash
sdd init                                # Bootstrap a repo with the framework
sdd init --tier team                    # Bootstrap with team-tier defaults
sdd validate                            # Validate every YAML in .governance/
sdd generate-acceptance --from-tests    # Generate starter acceptance spec from existing pytest tests
sdd doctor                              # Diagnose what's present, what's missing, what to do next

# Findings — the LLM-wiki / knowledge block layer (v0.2)
sdd findings add                        # Record a finding via $EDITOR
sdd findings add --from-task BBS-127    # Pre-fill from task context
sdd findings list --capability auth     # List findings filtered by capability or tag
sdd findings show <id>                  # Show a finding's full content

# Tech debt backlog — findings tagged tech-debt | vulnerability | code-smell
make debt                               # List debt / vulns / smells
make debt-open                          # List suspected + confirmed findings
# See .governance/wiki/debt-backlog.md

# MCP server for IDE integration (v0.2, requires `pip install 'sdd-plus-plus[serve]'`)
sdd serve                               # Start the MCP server on stdio
sdd serve --transport http              # HTTP/SSE transport for remote setups
```

### Cursor integration

After `pip install 'sdd-plus-plus[serve]'`, add to `.cursor/mcp.json` (per-project) or `~/.cursor/mcp.json` (global):

```json
{
  "mcpServers": {
    "sdd-governance": {
      "command": "sdd",
      "args": ["serve", "--target", "/abs/path/to/your/repo"]
    }
  }
}
```

Claude Code, GitHub Copilot, Aider, and any other MCP-compatible client work the same way — point them at `sdd serve`. The AI then gets `list_capabilities`, `get_capability`, `list_tasks`, `get_task`, `get_acceptance`, `list_findings`, `search_findings`, `get_finding`, and `validate` as native tools. No more "AI ignores the docs" — the framework is in the AI's tool palette.

---

## Why this exists

Most spec-driven development tools today (spec-kit, Kiro, Tessl) have one or more of these problems:

- They generate 8 markdown files for a 3-point story (friction-to-value ratio is wrong)
- They use natural-language prose as the spec — AI writes it fluently and wrong
- They have no migration path from existing TDD codebases
- They produce zero data on whether they're working in real codebases

`sdd-plus-plus` is designed against those failure modes:

- **Structured, not prose.** Specs are JSON Schema-validated YAML, ~30 lines for a small task. AI cannot smuggle in vagueness.
- **AI authoring boundary.** AI implements tests against the spec; it cannot author the spec layer itself. The schema has an `authored_by.ai_assistance: forbidden` field, defaulted on.
- **TDD-compatible from day 1.** `sdd generate-acceptance --from-tests` reads your existing pytest files and produces a starter acceptance spec — no blank page.
- **Value at every step.** Step 1 alone (just `sdd init`) gives you structured intent artifacts. Each step has standalone payoff.

---

## Philosophy

Read [docs/philosophy.md](docs/philosophy.md) once. After that, the framework guides you through forms and CI checks. You don't memorize anything.

The four principles, in one line each:

1. **Governance is embedded, not sidecar.** Rules live in the repo, run in CI, gate the merge button.
2. **Skills are executable contracts, not prompt snippets.** Schemas + executable tests, not markdown promises.
3. **Authority must be bounded.** Every task declares non-goals and AI do-not-modify paths.
4. **Evidence is required for trust.** Every change traces to a task card, every task to a capability, every capability to a principle.

---

## Roadmap and north star

We hold ourselves to one test, from [Ka Mok's "Future of Software Engineering Part 1"](https://medium.com/@hey.kamok/future-of-software-engineering-part-1-the-individual-ebe1eb9357a6):

> Can an engineer who uses sdd-plus-plus daily explain, in their own words and without referring to the spec, the architectural trade-offs of the last feature they shipped?

If yes, the framework is making senior thinking visible and juniors are absorbing it. If no, the framework has automated judgment away — exactly what it was built to prevent.

v0.3 ("Judgment Development") targets this test directly with pre-implementation intent capture, post-merge reflection, inverted authorship mode, `# why:` annotations, and quarterly comprehension probes. See [ROADMAP.md](ROADMAP.md) for the full release plan.

---

## Adoption playbook

The framework targets 95%+ adoption by being adopted incrementally, not all-at-once:

| When | What you turn on | What you get |
|---|---|---|
| Day 1 | `sdd init` | Schema-validated YAML structure, AGENTS.md, CI workflow |
| Day 2 | `sdd generate-acceptance --from-tests` | Starter acceptance spec built from your existing tests |
| Week 1 | CI workflow on a feature branch | Drift detection, schema validation gates |
| Week 2 | AI rules pointing at active task card | "AI ignores the spec" becomes mechanically impossible |
| Month 1 | Case-id linkage gate | Tests must trace to a case in the spec |
| Month 2 | Mutation testing nightly | Calibrated test quality becomes visible |
| Month 3 | Graduated trust by domain | AI autonomy levels per area, based on track record |

Each step has standalone value. Stop at any step, you're better off than not starting.

---

## License

Apache-2.0. See [LICENSE](LICENSE).

---

## Status

**Alpha (v0.1.0).** The framework, schemas, and CI workflow are battle-tested in `bee-skill-registry` (the parent project this tool was extracted from). The Python CLI is new. File issues; expect rough edges.
