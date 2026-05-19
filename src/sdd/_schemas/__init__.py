"""JSON Schemas bundled inside sdd-plus-plus.

These schemas are NOT exposed in the user's `.governance/` tree. The CLI loads them from
package data via importlib.resources and uses them to validate user-authored YAML
(spec.md frontmatter, plan.md frontmatter, finding YAML, REGISTRY.yaml).

Why hidden:
  - Users don't need to see schema files; the validator loads them automatically.
  - Hiding them means schema upgrades ship with the tool, not via copy-paste into every repo.
  - Adopters get the latest validation rules just by upgrading sdd-plus-plus.
"""
from __future__ import annotations

from importlib import resources
from pathlib import Path


SCHEMA_NAMES = (
    "capability_spec",
    "plan",
    "registry",
    "finding",
)


def schema_path(name: str) -> Path:
    """Return the absolute path to a bundled schema YAML."""
    if name not in SCHEMA_NAMES:
        raise ValueError(f"Unknown schema '{name}'. Known: {SCHEMA_NAMES}")
    return Path(str(resources.files("sdd._schemas") / f"{name}.schema.yaml"))
