"""`sdd serve` — expose the v0.3 governance framework as MCP tools.

Tool list (v0.3):
  - list_capabilities()
  - get_capability(capability_id)
  - get_registry()
  - get_arch_spec()
  - list_plans(status?)
  - get_plan(plan_id)
  - propose_plan(task_id, capability, draft_body) — saves a draft plan; cannot self-accept
  - list_findings(capability?, tag?, status?)
  - get_finding(finding_id)
  - search_findings(query)
  - validate()
  - get_progress()
  - record_progress(message, kind?)
  - record_session_end(summary)

Critical AI guardrails:
  - propose_plan saves status: draft only. accepted_by is empty.
  - There is no MCP tool to accept a plan. Acceptance requires a human running
    `sdd plan accept --by @<handle>` from a terminal.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from sdd._paths import (
    arch_spec_path,
    capabilities_dir,
    findings_dir,
    governance_dir,
    instructions_md_path,
    plan_dir,
    principles_md_path,
    progress_md_path,
    registry_path,
    target_root,
    wiki_dir,
)
from sdd._yaml import load_yaml


_TARGET: Path | None = None


def _get_target() -> Path:
    return _TARGET if _TARGET is not None else target_root()


def _set_target(path: Path) -> None:
    global _TARGET
    _TARGET = path.resolve()


def _safe_yaml(path: Path) -> dict | None:
    """v0.4 — pure YAML, no frontmatter."""
    try:
        doc = load_yaml(path)
        return doc if isinstance(doc, dict) else None
    except Exception:
        return None


# Backwards-compat alias for any code still referring to the v0.3 frontmatter loader
_safe_fm = _safe_yaml


# -----------------------------------------------------------------------------
# Pure-logic impls (testable without MCP)
# -----------------------------------------------------------------------------


def _impl_list_capabilities(target: Path | None = None) -> list[dict]:
    out: list[dict] = []
    if not capabilities_dir(target).exists():
        return out
    for path in sorted(capabilities_dir(target).glob("*/spec.yaml")):
        fm = _safe_fm(path)
        if not fm:
            continue
        out.append({
            "id": fm.get("id"),
            "name": fm.get("name"),
            "purpose": (fm.get("purpose") or "")[:200],
            "tier": fm.get("tier"),
            "status": fm.get("status"),
            "owner": (fm.get("owner") or {}).get("human"),
            "file": str(path.relative_to(target_root(target))),
        })
    return out


def _impl_get_capability(capability_id: str, target: Path | None = None) -> dict | None:
    path = capabilities_dir(target) / capability_id / "spec.yaml"
    if path.exists():
        return _safe_fm(path)
    # Fallback: scan
    if capabilities_dir(target).exists():
        for p in capabilities_dir(target).glob("*/spec.yaml"):
            fm = _safe_fm(p)
            if fm and fm.get("id") == capability_id:
                return fm
    return None


def _impl_get_registry(target: Path | None = None) -> dict | None:
    p = registry_path(target)
    if not p.exists():
        return None
    try:
        return load_yaml(p)
    except Exception:
        return None


def _impl_get_arch_spec(target: Path | None = None) -> str:
    p = arch_spec_path(target)
    if not p.exists():
        return ""
    return p.read_text(encoding="utf-8")


def _impl_list_plans(
    status: str | None = None, target: Path | None = None
) -> list[dict]:
    out: list[dict] = []
    if not plan_dir(target).exists():
        return out
    for path in sorted(plan_dir(target).glob("*.plan.yaml")):
        fm = _safe_fm(path)
        if not fm:
            continue
        if status and fm.get("status") != status:
            continue
        out.append({
            "plan_id": fm.get("plan_id"),
            "task_id": fm.get("task_id"),
            "capability": fm.get("capability"),
            "status": fm.get("status"),
            "accepted_by": fm.get("accepted_by") or "",
            "file": str(path.relative_to(target_root(target))),
        })
    return out


def _impl_get_plan(plan_id: str, target: Path | None = None) -> dict | None:
    direct = plan_dir(target) / f"{plan_id}.plan.yaml"
    if direct.exists():
        return _safe_fm(direct)
    if plan_dir(target).exists():
        for p in plan_dir(target).glob("*.plan.yaml"):
            fm = _safe_fm(p)
            if fm and fm.get("plan_id") == plan_id:
                return fm
    return None


def _impl_list_findings(
    capability: str | None = None,
    tag: str | None = None,
    status: str | None = None,
    target: Path | None = None,
) -> list[dict]:
    out: list[dict] = []
    if not findings_dir(target).exists():
        return out
    for path in sorted(findings_dir(target).glob("*.yaml")):
        if path.name == ".gitkeep":
            continue
        fm = _safe_yaml(path)
        if not fm:
            continue
        if capability and capability not in (fm.get("related_capabilities") or []):
            continue
        if tag and tag not in (fm.get("tags") or []):
            continue
        if status and fm.get("status") != status:
            continue
        out.append({
            "id": fm.get("id"),
            "title": fm.get("title"),
            "status": fm.get("status"),
            "severity": fm.get("severity"),
            "discovered_at": fm.get("discovered_at"),
            "related_capabilities": fm.get("related_capabilities") or [],
            "tags": fm.get("tags") or [],
            "file": str(path.relative_to(target_root(target))),
        })
    return out


def _impl_get_finding(finding_id: str, target: Path | None = None) -> dict | None:
    direct = findings_dir(target) / f"{finding_id}.yaml"
    if direct.exists():
        return _safe_yaml(direct)
    if findings_dir(target).exists():
        for p in findings_dir(target).glob("*.yaml"):
            fm = _safe_yaml(p)
            if fm and fm.get("id") == finding_id:
                return fm
    return None


def _impl_search_findings(query: str, target: Path | None = None) -> list[dict]:
    """Substring search across finding metadata + body fields. v0.4 — pure YAML."""
    q = query.lower()
    out: list[dict] = []
    if not findings_dir(target).exists():
        return out
    for path in sorted(findings_dir(target).glob("*.yaml")):
        if path.name == ".gitkeep":
            continue
        fm = _safe_yaml(path)
        if not fm:
            continue
        # Build a haystack from all text-ish fields the schema knows about.
        body_text = " ".join(
            str(fm.get(k) or "")
            for k in ("title", "finding", "implications", "notes")
        )
        haystacks = [
            (fm.get("title") or "").lower(),
            body_text.lower(),
            " ".join(fm.get("tags") or []).lower(),
        ]
        if any(q in h for h in haystacks):
            out.append({
                "id": fm.get("id"),
                "title": fm.get("title"),
                "status": fm.get("status"),
                "severity": fm.get("severity"),
                "snippet": (fm.get("finding") or "")[:240],
            })
    return out


def _impl_validate(target: Path | None = None) -> dict:
    """Run validate and return structured summary."""
    from sdd.commands.validate import _cross_ref_checks, _load_validator, _validate_yaml_file

    tgt = target_root(target)
    gov = governance_dir(target)
    if not gov.exists():
        return {"ok": False, "reason": ".governance/ does not exist", "results": []}

    results: list[dict] = []

    if registry_path(target).exists():
        r = _validate_yaml_file(registry_path(target), _load_validator("registry"), "registry.schema.yaml")
        results.append({"file": str(r.file.relative_to(tgt)), "schema": r.schema, "passed": r.passed, "errors": r.errors})

    spec_v = _load_validator("capability_spec")
    if capabilities_dir(target).exists():
        for path in sorted(capabilities_dir(target).glob("*/spec.yaml")):
            r = _validate_yaml_file(path, spec_v, "capability_spec.schema.yaml")
            results.append({"file": str(r.file.relative_to(tgt)), "schema": r.schema, "passed": r.passed, "errors": r.errors})

    plan_v = _load_validator("plan")
    if plan_dir(target).exists():
        for path in sorted(plan_dir(target).glob("*.plan.yaml")):
            r = _validate_yaml_file(path, plan_v, "plan.schema.yaml")
            results.append({"file": str(r.file.relative_to(tgt)), "schema": r.schema, "passed": r.passed, "errors": r.errors})

    finding_v = _load_validator("finding")
    if findings_dir(target).exists():
        for path in sorted(findings_dir(target).glob("*.yaml")):
            if path.name == ".gitkeep":
                continue
            r = _validate_yaml_file(path, finding_v, "finding.schema.yaml")
            results.append({"file": str(r.file.relative_to(tgt)), "schema": r.schema, "passed": r.passed, "errors": r.errors})

    cross = _cross_ref_checks(target)
    failed = sum(1 for r in results if not r["passed"])
    return {
        "ok": failed == 0 and len(cross) == 0,
        "summary": {
            "files_validated": len(results),
            "passed": sum(1 for r in results if r["passed"]),
            "failed": failed,
            "cross_ref_issues": len(cross),
        },
        "results": results,
        "cross_ref_issues": cross,
    }


# -----------------------------------------------------------------------------
# MCP entrypoint
# -----------------------------------------------------------------------------


def _build_mcp() -> Any:
    try:
        from fastmcp import FastMCP
    except ImportError as e:
        raise SystemExit(
            "FATAL: fastmcp is not installed. Run `pip install 'sdd-plus-plus[serve]'`."
        ) from e

    mcp = FastMCP("sdd-governance")

    @mcp.tool()
    def list_capabilities() -> list[dict]:
        """List every capability defined in this repo's .governance/capabilities/."""
        return _impl_list_capabilities(_get_target())

    @mcp.tool()
    def get_capability(capability_id: str) -> dict | None:
        """Get the full capability spec frontmatter by id."""
        return _impl_get_capability(capability_id, _get_target())

    @mcp.tool()
    def get_registry() -> dict | None:
        """Return the continuous capability registry (active + roadmap + deprecated)."""
        return _impl_get_registry(_get_target())

    @mcp.tool()
    def get_arch_spec() -> str:
        """Return the whole-system architecture spec content (.governance/arch_spec.md)."""
        return _impl_get_arch_spec(_get_target())

    @mcp.tool()
    def get_principles() -> str:
        """Return .governance/wiki/principles.md — the five governing principles.

        Load this once per session. The principles bind humans, agents, and tools equally.
        """
        path = principles_md_path(_get_target())
        return path.read_text(encoding="utf-8") if path.exists() else ""

    @mcp.tool()
    def get_instructions() -> str:
        """Return .governance/instructions.md — the AI's standing orders for this repo.

        Load this at session start. It tells you how to operate: when to challenge,
        what you may and may not author, how to use the other MCP tools.
        """
        path = instructions_md_path(_get_target())
        return path.read_text(encoding="utf-8") if path.exists() else ""

    @mcp.tool()
    def get_coding_standards() -> str:
        """Return .governance/wiki/coding-standards.md — the team's tribal knowledge.

        Loads conventions that lint and type-check cannot enforce: error handling philosophy,
        logging patterns, library preferences, anti-patterns the team has hit before.
        Read before generating code; check whenever you're about to default to a "popular"
        pattern from training data instead of what this codebase actually uses.
        """
        path = wiki_dir(_get_target()) / "coding-standards.md"
        return path.read_text(encoding="utf-8") if path.exists() else ""

    @mcp.tool()
    def propose_finding(
        title: str,
        finding: str,
        related_capability: str,
        severity: str = "medium",
        evidence: list[str] | None = None,
        tags: list[str] | None = None,
    ) -> dict:
        """Propose a candidate finding (status: suspected, ai_assistance: suggested).

        Use this when you discover something non-obvious during a session: a gotcha,
        a behavioral quirk, a non-obvious constraint. The finding is saved as `suspected`
        — a human must verify it via `sdd findings list --status suspected` and edit the
        file to advance status to `confirmed`. You cannot confirm findings yourself.

        Args:
            title: One-line title (max 120 chars).
            finding: The body — what was observed, what makes it noteworthy (≥ 50 chars).
            related_capability: Capability id this affects.
            severity: low / medium / high / critical. Default medium.
            evidence: References to logs, tests, commits.
            tags: Free-form tags for cross-cutting categorization.

        Returns: {finding_id, file, status: 'suspected'}.
        """
        import datetime as _dt
        import re as _re
        from sdd._paths import findings_dir as _fd

        target = _get_target()
        out_root = _fd(target)
        out_root.mkdir(parents=True, exist_ok=True)
        # Slugify title
        slug = _re.sub(r"[^a-zA-Z0-9\s-]", "", title).strip().lower()
        slug = _re.sub(r"[-\s]+", "-", slug) or "untitled-finding"
        out_path = out_root / f"{slug}.yaml"
        n = 2
        while out_path.exists():
            out_path = out_root / f"{slug}-{n}.yaml"
            slug = f"{slug.rsplit('-', 1)[0] if '-' in slug else slug}-{n}"
            n += 1

        today = _dt.date.today().isoformat()
        doc = {
            "id": slug,
            "title": title,
            "status": "suspected",
            "severity": severity,
            "discovered_by": "@mcp-client",  # Will be re-attributed when human confirms
            "discovered_at": today,
            "ai_assistance": "suggested",
            "related_capabilities": [related_capability] if related_capability else [],
            "tags": tags or [],
            "finding": finding,
            "evidence": evidence or [],
            "status_history": [
                {"date": today, "status": "suspected", "by": "@mcp-client",
                 "note": "Surfaced by AI via propose_finding. Awaiting human verification."},
            ],
        }
        from sdd._yaml import dump_yaml as _dy
        _dy(doc, out_path)
        from sdd._progress import record as _rec
        _rec(target=target, kind="finding-proposed",
             message=f"{slug} proposed (suspected) — {title[:80]}")
        return {
            "finding_id": slug,
            "file": str(out_path.relative_to(target)),
            "status": "suspected",
            "note": "Status: suspected. A human must verify and advance to `confirmed`.",
        }

    @mcp.tool()
    def list_plans(status: str | None = None) -> list[dict]:
        """List plans, optionally filtered by status (draft/accepted/executed/rejected/archived)."""
        return _impl_list_plans(status, _get_target())

    @mcp.tool()
    def get_plan(plan_id: str) -> dict | None:
        """Get a plan's frontmatter by id."""
        return _impl_get_plan(plan_id, _get_target())

    @mcp.tool()
    def propose_plan(
        task_id: str,
        capability: str,
        understood_request: str,
        concerns: list[str],
        alternatives_considered: list[str],
        in_scope: list[str],
        non_goals: list[str],
        body: str = "",
    ) -> dict:
        """Propose (save as DRAFT) a plan. Cannot mark it accepted — humans only.

        Args:
            task_id: the task this plan addresses.
            capability: capability id.
            understood_request: the AI's restatement of the user's ask.
            concerns: AI's concerns. At least one entry. Use "no concern surfaced — checked X" if you really have none.
            alternatives_considered: alternative approaches. At least one.
            in_scope: list of in-scope deliverables.
            non_goals: list of bounding non-goals.
            body: optional markdown plan body.

        Returns: {plan_id, file, status: 'draft', accept_command}.
        """
        import datetime as _dt
        from sdd._yaml import render_frontmatter_file
        from sdd._paths import plan_dir as _pd

        target = _get_target()
        out_root = _pd(target)
        out_root.mkdir(parents=True, exist_ok=True)
        plan_id = f"{task_id}-plan-001"
        out_path = out_root / f"{plan_id}.plan.md"
        n = 2
        while out_path.exists():
            plan_id = f"{task_id}-plan-{n:03d}"
            out_path = out_root / f"{plan_id}.plan.md"
            n += 1

        fm = {
            "plan_id": plan_id,
            "task_id": task_id,
            "capability": capability,
            "generated_by": {
                "tool": "mcp-client",
                "generated_at": _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            },
            "status": "draft",
            "accepted_by": "",
            "accepted_at": "",
            "challenge": {
                "understood_request": understood_request,
                "concerns": concerns,
                "alternatives_considered": alternatives_considered,
            },
            "scope": {"in_scope": in_scope, "non_goals": non_goals},
            "ai_context": {
                "required_reading": [
                    ".governance/wiki/principles.md",
                    ".governance/instructions.md",
                    f".governance/capabilities/{capability}/spec.md",
                ],
                "do_not_modify": [".governance/_schemas/", ".governance/wiki/principles.md"],
                "preferred_patterns": [],
            },
        }
        out_path.write_text(
            render_frontmatter_file(fm, "\n# Plan: " + task_id + "\n\n" + body + "\n"),
            encoding="utf-8",
        )
        from sdd._progress import record as _rec
        _rec(target=target, kind="plan-drafted",
             message=f"{plan_id} (task {task_id}) — proposed via MCP, awaiting human acceptance")
        return {
            "plan_id": plan_id,
            "file": str(out_path.relative_to(target)),
            "status": "draft",
            "accept_command": f"sdd plan accept --id {plan_id} --by @<human-handle>",
            "note": "Plan is DRAFT. A human must run the accept_command before code may be written.",
        }

    @mcp.tool()
    def list_findings(
        capability: str | None = None,
        tag: str | None = None,
        status: str | None = None,
    ) -> list[dict]:
        """List findings, optionally filtered."""
        return _impl_list_findings(capability, tag, status, _get_target())

    @mcp.tool()
    def get_finding(finding_id: str) -> dict | None:
        """Get a finding's full frontmatter + body by id."""
        return _impl_get_finding(finding_id, _get_target())

    @mcp.tool()
    def search_findings(query: str) -> list[dict]:
        """Substring search over finding titles, body, and tags."""
        return _impl_search_findings(query, _get_target())

    @mcp.tool()
    def validate() -> dict:
        """Run schema validation across the .governance/ tree."""
        return _impl_validate(_get_target())

    @mcp.tool()
    def get_progress() -> str:
        """Return current .governance/progress.md content."""
        from sdd._progress import update_progress_file
        target = _get_target()
        path = progress_md_path(target)
        if not path.exists():
            update_progress_file(target)
        if path.exists():
            return path.read_text(encoding="utf-8")
        return "No progress.md available — .governance/ may not be initialized."

    @mcp.tool()
    def record_progress(message: str, kind: str = "progress") -> dict:
        """Record a progress checkpoint. Refreshes progress.md."""
        from sdd._progress import record as _rec
        out = _rec(target=_get_target(), kind=kind, message=message)
        return {"recorded": out is not None, "progress_md_path": str(out) if out else ""}

    @mcp.tool()
    def record_session_end(summary: str) -> dict:
        """Record that the current AI session is ending."""
        from sdd._progress import record as _rec
        out = _rec(target=_get_target(), kind="session-end", message=summary)
        return {"recorded": out is not None, "progress_md_path": str(out) if out else ""}

    return mcp


def run_serve(target: Path | None, transport: str) -> int:
    if target is not None:
        _set_target(target)
    mcp = _build_mcp()
    if transport == "http":
        mcp.run(transport="http")
    else:
        mcp.run()
    return 0
