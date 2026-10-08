# Worked Example: Token Bucket Rate Limiter

This directory provides a minimal, complete worked example of the **Spec-Driven Development Plus Plus (SDD++)** workflow.

It demonstrates how AI-assisted feature development is governed from human intent to passing contract test without letting AI author contracts or self-accept plans.

---

## 1. Directory Structure

```text
examples/worked-example/
├── README.md                                    # This walkthrough guide
├── .governance/
│   ├── capabilities/
│   │   ├── REGISTRY.yaml                        # Continuous capability registry
│   │   └── rate-limiter/
│   │       ├── spec.yaml                        # Canonical human-authored capability contract
│   │       └── design.md                        # Architecture & algorithmic design
│   ├── plan/
│   │   └── RL-1-plan-001.plan.yaml              # AI-drafted, human-accepted implementation plan
│   └── wiki/
│       └── findings/
│           └── wall-clock-drift.yaml            # Captured gotcha & institutional knowledge
├── src/
│   └── rate_limiter/
│       ├── __init__.py                          # Public package exports
│       └── limiter.py                           # Thread-safe TokenBucket implementation
└── tests/
    ├── __init__.py
    └── contract/
        ├── __init__.py
        └── test_rate_limiter.py                 # Contract tests bound to case_ids with '# why:'
```

---

## 2. The SDD++ Workflow by Example

### Step 1: Human Authors Capability Specification
The human engineer owns the capability definition. AI is forbidden from authoring or modifying `spec.yaml` without human governance.
- **Artifact**: [`.governance/capabilities/rate-limiter/spec.yaml`](.governance/capabilities/rate-limiter/spec.yaml)
- **What it defines**: Inputs, outputs, system invariants, acceptance `cases` (e.g., `allow-within-capacity`, `reject-when-exhausted`), definition of done, and `forbidden` behaviors (e.g., using `time.time()` or partial deductions).
- **Registry**: Registered in [`.governance/capabilities/REGISTRY.yaml`](.governance/capabilities/REGISTRY.yaml).

### Step 2: AI Proposes Plan with Mandatory Challenge
When tasked with implementing task `RL-1`, the AI drafts an implementation plan. The AI must populate the `challenge` block (pushback, concerns, alternatives) and define `non_goals`.
- **Artifact**: [`.governance/plan/RL-1-plan-001.plan.yaml`](.governance/plan/RL-1-plan-001.plan.yaml)
- **Key Gate**: The plan starts in `status: draft`. AI cannot self-accept.

### Step 3: Human Accepts the Plan
The human owner reviews the AI's proposal, concerns, and scope boundaries, and accepts the plan via:
```bash
sdd plan accept --id RL-1-plan-001 --by @naveen-bhalla
```
The plan status transitions to `accepted` with a recorded timestamp and human signature.

### Step 4: AI Implements Code & Contract Tests
Implementation proceeds against the accepted plan. Every test in `tests/contract/` explicitly binds to a `case_id` defined in the capability spec and includes a human-verifiable `# why:` explanation comment.
- **Source Code**: [`src/rate_limiter/limiter.py`](src/rate_limiter/limiter.py)
- **Contract Tests**: [`tests/contract/test_rate_limiter.py`](tests/contract/test_rate_limiter.py)

### Step 5: Knowledge Accumulation (Findings)
During design and testing, discovered gotchas (such as wall-clock NTP jumps corrupting rate limiting) are recorded as structured findings for future tasks and agents.
- **Artifact**: [`.governance/wiki/findings/wall-clock-drift.yaml`](.governance/wiki/findings/wall-clock-drift.yaml)

---

## 3. Running Validation & Tests

To validate the governance artifacts against the bundled schemas:
```bash
sdd validate --target examples/worked-example
```

To run the contract test suite:
```bash
pytest examples/worked-example/tests/contract/
```
