"""`sdd status` — show, update, or refresh the running status.md.

Three subcommands:
  - sdd status            : print the current status.md to stdout
  - sdd status update     : append a structured event + refresh status.md
  - sdd status refresh    : just re-render (no event appended)

The status mechanism is also called implicitly by other commands (init, validate, doctor,
generate-acceptance, findings add) via sdd._status.record(). And via the `sdd serve` MCP
tools `record_progress` and `record_session_end`.
"""
from __future__ import annotations

from pathlib import Path

import click

from sdd._paths import governance_dir, status_md_path, target_root
from sdd._status import record, update_status_file


def run_status_show(target: Path | None) -> int:
    """Print the current status.md to stdout."""
    path = status_md_path(target)
    if not path.exists():
        gov = governance_dir(target)
        if not gov.exists():
            click.secho(
                f"FATAL: no .governance/ at {target_root(target)}. Run `sdd init` first.",
                err=True,
                fg="red",
            )
            return 2
        # Governance exists but status.md doesn't — render once and show.
        update_status_file(target)

    if not path.exists():
        click.secho("Could not produce status.md.", err=True, fg="red")
        return 1
    click.echo(path.read_text(encoding="utf-8"))
    return 0


def run_status_update(
    target: Path | None, kind: str, message: str, actor: str | None
) -> int:
    """Append an event and refresh status.md."""
    out = record(target=target, kind=kind, message=message, actor=actor)
    if out is None:
        click.secho(
            f"FATAL: no .governance/ at {target_root(target)}. Run `sdd init` first.",
            err=True,
            fg="red",
        )
        return 2
    try:
        rel = out.relative_to(target_root(target))
    except ValueError:
        rel = out
    click.secho(f"+ event: [{kind}] {message}", fg="green")
    click.echo(f"  status refreshed at {rel}")
    return 0


def run_status_refresh(target: Path | None) -> int:
    """Re-render status.md without appending an event."""
    out = update_status_file(target)
    if out is None:
        click.secho(
            f"FATAL: no .governance/ at {target_root(target)}. Run `sdd init` first.",
            err=True,
            fg="red",
        )
        return 2
    try:
        rel = out.relative_to(target_root(target))
    except ValueError:
        rel = out
    click.secho(f"refreshed {rel}", fg="cyan")
    return 0
