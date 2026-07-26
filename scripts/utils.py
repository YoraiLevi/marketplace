#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
utils.py — shared helpers for the marketplace generator.

Provides:
  - GENERATED, MARKETPLACE_JSON constants
  - scan_source_dir   — list instance names under a source directory
  - _load_plugin_json — cached JSON read of a source plugin.json
  - _frontmatter      — YAML frontmatter parser for markdown files
  - _to_json          — deterministic JSON pretty-print
  - _marketplace_*    — .metadata-MARKETPLACE.toml field accessors
  - write_plugin_json — write .claude-plugin/plugin.json under a target dir
"""

from __future__ import annotations

import json
import re
import tomllib
from functools import cache
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC = REPO_ROOT / "src"
# Generated output is namespaced per platform; Claude Code is the only
# platform today. A revived platform (issues #28-#36) gets a sibling dir
# (_generated/<platform>/), never mixes into this one.
GENERATED = REPO_ROOT / "_generated" / "claude-code"
MARKETPLACE_JSON = REPO_ROOT / ".claude-plugin" / "marketplace.json"
MARKETPLACE_TOML = SRC / ".metadata-MARKETPLACE.toml"


def scan_source_dir(source_dir: Path) -> list[str]:
    """List instance names (subdirectory names) under a source directory.

    Returns an empty list if the directory doesn't exist.
    Results are sorted for deterministic output.
    """
    if not source_dir.exists():
        return []
    return sorted(d.name for d in source_dir.iterdir() if d.is_dir())


@cache
def _load_plugin_json(path: Path) -> dict:
    """Cached read of a plugin.json file. Path must be absolute."""
    return json.loads(path.read_text(encoding="utf-8"))


def _is_candidate_subdir(d: Path) -> bool:
    """True if ``d`` is a directory that looks like a real plugin source subdir.

    Filters out tool-generated junk: hidden dirs (``.git``, ``.DS_Store``-
    adjacent IDE artifacts) and ``__pycache__``. Used by SkillConstruct's
    layout-detection branch to prevent ``skills/__pycache__/SKILL.md``
    from flipping ``has_subdir=True`` and routing a solo plugin into
    multi-layout emission.
    """
    if not d.is_dir():
        return False
    if d.name.startswith("."):
        return False
    if d.name == "__pycache__":
        return False
    return True


def _read_source_plugin_description(src_plugin_dir: Path, fallback: str) -> str:
    """Read the plugin-level description from ``<src>/.metadata-SKILL.toml``.

    This is the marketplace-listing one-liner, distinct from per-component
    descriptions (which live in each SKILL.md frontmatter). Skills under the
    multi-skill layout have no single SKILL.md to pull a description from,
    so the operator authors it in the plugin's metadata file:

        description = "One-line marketplace listing for this plugin."

    ``.metadata-*.toml`` files are operator-edited source intent (dot-prefixed
    like ``.env`` — a fork edits them and ships its own); the generator turns
    them into the platform-shaped ``.claude-plugin/plugin.json`` under
    ``_generated/``. Source trees never contain ``.claude-plugin/`` (rule R6).

    Falls back to ``fallback`` (typically the plugin directory name) when the
    file is missing, unparseable, or has no non-empty ``description``.
    """
    meta_path = src_plugin_dir / ".metadata-SKILL.toml"
    if not meta_path.exists():
        return fallback
    try:
        with open(meta_path, "rb") as f:
            data = tomllib.load(f)
    except (tomllib.TOMLDecodeError, OSError):
        return fallback
    desc = data.get("description")
    return desc if isinstance(desc, str) and desc else fallback


def _frontmatter(path: Path) -> dict:
    """Parse YAML frontmatter (key: value lines) from a markdown file.

    Handles simple scalar values only — lists and nested objects are not
    parsed. Returns an empty dict if no frontmatter block is found.
    """
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end == -1:
        return {}
    fm_text = text[4:end]
    result: dict[str, str] = {}
    for raw in fm_text.splitlines():
        raw = raw.strip()
        if not raw or raw.startswith("#"):
            continue
        if ":" not in raw:
            continue
        key, _, val = raw.partition(":")
        result[key.strip()] = val.strip().strip('"').strip("'")
    return result


def _to_json(obj: dict) -> str:
    """Pretty-print a dict as JSON with 2-space indent and trailing newline."""
    return json.dumps(obj, indent=2) + "\n"


@cache
def _load_marketplace_toml() -> dict:
    """Load and cache src/.metadata-MARKETPLACE.toml."""
    with open(MARKETPLACE_TOML, "rb") as f:
        return tomllib.load(f)


def _marketplace_version() -> str:
    """Read the marketplace version from the marketplace metadata file."""
    return _load_marketplace_toml()["marketplace"]["version"]


def _marketplace_author() -> dict:
    """Build author dict (name + url) from the marketplace metadata file."""
    mp = _load_marketplace_toml()
    return {"name": mp["owner"]["name"], "url": mp["owner"]["url"]}


def _marketplace_name() -> str:
    """Read the marketplace name from the marketplace metadata file.

    This is the string after the ``@`` in
    ``claude plugin install <plugin>@<marketplace>``. Single source of
    truth in src/.metadata-MARKETPLACE.toml. Written into the top-level
    ``.claude-plugin/marketplace.json`` ``name`` field by
    ``_write_marketplace_json`` in ``scripts/generate_manifest.py``.
    See docs/ARCHITECTURE.md ("The name chain").
    """
    return _load_marketplace_toml()["marketplace"]["name"]


def _marketplace_description() -> str:
    """Read the marketplace description from the marketplace metadata file.

        """
    return _load_marketplace_toml()["marketplace"]["description"]


def write_plugin_json(target_dir: Path, plugin_json: dict) -> None:
    """Write plugin.json under target_dir/.claude-plugin/plugin.json.

    Creates the .claude-plugin/ subdirectory if it doesn't exist.

    Uses ``newline=""`` so the embedded ``\\n`` line endings produced by
    ``_to_json`` are written verbatim on every platform (without this,
    Python on Windows translates ``\\n`` to ``\\r\\n`` and breaks our
    byte-identity drift check against LF-committed files).
    """
    plugin_subdir = target_dir / ".claude-plugin"
    plugin_subdir.mkdir(parents=True, exist_ok=True)
    (plugin_subdir / "plugin.json").write_text(
        _to_json(plugin_json), encoding="utf-8", newline=""
    )

def skill_components(plugin_dir: Path) -> list[dict]:
    """Enumerate a skill plugin's components: [{name, description, dir}].

    Solo layout yields one entry with ``dir=None`` (the plugin dir itself is
    the component); multi layout yields one entry per ``skills/<dir>/SKILL.md``
    with ``dir`` set to the component folder name. Shared by the source
    validator (naming rules) and the catalog generator (invocation tables).
    """
    out: list[dict] = []
    root = plugin_dir / "SKILL.md"
    if root.exists():
        fm = _frontmatter(root)
        out.append({
            "name": fm.get("name") or plugin_dir.name,
            "description": fm.get("description") or "",
            "dir": None,
        })
    sub = plugin_dir / "skills"
    if sub.is_dir():
        for d in sorted(sub.iterdir()):
            sk = d / "SKILL.md"
            if sk.exists():
                fm = _frontmatter(sk)
                out.append({
                    "name": fm.get("name") or d.name,
                    "description": fm.get("description") or "",
                    "dir": d.name,
                })
    return out


def _marketplace_repo_slug() -> str:
    """``<owner>/<repo>`` from the metadata repository URL (or the full URL).

    ``claude plugin marketplace add`` accepts the GitHub shortform; when the
    repository URL is not a github.com URL, fall back to the URL itself.
    """
    url = _load_marketplace_toml().get("repository", {}).get("url", "")
    m = re.match(r"https?://github\.com/([^/]+/[^/]+?)(?:\.git)?/?$", url)
    return m.group(1) if m else url


def _marketplace_display_name() -> str:
    """Human-facing marketplace title (falls back to the identity name)."""
    mp = _load_marketplace_toml().get("marketplace", {})
    return mp.get("display_name") or mp.get("name", "Marketplace")

