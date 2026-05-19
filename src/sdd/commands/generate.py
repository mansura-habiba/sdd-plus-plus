"""`sdd generate-acceptance --from-tests` — seed acceptance cases from existing pytest tests.

In v0.3 the acceptance section lives INSIDE capabilities/<id>/spec.md frontmatter under
the `cases` key. This command discovers tests and writes a starter cases array to the
target capability's spec.md (preserving everything else).

The generator is conservative: status stays draft, every case has minimal fields,
forbidden_implementations is empty. The human curates.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

import click

from sdd._paths import capabilities_dir, target_root
from sdd._yaml import load_frontmatter_file, render_frontmatter_file


@dataclass
class TestSeed:
    function_name: str
    file: Path
    docstring: str | None
    kind: str

    @property
    def case_id(self) -> str:
        return self.function_name.removeprefix("test_").replace("_", "-")

    @property
    def description(self) -> str:
        if self.docstring:
            return self.docstring.strip().splitlines()[0]
        return self.function_name.removeprefix("test_").replace("_", " ").capitalize()


def _infer_kind(name: str, doc: str | None) -> str:
    n = name.lower()
    d = (doc or "").lower()
    if any(t in n for t in ("reject", "fail", "raise", "invalid", "bad", "missing", "denied", "blocked")):
        return "negative"
    if "idempot" in n or "idempot" in d:
        return "idempotence"
    if any(t in n for t in ("property", "invariant", "for_any", "for_all", "hypothesis")):
        return "invariant"
    if any(t in n for t in ("perf", "latency", "throughput", "speed", "benchmark")):
        return "performance"
    if any(t in n for t in ("security", "auth", "injection", "sanitize")):
        return "security"
    if any(t in n for t in ("boundary", "edge", "empty", "max", "min", "limit", "overflow")):
        return "boundary"
    if any(t in n for t in ("regression", "issue_", "bug_")):
        return "regression"
    return "positive"


def _parse_test_file(path: Path) -> list[TestSeed]:
    seeds: list[TestSeed] = []
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        return seeds
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        if not node.name.startswith("test_"):
            continue
        doc = ast.get_docstring(node)
        seeds.append(
            TestSeed(function_name=node.name, file=path, docstring=doc, kind=_infer_kind(node.name, doc))
        )
    return seeds


def _discover(from_tests: Path) -> list[TestSeed]:
    seeds: list[TestSeed] = []
    paths = [from_tests] if from_tests.is_file() and from_tests.suffix == ".py" else sorted(from_tests.rglob("test_*.py"))
    for p in paths:
        seeds.extend(_parse_test_file(p))
    return seeds


def run_generate_acceptance(
    from_tests: Path | None,
    capability: str,
    target: Path | None,
    output: Path | None,
) -> int:
    tgt = target_root(target)
    if from_tests is None:
        from_tests = tgt / "tests"
        if not from_tests.exists():
            click.secho(
                f"FATAL: --from-tests not provided and {from_tests} does not exist.",
                err=True, fg="red",
            )
            return 2

    seeds = _discover(from_tests)
    if not seeds:
        click.secho(f"No test_* functions found under {from_tests}.", err=True, fg="yellow")
        return 1

    # Locate target spec.md
    spec_path = capabilities_dir(target) / capability / "spec.md"
    if not spec_path.exists():
        click.secho(
            f"FATAL: capability '{capability}' has no spec.md at {spec_path}. "
            "Create the folder first or rename example-feature/.",
            err=True, fg="red",
        )
        return 2

    fm, body = load_frontmatter_file(spec_path)
    if fm is None:
        click.secho(f"FATAL: {spec_path} has no frontmatter.", err=True, fg="red")
        return 1

    new_cases: list[dict] = []
    for seed in seeds:
        try:
            rel = seed.file.relative_to(tgt)
        except ValueError:
            rel = seed.file
        new_cases.append({
            "id": seed.case_id,
            "kind": seed.kind,
            "priority": "normal",
            "description": seed.description,
            "test_id": f"{rel}::{seed.function_name}",
        })

    fm["cases"] = new_cases
    spec_path.write_text(render_frontmatter_file(fm, body), encoding="utf-8")

    by_kind: dict[str, int] = {}
    for s in seeds:
        by_kind[s.kind] = by_kind.get(s.kind, 0) + 1

    click.secho(f"sdd generate-acceptance — updated {spec_path.relative_to(tgt)}", bold=True)
    click.echo(f"  capability: {capability}")
    click.echo(f"  cases written: {len(new_cases)}")
    for k in sorted(by_kind):
        click.echo(f"    {k}: {by_kind[k]}")
    click.echo()
    click.secho("Curate these cases before relying on them.", fg="yellow", bold=True)
    if "negative" not in by_kind:
        click.secho("Coverage warning: no negative cases inferred. Add at least one.", fg="yellow")

    from sdd._progress import record
    record(
        target=target,
        kind="acceptance-generated",
        message=f"{capability}: {len(new_cases)} cases from {from_tests}",
    )
    return 0
