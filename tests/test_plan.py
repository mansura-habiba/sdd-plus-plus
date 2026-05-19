"""Tests for `sdd plan` (v0.4 — canonical YAML)."""
from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
from click.testing import CliRunner

from sdd._yaml import load_yaml
from sdd.cli import main


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def init_repo(runner: CliRunner, tmp_path: Path) -> Path:
    runner.invoke(main, ["init", "--target", str(tmp_path)])
    return tmp_path


def _valid_plan_body(task_id: str, capability: str, status: str = "draft", accepted_by: str = "") -> str:
    return textwrap.dedent(
        f"""\
        plan_id: {task_id}-plan-001
        task_id: {task_id}
        capability: {capability}
        generated_by:
          tool: human
          generated_at: "2026-05-19T10:00:00Z"
        status: {status}
        accepted_by: "{accepted_by}"
        accepted_at: ""
        challenge:
          understood_request: "Test plan creation. This is a fixture, not a real ask."
          concerns:
            - "If this fixture leaks into real plans, it would pollute the registry."
          alternatives_considered:
            - "Could inline plan body via Python instead of YAML — rejected for readability."
        scope:
          in_scope:
            - "Demonstrate a valid plan structure"
          non_goals:
            - "Do not represent real work"
        ai_context:
          required_reading:
            - .governance/wiki/principles.md
          do_not_modify:
            - .governance/_schemas/
          preferred_patterns: []
        """
    )


def test_plan_new_via_file_succeeds(
    runner: CliRunner, init_repo: Path, tmp_path: Path
) -> None:
    src = tmp_path / "plan.yaml"
    src.write_text(_valid_plan_body("TEST-1", "example-feature"))
    result = runner.invoke(
        main,
        ["plan", "new", "--target", str(init_repo),
         "--task", "TEST-1", "--capability", "example-feature", "--file", str(src)],
    )
    assert result.exit_code == 0, result.output
    out_path = init_repo / ".governance" / "plan" / "TEST-1-plan-001.plan.yaml"
    assert out_path.exists()


def test_plan_new_rejects_pre_accepted(
    runner: CliRunner, init_repo: Path, tmp_path: Path
) -> None:
    src = tmp_path / "preaccepted.yaml"
    src.write_text(_valid_plan_body("TEST-2", "example-feature", status="accepted", accepted_by="@me"))
    result = runner.invoke(
        main,
        ["plan", "new", "--target", str(init_repo),
         "--task", "TEST-2", "--capability", "example-feature", "--file", str(src)],
    )
    assert result.exit_code == 1
    assert "cannot be created in `accepted` status" in result.output


def test_plan_new_rejects_accepted_by_without_accepted_status(
    runner: CliRunner, init_repo: Path, tmp_path: Path
) -> None:
    src = tmp_path / "with_handle.yaml"
    src.write_text(_valid_plan_body("TEST-3", "example-feature", status="draft", accepted_by="@me"))
    result = runner.invoke(
        main,
        ["plan", "new", "--target", str(init_repo),
         "--task", "TEST-3", "--capability", "example-feature", "--file", str(src)],
    )
    assert result.exit_code == 1
    assert "accepted_by must be empty" in result.output


def test_plan_accept_rejects_non_human_handle(
    runner: CliRunner, init_repo: Path, tmp_path: Path
) -> None:
    src = tmp_path / "p.yaml"
    src.write_text(_valid_plan_body("TEST-4", "example-feature"))
    runner.invoke(
        main,
        ["plan", "new", "--target", str(init_repo), "--task", "TEST-4",
         "--capability", "example-feature", "--file", str(src)],
    )
    result = runner.invoke(
        main,
        ["plan", "accept", "--target", str(init_repo),
         "--id", "TEST-4-plan-001", "--by", "no-at-symbol"],
    )
    assert result.exit_code == 2
    assert "must be a handle" in result.output


def test_plan_accept_sets_accepted_by_and_status(
    runner: CliRunner, init_repo: Path, tmp_path: Path
) -> None:
    src = tmp_path / "p.yaml"
    src.write_text(_valid_plan_body("TEST-5", "example-feature"))
    runner.invoke(
        main,
        ["plan", "new", "--target", str(init_repo), "--task", "TEST-5",
         "--capability", "example-feature", "--file", str(src)],
    )
    result = runner.invoke(
        main,
        ["plan", "accept", "--target", str(init_repo),
         "--id", "TEST-5-plan-001", "--by", "@mansura"],
    )
    assert result.exit_code == 0, result.output
    assert "accepted" in result.output
    path = init_repo / ".governance" / "plan" / "TEST-5-plan-001.plan.yaml"
    doc = load_yaml(path)
    assert doc["status"] == "accepted"
    assert doc["accepted_by"] == "@mansura"
    assert doc["accepted_at"]


def test_plan_list_shows_drafted_plans(
    runner: CliRunner, init_repo: Path, tmp_path: Path
) -> None:
    src = tmp_path / "p.yaml"
    src.write_text(_valid_plan_body("TEST-6", "example-feature"))
    runner.invoke(
        main,
        ["plan", "new", "--target", str(init_repo), "--task", "TEST-6",
         "--capability", "example-feature", "--file", str(src)],
    )
    result = runner.invoke(main, ["plan", "list", "--target", str(init_repo)])
    assert result.exit_code == 0
    assert "TEST-6-plan-001" in result.output


def test_plan_show_unknown_returns_1(runner: CliRunner, init_repo: Path) -> None:
    result = runner.invoke(
        main, ["plan", "show", "nonexistent-plan", "--target", str(init_repo)]
    )
    assert result.exit_code == 1
    assert "No plan" in result.output


def test_plan_schema_rejects_missing_challenge(
    runner: CliRunner, init_repo: Path, tmp_path: Path
) -> None:
    src = tmp_path / "no_challenge.yaml"
    src.write_text(
        textwrap.dedent(
            """\
            plan_id: TEST-7-plan-001
            task_id: TEST-7
            capability: example-feature
            generated_by:
              tool: human
              generated_at: "2026-05-19T10:00:00Z"
            status: draft
            accepted_by: ""
            accepted_at: ""
            scope:
              in_scope: ["x"]
              non_goals: ["y"]
            """
        )
    )
    result = runner.invoke(
        main,
        ["plan", "new", "--target", str(init_repo), "--task", "TEST-7",
         "--capability", "example-feature", "--file", str(src)],
    )
    assert result.exit_code == 1
    assert "Validation failed" in result.output
