"""`sdd validate` — validate the v0.3 governance tree.

Schemas are loaded from the bundled sdd._schemas package, not from .governance/.
Adopters never copy schemas; they get the latest by upgrading the tool.

Validates:
  - capabilities/REGISTRY.yaml against registry schema
  - capabilities/<id>/spec.md frontmatter against capability_spec schema
  - plan/<task-id>.plan.md frontmatter against plan schema
  - wiki/findings/<id>.md frontmatter against finding schema
  - Cross-references (capability ids in REGISTRY exist as folders, plan capabilities resolve, etc.)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import click
from jsonschema import Draft202012Validator

from sdd._paths import (
    capabilities_dir,
    findings_dir,
    governance_dir,
    plan_dir,
    registry_path,
    target_root,
)
from sdd._schemas import schema_path
from sdd._yaml import load_yaml


@dataclass
class ValidationResult:
    file: Path
    schema: str
    errors: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.errors


def _load_validator(name: str) -> Draft202012Validator:
    return Draft202012Validator(load_yaml(schema_path(name)))


def _format_errors(errors_iter) -> list[str]:
    return [
        f"at {'/'.join(map(str, err.path)) or '<root>'}: {err.message}"
        for err in errors_iter
    ]


def _validate_yaml_file(
    path: Path, validator: Draft202012Validator, schema_label: str
) -> ValidationResult:
    """Validate a pure YAML file (no frontmatter parsing — v0.4 pivot)."""
    res = ValidationResult(file=path, schema=schema_label)
    try:
        doc = load_yaml(path)
    except Exception as e:
        res.errors.append(f"YAML parse error: {e}")
        return res
    if not isinstance(doc, dict):
        res.errors.append("top-level YAML must be a mapping")
        return res
    res.errors.extend(
        _format_errors(sorted(validator.iter_errors(doc), key=lambda e: list(e.path)))
    )
    return res


# Backwards-compat alias retained in case any external code or tests still call it
_validate_frontmatter_file = _validate_yaml_file


def _cross_ref_checks(target: Path | None) -> list[str]:
    issues: list[str] = []
    tgt = target_root(target)

    # REGISTRY entries must point at existing spec.md files
    reg_path = registry_path(target)
    if reg_path.exists():
        try:
            reg = load_yaml(reg_path) or {}
        except Exception:
            reg = {}
        for entry in (reg.get("capabilities") or []):
            if not isinstance(entry, dict):
                continue
            sp = entry.get("spec_path")
            if sp and not (tgt / sp).exists():
                issues.append(
                    f"REGISTRY entry {entry.get('id')}: spec_path '{sp}' does not exist."
                )

    # Plans must reference existing capabilities (v0.4 — pure YAML)
    if plan_dir(target).exists():
        for path in plan_dir(target).glob("*.plan.yaml"):
            try:
                fm = load_yaml(path)
            except Exception:
                continue
            if not isinstance(fm, dict):
                continue
            cap = fm.get("capability")
            if cap:
                cap_path = capabilities_dir(target) / cap / "spec.yaml"
                if not cap_path.exists():
                    issues.append(
                        f"Plan {path.name}: capability '{cap}' has no spec.yaml at {cap_path}."
                    )

    return issues


def run_validate(target: Path | None, strict: bool) -> int:
    tgt = target_root(target)
    gov = governance_dir(target)

    if not gov.exists():
        click.secho(
            f"FATAL: no .governance/ directory at {tgt}. Run `sdd init` first.",
            err=True,
            fg="red",
        )
        return 2

    results: list[ValidationResult] = []

    # Registry
    if registry_path(target).exists():
        results.append(
            _validate_yaml_file(
                registry_path(target),
                _load_validator("registry"),
                "registry.schema.yaml",
            )
        )

    # Capability spec.yaml files (v0.4 — pure YAML)
    spec_v = _load_validator("capability_spec")
    if capabilities_dir(target).exists():
        for path in sorted(capabilities_dir(target).glob("*/spec.yaml")):
            results.append(_validate_yaml_file(path, spec_v, "capability_spec.schema.yaml"))

    # Plan files (v0.4 — pure YAML)
    plan_v = _load_validator("plan")
    if plan_dir(target).exists():
        for path in sorted(plan_dir(target).glob("*.plan.yaml")):
            results.append(_validate_yaml_file(path, plan_v, "plan.schema.yaml"))

    # Finding files (v0.4 — pure YAML)
    finding_v = _load_validator("finding")
    if findings_dir(target).exists():
        for path in sorted(findings_dir(target).glob("*.yaml")):
            if path.name == ".gitkeep":
                continue
            results.append(_validate_yaml_file(path, finding_v, "finding.schema.yaml"))

    passed = [r for r in results if r.passed]
    failed = [r for r in results if not r.passed]

    click.secho("sdd validate", bold=True)
    click.echo(f"  target: {tgt}")
    click.echo(f"  files validated: {len(results)}")
    click.echo()

    for r in results:
        color = "green" if r.passed else "red"
        try:
            rel = r.file.relative_to(tgt)
        except ValueError:
            rel = r.file
        click.secho(
            f"  [{'PASS' if r.passed else 'FAIL'}] {rel} ({r.schema})",
            fg=color,
        )
        for err in r.errors:
            click.secho(f"      · {err}", fg="red")

    cross = _cross_ref_checks(target)
    if cross:
        click.echo()
        click.secho("Cross-reference issues:", fg="yellow", bold=True)
        for c in cross:
            click.secho(f"  · {c}", fg="yellow")

    click.echo()
    click.secho(
        f"Summary: {len(passed)} passed, {len(failed)} failed, {len(cross)} cross-ref issues.",
        bold=True,
    )

    # Record progress event
    from sdd._progress import record

    record(
        target=target,
        kind="validate",
        message=f"{len(passed)} passed, {len(failed)} failed, {len(cross)} cross-ref issues.",
    )

    if failed:
        return 1
    if strict and cross:
        return 1
    return 0
