"""`sdd graph` — optional Graphify companion for graph engineering.

Thin CLI wrappers around the ``graphify`` binary. No hard dependency —
missing install or graph yields a clear hint and non-zero exit.
"""
from __future__ import annotations

from pathlib import Path

import click

from sdd.commands import _graphify as gfy


def run_graph_status(target: Path | None = None) -> int:
    st = gfy.status(target)
    click.echo(f"enabled:     {st.enabled}")
    click.echo(f"graphify:    {st.graphify_bin or '(not found)'}")
    click.echo(f"graph_path:  {st.graph_path}")
    click.echo(f"graph_exists:{st.graph_exists}")
    if st.node_count is not None:
        click.echo(f"nodes:       {st.node_count}")
    if st.edge_count is not None:
        click.echo(f"edges:       {st.edge_count}")
    click.echo(st.message)
    if not st.enabled:
        return 2
    if st.graphify_bin is None or not st.graph_exists:
        return 1
    return 0


def _emit_result(result: gfy.GraphifyResult) -> int:
    if result.stdout:
        click.echo(result.stdout, nl=not result.stdout.endswith("\n"))
    if result.stderr:
        click.echo(result.stderr, err=True, nl=not result.stderr.endswith("\n"))
    if not result.ok and result.error and not result.stderr:
        click.secho(result.error, err=True, fg="red")
    return 0 if result.ok else (result.exit_code or 1)


def run_graph_update(target: Path | None = None, force: bool = False) -> int:
    return _emit_result(gfy.update_graph(target=target, force=force))


def run_graph_query(
    question: str,
    target: Path | None = None,
    budget: int | None = None,
    dfs: bool = False,
) -> int:
    return _emit_result(
        gfy.query(question, target=target, budget=budget, dfs=dfs)
    )


def run_graph_path(a: str, b: str, target: Path | None = None) -> int:
    return _emit_result(gfy.path_between(a, b, target=target))


def run_graph_explain(concept: str, target: Path | None = None) -> int:
    return _emit_result(gfy.explain(concept, target=target))


def run_graph_memory_save(
    question: str,
    answer: str,
    *,
    target: Path | None = None,
    result_type: str = "query",
    nodes: tuple[str, ...] = (),
    outcome: str | None = None,
    correction: str | None = None,
    memory_dir: Path | None = None,
) -> int:
    return _emit_result(
        gfy.save_memory(
            question=question,
            answer=answer,
            target=target,
            result_type=result_type,
            nodes=nodes or None,
            outcome=outcome,
            correction=correction,
            memory_dir=memory_dir,
        )
    )


def run_graph_reflect(
    target: Path | None = None,
    memory_dir: Path | None = None,
    out: Path | None = None,
) -> int:
    return _emit_result(
        gfy.reflect(target=target, memory_dir=memory_dir, out=out)
    )
