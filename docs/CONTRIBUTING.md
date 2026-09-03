---
date: 2026-07-25
purpose: the one-folder contribution contract, local gate, conventions
status: live
---

# Contributing

The contract: **you touch `src/` only; CI owns everything generated.** A contribution is a capability folder and nothing else — no manifest edits, no generator runs, no version bumps.

## Capability types

Each capability type has its own source folder and format guide under [`docs/capabilities/`](capabilities/) — one umbrella, one file per type; future types land as sibling rows here and sibling files there.

| Type | Contribute into | Format guide | Status |
|---|---|---|---|
| **Skills** | `src/skills/<name>/` | [`capabilities/skills.md`](capabilities/skills.md) | shipping |
| Agents, hooks, MCP servers, … | — | future siblings in `docs/capabilities/` | planned — [tracked issues](https://github.com/DgxSparkLabs/marketplace-template/issues/18) |

## Prerequisites

- [`uv`](https://docs.astral.sh/uv/) if you want to run the local gate (macOS/Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh` · Windows: `irm https://astral.sh/uv/install.ps1 | iex`)
- The `claude` CLI if you want the final validate step locally (optional — CI runs it regardless)

## Adding a skill

Full format reference: [`capabilities/skills.md`](capabilities/skills.md). Quick version:

1. Create the folder — scaffold (`uv run scripts/new_construct.py skill my-skill`) or by hand:
   - **Solo layout**: `src/skills/my-plugin/SKILL.md` — frontmatter `description:` required; `name:` optional (defaults to the folder name). The folder names the *plugin*; `name:` names the skill, and the generator publishes it as `skills/<name>/SKILL.md`
   - **Multi layout**: `src/skills/my-plugin/skills/<skill-name>/SKILL.md` per skill, plus a one-liner in `src/skills/my-plugin/.metadata-SKILL.toml` (`description = "..."` — the only key the generator reads; anything else, or any source `.claude-plugin/` directory, fails validation per [hygiene/metadata-keys](../_generated/LINTING_RULES.md#hygienemetadata-keys); without the file the plugin description falls back to the folder name)
2. Follow the naming rules — the full, generated list with rationale and a real captured failure per rule is [`_generated/LINTING_RULES.md`](../_generated/LINTING_RULES.md); the short version: kebab-case everywhere, folder name ≤ 32 chars, in the multi layout, a skill folder's name must equal its frontmatter `name:` when one is set ([hygiene/folder-matches-name](../_generated/LINTING_RULES.md#hygienefolder-matches-name)).
3. Commit and push / open a PR. That's it — same-repo PRs and pushes to main get manifests regenerated and committed by `regen-bot`; fork PRs are checked by the drift gate (run `uv run scripts/generate_manifest.py` and commit the output, or use `scripts/regen.sh`/`.ps1`).

## The local gate (optional but recommended)

```bash
uv run scripts/tasks.py verify
```

Runs, in order: `lint.py` (structure + naming standard) → drift check → the test suites (`test_marketplace`, `test_tooling` — with a nonzero-test-count assertion) → `claude plugin validate ./`. All must pass. CI runs the same steps split across `ci.yml` (validate → drift → suites) and `compat-validate.yml` (`claude plugin validate`); `tests/run-ci-local.sh` replays the CI workflow locally via act if you want the exact workflow bytes.

## Conventions

- Every document with headings carries a table of contents, and every heading is followed immediately by a link back to it (`[↑ Table of contents](#table-of-contents)`) — the generated catalog is the reference implementation.
- kebab-case names; Python is PEP 723 + `uv run` (never `pip`); shell scripts use `set -euo pipefail`.
- PR-only to `main`; feature branches push freely.
- No AI co-author attribution in commits.
- Never hand-edit anything under `_generated/` (including the generated catalog doc) or `.claude-plugin/` — regenerated from scratch every run.
- After fixing any bug worth remembering, record it in the fixing PR/issue so the next person can find it by search.
- Install the pre-push hook once: `pre-commit install` (runs `lint.py` on `src/` before each commit).

## Something broke?

Symptom-indexed fixes for the common issues: [`troubleshooting/`](troubleshooting/).

## Session-local ignores

Working files that belong to your machine, not the template (agent scratch dirs, research caches), do not go in the tracked `.gitignore`. Use a repo-local excludes file instead:

```bash
git config --local core.excludesFile .mygitignore
printf '.mygitignore
<your-dirs>/
' > .mygitignore
```

`.mygitignore` ignores itself, so it never shows up in `git status` and never ships to forks.

## Testing notes

- `tests/test_marketplace.py` — source layout, generated-output invariants, naming composition (`TestGeneratedPlugins.test_individual_plugin_name_is_unique_brand_namespace`), drift, secrets scan.
- `tests/test_tooling.py` — `lint.py` (including adversarial fixtures per rule) and the scaffolder.
- Verify a new guard by making it FAIL once — a guard only ever seen green proves nothing (e.g. `TestDriftGateReadOnly` injects drift and asserts the check fails twice).
