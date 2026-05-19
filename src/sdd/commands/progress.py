"""`sdd progress` — show, update, or refresh .governance/progress.md.

v0.3: renamed from `sdd status`. `sdd status` remains as a deprecated alias in cli.py.
"""
from __future__ import annotations

from pathlib import Path

import click

from sdd._paths import governance_dir, progress_md_path, target_root
from sdd._progress import record, update_progress_file


def run_progress_show(target: Path | None) -> int:
    path = progress_md_path(target)
    if not path.exists():
        gov = governance_dir(target)
        if not gov.exists():
            click.secho(
                f"FATAL: no .governance/ at {target_root(target)}. Run `sdd init` first.",
                err=True, fg="red",
            )
            return 2
        update_progress_file(target)
    if not path.exists():
        click.secho("Could not produce progress.md.", err=True, fg="red")
        return 1
    click.echo(path.read_text(encoding="utf-8"))
    return 0


def run_progress_update(
    target: Path | None, kind: str, message: str, actor: str | None
) -> int:
    out = record(target=target, kind=kind, message=message, actor=actor)
    if out is None:
        click.secho(
            f"FATAL: no .governance/ at {target_root(target)}. Run `sdd init` first.",
            err=True, fg="red",
        )
        return 2
    click.secho(f"+ event: [{kind}] {message}", fg="green")
    try:
        rel = out.relative_to(target_root(target))
    except ValueError:
        rel = out
    click.echo(f"  progress refreshed at {rel}")
    return 0


def run_progress_refresh(target: Path | None) -> int:
    out = update_progress_file(target)
    if out is None:
        click.secho(
            f"FATAL: no .governance/ at {target_root(target)}. Run `sdd init` first.",
            err=True, fg="red",
        )
        return 2
    try:
        rel = out.relative_to(target_root(target))
    except ValueError:
        rel = out
    click.secho(f"refreshed {rel}", fg="cyan")
    return 0
