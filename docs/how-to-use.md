# How to Use SDD++

> A practical, step-by-step guide for teams adopting Spec-Driven Development Plus Plus. Start here, follow the steps in order, and you'll have a governed repository with working CI gates in under an hour.

**Prerequisites:** Python 3.11+ and a Git repository.

---

## Table of contents

1. [Install the tool](#1-install-the-tool)
2. [Bootstrap your repo](#2-bootstrap-your-repo)
3. [Write your first capability spec](#3-write-your-first-capability-spec)
4. [Connect your AI assistant](#4-connect-your-ai-assistant)
5. [Work a task end to end](#5-work-a-task-end-to-end)
6. [Validate and run CI](#6-validate-and-run-ci)
7. [Record findings](#7-record-findings)
8. [Track progress across sessions](#8-track-progress-across-sessions)
9. [Migrate existing tests](#9-migrate-existing-tests)
10. [Day-to-day reference](#10-day-to-day-reference)

---

## 1. Install the tool

```bash
pip install sdd-plus-plus
```

Verify:

```bash
sdd --version
```

For MCP server support (Cursor, Claude Code, Copilot integration):

```bash
pip install 'sdd-plus-plus[serve]'
```

---

## 2. Bootstrap your repo

```bash
cd your-repo
sdd init
```

This creates the `.governance/` directory and an `AGENTS.md` at the repo root. The full structure:

```
your-repo/
├── AGENTS.md                          # AI standing orders (auto-loaded by Cursor/Claude/Copilot)
├── .governance/
│   ├── instructions.md                # Canonical AI rules (AGENTS.md is a copy)
│   ├── arch_spec.md                   # Whole-system architecture
│   ├── progress.md                    # Auto-generated session snapshot
│   │
│   ├── wiki/
│   │   ├── principles.md              # The governing principles
│   │   ├── coding-standards.md        # Tribal knowledge: naming, error handling, anti-patterns
│   │   └── findings/                  # Accumulated discoveries
│   │
│   ├── capabilities/
│   │   ├── REGISTRY.yaml              # Master list of capabilities
│   │   └── example-feature/
│   │       └── spec.md                # Starter capability spec (rename and edit)
│   │
│   └── plan/
│       └── example.plan.md            # Example plan (shows the expected shape)
│
├── .github/
│   ├── ISSUE_TEMPLATE/task-card.yml   # Structured issue form
│   ├── pull_request_template.md       # Ownership disclosure checklist
│   └── workflows/governance.yml       # CI gates
│
└── tests/contract/                    # Schema validation tests
```

**Tiers control strictness.** The default is `team`. For stricter governance:

```bash
sdd init --tier org         # Organization-wide defaults
sdd init --tier regulated   # Maximum enforcement
```

Preview without writing files:

```bash
sdd init --dry-run
```

---

## 3. Write your first capability spec

A capability is a bounded area of system functionality — "authentication," "billing," "notifications," etc. Each one gets a `spec.md` with YAML frontmatter (the machine-readable contract) and a markdown body (the human-readable rationale).

### Step 1: Create the capability directory

```bash
mkdir -p .governance/capabilities/auth
```

### Step 2: Write the spec

Create `.governance/capabilities/auth/spec.md`:

```yaml
---
id: auth
name: "User Authentication"
purpose: |
  Handles user login, session management, and token refresh. If this
  capability breaks, no user can access the system. All API endpoints
  behind the auth middleware become unreachable.
status: active
tier: team

owner:
  human: "@your-handle"

contract:
  inputs:
    - name: credentials
      shape: "{ email: string, password: string }"
      description: "User-supplied login credentials."
  outputs:
    - name: session_token
      shape: "{ token: string, expires_at: ISO8601 }"
      description: "JWT session token with expiry."
  invariants:
    - "Expired tokens are always rejected, even if the signature is valid."
    - "Failed login attempts never leak whether the email exists."

cases:
  - id: login-happy-path
    kind: positive
    priority: critical
    description: "Valid credentials return a session token."
    test_id: "tests/contract/test_auth.py::test_login_happy_path"
  - id: login-wrong-password
    kind: negative
    priority: critical
    description: "Wrong password returns 401 with generic message."
    test_id: "tests/contract/test_auth.py::test_login_wrong_password"
  - id: token-expired
    kind: boundary
    priority: high
    description: "Request with an expired token returns 401."
    test_id: "tests/contract/test_auth.py::test_expired_token_rejected"

definition_of_done:
  conditions:
    - id: all-cases-pass
      statement: "Every case above has a passing test."
      verifiable_by: contract_test
      evidence_ref: "tests/contract/test_auth.py"
    - id: schema-valid
      statement: "This spec.md frontmatter validates against the schema."
      verifiable_by: schema_validation

non_functional:
  performance: "p95 login latency < 300ms"
  security: "Passwords hashed with bcrypt, min cost 12. No plaintext logging."

tasks_must:
  use_patterns:
    - "Repository pattern for user lookups"
  avoid_dependencies:
    - "No ORM magic — raw SQL or query builder only"

forbidden:
  - "Never store plaintext passwords."
  - "Never return different error messages for 'email not found' vs 'wrong password.'"
---

# User Authentication

## Purpose

Authentication is the front door. Every API call passes through it.

## Design notes

JWT with short-lived access tokens (15 min) and longer refresh tokens (7 days).
Refresh rotation: each refresh issues a new refresh token and invalidates the old one.

## Open questions

- Should we support OAuth2 social login in v1, or defer?
- Rate limiting on login endpoint — per-IP or per-account?
```

### Step 3: Register the capability

Add it to `.governance/capabilities/REGISTRY.yaml`:

```yaml
capabilities:
  - id: auth
    name: "User Authentication"
    status: active
```

### Step 4: Validate

```bash
sdd validate
```

If any required field is missing or malformed, the validator tells you exactly what to fix.

---

## 4. Connect your AI assistant

### Cursor

Add to `.cursor/mcp.json` in your project (or `~/.cursor/mcp.json` globally):

```json
{
  "mcpServers": {
    "sdd-governance": {
      "command": "sdd",
      "args": ["serve", "--target", "/absolute/path/to/your/repo"]
    }
  }
}
```

### Claude Code

```bash
claude mcp add sdd-governance -- sdd serve --target /absolute/path/to/your/repo
```

### Any MCP-compatible client

Point it at `sdd serve`. The server exposes these tools to the AI:

| Tool | What it does |
|---|---|
| `get_instructions()` | Loads the AI standing orders |
| `get_principles()` | Loads the governing principles |
| `get_coding_standards()` | Loads tribal knowledge |
| `get_arch_spec()` | Loads system architecture |
| `list_capabilities()` | Lists all capabilities |
| `get_capability(id)` | Reads a specific capability spec |
| `get_registry()` | Full capability registry |
| `list_findings(capability)` | Surfaces known gotchas |
| `search_findings(query)` | Searches findings by keyword |
| `propose_plan(...)` | Drafts a plan (status: draft only) |
| `record_progress(message)` | Logs a progress checkpoint |
| `record_session_end(summary)` | Logs session conclusion |
| `get_progress()` | Loads the current progress snapshot |
| `validate()` | Runs schema + cross-reference checks |

The AI can query and draft — it cannot accept plans, confirm findings, or edit specs.

### Optional: Graphify knowledge-graph search

For cross-cutting architecture and “what connects to what” questions, this repo
also supports [Graphify](https://github.com/Graphify-Labs/graphify) alongside the
MCP tools above.

```bash
# once per machine
pipx install graphifyy   # CLI name is still `graphify`
graphify cursor install  # writes .cursor/rules/graphify.mdc

# build / refresh the code graph (no API key)
graphify update .

# search
graphify query "how does search_findings relate to wiki findings?"
graphify path "findings_dir" "search_findings"
graphify explain "propose_plan"
```

The graph lives at `graphify-out/graph.json`. Cursor loads `.cursor/rules/graphify.mdc`
so agents prefer Graphify for architecture questions, while findings/specs/plans
still go through `sdd serve`.

To pull markdown wiki docs and PDFs into the graph (semantic pass), run
`/graphify --update` in an AI assistant, or `graphify extract .` with an LLM
backend configured. Until then, `graphify update .` keeps the code AST graph current.

---

## 5. Work a task end to end

This is the core workflow. Every non-trivial change follows these steps.

### Step 1: File an issue

Use the GitHub issue template (`task-card.yml`) scaffolded by `sdd init`. Fill in:

- **Parent capability** — which capability this task belongs to
- **One-line goal** — what you're doing
- **Bigger picture** — why it matters (minimum 50 characters)
- **In-scope** — what the task includes
- **Out-of-scope** — what it explicitly does not include

### Step 2: Draft a plan

Ask your AI assistant:

> "Draft a plan for issue #42 against the auth capability."

The AI calls `propose_plan` via MCP and saves a plan to `.governance/plan/<task-id>.plan.md` with `status: draft`.

Or use the CLI directly:

```bash
sdd plan new --task GH-42 --capability auth --tool cursor
```

Every plan must include a **challenge block** — the AI's pushback record:

```yaml
challenge:
  understood_request: |
    Add rate limiting to the login endpoint, 5 attempts per minute per IP.
  concerns:
    - "Per-IP limiting can be bypassed with rotating proxies — this is a
      partial defense, not a complete one."
    - "Our test suite uses in-memory fakes that won't exercise the Redis
      lock path under contention."
  alternatives_considered:
    - "Token bucket algorithm — rejected: harder to reason about for
      credential-stuffing economics."
```

Plans without a populated challenge block fail schema validation. This is the anti-sycophancy mechanism.

### Step 3: Review and accept the plan

Read the plan — especially the challenge block and the non-goals. Then:

```bash
sdd plan accept --id GH-42-plan-001 --by @your-handle
```

This is the **only** way a plan advances to `accepted`. The AI cannot do this — the MCP toolset deliberately has no accept operation. The schema rejects non-human handles.

### Step 4: Implement

Work with the AI to write the code. `AGENTS.md` (auto-loaded by the AI) instructs it to:

1. Read the parent capability's `spec.md`
2. Check for related findings via `list_findings`
3. Follow `coding-standards.md`
4. Respect the plan's `do_not_modify` paths
5. Write tests against named `case_id`s from the spec

### Step 5: Validate locally

```bash
sdd validate
```

This checks all YAML frontmatter against the bundled schemas and runs cross-reference checks.

### Step 6: Open the PR

The PR template (scaffolded by `sdd init`) requires you to confirm:

- [ ] I have read every line of AI-generated code in this PR
- [ ] I can defend the architectural choices
- [ ] The AI's challenge block surfaced at least one concern, and I read it
- [ ] Ownership: @your-handle

### Step 7: CI runs the gates

The governance workflow runs automatically:

1. **Schema validation** — `sdd validate --strict`
2. **Contract tests** — your test suite against named case_ids
3. **Ownership disclosure** — PR template filled in
4. **Protected paths** — specs not modified without `spec-change` label

All gates must pass before human review is assigned.

### Step 8: Human review

The reviewer focuses on **judgment** — architectural fit, business sense, edge cases. Compliance is already handled by CI.

### Step 9: Merge and record outcome

After merge, optionally record the outcome for calibration tracking:

```bash
sdd plan outcome --id GH-42-plan-001 --outcome success
```

---

## 6. Validate and run CI

### Local validation

```bash
sdd validate              # Standard check
sdd validate --strict     # CI-level strictness
```

### Diagnose adoption gaps

```bash
sdd doctor
```

This runs a 9-milestone diagnostic and tells you what's present, what's missing, and what to do next. Use it as your adoption checklist.

### View plans

```bash
sdd plan list                    # All plans
sdd plan list --status draft     # Only drafts
sdd plan list --status accepted  # Only accepted
sdd plan show <plan-id>          # Full content of a specific plan
```

---

## 7. Record findings

Findings are the team's accumulated knowledge — gotchas, confirmed bug patterns, behavioral quirks. They prevent the same mistake from being re-derived every AI session.

### Add a finding

```bash
sdd findings add                          # Opens your $EDITOR
sdd findings add --from-task GH-42        # Pre-fills context from a task
```

A finding includes:

- **Title** — what was discovered
- **Finding** — the detailed description
- **Evidence** — how you know it's true
- **Severity** — low / medium / high / critical
- **Related capability** — which area of the system it affects
- **Status** — `suspected` (AI or human filed it) or `confirmed` (human verified)

AI assistants can file findings via `propose_finding` MCP tool — these start as `suspected`. A human must verify and advance to `confirmed`.

### Browse findings

```bash
sdd findings list                          # All findings
sdd findings list --capability auth        # Filtered by capability
sdd findings show <finding-id>             # Full content
```

### Why this matters

When an AI starts a new session, it calls `list_findings(capability='auth')` and sees every known gotcha for that area. Knowledge accumulates instead of evaporating between sessions.

---

## 8. Track progress across sessions

AI sessions are ephemeral. Progress tracking makes state persistent.

### Record a milestone

```bash
sdd update-status --kind milestone --message "Auth capability: login and token refresh implemented, all 3 contract tests passing"
```

### Record a session end

```bash
sdd update-status --kind session-end --message "Implemented rate limiter. Left: integration tests and Redis connection pool warmup."
```

Or via the AI's MCP tools: `record_progress(message='...')` and `record_session_end(summary='...')`.

### View current state

```bash
sdd progress               # Shows progress.md content
sdd progress refresh        # Re-renders from current state
```

The next AI session loads `progress.md` via `get_progress()` and picks up where the last one left off — no re-reading the whole `.governance/` tree, no losing context.

---

## 9. Migrate existing tests

If you already have a test suite, SDD++ works with it directly. The migration command reads your existing test files and seeds a starter `cases` array in a capability spec:

```bash
sdd generate-acceptance \
  --from-tests tests/test_auth.py \
  --capability auth
```

This parses your pytest (or other framework) test files and generates case entries like:

```yaml
cases:
  - id: test-login-happy-path
    kind: positive
    description: "Auto-generated from test_login_happy_path"
    test_id: "tests/test_auth.py::test_login_happy_path"
```

You then edit the generated entries to add proper descriptions, kinds, and priorities. Your existing tests keep running unchanged — SDD++ adds a spec layer above them.

---

## 10. Day-to-day reference

### Who does what

| Action | Human | AI | Framework |
|---|---|---|---|
| Write capability specs | Owns | May draft, human verifies | Validates schema |
| Write principles, architecture | Owns | Cannot touch | Validates schema |
| Write coding standards | Owns | May suggest additions | Loads into AI sessions |
| Draft plans | May write | Primary drafter | Enforces challenge block |
| Accept plans | **Only human** | Cannot | Records `accepted_by` |
| Write code | Reviews | Primary writer | Enforces `do_not_modify` |
| Write tests | Reviews | Writes against case_ids | Validates linkage |
| File findings | May file as confirmed | Files as `suspected` | Surfaces to future sessions |
| Confirm findings | **Only human** | Cannot | Tracks status history |
| Record progress | May call CLI | Calls MCP tools | Persists and renders |

### Commands cheat sheet

```bash
# Bootstrap
sdd init                                    # Set up the framework
sdd init --tier org                         # Stricter defaults
sdd doctor                                  # What's present, what's missing

# Validate
sdd validate                                # Check all governance YAML
sdd validate --strict                       # CI-level strictness

# Plans
sdd plan new --task X --capability Y        # Draft a plan
sdd plan accept --id Z --by @handle         # Human accepts a plan
sdd plan list                               # List all plans
sdd plan show <id>                          # View a plan

# Findings
sdd findings add                            # Record a finding
sdd findings list --capability auth         # Browse findings
sdd findings show <id>                      # View a finding

# Progress
sdd update-status --kind milestone \
  --message "description"                   # Record a checkpoint
sdd progress refresh                        # Re-render progress.md

# AI integration
sdd serve                                   # Start MCP server (stdio)
sdd serve --transport http                  # MCP server over HTTP

# Tests
sdd generate-acceptance \
  --from-tests tests/foo.py \
  --capability bar                          # Seed cases from existing tests
```

### The adoption ladder

| When | What to turn on | What you get |
|---|---|---|
| Day 1 | `sdd init` | Governance structure, AGENTS.md, CI workflow |
| Day 2 | `sdd generate-acceptance --from-tests` | Cases seeded from your existing tests |
| Week 1 | CI workflow on a feature branch | Schema validation gates on every PR |
| Week 2 | AI rules pointing at active task card | AI reads the spec before generating code |
| Month 1 | Case-id linkage gate | Tests must trace to spec cases |
| Month 2 | Mutation testing (nightly) | Test quality becomes measurable |
| Month 3 | Graduated trust by domain | AI autonomy levels based on track record |

Each step has standalone value. Stop at any step and you're still better off than not starting.

---

## Further reading

- [System overview diagram](https://raw.githack.com/MANSURAH/sdd-plus-plus/main/whitepaper/sdd-plus-plus-overview.html)
- [Whitepaper](../whitepaper/whitepaper.md) — the full design rationale, measurement substrate, and benchmarks
- [USAGE.md](../src/sdd/templates/USAGE.md) — how humans and AI agents work the framework together (bundled with every `sdd init`)
- [Principles](../src/sdd/templates/wiki/principles.md) — the five governing principles
- [Example plan](../src/sdd/templates/plan/example.plan.md) — what a plan looks like, fully populated
- [Example capability spec](../src/sdd/templates/capabilities/example-feature/spec.md) — what a spec looks like
- [Example finding](../src/sdd/templates/examples/example-finding.finding.yaml) — what a finding looks like
