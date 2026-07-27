"""sdd CLI entry point — v0.3.

Commands:
  init                  Bootstrap a repo with the v0.3 framework.
  validate              Validate all governance YAML/frontmatter.
  generate-acceptance   Seed acceptance cases into a capability spec from tests.
  doctor                Diagnostic — what's present, what's missing.
  findings (add|list|show)   The LLM-wiki / knowledge layer.
  plan (new|accept|list|show)  AI-generated plans with mandatory human acceptance.
  progress (update|refresh)  Running progress log; `sdd progress` prints it.
  status                Deprecated alias for `sdd progress`.
  graph                 Optional Graphify companion (query / path / memory).
  serve                 MCP server exposing the framework to AI assistants.
"""
from __future__ import annotations

import sys
from pathlib import Path

import click

from sdd import __version__


@click.group(
    context_settings={"help_option_names": ["-h", "--help"]},
    invoke_without_command=False,
)
@click.version_option(version=__version__, prog_name="sdd")
def main() -> None:
    """sdd-plus-plus — Spec-Driven Development tooling for AI-assisted teams."""


# -----------------------------------------------------------------------------
# init
# -----------------------------------------------------------------------------


@main.command("init")
@click.option("--tier", type=click.Choice(["local", "team", "org", "regulated"], case_sensitive=False), default="team", show_default=True)
@click.option("--target", type=click.Path(file_okay=False, path_type=Path), default=None)
@click.option("--force", is_flag=True)
@click.option("--dry-run", is_flag=True)
def init_cmd(tier: str, target: Path | None, force: bool, dry_run: bool) -> None:
    """Bootstrap a repo with the v0.3 framework."""
    from sdd.commands.init import run_init
    sys.exit(run_init(tier=tier, target=target, force=force, dry_run=dry_run))


# -----------------------------------------------------------------------------
# validate
# -----------------------------------------------------------------------------


@main.command("validate")
@click.option("--target", type=click.Path(file_okay=False, exists=True, path_type=Path), default=None)
@click.option("--strict", is_flag=True)
def validate_cmd(target: Path | None, strict: bool) -> None:
    """Validate every YAML / frontmatter file in .governance/."""
    from sdd.commands.validate import run_validate
    sys.exit(run_validate(target=target, strict=strict))


# -----------------------------------------------------------------------------
# generate-acceptance
# -----------------------------------------------------------------------------


@main.command("generate-acceptance")
@click.option("--from-tests", type=click.Path(exists=True, path_type=Path), default=None)
@click.option("--capability", type=str, required=True)
@click.option("--target", type=click.Path(file_okay=False, path_type=Path), default=None)
@click.option("--output", type=click.Path(dir_okay=False, path_type=Path), default=None)
def generate_acceptance_cmd(from_tests: Path | None, capability: str, target: Path | None, output: Path | None) -> None:
    """Seed acceptance cases into capabilities/<cap>/spec.md from existing tests."""
    from sdd.commands.generate import run_generate_acceptance
    sys.exit(run_generate_acceptance(from_tests=from_tests, capability=capability, target=target, output=output))


# -----------------------------------------------------------------------------
# doctor
# -----------------------------------------------------------------------------


@main.command("doctor")
@click.option("--target", type=click.Path(file_okay=False, path_type=Path), default=None)
def doctor_cmd(target: Path | None) -> None:
    """Diagnose adoption state of the v0.3 framework."""
    from sdd.commands.doctor import run_doctor
    sys.exit(run_doctor(target=target))


# -----------------------------------------------------------------------------
# findings
# -----------------------------------------------------------------------------


@main.group("findings")
def findings_group() -> None:
    """Manage findings — the wiki/findings layer."""


@findings_group.command("add")
@click.option("--target", type=click.Path(file_okay=False, path_type=Path), default=None)
@click.option("--from-task", type=str, default=None)
@click.option("--capability", type=str, default=None)
@click.option("--title", type=str, default=None)
@click.option("--author", type=str, default=None)
@click.option("--file", "non_interactive_file", type=click.Path(exists=True, dir_okay=False, path_type=Path), default=None)
def findings_add_cmd(target, from_task, capability, title, author, non_interactive_file):
    """Record a new finding (editor-based, or import via --file)."""
    from sdd.commands.findings import run_findings_add
    sys.exit(run_findings_add(target=target, from_task=from_task, capability=capability, title=title, author=author, non_interactive_file=non_interactive_file))


@findings_group.command("list")
@click.option("--target", type=click.Path(file_okay=False, path_type=Path), default=None)
@click.option("--capability", type=str, default=None)
@click.option("--tag", type=str, default=None)
@click.option("--status", type=click.Choice(["suspected", "confirmed", "mitigated", "refuted", "archived"]), default=None)
def findings_list_cmd(target, capability, tag, status):
    """List findings, optionally filtered."""
    from sdd.commands.findings import run_findings_list
    sys.exit(run_findings_list(target=target, capability=capability, tag=tag, status=status))


@findings_group.command("show")
@click.argument("finding_id", type=str)
@click.option("--target", type=click.Path(file_okay=False, path_type=Path), default=None)
def findings_show_cmd(finding_id, target):
    """Show a finding's full content."""
    from sdd.commands.findings import run_findings_show
    sys.exit(run_findings_show(target=target, finding_id=finding_id))


# -----------------------------------------------------------------------------
# plan
# -----------------------------------------------------------------------------


@main.group("plan")
def plan_group() -> None:
    """Manage AI-generated plans with human ownership gates."""


@plan_group.command("new")
@click.option("--target", type=click.Path(file_okay=False, path_type=Path), default=None)
@click.option("--task", "task_id", type=str, required=True)
@click.option("--capability", type=str, required=True)
@click.option("--tool", type=str, default="human", help="Author tool — 'human', 'claude-code', 'cursor', etc.")
@click.option("--file", "non_interactive_file", type=click.Path(exists=True, dir_okay=False, path_type=Path), default=None)
def plan_new_cmd(target, task_id, capability, tool, non_interactive_file):
    """Draft a new plan. Status is always 'draft'; only `sdd plan accept` advances it."""
    from sdd.commands.plan import run_plan_new
    sys.exit(run_plan_new(target=target, task_id=task_id, capability=capability, tool=tool, non_interactive_file=non_interactive_file))


@plan_group.command("accept")
@click.option("--target", type=click.Path(file_okay=False, path_type=Path), default=None)
@click.option("--id", "plan_id", type=str, required=True)
@click.option("--by", type=str, required=True, help="Human handle (e.g. @mansura). Required — AI cannot self-accept.")
def plan_accept_cmd(target, plan_id, by):
    """A human signs off on a plan — sets accepted_by + accepted_at + status: accepted."""
    from sdd.commands.plan import run_plan_accept
    sys.exit(run_plan_accept(target=target, plan_id=plan_id, by=by))


@plan_group.command("list")
@click.option("--target", type=click.Path(file_okay=False, path_type=Path), default=None)
@click.option("--status", type=click.Choice(["draft", "accepted", "executed", "rejected", "archived"]), default=None)
def plan_list_cmd(target, status):
    """List plans, optionally filtered by status."""
    from sdd.commands.plan import run_plan_list
    sys.exit(run_plan_list(target=target, status=status))


@plan_group.command("show")
@click.argument("plan_id", type=str)
@click.option("--target", type=click.Path(file_okay=False, path_type=Path), default=None)
def plan_show_cmd(plan_id, target):
    """Show a plan's full content."""
    from sdd.commands.plan import run_plan_show
    sys.exit(run_plan_show(target=target, plan_id=plan_id))


# -----------------------------------------------------------------------------
# progress (was: status)
# -----------------------------------------------------------------------------


@main.group("progress", invoke_without_command=True)
@click.option("--target", type=click.Path(file_okay=False, path_type=Path), default=None)
@click.pass_context
def progress_group(ctx, target):
    """Show, update, or refresh .governance/progress.md."""
    if ctx.invoked_subcommand is None:
        from sdd.commands.progress import run_progress_show
        sys.exit(run_progress_show(target=target))


@progress_group.command("update")
@click.option("--target", type=click.Path(file_okay=False, path_type=Path), default=None)
@click.option("--kind", type=str, required=True)
@click.option("--message", type=str, required=True)
@click.option("--actor", type=str, default=None)
def progress_update_cmd(target, kind, message, actor):
    """Append an event and refresh progress.md."""
    from sdd.commands.progress import run_progress_update
    sys.exit(run_progress_update(target=target, kind=kind, message=message, actor=actor))


@progress_group.command("refresh")
@click.option("--target", type=click.Path(file_okay=False, path_type=Path), default=None)
def progress_refresh_cmd(target):
    """Re-render progress.md from current state."""
    from sdd.commands.progress import run_progress_refresh
    sys.exit(run_progress_refresh(target=target))


# Deprecated alias: sdd status → sdd progress
@main.command("status", hidden=True)
@click.option("--target", type=click.Path(file_okay=False, path_type=Path), default=None)
def status_alias_cmd(target):
    """Deprecated alias for `sdd progress`. Will be removed in v0.5."""
    click.secho("DEPRECATED: use `sdd progress` (status renamed to progress in v0.3).", err=True, fg="yellow")
    from sdd.commands.progress import run_progress_show
    sys.exit(run_progress_show(target=target))


# Top-level convenience: sdd update-status (equivalent to `sdd progress update`).
# Easier to type when you just want to log one thing.
@main.command("update-status")
@click.option("--target", type=click.Path(file_okay=False, path_type=Path), default=None)
@click.option("--kind", type=str, required=True, help="Event kind (e.g. progress, session-end, milestone, blocker).")
@click.option("--message", type=str, required=True, help="One-line description.")
@click.option("--actor", type=str, default=None, help="Who's recording. Defaults to @$USER.")
def update_status_cmd(target, kind, message, actor):
    """Append a progress event and refresh progress.md. Convenience alias for `sdd progress update`."""
    from sdd.commands.progress import run_progress_update
    sys.exit(run_progress_update(target=target, kind=kind, message=message, actor=actor))


# -----------------------------------------------------------------------------
# graph (optional Graphify companion)
# -----------------------------------------------------------------------------


@main.group("graph")
def graph_group() -> None:
    """Optional Graphify companion — graph engineering for developers and AI.

    Requires the `graphify` CLI on PATH (`pipx install graphifyy`). Does not
    replace findings authority; use `sdd findings` / MCP search_findings for
    status-aware knowledge blocks.
    """


@graph_group.command("status")
@click.option("--target", type=click.Path(file_okay=False, path_type=Path), default=None)
def graph_status_cmd(target):
    """Show whether graphify and graph.json are available."""
    from sdd.commands.graph import run_graph_status
    sys.exit(run_graph_status(target=target))


@graph_group.command("update")
@click.option("--target", type=click.Path(file_okay=False, path_type=Path), default=None)
@click.option("--force", is_flag=True, help="Pass --force to graphify update.")
def graph_update_cmd(target, force):
    """Refresh the code AST graph (no API key)."""
    from sdd.commands.graph import run_graph_update
    sys.exit(run_graph_update(target=target, force=force))


@graph_group.command("query")
@click.argument("question", type=str)
@click.option("--target", type=click.Path(file_okay=False, path_type=Path), default=None)
@click.option("--budget", type=int, default=None, help="Token budget for graphify query.")
@click.option("--dfs", is_flag=True, help="Use depth-first traversal.")
def graph_query_cmd(question, target, budget, dfs):
    """BFS/DFS traversal of graph.json for a question."""
    from sdd.commands.graph import run_graph_query
    sys.exit(run_graph_query(question, target=target, budget=budget, dfs=dfs))


@graph_group.command("path")
@click.argument("a", type=str)
@click.argument("b", type=str)
@click.option("--target", type=click.Path(file_okay=False, path_type=Path), default=None)
def graph_path_cmd(a, b, target):
    """Shortest path between two nodes."""
    from sdd.commands.graph import run_graph_path
    sys.exit(run_graph_path(a, b, target=target))


@graph_group.command("explain")
@click.argument("concept", type=str)
@click.option("--target", type=click.Path(file_okay=False, path_type=Path), default=None)
def graph_explain_cmd(concept, target):
    """Plain-language explanation of a node and its neighbors."""
    from sdd.commands.graph import run_graph_explain
    sys.exit(run_graph_explain(concept, target=target))


@graph_group.group("memory")
def graph_memory_group() -> None:
    """Shared graph memory (graphify-out/memory) — chat forgets, graph doesn't."""


@graph_memory_group.command("save")
@click.option("--question", "question", type=str, required=True)
@click.option("--answer", "answer", type=str, required=True)
@click.option("--type", "result_type", type=str, default="query", show_default=True)
@click.option("--node", "nodes", multiple=True, help="Cited node label (repeatable).")
@click.option("--outcome", type=click.Choice(["useful", "dead_end", "corrected"]), default=None)
@click.option("--correction", type=str, default=None)
@click.option("--memory-dir", type=click.Path(file_okay=False, path_type=Path), default=None)
@click.option("--target", type=click.Path(file_okay=False, path_type=Path), default=None)
def graph_memory_save_cmd(question, answer, result_type, nodes, outcome, correction, memory_dir, target):
    """Save a Q&A result into graphify memory for the feedback loop."""
    from sdd.commands.graph import run_graph_memory_save
    sys.exit(run_graph_memory_save(
        question, answer, target=target, result_type=result_type,
        nodes=nodes, outcome=outcome, correction=correction, memory_dir=memory_dir,
    ))


@graph_group.command("reflect")
@click.option("--target", type=click.Path(file_okay=False, path_type=Path), default=None)
@click.option("--memory-dir", type=click.Path(file_okay=False, path_type=Path), default=None)
@click.option("--out", type=click.Path(dir_okay=False, path_type=Path), default=None)
def graph_reflect_cmd(target, memory_dir, out):
    """Aggregate memory outcomes into a deterministic lessons doc."""
    from sdd.commands.graph import run_graph_reflect
    sys.exit(run_graph_reflect(target=target, memory_dir=memory_dir, out=out))


# -----------------------------------------------------------------------------
# serve
# -----------------------------------------------------------------------------


@main.command("serve")
@click.option("--target", type=click.Path(file_okay=False, path_type=Path), default=None)
@click.option("--transport", type=click.Choice(["stdio", "http"]), default="stdio", show_default=True)
def serve_cmd(target, transport):
    """Run the sdd-governance MCP server (for Cursor / Claude Code / Copilot)."""
    from sdd.commands.serve import run_serve
    sys.exit(run_serve(target=target, transport=transport))


if __name__ == "__main__":
    main()
