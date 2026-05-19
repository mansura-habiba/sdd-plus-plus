"""Path resolution helpers for the v0.3 layout.

v0.3 layout:
    .governance/
      wiki/
        principles.md
        findings/<id>.md           # YAML frontmatter + markdown body
        practices/                 # optional
      capabilities/
        REGISTRY.yaml
        <id>/
          spec.md                  # YAML frontmatter + markdown body
      arch_spec.md
      instructions.md              # canonical AI rules
      plan/<task-id>.plan.md       # YAML frontmatter + markdown body
      progress.md                  # auto-generated
    AGENTS.md                      # at repo root — copy of instructions.md
"""
from __future__ import annotations

from importlib import resources
from pathlib import Path


def templates_dir() -> Path:
    return Path(str(resources.files("sdd") / "templates"))


def schemas_dir() -> Path:
    """Where bundled JSON schemas live (hidden from users)."""
    return Path(str(resources.files("sdd") / "_schemas"))


def target_root(cwd: Path | None = None) -> Path:
    return (cwd or Path.cwd()).resolve()


def governance_dir(target: Path | None = None) -> Path:
    return target_root(target) / ".governance"


def wiki_dir(target: Path | None = None) -> Path:
    return governance_dir(target) / "wiki"


def findings_dir(target: Path | None = None) -> Path:
    return wiki_dir(target) / "findings"


def capabilities_dir(target: Path | None = None) -> Path:
    return governance_dir(target) / "capabilities"


def plan_dir(target: Path | None = None) -> Path:
    return governance_dir(target) / "plan"


def progress_md_path(target: Path | None = None) -> Path:
    return governance_dir(target) / "progress.md"


def progress_log_path(target: Path | None = None) -> Path:
    return governance_dir(target) / ".progress-log.yaml"


def instructions_md_path(target: Path | None = None) -> Path:
    return governance_dir(target) / "instructions.md"


def arch_spec_path(target: Path | None = None) -> Path:
    return governance_dir(target) / "arch_spec.md"


def principles_md_path(target: Path | None = None) -> Path:
    return wiki_dir(target) / "principles.md"


def registry_path(target: Path | None = None) -> Path:
    return capabilities_dir(target) / "REGISTRY.yaml"


def agents_md_path(target: Path | None = None) -> Path:
    """AGENTS.md lives at the repo root for AI-tool auto-load compatibility."""
    return target_root(target) / "AGENTS.md"


def github_dir(target: Path | None = None) -> Path:
    return target_root(target) / ".github"


def contract_tests_dir(target: Path | None = None) -> Path:
    return target_root(target) / "tests" / "contract"
