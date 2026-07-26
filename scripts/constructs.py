#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
constructs.py — Construct classes implementing the Construct protocol.

SkillConstruct is the only construct after the skills-only scope-down
(issue #18); the protocol + registry pattern is retained so re-expansion
(issues #20-#27) is a new class + registry entry.

Each class encapsulates:
  - prefix           : plugin name prefix (e.g., "skill")
  - source_directory : source tree root (e.g., Path("skills/"))
  - category         : marketplace.json category tag
  - build_plugin_json: produce plugin.json content dict (no I/O)
  - emit             : write the full plugin to target_dir (all I/O)

Registry:
  CONSTRUCTS: dict[str, Construct]  — single source of truth
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Protocol, runtime_checkable

from utils import (
    REPO_ROOT,
    _frontmatter,
    _is_candidate_subdir,
    _load_plugin_json,
    _marketplace_author,
    _marketplace_name,
    _marketplace_repo_slug,
    _marketplace_version,
    _read_source_plugin_description,
    skill_components,
    write_plugin_json,
)


@runtime_checkable
class Construct(Protocol):
    """A Claude Code plugin construct type."""

    prefix: str           # e.g., "skill"
    source_directory: Path  # e.g., Path("skills/") — relative to repo root
    category: str         # marketplace.json category tag (often == prefix)

    def build_plugin_json(self, name: str) -> dict:
        """Build the plugin.json content dict. Pure — no I/O."""
        ...

    def emit(self, name: str, target_dir: Path) -> None:
        """Write the full plugin to target_dir.

        Includes: copy source content, generate construct-specific
        artifacts (e.g., activate.sh for rules), and write
        .claude-plugin/plugin.json. Does ALL I/O for this instance.
        """
        ...


# ─── shared base helper ──────────────────────────────────────────────────────

def _base_plugin_shape(construct: Construct, name: str) -> dict:
    """Common plugin.json fields shared by all construct types.

    The ``name`` field is the **Claude plugin identifier** — unique per
    plugin, composed as ``<brand>-<construct.prefix>-<source-dir-name>``
    (e.g. ``dgxsparklabs-skill-example``). ``<brand>`` is derived from
    ``.metadata-MARKETPLACE.toml`` ``name`` by stripping the trailing ``-marketplace``
    suffix. Slash invocations follow the same pattern
    ``/<brand>-<construct.prefix>-<plugin>:<component>`` —
    e.g. ``/dgxsparklabs-skill-example:notebook``.

    The marketplace-entry name (what the operator types at install:
    ``claude plugin install skill-example@dgxsparklabs-marketplace``) is
    a separate, unprefixed identifier composed by ``_make_marketplace_entry``
    in ``scripts/generate_manifest.py`` from ``plugin_dir.name``
    (``<construct.prefix>-<source-dir-name>``).

    History: an earlier attempt (Path A, ``d641f92``, 2026-05-27) used a
    shared ``<brand>-<construct.category>`` here so multiple plugins of one
    construct shared a slash namespace; ``claude plugin details`` then
    collapsed to a single first-installed-wins view of the components.
    Path A was reverted on 2026-05-28 per
    ``the project-memory branch (multi-instance PLAN)``.
    """
    mp_name = _marketplace_name()
    brand = mp_name.removesuffix("-marketplace") if mp_name.endswith("-marketplace") else mp_name
    return {
        "name": f"{brand}-{construct.prefix}-{name}",
        "version": _marketplace_version(),
        "author": _marketplace_author(),
    }


# ─── Construct implementations ────────────────────────────────────────────────

class SkillConstruct:
    # `prefix` controls both the INSTALL-time marketplace name
    # (e.g. `skill-example` in `claude plugin install skill-example@...`)
    # and the plugin.json `name` (composed in `_base_plugin_shape` as
    # `<brand>-<prefix>-<source-dir>`, e.g. `dgxsparklabs-skill-example`).
    # The slash form is `/dgxsparklabs-skill-example:<frontmatter-name>`.
    #
    # Two source layouts are supported per plugin (build_plugin_json picks):
    #   1. Solo:  skills/<plugin>/SKILL.md                       → skills: ["./"]
    #   2. Multi: skills/<plugin>/skills/<a>/SKILL.md
    #             skills/<plugin>/skills/<b>/SKILL.md  ...        → skills: ["./skills/"]
    # The plugin-level description for the multi layout is operator-authored
    # at skills/<plugin>/.metadata-SKILL.toml (read by
    # _read_source_plugin_description), since there's no single SKILL.md to
    # pull it from.
    prefix = "skill"
    source_directory = REPO_ROOT / "src" / "skills"
    category = "skill"

    def build_plugin_json(self, name: str) -> dict:
        base = _base_plugin_shape(self, name)
        src = self.source_directory / name
        root_skill = src / "SKILL.md"
        skills_subdir = src / "skills"

        has_root = root_skill.exists()
        # ``_is_candidate_subdir`` filters out junk dirs (``__pycache__``,
        # hidden dirs) so a stray ``skills/__pycache__/SKILL.md`` doesn't
        # falsely flip ``has_subdir=True`` and route a solo plugin into
        # multi-layout emission.
        has_subdir = skills_subdir.is_dir() and any(
            (d / "SKILL.md").exists()
            for d in skills_subdir.iterdir()
            if _is_candidate_subdir(d)
        )

        if has_root and has_subdir:
            raise ValueError(
                f"Source plugin {src} contains BOTH a root SKILL.md AND a "
                f"skills/ subdir with skill children. Pick one layout: either "
                f"move the root SKILL.md into skills/<name>/ or remove the "
                f"skills/ subdir."
            )
        if not has_root and not has_subdir:
            raise ValueError(
                f"Source plugin {src} contains neither a root SKILL.md "
                f"(single-skill layout) nor a skills/<name>/SKILL.md subdir "
                f"(multi-skill layout). Create one or the other."
            )

        # Solo-layout description fallback chain (most specific first):
        #   1. SKILL.md frontmatter ``description:`` — the per-skill tooltip
        #      doubles as a sensible plugin description when there's only one
        #      skill in the plugin.
        #   2. ``<src>/.claude-plugin/plugin.json`` ``description`` — operator-
        #      authored plugin-level one-liner (separate concern but the right
        #      backstop when frontmatter is absent).
        #   3. Dir name — last resort, handled inside the helper.
        # Multi-layout has no single SKILL.md, so it goes straight to the
        # plugin-level description (which is the right shape for marketplace
        # listing when the plugin ships multiple skills).
        if has_root:
            fm = _frontmatter(root_skill)
            base["description"] = (
                fm.get("description") or _read_source_plugin_description(src, name)
            )
        else:
            base["description"] = _read_source_plugin_description(src, name)
        base["skills"] = ["./"] if has_root else ["./skills/"]
        base["keywords"] = ["skill", name]
        return base

    def emit(self, name: str, target_dir: Path) -> None:
        # Copy entire source tree (SKILL.md or skills/<n>/SKILL.md, plus
        # any scripts/ references/ etc.)
        shutil.copytree(
            self.source_directory / name,
            target_dir,
            dirs_exist_ok=True,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".metadata-*"),
        )
        # Write plugin.json under .claude-plugin/ (overrides any source copy)
        write_plugin_json(target_dir, self.build_plugin_json(name))


    def catalog_section(self, name: str) -> str:
        """Render this plugin's section of the generated catalog doc.

        Heading contract (_generated/CATALOG_AND_INSTALLATION_INSTRUCTIONS.md):
        ``###`` plugin · ``####`` platform · ``#####`` install method /
        Invocation · ``######`` Deletion per method. Claude Code is the only
        platform today; a revived platform (issues #28-#36) adds a sibling
        ``####`` block here. All commands render with THIS marketplace's
        identity so every fork's catalog is copy-pasteable as-is.
        """
        mp = _marketplace_name()
        brand = mp.removesuffix("-marketplace") if mp.endswith("-marketplace") else mp
        slug = _marketplace_repo_slug()
        entry = f"{self.prefix}-{name}"
        namespace = f"{brand}-{self.prefix}-{name}"
        src = self.source_directory / name
        comps = skill_components(src)
        desc = self.build_plugin_json(name)["description"]
        solo = any(c["dir"] is None for c in comps)
        L: list[str] = []
        A = L.append
        A(f"### {entry}")
        A("")
        A(desc)
        A("")
        A("#### Claude Code")
        A("")
        A("##### Plugin installation")
        A("")
        A("```bash")
        A(f"claude plugin marketplace add {slug}        # once per machine")
        A(f"claude plugin install {entry}@{mp} --scope user")
        A("```")
        A("")
        A("Scopes: `--scope user` (all your projects) | `--scope project` "
          "(shared with your team via `.claude/settings.json`).")
        A("")
        A("> **Warning:** `--scope project` writes `.claude/settings.json` in the "
          "directory you run it from - run it from the root of the project you "
          "mean to configure.")
        A("")
        A("###### Deletion")
        A("")
        A("```bash")
        A(f"claude plugin uninstall {entry} --scope user")
        A("```")
        A("")
        A("> **Warning:** uninstall requires the same `--scope` the install used; "
          "without it the CLI reports the plugin as enabled in another scope.")
        A("")
        A("##### Directly")
        A("")
        A("Copy the skill source into your personal skills directory - no "
          "marketplace registration, no updates:")
        A("")
        A("```bash")
        A(f"git clone https://github.com/{slug} /tmp/mp" if "/" in slug and not slug.startswith("http") else f"git clone {slug} /tmp/mp")
        if solo:
            A(f"cp -r /tmp/mp/src/skills/{name} ~/.claude/skills/{name}")
        else:
            for c in comps:
                A(f"cp -r /tmp/mp/src/skills/{name}/skills/{c['dir']} ~/.claude/skills/{c['dir']}")
        A("```")
        A("")
        A("###### Deletion")
        A("")
        A("```bash")
        if solo:
            A(f"rm -rf ~/.claude/skills/{name}")
        else:
            for c in comps:
                A(f"rm -rf ~/.claude/skills/{c['dir']}")
        A("```")
        A("")
        A("##### Invocation")
        A("")
        A("| Component | Description | Slash command | Flat shortcut |")
        A("|---|---|---|---|")
        for c in comps:
            A(f"| {c['name']} | {c['description']} | `/{namespace}:{c['name']}` | `/{c['name']}` |")
        A("")
        A("> **Note:** the flat shortcut resolves only while the component name "
          "is unambiguous across your installed skills; the namespaced form "
          "always works.")
        A("")
        return chr(10).join(L)


# ─── Registry ────────────────────────────────────────────────────────────────

CONSTRUCTS: dict[str, Construct] = {
    "skill": SkillConstruct(),
}
