---
date: 2026-07-25
purpose: generator architecture, protocols, generation phases (skills-only)
status: live
---

# Architecture

The generator turns skill sources under `src/skills/` into Claude Code and OMP (Oh My Pi) install artifacts. Two protocols — `Construct` and `Platform` — encapsulate per-type and per-platform behavior; a thin orchestrator (`scripts/generate_manifest.py`) runs the phases in order. After the #18 scope-down there is one construct (`SkillConstruct`) and two platforms (`ClaudeCodePlatform` and `OmpPlatform`); the protocol + registry pattern is retained so a re-expansion (issues #20–#36) is a new class + registry entry, not a redesign.

## Sources of truth vs. generated

Every file in the repo has exactly one owner.

**Humans edit (source intent):**

- `src/.metadata-MARKETPLACE.toml` — marketplace identity (name, owner, repo URL, description). The one file a forker must edit.
- `src/skills/<plugin>/` — skill content: `SKILL.md` (solo layout) or `skills/<name>/SKILL.md` (multi layout). Forks own this tree outright — adding, editing, and deleting anything (the shipped examples included) is supported; nothing in the machinery assumes a specific skill exists.
- `src/skills/<plugin>/.metadata-SKILL.toml` — optional plugin-level metadata; required for the multi layout, where no single SKILL.md can supply the marketplace-listing `description`. Only `description` is read ([hygiene/metadata-keys](../_generated/LINTING_RULES.md#hygienemetadata-keys)).

`.metadata-*.toml` is the convention for all operator-edited metadata: dot-prefixed like `.env` — a fork edits these files and ships its own values. Source trees never contain `.claude-plugin/`; that shape belongs exclusively to generated output ([hygiene/no-packaging-in-source](../_generated/LINTING_RULES.md#hygieneno-packaging-in-source) rejects a source `.claude-plugin/` outright).

**Generator owns (regenerated from scratch every run — hand-edits are lost):**

- `_generated/claude-code/<plugin>/` — the installable plugins, platform-namespaced. Claude Code owns this mirror; OMP reuses it (issue #67) and adds only a sibling top-level manifest, so there is no separate OMP plugin tree. A future mirror-based platform (issues #28–#36) gets its own `_generated/<platform>/` and never mixes. Both source layouts converge here on one shape — `skills/<skill-name>/SKILL.md` declared as `skills: ["./skills/"]` — so a published plugin never points at its own root.
- `.claude-plugin/marketplace.json` and `.omp-plugin/marketplace.json` — the top-level manifests `claude plugin marketplace add` and `omp plugin marketplace add` read; one per registered platform, each shaped by its platform's `marketplace_manifest`. They share the plugin entries pointing at the mirror but differ in owner and marketplace-description shape: Claude uses a top-level `description` and `owner.url`; OMP uses `metadata.description` and the documented `{name, email?}` owner shape. OMP reads per-plugin manifests from `.omp-plugin/plugin.json`, falling back to `.claude-plugin/`. The comparison and divergence policy live in [docs/platforms/omp.md](platforms/omp.md).
- `_generated/CATALOG_AND_INSTALLATION_INSTRUCTIONS.md` — the catalog: every plugin, every install/removal path, invocation tables — rendered with this marketplace's identity.
- `_generated/LINTING_RULES.md` — every lint rule this marketplace enforces, rendered from the `scripts/lint_rules/` registry. Each rule owns its check and a mandatory counterexample; `tests/test_marketplace.py` (`TestLintRegistry`) proves every rule reachable by executing that counterexample, so a rule cannot be published as enforced while being dead.

`docs/` now contains ONLY human-authored prose; everything machine-written lives under `_generated/`.

**Neither (plumbing, hand-maintained but not content):** `scripts/` (generator, validators, task runner), `tests/`, `.github/` CI (every workflow except the fork-owned `custom-*.yml`), `docs/` prose.
- In CI, `regen-bot.yml` runs the generator and commits the result (identity `marketplace-generator`) on pushes to main and same-repo PRs; `ci.yml`'s `--check` drift gate rejects any tree where regeneration is not a no-op.

**Fork-owned (a fork's own machinery, never the template's):** `custom/` and `.github/workflows/custom-*.yml` — a fork's scripts, tests, and workflows. Outside `src/` (not published capabilities) and outside the generator/lint scope, yet reserved for the fork and protected by `merge=ours`, so template syncs never touch them; the template ships only a hello-world example in each. See [`docs/UPDATING.md`](UPDATING.md).

## The generation phases

| Phase | Output | Notes |
|---|---|---|
| 1 | `_generated/claude-code/skill-<name>/` + its `.claude-plugin/plugin.json` | one per source plugin; `Construct.emit` copies content, composes plugin.json |
| 5 | `.claude-plugin/marketplace.json` + `.omp-plugin/marketplace.json` | one per platform in `PLATFORMS`, each shaped by its platform's `marketplace_manifest` from in-memory entries, sorted for deterministic diffs |
| 7 | `_generated/CATALOG_AND_INSTALLATION_INSTRUCTIONS.md` | generated catalog + installation instructions; drift-checked like the manifests |
| 8 | `_generated/LINTING_RULES.md` | the lint-rule list, rendered from the `scripts/lint_rules/` registry; drift-checked |

Phase numbering is deliberately sparse: the retired phases (1.5/2a/3/4/4.5/5.5/6 — per-platform manifests, bundles, mirrors) emitted per-platform manifests, bundles, and mirrors for removed capabilities — see git history and #18's child issues.

## The name chain (see issue #19 for the enforced standard)

`src/.metadata-MARKETPLACE.toml` `name` → marketplace identity (after `@` in install commands); minus its `-marketplace` suffix → the **brand**. Install name = `skill-<srcdir>` (`generate_manifest.py`, marketplace entry). Slash namespace = `<brand>-skill-<srcdir>` (`constructs.py`, `_base_plugin_shape`). Component name = SKILL.md frontmatter `name:`. Enforcement: `scripts/lint.py` — every rule, its rationale, and a captured example failure are in [`_generated/LINTING_RULES.md`](../_generated/LINTING_RULES.md). `TestGeneratedPlugins.test_individual_plugin_name_is_unique_brand_namespace` double-covers the composed-name invariant.

## Verification chain

`uv run scripts/tasks.py verify` = `lint.py` → `--check` drift gate → test suites (invoked via `-m unittest` with a nonzero-test-count assertion — see the `project-memory` branch (PITFALLS, "vacuous green")) → `claude plugin validate ./`. CI mirrors the same steps; compat workflows additionally exercise registration → install → listing against the real CLI.

## How to extend

- **New skill**: drop a folder — no code.
- **New construct type / platform** (re-expansion): new class implementing the protocol + registry entry, plus a `scripts/lint_rules/` topic module for its construct-specific rules (universal rules cover it automatically via `constructs=ALL`). Before starting, check the candidate for **upstream absorption** — a capability folded into another capability has no surfaces of its own to standardise (see issue #20: slash commands were absorbed into skills) — then pass the #19 naming gate before shipping.
