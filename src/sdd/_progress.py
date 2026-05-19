"""Progress snapshot — the running progress log for `.governance/`.

After every sdd command (and on agent session end via MCP), we append an event to
`.governance/.progress-log.yaml` and re-render `.governance/progress.md`. The markdown file
is a token-efficient snapshot of "what's happening here, right now."

v0.3: renamed from status.md to progress.md to match the user's mental model.

The human-editable Notes section is delimited by `<!-- SDD-NOTES-START -->` /
`<!-- SDD-NOTES-END -->` markers. Regeneration preserves whatever is between them.
"""
from __future__ import annotations

import datetime as _dt
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

from sdd._paths import (
    capabilities_dir,
    findings_dir,
    governance_dir,
    plan_dir,
    progress_log_path,
    progress_md_path,
)
from sdd._yaml import (
    dump_yaml,
    load_yaml,
)


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
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _default_actor() -> str:
    user = os.environ.get("USER") or "unknown"
    return f"@{user}"


def _load_log(target: Path | None) -> list[Event]:
    path = progress_log_path(target)
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
    path = progress_log_path(target)
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
    gov = governance_dir(target)
    if not gov.exists():
        return Event(ts=_now(), kind=kind, message=message, actor=actor or _default_actor())

    log = _load_log(target)
    event = Event(ts=_now(), kind=kind, message=message, actor=actor or _default_actor())
    log.append(event)
    _save_log(target, log)
    return event


# -----------------------------------------------------------------------------
# Snapshot collection — v0.3 layout
# -----------------------------------------------------------------------------


@dataclass
class GovernanceSnapshot:
    capability_count: int = 0
    capability_names: list[str] = field(default_factory=list)
    plan_count_by_status: dict[str, int] = field(default_factory=dict)
    in_flight_plans: list[dict[str, str]] = field(default_factory=list)
    open_findings: list[dict[str, str]] = field(default_factory=list)
    pending_actions: list[str] = field(default_factory=list)


def _spec_files(target: Path | None) -> list[Path]:
    """All capabilities/<id>/spec.yaml files (v0.4 — pure YAML)."""
    cap = capabilities_dir(target)
    if not cap.exists():
        return []
    return list(cap.glob("*/spec.yaml"))


def _plan_files(target: Path | None) -> list[Path]:
    pd = plan_dir(target)
    if not pd.exists():
        return []
    return list(pd.glob("*.plan.yaml"))


def _finding_files(target: Path | None) -> list[Path]:
    fd = findings_dir(target)
    if not fd.exists():
        return []
    return [p for p in fd.glob("*.yaml") if p.name != ".gitkeep"]


def _safe_yaml(path: Path) -> dict | None:
    try:
        doc = load_yaml(path)
        return doc if isinstance(doc, dict) else None
    except Exception:
        return None


def collect_snapshot(target: Path | None) -> GovernanceSnapshot:
    snap = GovernanceSnapshot()

    # Capabilities
    for path in sorted(_spec_files(target)):
        doc = _safe_yaml(path)
        if doc is None:
            continue
        snap.capability_count += 1
        snap.capability_names.append(
            f"{doc.get('id', path.parent.name)} — {doc.get('name', '(unnamed)')} [{doc.get('status', '?')}]"
        )

    # Plans
    for path in sorted(_plan_files(target)):
        doc = _safe_yaml(path)
        if doc is None:
            continue
        status = doc.get("status", "draft")
        snap.plan_count_by_status[status] = snap.plan_count_by_status.get(status, 0) + 1
        if status in ("draft", "accepted"):
            snap.in_flight_plans.append(
                {
                    "id": doc.get("plan_id", path.stem.replace(".plan", "")),
                    "task_id": doc.get("task_id", "(no task)"),
                    "status": status,
                    "capability": doc.get("capability", ""),
                }
            )

    # Open findings (suspected or confirmed)
    for path in sorted(_finding_files(target)):
        doc = _safe_yaml(path)
        if doc is None:
            continue
        status = doc.get("status", "suspected")
        if status not in ("suspected", "confirmed"):
            continue
        snap.open_findings.append(
            {
                "id": doc.get("id", path.stem),
                "title": doc.get("title", ""),
                "status": status,
                "severity": doc.get("severity", "—"),
            }
        )

    # Pending actions — derived heuristics
    if snap.capability_count == 0:
        snap.pending_actions.append(
            "No capability spec yet — rename .governance/capabilities/example-feature/ "
            "and edit its spec.md."
        )
    if snap.in_flight_plans and not any(p["status"] == "accepted" for p in snap.in_flight_plans):
        snap.pending_actions.append(
            "Draft plan(s) exist but none are accepted. A human must run "
            "`sdd plan accept --id <plan> --by @handle`."
        )
    if snap.open_findings:
        critical = [
            f for f in snap.open_findings
            if f.get("severity") in ("high", "critical") and f["status"] == "confirmed"
        ]
        if critical:
            snap.pending_actions.append(
                f"{len(critical)} confirmed high/critical finding(s) need mitigation."
            )

    return snap


# -----------------------------------------------------------------------------
# Markdown rendering
# -----------------------------------------------------------------------------


def _preserve_notes(existing_md: str | None) -> str:
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


def render_progress_md(target: Path | None, existing_md: str | None = None) -> str:
    snap = collect_snapshot(target)
    log = _load_log(target)
    notes_block = _preserve_notes(existing_md)
    now = _now()

    lines: list[str] = []
    lines.append("# Governance progress\n")
    lines.append(
        f"> Auto-generated by `sdd progress` at {now}. Do not hand-edit outside the Notes section."
    )
    lines.append("")

    # --- Snapshot ---
    lines.append("## Snapshot\n")
    lines.append(f"- Capabilities: **{snap.capability_count}**")
    if snap.capability_names:
        for name in snap.capability_names:
            lines.append(f"  - {name}")
    lines.append(f"- Plans by status:")
    if snap.plan_count_by_status:
        for status, count in sorted(snap.plan_count_by_status.items()):
            lines.append(f"  - {status}: {count}")
    else:
        lines.append("  - _(no plans drafted yet)_")
    lines.append(f"- Open findings (suspected or confirmed): **{len(snap.open_findings)}**")
    if snap.open_findings:
        for f in snap.open_findings:
            lines.append(
                f"  - {f['id']} [{f['status']}/{f['severity']}] — {f['title']}"
            )
    lines.append("")

    # --- In-flight plans ---
    if snap.in_flight_plans:
        lines.append("## Plans in flight\n")
        for p in snap.in_flight_plans:
            lines.append(
                f"- **{p['id']}** ({p['status']}) — task {p['task_id']}, capability {p['capability']}"
            )
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


def update_progress_file(target: Path | None) -> Path | None:
    gov = governance_dir(target)
    if not gov.exists():
        return None
    out_path = progress_md_path(target)
    existing = out_path.read_text(encoding="utf-8") if out_path.exists() else None
    content = render_progress_md(target, existing_md=existing)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(content, encoding="utf-8")
    return out_path


def record(
    target: Path | None,
    kind: str,
    message: str,
    actor: str | None = None,
) -> Path | None:
    """High-level convenience: append event + refresh progress.md."""
    append_event(target, kind, message, actor)
    return update_progress_file(target)
