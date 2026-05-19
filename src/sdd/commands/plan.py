"""`sdd plan` — AI-generated plans, canonical YAML (v0.4).

Plans live at `.governance/plan/<plan-id>.plan.yaml`. Pure YAML — no markdown body.
Narrative fields (steps, risks, notes) are first-class schema fields.

Subcommands:
  - sdd plan new      : scaffold a new plan (editor-based or --file)
  - sdd plan accept   : human signs off (sets accepted_by + accepted_at)
  - sdd plan list     : list plans
  - sdd plan show     : show one plan

Ownership gates:
  - Schema enforces: if status == accepted, accepted_by must match `^@[a-zA-Z0-9_-]+$`.
  - `sdd plan accept --by @<handle>` is the ONLY way to advance status to accepted.
  - The MCP `propose_plan` tool can only save status: draft.
"""
from __future__ import annotations

import datetime as _dt
import os
import re
import subprocess
import tempfile
from pathlib import Path

import click
from jsonschema import Draft202012Validator

from sdd._paths import (
    governance_dir,
    plan_dir,
    target_root,
)
from sdd._schemas import schema_path
from sdd._yaml import (
    dump_yaml,
    dump_yaml_string,
    load_yaml,
)


def _now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _plan_template_doc(task_id: str, capability: str, tool: str) -> dict:
    """Build the in-memory dict for a starter plan."""
    plan_id = f"{task_id}-plan-001"
    return {
        "plan_id": plan_id,
        "task_id": task_id,
        "capability": capability,
        "generated_by": {"tool": tool, "generated_at": _now_iso()},
        "status": "draft",
        "accepted_by": "",
        "accepted_at": "",
        "challenge": {
            "understood_request": "TODO — restate the user's ask in your own words (≥ 30 chars). AI: this is your forced first-think step.",
            "concerns": [
                "TODO — at least one concern. If no concern: 'No concern surfaced — checked spec and findings, no contradiction.'",
            ],
            "alternatives_considered": [
                "TODO — at least one alternative. If none came to mind, say so explicitly.",
            ],
        },
        "scope": {
            "in_scope": ["TODO — concrete deliverable 1"],
            "non_goals": ["TODO — at least one bounding non-goal"],
        },
        "ai_context": {
            "required_reading": [
                ".governance/wiki/principles.md",
                ".governance/instructions.md",
                f".governance/capabilities/{capability}/spec.yaml",
            ],
            "do_not_modify": [
                ".governance/_schemas/",
                ".governance/wiki/principles.md",
            ],
            "preferred_patterns": [],
        },
        "steps": ["TODO — concrete step 1"],
        "files_to_touch": ["TODO — first file path"],
        "tests_to_satisfy": ["TODO — case_id from the capability's spec.yaml"],
        "risks": ["TODO — if 'no risks', that's itself worth interrogating."],
        "confidence": {"overall": 0.8},
        "notes": "TODO — anything the human reviewer should see that doesn't fit the structured fields above.",
    }


def _plan_template_text(task_id: str, capability: str, tool: str) -> str:
    """Render the plan template as a YAML string with a header comment."""
    header = (
        "# yaml-language-server: $schema=../_schemas/plan.schema.yaml\n"
        "#\n"
        "# AI-generated plan. The `challenge` block MUST be honestly populated before saving.\n"
        "# Empty challenge = invalid plan. Humans accept via `sdd plan accept --by @<handle>`.\n"
        "#\n"
    )
    return header + dump_yaml_string(_plan_template_doc(task_id, capability, tool))


def _open_editor(content: str) -> str | None:
    editor = os.environ.get("EDITOR") or os.environ.get("VISUAL") or "vi"
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".plan.yaml", delete=False, encoding="utf-8"
    ) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)
    try:
        rc = subprocess.call([editor, str(tmp_path)])
        if rc != 0:
            return None
        return tmp_path.read_text(encoding="utf-8")
    finally:
        try:
            tmp_path.unlink()
        except FileNotFoundError:
            pass


def _validate_plan(doc: dict) -> list[str]:
    schema = load_yaml(schema_path("plan"))
    v = Draft202012Validator(schema)
    return [
        f"at {'/'.join(map(str, err.path)) or '<root>'}: {err.message}"
        for err in sorted(v.iter_errors(doc), key=lambda e: list(e.path))
    ]


def _check_todos(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if "TODO" in line]


def _load_plan_from_text(text: str) -> dict | None:
    """Parse YAML text safely; return None on failure."""
    from io import StringIO
    from ruamel.yaml import YAML

    try:
        doc = YAML(typ="rt").load(StringIO(text))
        return doc if isinstance(doc, dict) else None
    except Exception:
        return None


# -----------------------------------------------------------------------------
# new
# -----------------------------------------------------------------------------


def run_plan_new(
    target: Path | None,
    task_id: str,
    capability: str,
    tool: str,
    non_interactive_file: Path | None,
) -> int:
    tgt = target_root(target)
    if not governance_dir(target).exists():
        click.secho(f"FATAL: no .governance/ at {tgt}. Run `sdd init`.", err=True, fg="red")
        return 2

    out_root = plan_dir(target)
    out_root.mkdir(parents=True, exist_ok=True)
    out_path = out_root / f"{task_id}-plan-001.plan.yaml"
    n = 2
    while out_path.exists():
        out_path = out_root / f"{task_id}-plan-{n:03d}.plan.yaml"
        n += 1

    # --- Non-interactive (file import) ---
    if non_interactive_file is not None:
        if not non_interactive_file.exists():
            click.secho(f"FATAL: --file {non_interactive_file} does not exist.", err=True, fg="red")
            return 2
        body = non_interactive_file.read_text(encoding="utf-8")
        doc = _load_plan_from_text(body)
        if doc is None:
            click.secho("FATAL: file is not valid YAML.", err=True, fg="red")
            return 1
        if doc.get("status") == "accepted":
            click.secho(
                "FATAL: a plan cannot be created in `accepted` status. Save as draft first, "
                "then run `sdd plan accept`.",
                err=True, fg="red",
            )
            return 1
        if doc.get("accepted_by") and doc.get("status") != "accepted":
            click.secho(
                "FATAL: accepted_by must be empty for non-accepted plans. Only "
                "`sdd plan accept --by @<human>` sets accepted_by.",
                err=True, fg="red",
            )
            return 1
        errs = _validate_plan(doc)
        if errs:
            click.secho("Validation failed:", err=True, fg="red")
            for e in errs:
                click.secho(f"  · {e}", err=True, fg="red")
            return 1
        out_path = out_root / f"{doc.get('plan_id', out_path.stem)}.plan.yaml"
        out_path.write_text(body, encoding="utf-8")
        click.secho(f"+ {out_path.relative_to(tgt)}", fg="green")
        from sdd._progress import record
        record(target=target, kind="plan-drafted",
               message=f"{doc.get('plan_id')} (task {doc.get('task_id')}) — status: draft")
        return 0

    # --- Interactive editor ---
    template = _plan_template_text(task_id=task_id, capability=capability, tool=tool)
    edited = _open_editor(template)
    if edited is None:
        click.secho("Editor exited non-zero. Plan not saved.", err=True, fg="yellow")
        return 1

    todos = _check_todos(edited)
    if todos:
        click.secho("TODO sentinels still present:", err=True, fg="yellow")
        for t in todos[:10]:
            click.secho(f"  · {t}", err=True, fg="yellow")
        if not click.confirm("Save as draft anyway?", default=False):
            return 1

    doc = _load_plan_from_text(edited)
    if doc is None:
        click.secho("FATAL: edited content is not valid YAML.", err=True, fg="red")
        return 1
    if doc.get("status") == "accepted":
        click.secho(
            "Plans created via `sdd plan new` must start as `draft`. Accept separately.",
            err=True, fg="red",
        )
        return 1
    if doc.get("accepted_by"):
        click.secho(
            "accepted_by must be empty until a human runs `sdd plan accept --by @<handle>`.",
            err=True, fg="red",
        )
        return 1

    errs = _validate_plan(doc)
    if errs:
        click.secho("Validation failed:", err=True, fg="red")
        for e in errs:
            click.secho(f"  · {e}", err=True, fg="red")
        return 1

    if doc.get("plan_id"):
        out_path = out_root / f"{doc['plan_id']}.plan.yaml"
    out_path.write_text(edited, encoding="utf-8")
    click.secho(f"+ {out_path.relative_to(tgt)}", fg="green")
    click.echo(f"  status: draft — accept with: sdd plan accept --id {doc.get('plan_id')} --by @<handle>")

    from sdd._progress import record
    record(target=target, kind="plan-drafted",
           message=f"{doc.get('plan_id')} (task {doc.get('task_id')}) — status: draft")
    return 0


# -----------------------------------------------------------------------------
# accept
# -----------------------------------------------------------------------------


_HUMAN_HANDLE_RE = re.compile(r"^@[a-zA-Z0-9_-]+$")


def run_plan_accept(target: Path | None, plan_id: str, by: str) -> int:
    tgt = target_root(target)
    if not _HUMAN_HANDLE_RE.match(by):
        click.secho(
            f"FATAL: --by must be a handle of the form @name (got '{by}').",
            err=True, fg="red",
        )
        return 2

    out_root = plan_dir(target)
    candidates = list(out_root.glob(f"{plan_id}.plan.yaml"))
    if not candidates:
        for path in out_root.glob("*.plan.yaml"):
            doc = load_yaml(path) if path.exists() else None
            if isinstance(doc, dict) and doc.get("plan_id") == plan_id:
                candidates = [path]
                break

    if not candidates:
        click.secho(f"No plan with id '{plan_id}'.", err=True, fg="red")
        return 1

    path = candidates[0]
    doc = load_yaml(path)
    if not isinstance(doc, dict):
        click.secho(f"FATAL: {path} is not a valid YAML mapping.", err=True, fg="red")
        return 1

    if doc.get("status") == "accepted":
        click.secho(
            f"Plan {plan_id} is already accepted by {doc.get('accepted_by')}.",
            fg="yellow",
        )
        return 0

    doc["status"] = "accepted"
    doc["accepted_by"] = by
    doc["accepted_at"] = _now_iso()

    errs = _validate_plan(doc)
    if errs:
        click.secho("Validation failed after accept update:", err=True, fg="red")
        for e in errs:
            click.secho(f"  · {e}", err=True, fg="red")
        return 1

    dump_yaml(doc, path)
    click.secho(f"accepted: {plan_id} by {by} at {doc['accepted_at']}", fg="green")

    from sdd._progress import record
    record(target=target, kind="plan-accepted",
           message=f"{plan_id} accepted by {by}", actor=by)
    return 0


# -----------------------------------------------------------------------------
# list / show
# -----------------------------------------------------------------------------


def run_plan_list(target: Path | None, status: str | None) -> int:
    root = plan_dir(target)
    if not root.exists():
        click.echo("No plans yet. Use `sdd plan new --task <id> --capability <cap>` to draft one.")
        return 0
    rows: list[tuple[Path, dict]] = []
    for path in sorted(root.glob("*.plan.yaml")):
        doc = load_yaml(path)
        if not isinstance(doc, dict):
            continue
        if status and doc.get("status") != status:
            continue
        rows.append((path, doc))
    if not rows:
        click.echo("No plans match the filter.")
        return 0
    click.secho(f"{len(rows)} plan(s):", bold=True)
    for path, doc in rows:
        st = doc.get("status", "?")
        color = {
            "draft": "yellow",
            "accepted": "green",
            "executed": "cyan",
            "rejected": "red",
            "archived": "white",
        }.get(st, "white")
        click.echo(
            f"  {click.style(doc.get('plan_id', path.stem), bold=True)} "
            f"[{click.style(st, fg=color)}] "
            f"task={doc.get('task_id')} cap={doc.get('capability')} "
            f"by={doc.get('accepted_by') or '—'}"
        )
    return 0


def run_plan_show(target: Path | None, plan_id: str) -> int:
    root = plan_dir(target)
    direct = root / f"{plan_id}.plan.yaml"
    if direct.exists():
        click.echo(direct.read_text(encoding="utf-8"))
        return 0
    if root.exists():
        for path in root.glob("*.plan.yaml"):
            doc = load_yaml(path)
            if isinstance(doc, dict) and doc.get("plan_id") == plan_id:
                click.echo(path.read_text(encoding="utf-8"))
                return 0
    click.secho(f"No plan with id '{plan_id}'.", err=True, fg="red")
    return 1
