# Developer guide: creating a governed automated agent harness

> **Status:** Proposed developer experience for issue #1  
> **Capability:** `automated-agent-harness`  
> **Owner:** `@mansura-habiba`  
> **Target release:** v0.4  
> **Related plan:** `SDD-1-plan-001`

This guide defines how a developer will use SDD++ to create and operate a
repository-owned automated agent-session harness with limited human override.

The commands in this document describe the intended capability. Until issue #1
is implemented and released, treat them as the product contract for the CLI,
generated files, validation, and control behaviour—not as commands that already
exist in the current package.

---

## 1. What the harness is

The harness is not a coding model and is not a replacement for Codex, Claude
Code, Cursor, Copilot, or another execution provider.

```text
Agent provider
  supplies reasoning, code generation, and tool use

SDD++ harness
  controls task eligibility, context, isolation, authority, evidence,
  verification, session state, retries, and human intervention
```

The harness answers:

- Which task may run next?
- Has a human accepted the governing plan?
- Which files and commands may the agent use?
- Is the task blocked by dependencies?
- Is another session already working on it?
- Where should the session run?
- How long may it run?
- What evidence must it produce?
- Which actions require human approval?
- How can a human pause, stop, redirect, or take over?
- How can the session resume without losing its history?

The core operating principle is:

> The agent performs work. The harness controls the conditions under which work
> may occur.

---

## 2. Intended developer workflow

```text
Install SDD++
  ↓
Initialise repository governance
  ↓
Create or select a human-owned capability
  ↓
Create a task and accepted implementation plan
  ↓
Initialise the harness
  ↓
Configure provider, autonomy, permissions, and verification
  ↓
Validate readiness
  ↓
Run one bounded session or enable scheduled selection
  ↓
Inspect events, evidence, status, and pull request
  ↓
Use human controls only when required
  ↓
Merge manually and release the next dependency
```

Target quick start:

```bash
pip install 'sdd-plus-plus[serve]'

cd your-repository
sdd init
sdd harness init
sdd harness validate
sdd harness run --task 45
```

A continuous but bounded queue will use:

```bash
sdd harness run --next
```

or a generated GitHub Actions schedule.

---

## 3. Prerequisites

Before creating a harness, the repository must have:

1. SDD++ governance initialised.
2. At least one active capability specification.
3. A task linked to that capability.
4. A valid implementation plan.
5. Human acceptance of the plan where required by the autonomy profile.
6. Verification commands that work locally.
7. A supported provider adapter or generic command adapter.

Initialise governance first:

```bash
sdd init --tier team
sdd validate --strict
```

The harness will refuse to start when the governance foundation is missing or
invalid.

---

## 4. Generated structure

Running:

```bash
sdd harness init
```

will generate or propose the following structure:

```text
.governance/
  harness/
    harness.yaml
    README.md

    prompts/
      implement-task.md
      review-result.md
      repair-failure.md

    runs/
      .gitkeep

    events/
      .gitkeep

    overrides/
      .gitkeep

    adapters/
      README.md

.github/
  workflows/
    sdd-agent-harness.yml
```

Runtime-created records will look like:

```text
.governance/harness/
  runs/
    run-20260804-0017.yaml

  events/
    run-20260804-0017.jsonl

  overrides/
    run-20260804-0017.override.jsonl
```

The default scaffold must not overwrite an existing harness configuration unless
the developer explicitly uses `--force`.

Preview without writing:

```bash
sdd harness init --dry-run
```

Choose a preset:

```bash
sdd harness init --profile supervised
sdd harness init --profile bounded
sdd harness init --profile continuous
```

---

## 5. Configure the harness

The primary configuration file is:

```text
.governance/harness/harness.yaml
```

Example:

```yaml
version: 1

identity:
  name: agentops-development-harness
  owner: "@mansura-habiba"

repository:
  default_branch: main
  branch_prefix: agent/
  worktree_root: .worktrees/agent-sessions
  one_task_per_branch: true

provider:
  adapter: command
  command:
    executable: codex
    args:
      - exec
      - --full-auto
      - --prompt-file
      - "{prompt_file}"
  environment_allowlist:
    - PATH
    - HOME
    - CODEX_HOME
  secret_allowlist: []

selection:
  source: github-issues
  required_labels:
    - agent-ready
  excluded_labels:
    - human-required
    - agent-blocked
    - agent-running
    - no-agent
  exclude_epics: true
  require_capability: true
  require_plan: true
  require_dependencies_closed: true
  require_acceptance_cases: true
  maximum_tasks_per_session: 1

execution:
  autonomy_profile: bounded
  maximum_parallel_sessions: 1
  lease_minutes: 180
  heartbeat_seconds: 60
  timeout_minutes: 120
  maximum_attempts: 2
  stale_after_minutes: 10

permissions:
  allowed_paths:
    - src/**
    - tests/**
    - docs/**
  prohibited_paths:
    - .governance/wiki/principles.md
    - .governance/arch_spec.md
    - .governance/capabilities/**/spec.yaml
    - .github/workflows/release.yml
    - CODEOWNERS
  allowed_commands:
    - pytest
    - ruff
    - python
    - git
  prohibited_commands:
    - git push --force
    - gh pr merge
    - kubectl
    - terraform apply

verification:
  commands:
    - pytest
    - ruff check src tests
    - sdd validate --strict
  require_contract_cases: true
  require_clean_worktree: true
  allow_known_baseline_failures: false

pull_request:
  create: true
  draft_on_partial_result: true
  auto_merge: false
  require_owner_handle: true
  require_issue_reference: true

human_gates:
  plan_acceptance: required
  launch: automatic
  privileged_commands: required
  governance_changes: forbidden
  pull_request_merge: required
  deployment: forbidden

retention:
  event_days: 90
  evidence_days: 90
  redact_secrets: true
```

### Configuration rule

The harness configuration can make execution stricter than the parent capability
or plan. It cannot make execution less restrictive.

Effective authority is the intersection of:

```text
Repository instructions
∩ capability contract
∩ accepted plan
∩ harness configuration
∩ provider adapter limits
∩ current human override state
```

If any layer denies an operation, the operation is denied.

---

## 6. Choose an autonomy profile

### 6.1 Supervised

Use for early adoption, high-risk code, architecture changes, security-sensitive
work, or unfamiliar providers.

```yaml
execution:
  autonomy_profile: supervised

human_gates:
  plan_acceptance: required
  launch: required
  every_command: optional-policy
  pull_request_merge: required
```

The harness may prepare a session, but it waits for a human before launch.

Recommended for:

- new repositories;
- new provider adapters;
- security and identity code;
- public API changes;
- schema migrations;
- release infrastructure.

### 6.2 Bounded

This is the recommended default.

```yaml
execution:
  autonomy_profile: bounded

human_gates:
  plan_acceptance: required
  launch: automatic
  privileged_commands: required
  pull_request_merge: required
```

The agent can work independently inside an accepted task, plan, path allowlist,
command allowlist, time budget, and verification policy.

A human is still required for:

- accepting the implementation plan;
- expanding scope;
- modifying governance contracts;
- privileged or destructive commands;
- merging the pull request;
- deployment.

### 6.3 Continuous

Use only after the bounded profile has a reliable track record.

```yaml
execution:
  autonomy_profile: continuous
  maximum_parallel_sessions: 2
  maximum_attempts: 2
  timeout_minutes: 90

selection:
  maximum_tasks_per_session: 1
```

Continuous means the scheduler may repeatedly select the next eligible task. It
does **not** mean unlimited authority.

Continuous mode still cannot:

- accept its own plan;
- merge pull requests by default;
- deploy;
- change capability specifications;
- edit governance principles;
- read undeclared secrets;
- exceed path or command permissions;
- ignore stop, pause, or takeover events.

---

## 7. Configure a provider adapter

The core harness is provider-neutral. Adapters translate a governed session into
one provider invocation and normalise its result.

### 7.1 Generic command adapter

```yaml
provider:
  adapter: command
  command:
    executable: my-agent-cli
    args:
      - run
      - --prompt
      - "{prompt_file}"
      - --workdir
      - "{worktree}"
```

The adapter receives placeholders such as:

```text
{run_id}
{task_id}
{capability_id}
{plan_id}
{prompt_file}
{repository}
{worktree}
{branch}
{event_file}
{evidence_dir}
```

### 7.2 Codex adapter

Illustrative target configuration:

```yaml
provider:
  adapter: codex
  model: default
  mode: repository-write
  prompt_template: .governance/harness/prompts/implement-task.md
```

The adapter must not make Codex-specific fields part of the core run-state
schema. Provider details belong under namespaced metadata.

### 7.3 Claude Code adapter

```yaml
provider:
  adapter: claude-code
  permission_mode: acceptEdits
  prompt_template: .governance/harness/prompts/implement-task.md
```

### 7.4 Custom adapter

A custom adapter must implement the equivalent of:

```python
class HarnessProviderAdapter(Protocol):
    def prepare(self, session: SessionContext) -> PreparedInvocation: ...
    def start(self, invocation: PreparedInvocation) -> ProviderRun: ...
    def poll(self, run: ProviderRun) -> ProviderStatus: ...
    def request_stop(self, run: ProviderRun) -> None: ...
    def collect_result(self, run: ProviderRun) -> ProviderResult: ...
```

Adapter responsibilities:

- invoke the provider;
- expose process or remote-run identity;
- emit heartbeats;
- surface stdout, stderr, and structured result references;
- respond to stop requests;
- return provider status.

Adapter non-responsibilities:

- choosing tasks;
- deciding whether a plan is accepted;
- bypassing path controls;
- deciding merge eligibility;
- rewriting session history;
- granting authority.

---

## 8. Prepare governed work

The harness executes tasks, not unstructured prompts.

A runnable task needs:

```text
GitHub issue or local task
  ↓
Parent capability
  ↓
Capability acceptance cases
  ↓
Implementation plan
  ↓
Human plan acceptance, when required
  ↓
Harness eligibility
```

Create a plan:

```bash
sdd plan new \
  --task 45 \
  --capability agentic-topology \
  --tool human
```

Review it, then accept it through a human-driven command:

```bash
sdd plan accept \
  --id ISSUE-45-plan-001 \
  --by @mansura-habiba
```

The harness will reject a task when:

- the capability is missing;
- the capability is retired;
- the plan is missing;
- the plan is still draft;
- the task has unresolved dependencies;
- acceptance cases are missing;
- the issue is already claimed;
- an open PR already implements the task;
- a human-required label is present;
- the requested files exceed allowed scope;
- the branch base is stale beyond policy.

---

## 9. Validate before running

Run:

```bash
sdd harness validate
```

Expected checks:

```text
[PASS] SDD++ governance is valid
[PASS] harness.yaml matches schema version 1
[PASS] provider adapter is available
[PASS] owner handle is declared
[PASS] allowed and prohibited paths do not conflict
[PASS] verification commands are configured
[PASS] human merge gate is enabled
[PASS] event and run directories are writable
[WARN] continuous mode has not completed calibration threshold
```

Validate one task:

```bash
sdd harness validate --task 45
```

Explain eligibility:

```bash
sdd harness plan --task 45
```

Example output:

```text
Task #45 is eligible.

Capability: agentic-topology
Plan: ISSUE-45-plan-001 (accepted by @mansura-habiba)
Dependencies: #6 closed, #7 closed, #32 closed
Provider: codex
Branch: agent/issue-45-topology-semantics
Lease: 180 minutes
Verification: 3 commands
Human gates: merge, privileged commands
```

For a blocked task:

```text
Task #46 is not eligible.

Blocked by:
- dependency #45 is open
- required capability case topology-boundary-crossing has no test_id
```

Eligibility must be explainable. The harness must not return only a Boolean.

---

## 10. Run one bounded session

Run a specific task:

```bash
sdd harness run --task 45
```

The harness performs:

```text
1. Resolve task, capability, plan, and findings.
2. Validate effective permissions.
3. Check dependencies and existing claims.
4. Create a lease.
5. Create an isolated branch and worktree.
6. Build the governed prompt bundle.
7. Start the provider adapter.
8. Record events and heartbeats.
9. Observe pause, stop, approval, and takeover state.
10. Collect provider result.
11. Run independent verification.
12. Create or prepare a pull request.
13. Record final outcome and release the lease.
```

Run the next eligible task:

```bash
sdd harness run --next
```

Preview selection without starting:

```bash
sdd harness run --next --dry-run
```

Expected dry-run output:

```text
Selected task: #45
Reason: highest-priority dependency-ready bounded task
Would create branch: agent/issue-45-topology-semantics
Would create worktree: .worktrees/agent-sessions/run-20260804-0017
Would run provider: codex
Would run verification: pytest; ruff check; sdd validate --strict
No changes made.
```

---

## 11. Session lifecycle

Normal states:

```text
created
→ eligible
→ claimed
→ preparing
→ running
→ verifying
→ review-required
→ completed
```

Exceptional states:

```text
blocked
paused
retrying
stale
stopping
stopped
takeover
failed
cancelled
```

A run record contains:

```yaml
run_id: run-20260804-0017
task_id: "45"
capability_id: agentic-topology
plan_id: ISSUE-45-plan-001
state: running
owner: "@mansura-habiba"
provider:
  adapter: codex
  provider_run_id: provider-abc123
lease:
  lane: default
  claimed_at: "2026-08-04T14:00:00Z"
  expires_at: "2026-08-04T17:00:00Z"
workspace:
  branch: agent/issue-45-topology-semantics
  worktree: .worktrees/agent-sessions/run-20260804-0017
verification:
  status: pending
human_control:
  mode: agent
```

---

## 12. Inspect status

List current sessions:

```bash
sdd harness status
```

Inspect one session:

```bash
sdd harness status --run run-20260804-0017
```

Expected information:

```text
Run: run-20260804-0017
Task: #45 — Define topology semantics
State: running
Provider: codex
Elapsed: 00:37:12
Last heartbeat: 18 seconds ago
Lease expires: 02:22:48
Branch: agent/issue-45-topology-semantics
Files changed: 7
Verification: not started
Human control: agent
Pending approvals: none
```

Show events:

```bash
sdd harness status \
  --run run-20260804-0017 \
  --events
```

---

## 13. Human override controls

Human controls are append-only governance events. They do not rewrite the
session record or delete previous agent activity.

### Pause

```bash
sdd harness pause \
  --run run-20260804-0017 \
  --by @mansura-habiba \
  --reason "Reviewing unexpected schema change"
```

Pause means:

- do not start new agent actions;
- request the provider to reach a safe checkpoint;
- preserve worktree and lease;
- retain all events and evidence;
- allow inspection.

### Resume

```bash
sdd harness resume \
  --run run-20260804-0017 \
  --by @mansura-habiba
```

Resume does not start a new history. It continues from the existing run state
and event cursor.

### Stop

```bash
sdd harness stop \
  --run run-20260804-0017 \
  --by @mansura-habiba \
  --reason "Task scope is no longer valid"
```

Stop means:

- request provider termination;
- prohibit further tool use;
- retain worktree for inspection;
- mark verification as not completed unless already finished;
- release or quarantine the lease according to policy.

### Take over

```bash
sdd harness takeover \
  --run run-20260804-0017 \
  --by @mansura-habiba \
  --reason "Human will complete migration manually"
```

Takeover means:

- agent execution stops;
- human becomes the active controller;
- the same branch and worktree remain available;
- future commands are marked as human activity;
- the run remains auditable.

### Release control back to the agent

```bash
sdd harness release \
  --run run-20260804-0017 \
  --by @mansura-habiba
```

Release requires the current task, plan, scope, permissions, and lease to remain
valid. If they changed during takeover, a new validation or plan revision is
required.

### Redirect

Redirection must remain inside the accepted task and plan.

```bash
sdd harness redirect \
  --run run-20260804-0017 \
  --by @mansura-habiba \
  --instruction "Keep the schema unchanged; add adapter types in a new module"
```

A redirect that expands scope is rejected and requires a plan revision.

---

## 14. Approvals during a session

The provider may request a privileged operation:

```text
Request: modify .github/workflows/governance.yml
Reason: add a harness check
Policy: protected path
Outcome: approval required
```

Inspect pending approvals:

```bash
sdd harness status --approvals
```

Approve:

```bash
sdd harness approve \
  --run run-20260804-0017 \
  --request approval-004 \
  --by @mansura-habiba \
  --reason "Workflow change is in accepted plan"
```

Deny:

```bash
sdd harness deny \
  --run run-20260804-0017 \
  --request approval-004 \
  --by @mansura-habiba \
  --reason "Protected workflow is out of task scope"
```

The agent cannot approve its own request.

---

## 15. Leases, heartbeats, and stale recovery

Each running lane may hold one task lease.

```text
Task #45
  claimed by run-20260804-0017
  lane default
  lease expires 17:00 UTC
```

The provider or harness emits heartbeats. When heartbeats stop:

```text
running
→ stale
→ recovery decision
```

Inspect stale sessions:

```bash
sdd harness status --state stale
```

Recover:

```bash
sdd harness resume \
  --run run-20260804-0017 \
  --by @mansura-habiba
```

Retry from a new provider process while preserving the same logical history:

```bash
sdd harness retry \
  --run run-20260804-0017 \
  --by @mansura-habiba
```

Abandon and release the task:

```bash
sdd harness stop \
  --run run-20260804-0017 \
  --by @mansura-habiba \
  --reason "Provider process unavailable"
```

The harness must not silently let another session claim the task while the old
lease is still valid.

---

## 16. Verification and evidence

The provider's claim that work is complete is not the final result.

Verification runs independently from provider reasoning:

```text
Provider result
  ↓
Path and scope validation
  ↓
Contract case validation
  ↓
Configured commands
  ↓
Diff and prohibited-pattern checks
  ↓
Pull-request evidence summary
```

Example:

```yaml
verification:
  commands:
    - pytest tests/contract/test_topology.py -v
    - pytest
    - ruff check src tests
    - sdd validate --strict
```

Every session records:

- command;
- start and completion times;
- exit code;
- captured output reference;
- environment fingerprint without secrets;
- affected acceptance cases;
- whether the command ran inside the isolated worktree;
- final verification status.

A failed verification result may trigger the configured repair prompt, subject
to the retry budget:

```text
verifying
→ repair-required
→ retrying
→ running
→ verifying
```

The harness must never weaken or delete tests to make verification pass.

---

## 17. Pull-request behaviour

Default policy:

```yaml
pull_request:
  create: true
  auto_merge: false
```

Generated PR content should include:

```markdown
## Summary

## Task and capability

- Issue: #45
- Capability: agentic-topology
- Plan: ISSUE-45-plan-001
- Owner handle: @mansura-habiba

## Acceptance mapping

## Files changed

## Verification

## Human overrides

## Risks and limitations
```

The harness can open or update the PR. It does not merge it unless a future,
explicitly enabled low-risk policy permits auto-merge.

Initial SDD++ releases should keep automatic merge disabled.

---

## 18. Schedule repeated sessions

The generated workflow may support manual and scheduled execution:

```yaml
name: SDD agent harness

on:
  workflow_dispatch:
    inputs:
      task:
        description: Optional task ID
        required: false
  schedule:
    - cron: "17 */2 * * *"

concurrency:
  group: sdd-agent-harness
  cancel-in-progress: false

jobs:
  run-next:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pull-requests: write
      issues: write
      actions: read

    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - run: pip install -e ".[full]"

      - run: sdd harness validate

      - run: |
          if [ -n "${{ inputs.task }}" ]; then
            sdd harness run --task "${{ inputs.task }}"
          else
            sdd harness run --next
          fi
```

A production workflow will usually invoke a remote provider or queue rather than
running a long agent process directly on a short-lived CI runner.

---

## 19. Event and audit model

Session events are append-only JSON Lines records.

Example:

```json
{"id":"evt-001","type":"harness.run.created","run_id":"run-20260804-0017","time":"2026-08-04T14:00:00Z"}
{"id":"evt-002","type":"harness.task.claimed","run_id":"run-20260804-0017","task_id":"45","time":"2026-08-04T14:00:02Z"}
{"id":"evt-003","type":"harness.provider.started","run_id":"run-20260804-0017","time":"2026-08-04T14:00:08Z"}
{"id":"evt-004","type":"harness.override.paused","run_id":"run-20260804-0017","actor":"@mansura-habiba","time":"2026-08-04T14:37:12Z"}
```

Event families include:

```text
harness.run.*
harness.task.*
harness.lease.*
harness.provider.*
harness.tool.*
harness.verification.*
harness.approval.*
harness.override.*
harness.pull_request.*
harness.outcome.*
```

Humans and agents cannot rewrite committed events. Corrections are new events.

---

## 20. Security model

The harness should run with least privilege.

Recommended GitHub permissions:

```yaml
permissions:
  contents: write
  pull-requests: write
  issues: write
  actions: read
```

Avoid granting:

```text
administration
secrets management
branch protection modification
environment deployment approval
organisation management
```

Rules:

- Secrets are denied by default.
- Only named environment variables may enter the provider process.
- Prompt and log redaction runs before persistence.
- Provider output is untrusted input.
- Shell arguments use structured arrays, not string concatenation.
- Worktrees stay inside a configured root.
- Symlink escapes are rejected.
- Prohibited paths are checked before and after execution.
- Replay and inspection modes cannot invoke live tools.
- Human overrides take precedence over provider actions.

---

## 21. Adopt incrementally

### Stage 1: Scaffold only

```text
sdd harness init
sdd harness validate
```

Use the generated files as a manual operating contract.

### Stage 2: Supervised local run

```text
One task
One accepted plan
One local provider invocation
Human launch
Human merge
```

### Stage 3: Bounded automatic launch

```text
Automatic dependency-aware selection
Automatic branch/worktree creation
Automatic provider launch
Independent verification
Human merge
```

### Stage 4: Scheduled queue

```text
Periodic selection
Leases and stale recovery
Maximum two parallel sessions
No automatic merge
```

### Stage 5: Graduated trust

Grant broader autonomy only after measured evidence:

- completion success rate;
- verification pass rate;
- human override frequency;
- rollback rate;
- security findings;
- calibration accuracy;
- average review effort.

Autonomy should be earned per capability, not granted globally.

---

## 22. Example: Agentic Topology issue chain

Suppose the repository has:

```text
#45 Topology semantic contracts
#46 Compound renderer         depends on #45
#47 Lenses and diagnostics    depends on #45 and #46
#48 Diff and replay           depends on #45 and #46
#49 Accessibility tests       depends on #45, #46, #47, #48
```

The harness evaluates:

```text
#45 ready
#46 blocked
#47 blocked
#48 blocked
#49 blocked
```

After #45 is merged and closed:

```text
#46 ready
```

After #46 is merged:

```text
#47 ready
#48 ready
```

They may run in parallel only when:

- separate lanes are available;
- their allowed files do not conflict;
- both have accepted plans;
- the configured maximum parallel sessions permits it.

After #47 and #48 merge:

```text
#49 ready
```

The harness never starts #46 merely because #45 has an open PR. Dependencies are
released only by the configured completion policy, normally merge and issue
closure.

---

## 23. Common failure cases

### Task is not eligible

```bash
sdd harness plan --task 46
```

Resolve the reported dependency, plan, capability, or acceptance-case blocker.
Do not add a force flag that bypasses governance.

### Plan is still draft

A human must review and accept it:

```bash
sdd plan accept --id ISSUE-46-plan-001 --by @mansura-habiba
```

### Lease is held by another run

Inspect the active run:

```bash
sdd harness status --task 46
```

Wait, stop the old run, or recover a stale lease through a human control command.

### Provider does not stop

The harness records `stopping`, sends the provider stop request, waits for the
configured grace period, then terminates the local process or quarantines the
remote run. It must retain the event history.

### Verification passes locally but fails in CI

The PR remains open. The harness records the CI result and may create a bounded
repair attempt. It cannot merge or mark the task complete.

### Human changed files during the agent run

The harness detects worktree or branch divergence. It pauses and requires a
reconciliation decision rather than overwriting human changes.

### Governance file changed unexpectedly

The run is blocked immediately. The change is preserved for inspection but is
not accepted as valid work.

---

## 24. Developer checklist

Before first run:

- [ ] `sdd validate --strict` passes.
- [ ] Capability spec is human-owned and active.
- [ ] Task has explicit scope and non-goals.
- [ ] Plan is accepted by a human.
- [ ] Provider adapter works in a disposable repository.
- [ ] Allowed paths are narrower than the entire repository.
- [ ] Prohibited governance and release paths are configured.
- [ ] Verification commands pass on the baseline branch.
- [ ] Human merge is required.
- [ ] Stop and takeover commands were tested.
- [ ] Event and evidence retention is configured.
- [ ] No undeclared secrets enter the provider process.

Before enabling continuous mode:

- [ ] At least ten bounded sessions completed.
- [ ] No unresolved security incident occurred.
- [ ] Human override rate is understood.
- [ ] Stale lease recovery was tested.
- [ ] Parallel worktree isolation was tested.
- [ ] Provider failure and timeout were tested.
- [ ] CI repair budget is bounded.
- [ ] Auto-merge remains disabled unless separately approved.

---

## 25. What remains human-owned

Even with continuous execution, humans own:

- capability intent;
- acceptance cases;
- architectural decisions;
- plan acceptance;
- scope expansion;
- governance changes;
- privileged authority;
- merge decisions by default;
- deployment;
- accountability for outcomes.

The purpose of the harness is not to remove humans. It is to move human attention
from repetitive supervision to explicit decisions, exceptions, and review.

---

## 26. Implementation tracking

This guide is delivered with the governed proposal in pull request #2.
Implementation is tracked by issue #1.

The first implementation should prioritise:

1. configuration and run-state schemas;
2. `sdd harness init`;
3. `sdd harness validate`;
4. eligibility and lease contracts;
5. append-only events;
6. pause, resume, stop, takeover, and release controls;
7. generic provider adapter interface;
8. reference workflow and documentation;
9. tests and MCP exposure.

Live provider execution and automatic PR creation may be introduced only after
the scaffold, state, permission, event, override, and verification contracts are
stable.
