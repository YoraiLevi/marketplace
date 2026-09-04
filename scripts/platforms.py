#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
platforms.py — Platform classes implementing the Platform protocol.

Claude Code and OMP (Oh My Pi) are supported. After the skills-only,
Claude-first scope-down (issue #18) the Platform protocol is retained so each
added platform is a new class + registry entry, not a redesign. OMP reads the
same catalog (issue #67); it needs only a sibling top-level manifest.

Each class encapsulates:
  - name             : platform identifier
  - marketplace_json : path of this platform's top-level marketplace.json
  - supports         : set of Construct CLASSES this platform handles
  - marketplace_manifest(entries) -> dict : shape the top-level
      marketplace.json dict from the sorted plugin entries.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from constructs import (
    Construct,
    SkillConstruct,
)

from utils import (
    MARKETPLACE_JSON,
    OMP_MARKETPLACE_JSON,
    _marketplace_author,
    _marketplace_description,
    _marketplace_name,
    _marketplace_version,
)


def _omp_entry(entry: dict) -> dict:
    """Project a shared marketplace entry into OMP's documented entry shape.

    OMP documents plugin-entry author as {name, email?}; drop the Claude-only
    author.url. Every other field (name, source, description, version,
    category) is shared core and passes through unchanged.
    """
    shaped = dict(entry)  # preserve key order for stable JSON bytes
    shaped["author"] = {"name": entry["author"]["name"]}
    return shaped


class Platform(Protocol):
    """An AI coding platform we generate a top-level marketplace.json for."""

    name: str                       # e.g. "claude-code"
    marketplace_json: Path          # this platform's top-level marketplace.json path
    supports: set[type[Construct]]  # Construct CLASSES this platform lists

    def marketplace_manifest(self, entries: list[dict]) -> dict:
        """Shape the top-level marketplace.json dict from sorted plugin entries."""
        ...


class ClaudeCodePlatform:
    """Canonical platform reading .claude-plugin/marketplace.json.

    Claude Code reads .claude-plugin/marketplace.json (top-level manifest) and
    per-plugin .claude-plugin/plugin.json files directly; the generator writes
    both in its main phases. marketplace_manifest shapes Claude's documented
    top-level manifest: a top-level description and owner {name, url}.
    """

    name = "claude-code"
    marketplace_json = MARKETPLACE_JSON
    supports: set[type[Construct]] = {
        SkillConstruct,
    }

    def marketplace_manifest(self, entries: list[dict]) -> dict:
        # Claude Code's documented shape: top-level description, owner {name, url}.
        return {
            "name": _marketplace_name(),
            "owner": _marketplace_author(),
            "description": _marketplace_description(),
            "plugins": entries,
        }


class OmpPlatform:
    """Oh My Pi (the ``omp`` CLI) — first-party marketplace emission target.

    OMP's marketplace client reads ``.omp-plugin/marketplace.json`` first and
    falls back to ``.claude-plugin/marketplace.json``; its per-plugin manifest
    reader prefers ``.omp-plugin/plugin.json`` and falls back to
    ``.claude-plugin/plugin.json``. This platform emits OMP's own documented
    manifest shape (marketplace description under ``metadata.description``, owner
    and entry author limited to the documented ``{name, email?}`` keys), not a
    copy of the Claude manifest. Its entries point at the same
    ``_generated/claude-code/<plugin>`` dirs Claude uses, and OMP reads those
    dirs' ``.claude-plugin/plugin.json`` via its documented fallback, so no
    per-plugin ``.omp-plugin/plugin.json`` is emitted. OMP does not document a
    standalone per-plugin manifest schema. Verified against ``omp`` 18.1.6
    (issue #67); format relationship and divergence policy in
    ``docs/platforms/omp.md``.
    """

    name = "omp"
    marketplace_json = OMP_MARKETPLACE_JSON
    supports: set[type[Construct]] = {
        SkillConstruct,
    }

    def marketplace_manifest(self, entries: list[dict]) -> dict:
        # OMP-native shape (omp 18.1.6): marketplace description under
        # metadata.description, marketplace metadata version under
        # metadata.version, owner limited to the documented {name, email?} keys
        # (no url), and each entry's author reduced to the documented
        # {name, email?} shape. OMP still reads each plugin's manifest from
        # .claude-plugin/plugin.json via its documented fallback, so no
        # per-plugin .omp-plugin/plugin.json is emitted.
        return {
            "name": _marketplace_name(),
            "owner": {"name": _marketplace_author()["name"]},
            "metadata": {
                "description": _marketplace_description(),
                "version": _marketplace_version(),
            },
            "plugins": [_omp_entry(e) for e in entries],
        }


# ─── Registry ────────────────────────────────────────────────────────────────

PLATFORMS: dict[str, Platform] = {
    "claude-code": ClaudeCodePlatform(),
    "omp": OmpPlatform(),
}
