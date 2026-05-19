"""`sdd findings` — the LLM-wiki / Knowledge Block layer (v0.4 — canonical YAML).

Findings live under .governance/wiki/findings/<id>.yaml. Pure YAML, no markdown body.
Narrative content (the finding text, evidence, implications, mitigation, notes) is
captured as structured schema fields.

Three subcommands:
  - sdd findings add  : create a new finding (editor-based scaffold or --file import)
  - sdd findings list : list findings, optionally filtered
  - sdd findings show : show one finding's full content
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

from sdd._paths import findings_dir, governance_dir, target_root
from sdd._schemas import schema_path
from sdd._yaml import dump_yaml, dump_yaml_string, load_yaml


def _slugify(text: str) -> str:
    text = re.sub(r"[^a-zA-Z0-9\s-]", "", text).strip().lower()
    text = re.sub(r"[-\s]+", "-", text)
    return text or "untitled-finding"


def _finding_template_doc(
    finding_id: str,
    author: str,
    from_task: str | None,
    related_capability: str | None,
    title_hint: str | None,
) -> dict:
    today = _dt.date.today().isoformat()
    title = title_hint or "TODO — one-line finding title"
    doc = {
        "id": finding_id,
        "title": title,
        "status": "suspected",
        "severity": "medium",
        "discovered_by": author,
        "discovered_at": today,
        "ai_assistance": "none",
        "related_capabilities": [related_capability] if related_capability else [],
        "tags": [],
        "finding": (
            "TODO — describe what was observed and what makes it noteworthy. "
            "Minimum 50 characters of real content."
        ),
        "evidence": ["TODO — log line, test name, commit, PR, or incident reference"],
        "implications": "TODO — what this means for downstream work.",
        "mitigation": ["TODO — current best-known workaround, or 'none yet'"],
        "status_history": [
            {"date": today, "status": "suspected", "by": author, "note": "Initial filing."},
        ],
        "notes": "",
    }
    if from_task:
        doc["discovered_during"] = from_task
    return doc


def _finding_template_text(
    finding_id: str,
    author: str,
    from_task: str | None,
    related_capability: str | None,
    title_hint: str | None,
) -> str:
    header = (
        "# yaml-language-server: $schema=../../_schemas/finding.schema.yaml\n"
        "#\n"
        "# Edit fields, save, close the editor. Replace every TODO before saving.\n"
        "# AI-suggested findings stay status: suspected until a human marks them confirmed.\n"
        "#\n"
    )
    return header + dump_yaml_string(
        _finding_template_doc(finding_id, author, from_task, related_capability, title_hint)
    )


def _open_editor(content: str) -> str | None:
    editor = os.environ.get("EDITOR") or os.environ.get("VISUAL") or "vi"
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, encoding="utf-8"
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


def _validate_finding(doc: dict) -> list[str]:
    schema = load_yaml(schema_path("finding"))
    validator = Draft202012Validator(schema)
    return [
        f"at {'/'.join(map(str, err.path)) or '<root>'}: {err.message}"
        for err in sorted(validator.iter_errors(doc), key=lambda e: list(e.path))
    ]


def _check_todos(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if "TODO" in line]


def _load_yaml_from_text(text: str) -> dict | None:
    from io import StringIO
    from ruamel.yaml import YAML

    try:
        doc = YAML(typ="rt").load(StringIO(text))
        return doc if isinstance(doc, dict) else None
    except Exception:
        return None


# -----------------------------------------------------------------------------
# add
# -----------------------------------------------------------------------------


def run_findings_add(
    target: Path | None,
    from_task: str | None,
    capability: str | None,
    title: str | None,
    author: str | None,
    non_interactive_file: Path | None,
) -> int:
    tgt = target_root(target)
    if not governance_dir(target).exists():
        click.secho(f"FATAL: no .governance/ at {tgt}. Run `sdd init`.", err=True, fg="red")
        return 2

    if not author:
        user = os.environ.get("USER") or "unknown-author"
        author = user if user.startswith("@") else f"@{user}"

    finding_id = _slugify(title or f"finding-{_dt.date.today().isoformat()}")
    findings_root = findings_dir(target)
    findings_root.mkdir(parents=True, exist_ok=True)

    out_path = findings_root / f"{finding_id}.yaml"
    n = 2
    while out_path.exists():
        out_path = findings_root / f"{finding_id}-{n}.yaml"
        finding_id = f"{_slugify(title or 'untitled')}-{n}"
        n += 1

    # --- Non-interactive ---
    if non_interactive_file is not None:
        if not non_interactive_file.exists():
            click.secho(f"FATAL: --file {non_interactive_file} does not exist.", err=True, fg="red")
            return 2
        body = non_interactive_file.read_text(encoding="utf-8")
        doc = _load_yaml_from_text(body)
        if doc is None:
            click.secho("FATAL: input file is not valid YAML.", err=True, fg="red")
            return 1
        errs = _validate_finding(doc)
        if errs:
            click.secho("Validation failed:", err=True, fg="red")
            for e in errs:
                click.secho(f"  · {e}", err=True, fg="red")
            return 1
        out_path = findings_root / f"{doc.get('id', finding_id)}.yaml"
        out_path.write_text(body, encoding="utf-8")
        click.secho(f"+ {out_path.relative_to(tgt)}", fg="green")
        from sdd._progress import record
        record(target=target, kind="finding-added",
               message=f"{doc.get('id')} ({doc.get('status', 'suspected')}) — {doc.get('title', '')[:80]}")
        return 0

    # --- Interactive editor ---
    template = _finding_template_text(
        finding_id=finding_id,
        author=author,
        from_task=from_task,
        related_capability=capability,
        title_hint=title,
    )
    edited = _open_editor(template)
    if edited is None:
        click.secho("Editor exited non-zero. Finding not saved.", err=True, fg="yellow")
        return 1

    todos = _check_todos(edited)
    if todos:
        click.secho("TODO sentinels still present:", err=True, fg="yellow")
        for t in todos:
            click.secho(f"  · {t}", err=True, fg="yellow")
        if not click.confirm("Save anyway?", default=False):
            return 1

    doc = _load_yaml_from_text(edited)
    if doc is None:
        click.secho("FATAL: edited content is not valid YAML.", err=True, fg="red")
        return 1
    errs = _validate_finding(doc)
    if errs:
        click.secho("Validation failed:", err=True, fg="red")
        for e in errs:
            click.secho(f"  · {e}", err=True, fg="red")
        return 1

    if doc.get("id"):
        out_path = findings_root / f"{doc['id']}.yaml"
    out_path.write_text(edited, encoding="utf-8")
    click.secho(f"+ {out_path.relative_to(tgt)}", fg="green")

    from sdd._progress import record
    record(target=target, kind="finding-added",
           message=f"{doc.get('id')} ({doc.get('status', 'suspected')}) — {doc.get('title', '')[:80]}")
    return 0


# -----------------------------------------------------------------------------
# list / show
# -----------------------------------------------------------------------------


def _safe_load(path: Path) -> dict | None:
    try:
        doc = load_yaml(path)
        return doc if isinstance(doc, dict) else None
    except Exception:
        return None


def run_findings_list(
    target: Path | None,
    capability: str | None,
    tag: str | None,
    status: str | None,
) -> int:
    root = findings_dir(target)
    if not root.exists():
        click.echo("No findings yet. Use `sdd findings add` to record the first one.")
        return 0

    rows: list[tuple[str, dict]] = []
    for path in sorted(root.glob("*.yaml")):
        if path.name == ".gitkeep":
            continue
        doc = _safe_load(path)
        if not doc:
            continue
        if capability and capability not in (doc.get("related_capabilities") or []):
            continue
        if tag and tag not in (doc.get("tags") or []):
            continue
        if status and doc.get("status") != status:
            continue
        rows.append((path.stem, doc))

    if not rows:
        click.echo("No findings match the filters.")
        return 0

    click.secho(f"{len(rows)} finding(s):", bold=True)
    for fid, doc in rows:
        sev = doc.get("severity") or "—"
        st = doc.get("status") or "—"
        title = doc.get("title", "(no title)")
        color = {
            "confirmed": "red",
            "suspected": "yellow",
            "mitigated": "green",
            "refuted": "cyan",
            "archived": "white",
        }.get(st, "white")
        click.echo(
            f"  {click.style(fid, bold=True)} "
            f"[{click.style(st, fg=color)}/{sev}] {title}"
        )
    return 0


def run_findings_show(target: Path | None, finding_id: str) -> int:
    path = findings_dir(target) / f"{finding_id}.yaml"
    if not path.exists():
        click.secho(f"No finding with id '{finding_id}' at {path}", err=True, fg="red")
        return 1
    click.echo(path.read_text(encoding="utf-8"))
    return 0
