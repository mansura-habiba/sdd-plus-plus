"""Tests for `sdd findings` (v0.4 — canonical YAML, no frontmatter)."""
from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
from click.testing import CliRunner

from sdd.cli import main


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def init_repo(runner: CliRunner, tmp_path: Path) -> Path:
    result = runner.invoke(main, ["init", "--target", str(tmp_path)])
    assert result.exit_code == 0, result.output
    return tmp_path


def _write_finding(parent: Path, body: str, name: str = "draft.yaml") -> Path:
    parent.mkdir(parents=True, exist_ok=True)
    p = parent / name
    p.write_text(body, encoding="utf-8")
    return p


def test_findings_add_via_file_succeeds(
    runner: CliRunner, init_repo: Path, tmp_path: Path
) -> None:
    body = textwrap.dedent(
        """\
        id: cache-key-collision
        title: "Cache keys collide between user_id and tenant_id under prefix scheme"
        status: confirmed
        severity: high
        discovered_by: "@mansura"
        discovered_at: "2026-05-19"
        related_capabilities:
          - example-feature
        tags:
          - caching
          - data-integrity
        finding: |
          When tenant_id and user_id share a prefix, the cache layer aliases their entries
          because the key derivation truncates at the prefix boundary.
        """
    )
    src = _write_finding(tmp_path / "drafts", body)
    result = runner.invoke(
        main, ["findings", "add", "--target", str(init_repo), "--file", str(src)]
    )
    assert result.exit_code == 0, result.output
    out_path = init_repo / ".governance" / "wiki" / "findings" / "cache-key-collision.yaml"
    assert out_path.exists()
    assert "cache-key-collision" in out_path.read_text(encoding="utf-8")


def test_findings_add_validation_rejects_bad_handle(
    runner: CliRunner, init_repo: Path, tmp_path: Path
) -> None:
    body = textwrap.dedent(
        """\
        id: bad-handle
        title: "Bad handle test"
        status: suspected
        discovered_by: "not-a-handle"
        discovered_at: "2026-05-19"
        finding: "Body that is comfortably longer than fifty characters total length here."
        """
    )
    src = _write_finding(tmp_path / "drafts", body)
    result = runner.invoke(
        main, ["findings", "add", "--target", str(init_repo), "--file", str(src)]
    )
    assert result.exit_code == 1
    assert "Validation failed" in result.output


def test_findings_list_empty(runner: CliRunner, init_repo: Path) -> None:
    result = runner.invoke(main, ["findings", "list", "--target", str(init_repo)])
    assert result.exit_code == 0
    assert "No findings" in result.output or "0 finding" in result.output


def test_findings_list_filters_by_capability(
    runner: CliRunner, init_repo: Path, tmp_path: Path
) -> None:
    for fid, cap in [("first-finding", "example-feature"), ("second-finding", "other-cap")]:
        body = textwrap.dedent(
            f"""\
            id: {fid}
            title: "Finding about {cap}"
            status: suspected
            discovered_by: "@me"
            discovered_at: "2026-05-19"
            related_capabilities:
              - {cap}
            finding: "A body for {fid} that is comfortably longer than fifty characters total."
            """
        )
        src = _write_finding(tmp_path / "drafts", body, name=f"{fid}.yaml")
        result = runner.invoke(
            main, ["findings", "add", "--target", str(init_repo), "--file", str(src)]
        )
        assert result.exit_code == 0, result.output

    result = runner.invoke(main, ["findings", "list", "--target", str(init_repo)])
    assert "first-finding" in result.output
    assert "second-finding" in result.output

    result = runner.invoke(
        main, ["findings", "list", "--target", str(init_repo), "--capability", "example-feature"]
    )
    assert "first-finding" in result.output
    assert "second-finding" not in result.output


def test_findings_show(runner: CliRunner, init_repo: Path, tmp_path: Path) -> None:
    body = textwrap.dedent(
        """\
        id: showable-finding
        title: "A finding to show"
        status: confirmed
        severity: low
        discovered_by: "@me"
        discovered_at: "2026-05-19"
        finding: "A body for showable-finding that is comfortably longer than fifty characters."
        """
    )
    src = _write_finding(tmp_path / "drafts", body)
    runner.invoke(main, ["findings", "add", "--target", str(init_repo), "--file", str(src)])

    result = runner.invoke(
        main, ["findings", "show", "showable-finding", "--target", str(init_repo)]
    )
    assert result.exit_code == 0
    assert "A finding to show" in result.output


def test_findings_show_not_found(runner: CliRunner, init_repo: Path) -> None:
    result = runner.invoke(
        main, ["findings", "show", "nonexistent", "--target", str(init_repo)]
    )
    assert result.exit_code == 1
    assert "No finding" in result.output


def test_validate_includes_findings(
    runner: CliRunner, init_repo: Path, tmp_path: Path
) -> None:
    body = textwrap.dedent(
        """\
        id: validation-coverage-finding
        title: "Validation now covers findings too"
        status: confirmed
        severity: low
        discovered_by: "@me"
        discovered_at: "2026-05-19"
        finding: "After v0.4, sdd validate walks wiki/findings/ for pure YAML files and validates each."
        """
    )
    src = _write_finding(tmp_path / "drafts", body)
    runner.invoke(main, ["findings", "add", "--target", str(init_repo), "--file", str(src)])

    result = runner.invoke(main, ["validate", "--target", str(init_repo)])
    assert result.exit_code == 0, result.output
    assert "finding.schema.yaml" in result.output
    assert "0 failed" in result.output
