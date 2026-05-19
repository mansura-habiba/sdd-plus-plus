"""YAML I/O + Markdown frontmatter helpers.

We use ruamel.yaml (not PyYAML) because:
  - Round-trip preservation of comments — important when users edit generated files.
  - Block-style dumping by default — closer to what a human would write.
  - Standards-compliant YAML 1.2.

Frontmatter format used in v0.3 spec.md / plan.md / finding.md files:

    ---
    <yaml content>
    ---
    <markdown body>
"""
from __future__ import annotations

import re
from io import StringIO
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML


_FRONTMATTER_PATTERN = re.compile(
    r"^---\s*\n(?P<yaml>.*?)\n---\s*\n(?P<body>.*)$",
    re.DOTALL,
)


def _yaml() -> YAML:
    y = YAML(typ="rt")
    y.indent(mapping=2, sequence=4, offset=2)
    y.preserve_quotes = True
    y.width = 100
    return y


def load_yaml(path: Path) -> Any:
    """Load a pure YAML file."""
    with path.open(encoding="utf-8") as f:
        return _yaml().load(f)


def dump_yaml(data: Any, path: Path) -> None:
    """Write data to a YAML file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        _yaml().dump(data, f)


def dump_yaml_string(data: Any) -> str:
    """Render data as a YAML string."""
    buf = StringIO()
    _yaml().dump(data, buf)
    return buf.getvalue()


# -----------------------------------------------------------------------------
# Markdown frontmatter
# -----------------------------------------------------------------------------


def parse_frontmatter(text: str) -> tuple[dict | None, str]:
    """Split a markdown-with-frontmatter string into (yaml_data, markdown_body).

    Returns (None, full_text) if the text has no frontmatter block. This is permissive —
    we don't want to crash on legacy files; we want validation to flag them.
    """
    m = _FRONTMATTER_PATTERN.match(text)
    if not m:
        return None, text
    yaml_text = m.group("yaml")
    body = m.group("body")
    try:
        data = _yaml().load(StringIO(yaml_text))
    except Exception:
        return None, text
    if not isinstance(data, dict):
        return None, text
    return data, body


def load_frontmatter_file(path: Path) -> tuple[dict | None, str]:
    """Convenience: read a markdown file and return parsed frontmatter + body."""
    if not path.exists():
        return None, ""
    return parse_frontmatter(path.read_text(encoding="utf-8"))


def render_frontmatter_file(data: dict, body: str) -> str:
    """Inverse of parse_frontmatter — combine frontmatter dict + markdown body into a string."""
    yaml_text = dump_yaml_string(data).rstrip("\n")
    return f"---\n{yaml_text}\n---\n{body if body.startswith(chr(10)) else chr(10) + body}"


def write_frontmatter_file(path: Path, data: dict, body: str) -> None:
    """Write a frontmatter+body file to disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_frontmatter_file(data, body), encoding="utf-8")
