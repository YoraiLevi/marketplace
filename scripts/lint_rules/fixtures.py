"""fixtures.py — throwaway-repository builders used by counterexamples.

Stdlib only, and deliberately does NOT import model: counterexamples make
filesystems, not Violations. Every helper writes under the given root and
returns Paths, so a counterexample composes them into exactly the broken
input its rule needs.
"""

from __future__ import annotations

import json
from pathlib import Path

VALID_IDENTITY = """[marketplace]
name = "example-marketplace"
version = "1.0.0"
description = "Fixture marketplace."

[owner]
name = "Example"
url = "https://github.com/example"

[repository]
url = "https://github.com/example/example"
"""


def base(root: Path, identity: str = VALID_IDENTITY) -> Path:
    """Minimal, otherwise-valid source tree. Returns src/."""
    src = root / "src"
    (src / "skills").mkdir(parents=True, exist_ok=True)
    (src / ".metadata-MARKETPLACE.toml").write_text(identity, encoding="utf-8")
    return src


def identity_with(name: str) -> str:
    return VALID_IDENTITY.replace(
        'name = "example-marketplace"', f'name = "{name}"', 1
    )


def skill(src: Path, folder: str,
          frontmatter: str = "description: A fixture skill.") -> Path:
    """A solo-layout skill folder under src/skills/. Returns the folder."""
    d = src / "skills" / folder
    d.mkdir(parents=True, exist_ok=True)
    (d / "SKILL.md").write_text(
        f"---\n{frontmatter}\n---\nFixture body.\n", encoding="utf-8"
    )
    return d


def multi_skill(src: Path, plugin: str, child: str,
                frontmatter: str) -> Path:
    """One child of a multi-layout plugin. Returns the child folder."""
    d = src / "skills" / plugin / "skills" / child
    d.mkdir(parents=True, exist_ok=True)
    (d / "SKILL.md").write_text(
        f"---\n{frontmatter}\n---\nFixture body.\n", encoding="utf-8"
    )
    return d


def generated_plugin(root: Path, plugin_dir: str, plugin_name: str) -> Path:
    """A generated plugin wrapper under _generated/claude-code/. Returns its dir."""
    d = root / "_generated" / "claude-code" / plugin_dir / ".claude-plugin"
    d.mkdir(parents=True, exist_ok=True)
    (d / "plugin.json").write_text(
        json.dumps({"name": plugin_name, "description": "x", "version": "1.0.0"}),
        encoding="utf-8",
    )
    return d.parent
