"""Tests for optional Graphify companion (`sdd graph` / kb_* helpers)."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from sdd.cli import main
from sdd.commands import _graphify as gfy
from sdd.commands.serve import _impl_kb_path, _impl_kb_query


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def repo_with_graph(tmp_path: Path) -> Path:
    graph_dir = tmp_path / "graphify-out"
    graph_dir.mkdir()
    (graph_dir / "graph.json").write_text(
        json.dumps({"nodes": [{"id": "a"}, {"id": "b"}], "edges": [{"source": "a", "target": "b"}]}),
        encoding="utf-8",
    )
    gov = tmp_path / ".governance"
    gov.mkdir()
    (gov / "wiki").mkdir()
    (gov / "wiki" / "findings").mkdir(parents=True)
    return tmp_path


def test_resolve_graph_path_default(tmp_path: Path) -> None:
    assert gfy.resolve_graph_path(tmp_path) == (tmp_path / "graphify-out" / "graph.json").resolve()


def test_resolve_graph_path_from_config(tmp_path: Path) -> None:
    gov = tmp_path / ".governance"
    gov.mkdir()
    (gov / "config.yaml").write_text(
        "knowledge:\n  graphify:\n    enabled: true\n    graph_path: custom/g.json\n",
        encoding="utf-8",
    )
    assert gfy.resolve_graph_path(tmp_path) == (tmp_path / "custom" / "g.json").resolve()


def test_graphify_enabled_false(tmp_path: Path) -> None:
    gov = tmp_path / ".governance"
    gov.mkdir()
    (gov / "config.yaml").write_text(
        "knowledge:\n  graphify:\n    enabled: false\n",
        encoding="utf-8",
    )
    assert gfy.graphify_enabled(tmp_path) is False


def test_status_counts_nodes(repo_with_graph: Path) -> None:
    with patch.object(gfy, "find_graphify_bin", return_value="/usr/bin/graphify"):
        st = gfy.status(repo_with_graph)
    assert st.graph_exists is True
    assert st.node_count == 2
    assert st.edge_count == 1
    assert st.graphify_bin == "/usr/bin/graphify"


def test_run_graphify_missing_binary(tmp_path: Path) -> None:
    with patch.object(gfy, "find_graphify_bin", return_value=None):
        result = gfy.run_graphify(["query", "x"], target=tmp_path)
    assert result.ok is False
    assert result.exit_code == 127
    assert "pipx install graphifyy" in (result.error or "")


def test_run_graphify_disabled(tmp_path: Path) -> None:
    gov = tmp_path / ".governance"
    gov.mkdir()
    (gov / "config.yaml").write_text(
        "knowledge:\n  graphify:\n    enabled: false\n",
        encoding="utf-8",
    )
    with patch.object(gfy, "find_graphify_bin", return_value="/usr/bin/graphify"):
        result = gfy.run_graphify(["query", "x"], target=tmp_path)
    assert result.ok is False
    assert "disabled" in (result.error or "").lower()


def test_cli_graph_status_missing(runner: CliRunner, tmp_path: Path) -> None:
    with patch.object(gfy, "find_graphify_bin", return_value=None):
        result = runner.invoke(main, ["graph", "status", "--target", str(tmp_path)])
    assert result.exit_code != 0
    assert "graphify" in result.output.lower() or "pipx" in result.output.lower()


def test_cli_graph_query_missing_binary(runner: CliRunner, repo_with_graph: Path) -> None:
    with patch.object(gfy, "find_graphify_bin", return_value=None):
        result = runner.invoke(
            main, ["graph", "query", "anything", "--target", str(repo_with_graph)]
        )
    assert result.exit_code != 0
    assert "pipx install graphifyy" in result.output


def test_kb_query_falls_back_to_findings(repo_with_graph: Path) -> None:
    findings = repo_with_graph / ".governance" / "wiki" / "findings"
    findings.mkdir(parents=True, exist_ok=True)
    (findings / "cookie-samesite.yaml").write_text(
        "\n".join(
            [
                "id: cookie-samesite",
                'title: "Auth cookie SameSite"',
                "status: confirmed",
                "severity: medium",
                'discovered_by: "@me"',
                'discovered_at: "2026-07-26"',
                "related_capabilities:",
                "  - example-feature",
                'finding: "SameSite=Lax is required for the auth cookie in cross-site flows."',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    with patch.object(gfy, "find_graphify_bin", return_value=None):
        out = _impl_kb_query("SameSite", repo_with_graph)
    assert out["source"] == "findings_fallback"
    assert out["ok"] is True
    assert any(f.get("id") == "cookie-samesite" for f in out["findings"])


def test_kb_path_errors_without_graphify(tmp_path: Path) -> None:
    with patch.object(gfy, "find_graphify_bin", return_value=None):
        out = _impl_kb_path("A", "B", tmp_path)
    assert out["ok"] is False
    assert out.get("install_hint")
