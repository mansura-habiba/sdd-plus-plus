"""Tests for the progress mechanism (sdd._progress + `sdd progress` + auto-update hooks)."""
from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
from click.testing import CliRunner

from sdd._paths import progress_log_path, progress_md_path
from sdd._progress import (
    MAX_LOG,
    NOTES_END,
    NOTES_START,
    append_event,
    collect_snapshot,
    record,
    render_progress_md,
    update_progress_file,
)
from sdd.cli import main


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def init_repo(runner: CliRunner, tmp_path: Path) -> Path:
    runner.invoke(main, ["init", "--target", str(tmp_path)])
    return tmp_path


def test_init_writes_progress_md(init_repo: Path) -> None:
    p = progress_md_path(init_repo)
    assert p.exists()
    content = p.read_text(encoding="utf-8")
    assert "Governance progress" in content
    assert NOTES_START in content
    assert NOTES_END in content


def test_append_event_persists_to_log(init_repo: Path) -> None:
    append_event(init_repo, "test-event", "first event", actor="@tester")
    log = progress_log_path(init_repo)
    assert log.exists()
    text = log.read_text(encoding="utf-8")
    assert "test-event" in text
    assert "first event" in text


def test_log_rotates_at_max(init_repo: Path) -> None:
    for i in range(MAX_LOG + 10):
        append_event(init_repo, "noise", f"event {i}", actor="@tester")
    log = progress_log_path(init_repo)
    text = log.read_text(encoding="utf-8")
    # Each entry is preceded by "- ts:" (block-style list)
    count = text.count("- ts:")
    assert count <= MAX_LOG


def test_snapshot_after_init_counts_bundled_capability(init_repo: Path) -> None:
    snap = collect_snapshot(init_repo)
    assert snap.capability_count >= 1


def test_render_has_required_sections(init_repo: Path) -> None:
    md = render_progress_md(init_repo)
    for section in ("## Snapshot", "## Pending actions", "## Recent activity", "## Notes"):
        assert section in md


def test_notes_block_preserved_on_regeneration(init_repo: Path) -> None:
    p = progress_md_path(init_repo)
    original = p.read_text(encoding="utf-8")
    custom = "MY CUSTOM NOTES — should survive."
    new_content = original.replace(
        original[original.index(NOTES_START) : original.index(NOTES_END)],
        f"{NOTES_START}\n{custom}\n",
    )
    p.write_text(new_content, encoding="utf-8")
    record(init_repo, "test", "trigger refresh")
    final = p.read_text(encoding="utf-8")
    assert custom in final


def test_validate_appends_to_log(runner: CliRunner, init_repo: Path) -> None:
    runner.invoke(main, ["validate", "--target", str(init_repo)])
    text = progress_log_path(init_repo).read_text(encoding="utf-8")
    assert "validate" in text


def test_doctor_appends_to_log(runner: CliRunner, init_repo: Path) -> None:
    runner.invoke(main, ["doctor", "--target", str(init_repo)])
    text = progress_log_path(init_repo).read_text(encoding="utf-8")
    assert "doctor" in text


def test_progress_command_prints_md(runner: CliRunner, init_repo: Path) -> None:
    result = runner.invoke(main, ["progress", "--target", str(init_repo)])
    assert result.exit_code == 0
    assert "Governance progress" in result.output


def test_progress_update_appends_and_refreshes(
    runner: CliRunner, init_repo: Path
) -> None:
    result = runner.invoke(
        main,
        [
            "progress", "update",
            "--target", str(init_repo),
            "--kind", "session-end",
            "--message", "Wrapped up the spec review.",
        ],
    )
    assert result.exit_code == 0
    md = progress_md_path(init_repo).read_text(encoding="utf-8")
    assert "session-end" in md
    assert "spec review" in md


def test_update_status_alias_works(runner: CliRunner, init_repo: Path) -> None:
    """The top-level `sdd update-status` is an alias for `sdd progress update`."""
    result = runner.invoke(
        main,
        [
            "update-status",
            "--target", str(init_repo),
            "--kind", "milestone",
            "--message", "Hit a milestone via the alias.",
        ],
    )
    assert result.exit_code == 0
    md = progress_md_path(init_repo).read_text(encoding="utf-8")
    assert "milestone" in md
    assert "alias" in md


def test_progress_refresh_does_not_append(runner: CliRunner, init_repo: Path) -> None:
    before = progress_log_path(init_repo).read_text(encoding="utf-8")
    runner.invoke(main, ["progress", "refresh", "--target", str(init_repo)])
    after = progress_log_path(init_repo).read_text(encoding="utf-8")
    assert before == after


def test_progress_outside_init_returns_2(runner: CliRunner, tmp_path: Path) -> None:
    result = runner.invoke(main, ["progress", "--target", str(tmp_path)])
    assert result.exit_code == 2
    assert "no .governance/" in result.output


def test_update_progress_file_silent_no_governance(tmp_path: Path) -> None:
    """Best-effort: if .governance/ doesn't exist, update is a no-op."""
    out = update_progress_file(tmp_path)
    assert out is None
