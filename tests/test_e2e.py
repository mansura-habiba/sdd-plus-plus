"""End-to-end tests for the sdd CLI (v0.4 — canonical YAML)."""
from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from sdd.cli import main


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.mark.e2e
def test_init_creates_v04_layout(runner: CliRunner, tmp_path: Path) -> None:
    result = runner.invoke(main, ["init", "--target", str(tmp_path)])
    assert result.exit_code == 0, f"init failed:\n{result.output}"

    # Wiki
    assert (tmp_path / ".governance" / "wiki" / "principles.md").exists()
    assert (tmp_path / ".governance" / "wiki" / "coding-standards.md").exists()

    # Capabilities (now YAML)
    assert (tmp_path / ".governance" / "capabilities" / "REGISTRY.yaml").exists()
    assert (tmp_path / ".governance" / "capabilities" / "example-feature" / "spec.yaml").exists()

    # Top-level governance docs
    assert (tmp_path / ".governance" / "arch_spec.md").exists()
    assert (tmp_path / ".governance" / "instructions.md").exists()
    assert (tmp_path / ".governance" / "USAGE.md").exists()

    # Plan example (now YAML)
    assert (tmp_path / ".governance" / "plan" / "example.plan.yaml").exists()

    # AGENTS.md at repo root
    assert (tmp_path / "AGENTS.md").exists()

    # GitHub
    assert (tmp_path / ".github" / "ISSUE_TEMPLATE" / "task-card.yml").exists()
    assert (tmp_path / ".github" / "pull_request_template.md").exists()
    assert (tmp_path / ".github" / "workflows" / "governance.yml").exists()


@pytest.mark.e2e
def test_init_idempotent_without_force(runner: CliRunner, tmp_path: Path) -> None:
    runner.invoke(main, ["init", "--target", str(tmp_path)])
    marker = tmp_path / "AGENTS.md"
    marker.write_text("CUSTOM CONTENT — should survive a second init.")
    result = runner.invoke(main, ["init", "--target", str(tmp_path)])
    assert result.exit_code == 0
    assert marker.read_text() == "CUSTOM CONTENT — should survive a second init."


@pytest.mark.e2e
def test_init_force_overwrites(runner: CliRunner, tmp_path: Path) -> None:
    runner.invoke(main, ["init", "--target", str(tmp_path)])
    marker = tmp_path / "AGENTS.md"
    marker.write_text("WILL BE OVERWRITTEN")
    result = runner.invoke(main, ["init", "--target", str(tmp_path), "--force"])
    assert result.exit_code == 0
    assert marker.read_text() != "WILL BE OVERWRITTEN"


@pytest.mark.e2e
def test_init_dry_run_writes_nothing(runner: CliRunner, tmp_path: Path) -> None:
    result = runner.invoke(main, ["init", "--target", str(tmp_path), "--dry-run"])
    assert result.exit_code == 0
    assert "Dry run" in result.output
    assert not (tmp_path / ".governance").exists()
    assert not (tmp_path / "AGENTS.md").exists()


@pytest.mark.e2e
def test_validate_passes_on_fresh_init(runner: CliRunner, tmp_path: Path) -> None:
    runner.invoke(main, ["init", "--target", str(tmp_path)])
    result = runner.invoke(main, ["validate", "--target", str(tmp_path)])
    assert result.exit_code == 0, f"validate failed:\n{result.output}"
    assert "Summary:" in result.output
    assert "0 failed" in result.output


@pytest.mark.e2e
def test_validate_no_governance_dir_returns_2(runner: CliRunner, tmp_path: Path) -> None:
    result = runner.invoke(main, ["validate", "--target", str(tmp_path)])
    assert result.exit_code == 2
    assert "no .governance/" in result.output


@pytest.mark.e2e
def test_doctor_runs_on_empty_repo(runner: CliRunner, tmp_path: Path) -> None:
    result = runner.invoke(main, ["doctor", "--target", str(tmp_path)])
    assert result.exit_code == 0
    assert "score" in result.output.lower()


@pytest.mark.e2e
def test_doctor_after_init_shows_progress(runner: CliRunner, tmp_path: Path) -> None:
    runner.invoke(main, ["init", "--target", str(tmp_path)])
    result = runner.invoke(main, ["doctor", "--target", str(tmp_path)])
    assert result.exit_code == 0
    assert "/9 milestones" in result.output or "/9" in result.output


@pytest.mark.e2e
def test_progress_command_prints_md(runner: CliRunner, tmp_path: Path) -> None:
    runner.invoke(main, ["init", "--target", str(tmp_path)])
    result = runner.invoke(main, ["progress", "--target", str(tmp_path)])
    assert result.exit_code == 0
    assert "Governance progress" in result.output


@pytest.mark.e2e
def test_status_alias_deprecation_warning(runner: CliRunner, tmp_path: Path) -> None:
    runner.invoke(main, ["init", "--target", str(tmp_path)])
    result = runner.invoke(main, ["status", "--target", str(tmp_path)])
    assert result.exit_code == 0
    assert "DEPRECATED" in result.output
