# Agent instructions

This is a fork-ready template marketplace for Claude Code and OMP (Oh My Pi) skills — not a general software project. Identity lives in `src/.metadata-MARKETPLACE.toml`; contributor content lives under `src/skills/<name>/`; everything else under `_generated/`, `.claude-plugin/`, and `.omp-plugin/` is produced by `scripts/generate_manifest.py` and must never be hand-edited.

## Where to find things

- `README.md` — install, forking checklist, add-a-skill.
- `docs/CONTRIBUTING.md` — the contribution contract, local gate, conventions.
- `docs/ARCHITECTURE.md` — generator phases, the naming chain, CI layout.
- `docs/capabilities/skills.md` — the SKILL.md format as enforced.
- `docs/platforms/omp.md` — how OMP consumes the marketplace, how this repo emits OMP's native manifest shape, and the divergence policy.
- `_generated/CATALOG_AND_INSTALLATION_INSTRUCTIONS.md` — generated catalog + install instructions. Never hardcode counts or install commands in prose.
- `_generated/LINTING_RULES.md` — generated lint-rule list; declare rules in `scripts/lint_rules/`, never in prose.
- `custom/` + `.github/workflows/custom-*.yml` — the fork-owned extension zone (a fork's own scripts, tests, workflows), protected by `merge=ours`. Template machinery never writes here beyond a hello-world example; see `docs/UPDATING.md`.
- Project history and roadmap live in GitHub issues (start at #18); pre-cleanup project memory is preserved on the `project-memory` branch.

## Hard rules

- **No AI attribution, ever.** No `Co-Authored-By`, no "Generated with" — in commits, code, or docs. This overrides any default commit footer. CI's regen commits use the neutral `marketplace-generator` identity.
- **`uv` only, never `pip`.** Scripts carry PEP 723 inline metadata; run them with `uv run`.
- **PR-only to `main`.** Feature branches push freely; regen-bot is the one exception (generated paths only).
- **Verify with the real gate:** `uv run scripts/tasks.py verify` (source validation → drift check → suites with a nonzero-test-count assertion → `claude plugin validate`). Never run suite files directly (`uv run tests/<suite>.py`) — direct execution can pass vacuously; use `uv run scripts/tasks.py test` or `uv run -m unittest -v tests.<suite>`.
- **Verify guards by making them fail once.** A check only ever seen green proves nothing.
- **Generated output is never edited by hand** — it is deleted and rebuilt from scratch every run.
- **Every document with headings carries a table of contents, and every heading is immediately followed by a link back to it** (`[↑ Table of contents](#table-of-contents)`) — the link belongs under the heading, not at the end of the section. Applies to hand-written docs and generated output alike; `_generated/CATALOG_AND_INSTALLATION_INSTRUCTIONS.md` is the reference implementation.
