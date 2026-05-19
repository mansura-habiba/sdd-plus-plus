"""Status snapshot — the running progress log for `.governance/`.

After every sdd command (and on agent session end via MCP), we append an event to
`.governance/.status-log.yaml` and re-render `.governance/status.md`. The markdown file
is a token-efficient snapshot of "what's happening here, right now" that humans can read
and AI assistants can load instead of accumulating raw command history.

This is Gana's "intentional compaction" pattern: keep a running summary outside the
AI's context window so the window stays focused on the immediate task.

Files:
  - .governance/.status-log.yaml  — machine-readable event log, capped at MAX_LOG events.
  - .governance/status.md         — generated markdown, has auto-managed + human-editable sections.

The human-editable Notes section is delimited by `<!-- SDD-NOTES-START -->` /
`<!-- SDD-NOTES-END -->` markers. Regeneration preserves whatever is between them.
"""
from __future__ import annotations

import datetime as _dt
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from sdd._paths import (
    acceptance_dir,
    capabilities_dir,
    findings_dir,
    governance_dir,
    status_log_path,
    status_md_path,
    target_root,
    tasks_dir,
)
from sdd._yaml import dump_yaml, load_yaml


MAX_LOG = 50
NOTES_START = "<!-- SDD-NOTES-START -->"
NOTES_END = "<!-- SDD-NOTES-END -->"


# -----------------------------------------------------------------------------
# Event log
# -----------------------------------------------------------------------------


@dataclass
class Event:
    ts: str
    kind: str
    message: str
    actor: str = "unknown"


def _now() -> str:
    # ISO 8601 UTC seconds precision. Keep it simple, parseable.
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _default_actor() -> str:
    user = os.environ.get("USER") or "unknown"
    return f"@{user}"


def _load_log(target: Path | None) -> list[Event]:
    path = status_log_path(target)
    if not path.exists():
        return []
    doc = load_yaml(path)
    if not isinstance(doc, list):
        return []
    out: list[Event] = []
    for entry in doc:
        if not isinstance(entry, dict):
            continue
        out.append(
            Event(
                ts=str(entry.get("ts", "")),
                kind=str(entry.get("kind", "unknown")),
                message=str(entry.get("message", "")),
                actor=str(entry.get("actor", "unknown")),
            )
        )
    return out


def _save_log(target: Path | None, events: list[Event]) -> None:
    path = status_log_path(target)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = [
        {"ts": e.ts, "kind": e.kind, "message": e.message, "actor": e.actor}
        for e in events[-MAX_LOG:]
    ]
    dump_yaml(payload, path)


def append_event(
    target: Path | None,
    kind: str,
    message: str,
    actor: str | None = None,
) -> Event:
    """Append a new event to the log. Returns the event for chaining."""
    # If the governance dir doesn't exist (e.g. user ran a command outside an init'd repo),
    # don't fail — just no-op silently. Status is best-effort.
    gov = governance_dir(target)
    if not gov.exists():
        return Event(ts=_now(), kind=kind, message=message, actor=actor or _default_actor())

    log = _load_log(target)
    event = Event(ts=_now(), kind=kind, message=message, actor=actor or _default_actor())
    log.append(event)
    _save_log(target, log)
    return event


# -----------------------------------------------------------------------------
# State collection — what's currently in the .governance/ tree
# -----------------------------------------------------------------------------


@dataclass
class GovernanceSnapshot:
    capability_count: int = 0
    capability_names: list[str] = field(default_factory=list)
    task_count_by_status: dict[str, int] = field(default_factory=dict)
    in_progress_tasks: list[dict[str, str]] = field(default_factory=list)
    acceptance_specs: list[dict[str, str]] = field(default_factory=list)
    open_findings: list[dict[str, str]] = field(default_factory=list)
    pending_actions: list[str] = field(default_factory=list)


def _safe_load(path: Path) -> dict | None:
    try:
        doc = load_yaml(path)
        return doc if isinstance(doc, dict) else None
    except Exception:
        return None


def collect_snapshot(target: Path | None) -> GovernanceSnapshot:
    """Walk .governance/ and build a snapshot of current state."""
    snap = GovernanceSnapshot()

    # Capabilities
    if capabilities_dir(target).exists():
        for path in sorted(capabilities_dir(target).glob("*.yaml")):
            doc = _safe_load(path)
            if doc:
                snap.capability_count += 1
                snap.capability_names.append(
                    doc.get("id", path.stem) + " — " + (doc.get("name", "(unnamed)"))
                )

    # Tasks
    if tasks_dir(target).exists():
        for path in sorted(tasks_dir(target).glob("*.yaml")):
            doc = _safe_load(path)
            if not doc:
                continue
            status = doc.get("status", "unknown")
            snap.task_count_by_status[status] = snap.task_count_by_status.get(status, 0) + 1
            if status == "in_progress":
                snap.in_progress_tasks.append(
                    {
                        "id": doc.get("id", "(no id)"),
                        "title": doc.get("title", ""),
                        "tier": doc.get("tier", ""),
                    }
                )

    # Acceptance specs
    if acceptance_dir(target).exists():
        for path in sorted(acceptance_dir(target).glob("*.acceptance.yaml")):
            doc = _safe_load(path)
            if not doc:
                continue
            snap.acceptance_specs.append(
                {
                    "id": doc.get("id", path.stem),
                    "status": doc.get("status", "draft"),
                    "case_count": str(len(doc.get("cases") or [])),
                }
            )

    # Open findings (status: suspected or confirmed)
    if findings_dir(target).exists():
        for path in sorted(findings_dir(target).glob("*.finding.yaml")):
            doc = _safe_load(path)
            if not doc:
                continue
            status = doc.get("status", "suspected")
            if status not in ("suspected", "confirmed"):
                continue
            snap.open_findings.append(
                {
                    "id": doc.get("id", path.stem.removesuffix(".finding")),
                    "title": doc.get("title", ""),
                    "status": status,
                    "severity": doc.get("severity", "—"),
                }
            )

    # Pending actions — derived heuristics
    if snap.capability_count == 0:
        snap.pending_actions.append("No capability spec yet — rename .governance/capabilities/example-capability.yaml.")
    if snap.acceptance_specs and all(s["status"] != "ratified" for s in snap.acceptance_specs):
        snap.pending_actions.append("No ratified acceptance spec yet. Curate one and set status: ratified.")
    if snap.open_findings:
        confirmed_high = [f for f in snap.open_findings if f.get("severity") in ("high", "critical") and f["status"] == "confirmed"]
        if confirmed_high:
            snap.pending_actions.append(
                f"{len(confirmed_high)} confirmed high/critical finding(s) need mitigation."
            )

    return snap


# -----------------------------------------------------------------------------
# Markdown rendering
# -----------------------------------------------------------------------------


def _preserve_notes(existing_md: str | None) -> str:
    """Extract the human-editable Notes block from an existing status.md, if any."""
    default = "_Notes section — humans can edit between the markers. Auto-generated sections above and below are overwritten._\n"
    if not existing_md:
        return default
    m = re.search(
        rf"{re.escape(NOTES_START)}(.*?){re.escape(NOTES_END)}",
        existing_md,
        flags=re.DOTALL,
    )
    if not m:
        return default
    inner = m.group(1).strip("\n")
    return inner if inner.strip() else default


def render_status_md(target: Path | None, existing_md: str | None = None) -> str:
    """Render the full status.md content.

    Auto-managed sections are completely rewritten each call. The Notes section between
    the SDD-NOTES markers is preserved from existing_md.
    """
    snap = collect_snapshot(target)
    log = _load_log(target)
    notes_block = _preserve_notes(existing_md)
    now = _now()

    lines: list[str] = []
    lines.append("# Governance status\n")
    lines.append(
        f"> Auto-generated by `sdd status` at {now}. Do not hand-edit outside the Notes section."
    )
    lines.append("")

    # --- Snapshot ---
    lines.append("## Snapshot\n")
    lines.append(f"- Capabilities: **{snap.capability_count}**")
    if snap.capability_names:
        for name in snap.capability_names:
            lines.append(f"  - {name}")
    lines.append(f"- Tasks by status:")
    if snap.task_count_by_status:
        for status, count in sorted(snap.task_count_by_status.items()):
            lines.append(f"  - {status}: {count}")
    else:
        lines.append("  - _(no task cards filed yet)_")
    lines.append(f"- Acceptance specs: **{len(snap.acceptance_specs)}**")
    if snap.acceptance_specs:
        for s in snap.acceptance_specs:
            lines.append(f"  - {s['id']} ({s['status']}, {s['case_count']} cases)")
    lines.append(f"- Open findings (suspected or confirmed): **{len(snap.open_findings)}**")
    if snap.open_findings:
        for f in snap.open_findings:
            lines.append(
                f"  - {f['id']} [{f['status']}/{f['severity']}] — {f['title']}"
            )
    lines.append("")

    # --- Active tasks ---
    if snap.in_progress_tasks:
        lines.append("## Active tasks\n")
        for t in snap.in_progress_tasks:
            lines.append(f"- **{t['id']}** ({t['tier']}) — {t['title']}")
        lines.append("")

    # --- Pending actions ---
    lines.append("## Pending actions\n")
    if snap.pending_actions:
        for a in snap.pending_actions:
            lines.append(f"- {a}")
    else:
        lines.append("- _No pending framework-derived actions._")
    lines.append("")

    # --- Activity log ---
    lines.append(f"## Recent activity (last {min(len(log), MAX_LOG)})\n")
    if log:
        for e in reversed(log):
            lines.append(f"- `{e.ts}` **{e.kind}** ({e.actor}) — {e.message}")
    else:
        lines.append("- _No events logged yet._")
    lines.append("")

    # --- Notes (human-editable) ---
    lines.append("## Notes\n")
    lines.append(NOTES_START)
    lines.append(notes_block.rstrip("\n"))
    lines.append(NOTES_END)
    lines.append("")

    return "\n".join(lines)


# -----------------------------------------------------------------------------
# Update — write status.md to disk
# -----------------------------------------------------------------------------


def update_status_file(target: Path | None) -> Path | None:
    """Re-render status.md to disk. Returns the path, or None if .governance/ doesn't exist."""
    gov = governance_dir(target)
    if not gov.exists():
        return None
    out_path = status_md_path(target)
    existing = out_path.read_text(encoding="utf-8") if out_path.exists() else None
    content = render_status_md(target, existing_md=existing)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(content, encoding="utf-8")
    return out_path


def record(
    target: Path | None,
    kind: str,
    message: str,
    actor: str | None = None,
) -> Path | None:
    """High-level convenience: append event + refresh status.md.

    Use this from command handlers — single call covers both sides.
    """
    append_event(target, kind, message, actor)
    return update_status_file(target)
