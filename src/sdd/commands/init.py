"""`sdd init` — bootstrap a repo with the v0.3 framework.

v0.3 layout written:
    .governance/
      wiki/
        principles.md
        findings/.gitkeep
      capabilities/
        REGISTRY.yaml
        example-feature/
          spec.md
      arch_spec.md
      instructions.md
      plan/
        example.plan.md
    AGENTS.md             (at repo root — copy of instructions.md for tool compat)
    .github/
      ISSUE_TEMPLATE/task-card.yml
      pull_request_template.md
      workflows/governance.yml
    tests/contract/.gitkeep

Schemas are NOT written to .governance/ — they live inside the sdd package itself and
are loaded by `sdd validate` automatically.
"""
from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

import click

from sdd._paths import (
    agents_md_path,
    capabilities_dir,
    contract_tests_dir,
    findings_dir,
    github_dir,
    governance_dir,
    plan_dir,
    target_root,
    templates_dir,
    wiki_dir,
)


@dataclass(frozen=True)
class FileOp:
    src: Path
    dst: Path
    description: str


def _plan_file_ops(tmpl: Path, target: Path) -> list[FileOp]:
    gov = governance_dir(target)
    ops: list[FileOp] = []

    # --- Wiki ---
    ops.append(FileOp(tmpl / "wiki" / "principles.md", wiki_dir(target) / "principles.md",
                     "5 principles incl. ownership + challenge"))
    ops.append(FileOp(tmpl / "wiki" / "coding-standards.md", wiki_dir(target) / "coding-standards.md",
                     "tribal knowledge AI loads every session"))

    # --- Capabilities ---
    ops.append(FileOp(tmpl / "capabilities" / "REGISTRY.yaml",
                     capabilities_dir(target) / "REGISTRY.yaml",
                     "continuous capability registry"))
    ops.append(FileOp(tmpl / "capabilities" / "example-feature" / "spec.yaml",
                     capabilities_dir(target) / "example-feature" / "spec.yaml",
                     "starter capability spec — canonical YAML (rename and edit)"))

    # --- Top-level governance docs ---
    ops.append(FileOp(tmpl / "arch_spec.md", gov / "arch_spec.md",
                     "whole-system architecture (fill in TODOs)"))
    ops.append(FileOp(tmpl / "instructions.md", gov / "instructions.md",
                     "AI standing orders (canonical)"))
    ops.append(FileOp(tmpl / "USAGE.md", gov / "USAGE.md",
                     "human-agent workflow guide with examples"))

    # --- Plan example ---
    ops.append(FileOp(tmpl / "plan" / "example.plan.yaml", plan_dir(target) / "example.plan.yaml",
                     "starter plan — canonical YAML showing the challenge + ownership shape"))

    # --- AGENTS.md at repo root (copy of instructions.md for tool compat) ---
    ops.append(FileOp(tmpl / "instructions.md", agents_md_path(target),
                     "AGENTS.md at repo root — copy of instructions.md for AI tool auto-load"))

    # --- GitHub templates ---
    gh = github_dir(target)
    ops.append(FileOp(tmpl / "github" / "ISSUE_TEMPLATE" / "task-card.yml",
                     gh / "ISSUE_TEMPLATE" / "task-card.yml",
                     "GitHub Issue Form for tasks"))
    ops.append(FileOp(tmpl / "github" / "pull_request_template.md",
                     gh / "pull_request_template.md",
                     "PR template with ownership disclosure"))
    ops.append(FileOp(tmpl / "github" / "workflows" / "governance.yml",
                     gh / "workflows" / "governance.yml",
                     "CI gate"))

    return ops


def _ensure_marker_dirs(target: Path) -> None:
    """Empty dirs that should exist as containers for user-authored content."""
    for d in (
        findings_dir(target),
        plan_dir(target),
        contract_tests_dir(target),
    ):
        d.mkdir(parents=True, exist_ok=True)
        keep = d / ".gitkeep"
        if not keep.exists() and not any(d.iterdir()):
            keep.write_text("")


def run_init(
    tier: str,
    target: Path | None,
    force: bool,
    dry_run: bool,
) -> int:
    tgt = target_root(target)
    tmpl = templates_dir()

    if not tmpl.exists():
        click.secho(
            f"FATAL: bundled templates not found at {tmpl}. Reinstall sdd-plus-plus.",
            err=True,
            fg="red",
        )
        return 2

    ops = _plan_file_ops(tmpl, tgt)

    will_write: list[FileOp] = []
    will_skip: list[FileOp] = []
    for op in ops:
        if op.dst.exists() and not force:
            will_skip.append(op)
        else:
            will_write.append(op)

    click.secho(f"sdd init — target: {tgt}", bold=True)
    click.echo(f"  tier: {tier}")
    click.echo(f"  files to write: {len(will_write)}")
    click.echo(f"  files to skip (already exist): {len(will_skip)}")
    if will_skip:
        click.echo("  (use --force to overwrite)")
    click.echo()

    if dry_run:
        click.secho("Dry run — no files written.", fg="yellow")
        for op in will_write:
            try:
                rel = op.dst.relative_to(tgt)
            except ValueError:
                rel = op.dst
            click.echo(f"  + {rel}  ({op.description})")
        for op in will_skip:
            try:
                rel = op.dst.relative_to(tgt)
            except ValueError:
                rel = op.dst
            click.echo(f"  · {rel}  (exists)")
        return 0

    for op in will_write:
        op.dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(op.src, op.dst)
        try:
            rel = op.dst.relative_to(tgt)
        except ValueError:
            rel = op.dst
        click.secho(f"  + {rel}", fg="green")

    for op in will_skip:
        try:
            rel = op.dst.relative_to(tgt)
        except ValueError:
            rel = op.dst
        click.secho(f"  · {rel} (kept)", fg="cyan")

    _ensure_marker_dirs(tgt)

    # Status snapshot — write initial progress.md.
    from sdd._progress import record

    record(target=tgt, kind="init", message=f"Bootstrapped framework v0.3 at tier '{tier}'.")

    click.echo()
    click.secho("Done. Next steps:", bold=True)
    click.echo("  1. Edit .governance/capabilities/example-feature/spec.yaml — rename the folder and the id.")
    click.echo("  2. Edit .governance/capabilities/REGISTRY.yaml to point at your capability.")
    click.echo("  3. Edit .governance/arch_spec.md with your system architecture.")
    click.echo("  4. Run `sdd validate` to confirm everything passes.")
    click.echo("  5. File your first task via the GitHub Issue Form, then `sdd plan new --task <id>`.")
    click.echo()
    click.echo("See .governance/wiki/principles.md for the 5 governing principles.")
    click.echo("See .governance/instructions.md for AI behavior rules.")

    return 0
