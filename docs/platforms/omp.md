---
date: 2026-09-04
purpose: how Oh My Pi (OMP) consumes this marketplace, how the generator emits OMP's own manifest instead of copying the Claude Code manifest, and what to do when the two formats diverge
status: live
spec_checked: 2026-09-04 against omp 18.1.6 bundled docs (marketplace.md, skills/authoring-marketplaces.md, plugin-manager-installer-plumbing.md) and the Claude Code docs linked in section 6
---

# Oh My Pi (OMP) as a marketplace platform

This page is for a maintainer deciding whether a change on the OMP side needs a change in this repository. It explains what OMP reads from the repository, how the generator emits OMP's own manifest instead of copying the Claude Code manifest, where the two formats agree and differ, and what to do when they diverge. The code lives in `scripts/platforms.py` and in Phase 5 of `scripts/generate_manifest.py`. Issue #67 and PR #68 hold the history.

Each factual claim below cites its source: an `omp://` path names a page in the omp 18.1.6 documentation bundle, a URL names a Claude Code doc, and a code path names the file that implements the behaviour.

## Table of contents

- [1. What OMP reads from this repository](#1-what-omp-reads-from-this-repository)
- [2. How the generator emits OMP's native shape](#2-how-the-generator-emits-omps-native-shape)
- [3. Differences the repository does not yet use](#3-differences-the-repository-does-not-yet-use)
- [4. Evidence](#4-evidence)
- [5. Divergence policy](#5-divergence-policy)
- [6. Sources](#6-sources)

## 1. What OMP reads from this repository

[↑ Table of contents](#table-of-contents)

OMP reads a marketplace in two steps. First it reads the catalog, then it reads one plugin manifest per installed plugin.

- **Catalog.** OMP reads `.omp-plugin/marketplace.json`. When that file is absent, it falls back to `.claude-plugin/marketplace.json` (`omp://marketplace.md` L96). This repository ships both files, so OMP reads its own copy and Claude Code reads the Claude copy.
- **Plugin manifest.** For each entry, OMP resolves the `source` directory and reads `.omp-plugin/plugin.json`, falling back to `.claude-plugin/plugin.json` (`omp://skills/authoring-marketplaces.md` L212). This repository ships only `.claude-plugin/plugin.json` under `_generated/claude-code/<plugin>/`, so OMP reads it through that fallback. OMP does not document a standalone `.omp-plugin/plugin.json` format (`omp://skills/authoring-marketplaces.md` L195-212), so the repository does not invent one.
- **Skills.** Both tools find skills through the manifest's `skills` list. The repository sets `skills: ["./skills/"]` so a published plugin never points at its own root (`scripts/constructs.py`, `SkillConstruct.build_plugin_json`).
- **Install scope.** OMP installs at user or project scope, and a project install shadows a user install with the same id (`omp://marketplace.md`; `omp://plugin-manager-installer-plumbing.md`). Claude Code records enablement in `.claude/settings.json` per scope.
- **Commands.** The generator writes the OMP register, install, and remove commands into `_generated/CATALOG_AND_INSTALLATION_INSTRUCTIONS.md`. This page does not repeat them.

## 2. How the generator emits OMP's native shape

[↑ Table of contents](#table-of-contents)

Phase 5 of `scripts/generate_manifest.py` builds one list of plugin entries, then asks each platform to shape its own top-level manifest through `marketplace_manifest`. The two files are therefore not byte-identical. Each carries the shape its own tool documents.

The table shows the emitted fields and their sources.

| Field | `.claude-plugin/marketplace.json` (Claude Code) | `.omp-plugin/marketplace.json` (OMP) |
|---|---|---|
| Marketplace description | Top-level `description` (Claude plugin-marketplaces, optional fields) | `metadata.description` (`omp://marketplace.md` L131) |
| Marketplace version | Not emitted | `metadata.version` (`omp://marketplace.md` L131) |
| `owner` | `{name, url}` (Claude documents `owner.url`) | `{name}` (OMP documents `{name, email?}`; no `owner.url`) |
| Plugin entry `author` | `{name, url}` | `{name}` (OMP documents `{name, email?}`; no `author.url`) |
| Plugin entry `name`, `source`, `description`, `version`, `category` | Shared, identical in both files | Shared, identical in both files |

Both files list the same plugins pointing at the same `_generated/claude-code/<plugin>/` directories, so both tools install the same set. They differ only in fields that one tool documents and the other does not. OMP would tolerate the Claude-only keys as unused extras (`omp://skills/authoring-marketplaces.md` L60), but emitting OMP's own shape is what makes OMP a first-party target rather than a copy.

## 3. Differences the repository does not yet use

[↑ Table of contents](#table-of-contents)

The two standards differ in more places than the generator exercises. Each difference below needs a deliberate decision before the generator relies on it.

- **Source types.** OMP parses `npm` sources but rejects them at install; Claude Code installs them and accepts a `registry` field. Claude Code also documents `archive` and `command` sources that OMP does not. Both support `github`, `url`, and `git-subdir` with `ref` or `sha` (`omp://marketplace.md` L156-209).
- **`metadata.pluginRoot`.** OMP prepends it to relative `./` sources; Claude Code resolves bare names under it and ignores it for `./` sources. This repository emits neither `pluginRoot` nor bare sources.
- **Entry component fields.** OMP treats `strict`, `commands`, `agents`, `hooks`, and `mcpServers` on a catalog entry as unused metadata, and it materialises `lspServers` and `dapAdapters` at install. Claude Code has `lspServers` but no `dapAdapters` and treats several of these fields as functional.
- **Naming caps.** OMP caps a name at 64 characters and `name@marketplace` at 128 characters; the Claude Code schema states no cap.

## 4. Evidence

[↑ Table of contents](#table-of-contents)

- **Specification.** Sections 2 and 3 come from the omp 18.1.6 documentation bundle and the Claude Code docs listed in section 6, read on the `spec_checked` date.
- **Live install.** An isolated omp 18.1.6 session, run against a temporary user profile so no real `~/.omp` state changed, registered this repository from `.omp-plugin/marketplace.json`, installed plugins at project scope, and found every skill listed in the generated catalog (issue #67).
- **Guards.** `tests/test_omp.py` checks the native shape, the shared plugin core, the deliberate difference from the Claude manifest, and per-entry resolution through the `.claude-plugin/plugin.json` fallback. The `--check` drift gate compares `.omp-plugin/` byte-for-byte, like every other generated path (`scripts/generate_manifest.py`, `_check_drift`).

## 5. Divergence policy

[↑ Table of contents](#table-of-contents)

Both files share a plugin core and differ only where the standards document different shapes. When one tool needs a field the other does not read, follow these steps.

1. **Shape it at the platform.** Add the field to that platform's `marketplace_manifest` in `scripts/platforms.py`, and to `_omp_entry` for a per-entry OMP field. This is the "new class plus registry entry" model from issue #18, not a redesign. A per-plugin OMP manifest is a larger change, because OMP documents no `.omp-plugin/plugin.json` format today.
2. **Keep the shared-core check.** `tests/test_omp.py::test_shares_plugin_core_with_claude` asserts the same plugin-name set and equal `source`, `description`, `version`, `category`, and `author.name` per entry. Add a per-platform assertion for the new field rather than weakening this check.
3. **Keep the anti-copy check.** `test_diverges_from_claude` fails if the OMP manifest becomes a byte copy of the Claude manifest.
4. **Record it.** Add the field to the section 2 table with its citation, and update `spec_checked`.

## 6. Sources

[↑ Table of contents](#table-of-contents)

The omp documentation ships with the `omp` package; an omp session opens each path directly. Read on 2026-09-04 against omp 18.1.6:

- `omp://marketplace.md` (catalog location and format, top-level fields, plugin entry fields, source forms, scopes, naming rules)
- `omp://skills/authoring-marketplaces.md` (schema tables, source types, plugin directory layout, manifest precedence)
- `omp://plugin-manager-installer-plumbing.md` (on-disk model, install symlinks, lock file)

Claude Code documentation, read on 2026-09-04:

- [Plugin marketplaces](https://code.claude.com/docs/en/plugin-marketplaces) (marketplace schema, owner fields, optional fields, source types, file location)
- [Plugins reference](https://code.claude.com/docs/en/plugins-reference) (plugin.json schema, component path fields, version precedence, install scopes)

For symptoms specific to this marketplace, see [troubleshooting](../troubleshooting/).
