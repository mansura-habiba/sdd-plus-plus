"""Tests for `sdd serve` v0.3 — exercises the _impl_* logic functions directly."""
from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
from click.testing import CliRunner

from sdd.cli import main
from sdd.commands.serve import (
    _impl_get_arch_spec,
    _impl_get_capability,
    _impl_get_finding,
    _impl_get_plan,
    _impl_get_registry,
    _impl_list_capabilities,
    _impl_list_findings,
    _impl_list_plans,
    _impl_search_findings,
    _impl_validate,
)


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def init_repo(runner: CliRunner, tmp_path: Path) -> Path:
    runner.invoke(main, ["init", "--target", str(tmp_path)])
    return tmp_path


def _add_finding(
    runner: CliRunner, repo: Path, tmp_dir: Path, *, fid: str, cap: str, tags: list[str]
) -> None:
    tags_yaml = ("tags:\n" + "".join(f"  - {t}\n" for t in tags)) if tags else "tags: []\n"
    body = (
        textwrap.dedent(
            f"""\
            id: {fid}
            title: "Title for {fid}"
            status: confirmed
            severity: medium
            discovered_by: "@me"
            discovered_at: "2026-05-19"
            related_capabilities:
              - {cap}
            finding: "Body content for {fid} that is comfortably longer than fifty characters."
            """
        )
        + tags_yaml
    )
    src = tmp_dir / f"{fid}.src.yaml"
    src.write_text(body, encoding="utf-8")
    result = runner.invoke(
        main, ["findings", "add", "--target", str(repo), "--file", str(src)]
    )
    assert result.exit_code == 0, result.output


# -----------------------------------------------------------------------------
# Capability impl
# -----------------------------------------------------------------------------


def test_list_capabilities_after_init(init_repo: Path) -> None:
    caps = _impl_list_capabilities(init_repo)
    # The bundled example-feature ships with init.
    assert any(c["id"] == "example-feature" for c in caps)


def test_get_capability_returns_full_doc(init_repo: Path) -> None:
    doc = _impl_get_capability("example-feature", init_repo)
    assert doc is not None
    assert doc.get("id") == "example-feature"
    assert "contract" in doc
    assert "cases" in doc


def test_get_capability_unknown_returns_none(init_repo: Path) -> None:
    assert _impl_get_capability("does-not-exist", init_repo) is None


def test_get_registry(init_repo: Path) -> None:
    reg = _impl_get_registry(init_repo)
    assert reg is not None
    assert "capabilities" in reg
    assert isinstance(reg["capabilities"], list)


def test_get_arch_spec_returns_content(init_repo: Path) -> None:
    content = _impl_get_arch_spec(init_repo)
    assert "Architecture spec" in content


# -----------------------------------------------------------------------------
# Plan impl
# -----------------------------------------------------------------------------


def test_list_plans_after_init_has_example(init_repo: Path) -> None:
    """init ships an example.plan.md."""
    plans = _impl_list_plans(target=init_repo)
    assert any(p["plan_id"] == "plan-example-001" for p in plans)


def test_get_plan_by_id(init_repo: Path) -> None:
    doc = _impl_get_plan("plan-example-001", init_repo)
    assert doc is not None
    assert doc.get("status") == "draft"
    assert doc.get("accepted_by") == ""


# -----------------------------------------------------------------------------
# Findings impl
# -----------------------------------------------------------------------------


def test_list_findings_empty_after_init(init_repo: Path) -> None:
    assert _impl_list_findings(target=init_repo) == []


def test_list_findings_after_add(runner: CliRunner, init_repo: Path, tmp_path: Path) -> None:
    _add_finding(runner, init_repo, tmp_path, fid="finding-one", cap="cap-1", tags=["x", "y"])
    _add_finding(runner, init_repo, tmp_path, fid="finding-two", cap="cap-2", tags=["y", "z"])

    all_findings = _impl_list_findings(target=init_repo)
    assert {f["id"] for f in all_findings} == {"finding-one", "finding-two"}

    cap1 = _impl_list_findings(capability="cap-1", target=init_repo)
    assert {f["id"] for f in cap1} == {"finding-one"}

    tag_y = _impl_list_findings(tag="y", target=init_repo)
    assert {f["id"] for f in tag_y} == {"finding-one", "finding-two"}


def test_get_finding_round_trip(
    runner: CliRunner, init_repo: Path, tmp_path: Path
) -> None:
    _add_finding(runner, init_repo, tmp_path, fid="round-trip", cap="cap-x", tags=[])
    doc = _impl_get_finding("round-trip", init_repo)
    assert doc is not None
    assert doc.get("id") == "round-trip"
    assert doc.get("status") == "confirmed"


def test_search_findings_substring_match(
    runner: CliRunner, init_repo: Path, tmp_path: Path
) -> None:
    _add_finding(runner, init_repo, tmp_path, fid="searchable", cap="cap-x", tags=[])
    hits = _impl_search_findings("Title for searchable", init_repo)
    assert any(h["id"] == "searchable" for h in hits)

    hits = _impl_search_findings("totally-not-present", init_repo)
    assert hits == []


# -----------------------------------------------------------------------------
# Validate impl
# -----------------------------------------------------------------------------


def test_validate_impl_returns_ok_after_init(init_repo: Path) -> None:
    result = _impl_validate(init_repo)
    assert result["ok"] is True, result
    assert result["summary"]["failed"] == 0


# -----------------------------------------------------------------------------
# CLI smoke tests
# -----------------------------------------------------------------------------


def test_serve_command_help_works(runner: CliRunner) -> None:
    result = runner.invoke(main, ["serve", "--help"])
    assert result.exit_code == 0
    assert "MCP" in result.output or "Model Context Protocol" in result.output
