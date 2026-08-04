"""Optional Graphify companion — subprocess wrappers, no hard dependency.

Resolves graph path from project config (if present) or defaults to
``<repo>/graphify-out/graph.json``. Invokes the ``graphify`` CLI when installed;
callers degrade gracefully when it is missing.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from sdd._paths import governance_dir, target_root
from sdd._yaml import load_yaml

INSTALL_HINT = (
    "graphify is not installed or not on PATH. "
    "Install with: pipx install graphifyy  (CLI name remains `graphify`)"
)
DEFAULT_GRAPH_REL = Path("graphify-out") / "graph.json"
DEFAULT_TIMEOUT_S = 120


@dataclass(frozen=True)
class GraphifyStatus:
    """Snapshot of Graphify availability for a repo."""

    target: Path
    graphify_bin: str | None
    graph_path: Path
    graph_exists: bool
    enabled: bool
    node_count: int | None
    edge_count: int | None
    message: str


def _read_knowledge_graphify(target: Path | None) -> dict:
    """Load ``knowledge.graphify`` from ``.governance/config.yaml`` if present."""
    cfg_path = governance_dir(target) / "config.yaml"
    if not cfg_path.exists():
        return {}
    try:
        doc = load_yaml(cfg_path)
    except Exception:
        return {}
    if not isinstance(doc, dict):
        return {}
    knowledge = doc.get("knowledge")
    if not isinstance(knowledge, dict):
        return {}
    g = knowledge.get("graphify")
    return g if isinstance(g, dict) else {}


def graphify_enabled(target: Path | None = None) -> bool:
    cfg = _read_knowledge_graphify(target)
    if "enabled" not in cfg:
        return True
    return bool(cfg.get("enabled"))


def resolve_graph_path(target: Path | None = None) -> Path:
    """Resolve the graph.json path for this repo."""
    tgt = target_root(target)
    cfg = _read_knowledge_graphify(tgt)
    raw = cfg.get("graph_path")
    if isinstance(raw, str) and raw.strip():
        p = Path(raw).expanduser()
        return p if p.is_absolute() else (tgt / p).resolve()
    return (tgt / DEFAULT_GRAPH_REL).resolve()


def find_graphify_bin() -> str | None:
    return shutil.which("graphify")


def _count_graph(graph_path: Path) -> tuple[int | None, int | None]:
    if not graph_path.exists():
        return None, None
    try:
        data = json.loads(graph_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None, None
    nodes = data.get("nodes")
    edges = data.get("edges") or data.get("links")
    n = len(nodes) if isinstance(nodes, list) else None
    e = len(edges) if isinstance(edges, list) else None
    return n, e


def status(target: Path | None = None) -> GraphifyStatus:
    tgt = target_root(target)
    enabled = graphify_enabled(tgt)
    bin_path = find_graphify_bin()
    graph_path = resolve_graph_path(tgt)
    exists = graph_path.exists()
    n, e = _count_graph(graph_path) if exists else (None, None)

    parts: list[str] = []
    if not enabled:
        parts.append("knowledge.graphify.enabled is false in .governance/config.yaml")
    if bin_path is None:
        parts.append(INSTALL_HINT)
    if not exists:
        parts.append(
            f"No graph at {graph_path}. Run `sdd graph update` or `graphify update .`."
        )
    if not parts:
        parts.append(
            f"OK — graphify={bin_path}, graph={graph_path}, "
            f"nodes={n if n is not None else '?'}, edges={e if e is not None else '?'}"
        )

    return GraphifyStatus(
        target=tgt,
        graphify_bin=bin_path,
        graph_path=graph_path,
        graph_exists=exists,
        enabled=enabled,
        node_count=n,
        edge_count=e,
        message="; ".join(parts),
    )


@dataclass(frozen=True)
class GraphifyResult:
    ok: bool
    exit_code: int
    stdout: str
    stderr: str
    command: list[str]
    error: str | None = None


def run_graphify(
    args: Sequence[str],
    *,
    target: Path | None = None,
    timeout: int = DEFAULT_TIMEOUT_S,
    require_graph: bool = False,
    require_enabled: bool = True,
) -> GraphifyResult:
    """Run ``graphify <args>`` with cwd = target root.

    Does not raise on missing binary — returns ``GraphifyResult`` with ``ok=False``.
    """
    tgt = target_root(target)
    if require_enabled and not graphify_enabled(tgt):
        return GraphifyResult(
            ok=False,
            exit_code=2,
            stdout="",
            stderr="",
            command=[],
            error="Graphify disabled via knowledge.graphify.enabled=false",
        )

    bin_path = find_graphify_bin()
    if bin_path is None:
        return GraphifyResult(
            ok=False,
            exit_code=127,
            stdout="",
            stderr="",
            command=[],
            error=INSTALL_HINT,
        )

    if require_graph:
        gpath = resolve_graph_path(tgt)
        if not gpath.exists():
            return GraphifyResult(
                ok=False,
                exit_code=2,
                stdout="",
                stderr="",
                command=[],
                error=(
                    f"No graph at {gpath}. Run `sdd graph update` first "
                    "(or `graphify update .`)."
                ),
            )

    cmd = [bin_path, *args]
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(tgt),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return GraphifyResult(
            ok=False,
            exit_code=124,
            stdout="",
            stderr="",
            command=cmd,
            error=f"graphify timed out after {timeout}s",
        )
    except OSError as exc:
        return GraphifyResult(
            ok=False,
            exit_code=1,
            stdout="",
            stderr="",
            command=cmd,
            error=f"failed to run graphify: {exc}",
        )

    return GraphifyResult(
        ok=proc.returncode == 0,
        exit_code=proc.returncode,
        stdout=proc.stdout or "",
        stderr=proc.stderr or "",
        command=cmd,
        error=None if proc.returncode == 0 else (proc.stderr or proc.stdout or f"exit {proc.returncode}"),
    )


def query(
    question: str,
    *,
    target: Path | None = None,
    budget: int | None = None,
    dfs: bool = False,
) -> GraphifyResult:
    gpath = resolve_graph_path(target)
    args: list[str] = ["query", question, "--graph", str(gpath)]
    if dfs:
        args.append("--dfs")
    if budget is not None:
        args.extend(["--budget", str(budget)])
    return run_graphify(args, target=target, require_graph=True)


def path_between(
    a: str,
    b: str,
    *,
    target: Path | None = None,
) -> GraphifyResult:
    gpath = resolve_graph_path(target)
    return run_graphify(
        ["path", a, b, "--graph", str(gpath)],
        target=target,
        require_graph=True,
    )


def explain(
    concept: str,
    *,
    target: Path | None = None,
) -> GraphifyResult:
    gpath = resolve_graph_path(target)
    return run_graphify(
        ["explain", concept, "--graph", str(gpath)],
        target=target,
        require_graph=True,
    )


def update_graph(
    *,
    target: Path | None = None,
    force: bool = False,
) -> GraphifyResult:
    tgt = target_root(target)
    args = ["update", str(tgt)]
    if force:
        args.append("--force")
    return run_graphify(args, target=tgt, require_graph=False, timeout=300)


def save_memory(
    *,
    question: str,
    answer: str,
    target: Path | None = None,
    result_type: str = "query",
    nodes: Sequence[str] | None = None,
    outcome: str | None = None,
    correction: str | None = None,
    memory_dir: Path | None = None,
) -> GraphifyResult:
    args: list[str] = [
        "save-result",
        "--question", question,
        "--answer", answer,
        "--type", result_type,
    ]
    if nodes:
        args.append("--nodes")
        args.extend(list(nodes))
    if outcome:
        args.extend(["--outcome", outcome])
    if correction:
        args.extend(["--correction", correction])
    if memory_dir is not None:
        args.extend(["--memory-dir", str(memory_dir)])
    return run_graphify(args, target=target, require_graph=False)


def reflect(
    *,
    target: Path | None = None,
    memory_dir: Path | None = None,
    out: Path | None = None,
) -> GraphifyResult:
    gpath = resolve_graph_path(target)
    args: list[str] = ["reflect"]
    if memory_dir is not None:
        args.extend(["--memory-dir", str(memory_dir)])
    if out is not None:
        args.extend(["--out", str(out)])
    if gpath.exists():
        args.extend(["--graph", str(gpath)])
    return run_graphify(args, target=target, require_graph=False)
