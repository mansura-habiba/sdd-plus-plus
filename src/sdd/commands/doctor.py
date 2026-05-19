"""`sdd doctor` — diagnose the v0.3 adoption state."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import click

from sdd._paths import (
    agents_md_path,
    arch_spec_path,
    capabilities_dir,
    contract_tests_dir,
    findings_dir,
    github_dir,
    instructions_md_path,
    plan_dir,
    principles_md_path,
    registry_path,
    target_root,
)
from sdd._yaml import load_yaml


@dataclass
class Milestone:
    description: str
    passed: bool
    next_action: str


def _check(target: Path | None) -> list[Milestone]:
    tgt = target_root(target)
    ms: list[Milestone] = []

    ms.append(Milestone(
        ".governance/wiki/principles.md present",
        principles_md_path(target).exists(),
        "Run `sdd init` to install the principles doc.",
    ))
    ms.append(Milestone(
        ".governance/instructions.md present (AI rules)",
        instructions_md_path(target).exists(),
        "Run `sdd init` to install instructions.md.",
    ))
    ms.append(Milestone(
        "AGENTS.md at repo root (AI tool compat)",
        agents_md_path(target).exists(),
        "Run `sdd init` — it writes AGENTS.md as a copy of instructions.md.",
    ))
    ms.append(Milestone(
        ".governance/arch_spec.md present",
        arch_spec_path(target).exists(),
        "Run `sdd init` to install arch_spec.md and fill in the TODOs.",
    ))
    ms.append(Milestone(
        ".governance/capabilities/REGISTRY.yaml present",
        registry_path(target).exists(),
        "Run `sdd init` to install the registry.",
    ))

    # At least one real capability (not just example-feature)
    cap_count = 0
    if capabilities_dir(target).exists():
        for sp in capabilities_dir(target).glob("*/spec.yaml"):
            if sp.parent.name != "example-feature":
                cap_count += 1
    ms.append(Milestone(
        "At least one team-authored capability spec",
        cap_count > 0,
        "Rename .governance/capabilities/example-feature/ for your first real capability and edit spec.md.",
    ))

    # At least one accepted plan
    accepted_plans = 0
    if plan_dir(target).exists():
        for path in plan_dir(target).glob("*.plan.yaml"):
            try:
                doc = load_yaml(path)
            except Exception:
                continue
            if isinstance(doc, dict) and doc.get("status") == "accepted":
                accepted_plans += 1
    ms.append(Milestone(
        "At least one accepted plan (human signoff on AI work)",
        accepted_plans > 0,
        "Draft a plan with `sdd plan new --task <id> --capability <cap>`, then `sdd plan accept --by @handle`.",
    ))

    # CI workflow
    ms.append(Milestone(
        ".github/workflows/governance.yml present",
        (github_dir(target) / "workflows" / "governance.yml").exists(),
        "Run `sdd init` to install the CI gate.",
    ))

    # Contract tests directory
    contract = contract_tests_dir(target).exists() and any(
        contract_tests_dir(target).glob("test_*.py")
    )
    ms.append(Milestone(
        "tests/contract/ present with at least one test file",
        contract,
        "Add a contract test against a case_id from your capability's spec.md.",
    ))

    return ms


def run_doctor(target: Path | None) -> int:
    tgt = target_root(target)
    ms = _check(target)
    passed = sum(1 for m in ms if m.passed)
    total = len(ms)

    click.secho("sdd doctor", bold=True)
    click.echo(f"  target: {tgt}")
    click.echo(f"  score:  {passed}/{total} milestones")
    click.echo()

    for m in ms:
        mark = click.style("✓", fg="green") if m.passed else click.style("·", fg="yellow")
        click.echo(f"  {mark} {m.description}")
        if not m.passed:
            click.echo(click.style(f"      → {m.next_action}", fg="cyan"))

    click.echo()
    if passed == total:
        click.secho(
            "All milestones passed. Consider v0.3 features: `sdd intent`, `sdd reflect`, "
            "mutation testing, contracts.lock.",
            fg="green", bold=True,
        )
    else:
        next_up = next((m for m in ms if not m.passed), None)
        if next_up:
            click.secho(f"Next: {next_up.next_action}", bold=True)

    from sdd._progress import record
    record(target=target, kind="doctor", message=f"{passed}/{total} milestones passed.")
    return 0
