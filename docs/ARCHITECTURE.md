---
date: 2026-07-25
purpose: generator architecture, protocols, generation phases (skills-only)
status: live
---

# Architecture

The generator turns skill sources under `src/skills/` into Claude Code install artifacts. Two protocols — `Construct` and `Platform` — encapsulate per-type and per-platform behavior; a thin orchestrator (`scripts/generate_manifest.py`) runs the phases in order. After the #18 scope-down there is one construct (`SkillConstruct`) and one platform (`ClaudeCodePlatform`), but the protocol + registry pattern is retained so a re-expansion (issues #20–#36) is a new class + registry entry, not a redesign.

## Sources of truth vs. generated

Everything in the repo is one of two things; nothing is both.

**Humans edit (source intent):**

- `src/.metadata-MARKETPLACE.toml` — marketplace identity (name, owner, repo URL, description). The one file a forker must edit.
- `src/skills/<plugin>/` — skill content: `SKILL.md` (solo layout) or `skills/<name>/SKILL.md` (multi layout). Forks own this tree outright — adding, editing, and deleting anything (the shipped examples included) is supported; nothing in the machinery assumes a specific skill exists.
- `src/skills/<plugin>/.metadata-SKILL.toml` — optional plugin-level metadata; required for the multi layout, where no single SKILL.md can supply the marketplace-listing `description`. Only `description` is read (rule R6).

`.metadata-*.toml` is the convention for all operator-edited metadata: dot-prefixed like `.env` — a fork edits these files and ships its own values. Source trees never contain `.claude-plugin/`; that shape belongs exclusively to generated output (R6 rejects a source `.claude-plugin/` outright).

**Generator owns (regenerated from scratch every run — hand-edits are lost):**

- `_generated/claude-code/<plugin>/` — the installable plugins, platform-namespaced. Claude Code is the only platform today; a revived platform (issues #28–#36) gets a sibling `_generated/<platform>/` and never mixes.
- `.claude-plugin/marketplace.json` — the manifest `claude plugin marketplace add` reads.
- `docs/INVENTORY.md` — the authoritative plugin list.

**Neither (plumbing, hand-maintained but not content):** `scripts/` (generator, validators, task runner), `tests/`, `.github/` (CI), `docs/` prose.
- In CI, `regen-bot.yml` runs the generator and commits the result (identity `marketplace-generator`) on pushes to main and same-repo PRs; `ci.yml`'s `--check` drift gate rejects any tree where regeneration is not a no-op.

## The generation phases

| Phase | Output | Notes |
|---|---|---|
| 1 | `_generated/claude-code/skill-<name>/` + its `.claude-plugin/plugin.json` | one per source plugin; `Construct.emit` copies content, composes plugin.json |
| 5 | `.claude-plugin/marketplace.json` | from in-memory entries, sorted for deterministic diffs |
| 7 | `docs/INVENTORY.md` | generated authoritative plugin list; drift-checked like the manifests |

Phase numbering is deliberately sparse: the retired phases (1.5/2a/3/4/4.5/5.5/6 — per-platform manifests, bundles, mirrors) emitted per-platform manifests, bundles, and mirrors for removed capabilities — see git history and #18's child issues.

## The name chain (see issue #19 for the enforced standard)

`src/.metadata-MARKETPLACE.toml` `name` → marketplace identity (after `@` in install commands); minus its `-marketplace` suffix → the **brand**. Install name = `skill-<srcdir>` (`generate_manifest.py`, marketplace entry). Slash namespace = `<brand>-skill-<srcdir>` (`constructs.py`, `_base_plugin_shape`). Component name = SKILL.md frontmatter `name:`. Enforcement: `scripts/validate_source.py` (rules N1/N2/N4/R6/R8 on sources) + `tests/test_marketplace.py` `TestGeneratedPlugins.test_individual_plugin_name_is_unique_brand_namespace` (N3/N5 on generated output).

## Verification chain

`uv run scripts/tasks.py verify` = `validate_source.py` → `--check` drift gate → test suites (invoked via `-m unittest` with a nonzero-test-count assertion — see the `project-memory` branch (PITFALLS, "vacuous green")) → `claude plugin validate ./`. CI mirrors the same steps; compat workflows additionally exercise registration → install → listing against the real CLI.

## How to extend

- **New skill**: drop a folder — no code.
- **New construct type / platform** (re-expansion): new class implementing the protocol + registry entry; follow the construct/platform re-expansion issue for that capability and pass the #19 naming gate before shipping.
