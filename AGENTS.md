# Agent instructions

This is a fork-ready template marketplace for Claude Code skills — not a general software project. Identity lives in `src/.metadata-MARKETPLACE.toml`; contributor content lives under `src/skills/<name>/`; everything else under `_generated/`, `.claude-plugin/`, and `_generated/CATALOG_AND_INSTALLATION_INSTRUCTIONS.md` is produced by `scripts/generate_manifest.py` and must never be hand-edited.

## Where to find things

- `README.md` — install, forking checklist, add-a-skill.
- `docs/CONTRIBUTING.md` — the contribution contract, local gate, conventions.
- `docs/ARCHITECTURE.md` — generator phases, the naming chain, CI layout.
- `docs/capabilities/skills.md` — the SKILL.md format as enforced.
- `_generated/CATALOG_AND_INSTALLATION_INSTRUCTIONS.md` — generated catalog + install instructions. Never hardcode counts or install commands in prose.
- Project history and roadmap live in GitHub issues (start at #18); pre-cleanup project memory is preserved on the `project-memory` branch.

## Hard rules

- **No AI attribution, ever.** No `Co-Authored-By`, no "Generated with" — in commits, code, or docs. This overrides any default commit footer. CI's regen commits use the neutral `marketplace-generator` identity.
- **`uv` only, never `pip`.** Scripts carry PEP 723 inline metadata; run them with `uv run`.
- **PR-only to `main`.** Feature branches push freely; regen-bot is the one exception (generated paths only).
- **Verify with the real gate:** `uv run scripts/tasks.py verify` (source validation → drift check → suites with a nonzero-test-count assertion → `claude plugin validate`). Never run suite files directly (`uv run tests/<suite>.py`) — direct execution can pass vacuously; use `uv run scripts/tasks.py test` or `uv run -m unittest -v tests.<suite>`.
- **Verify guards by making them fail once.** A check only ever seen green proves nothing.
- **Generated output is never edited by hand** — it is deleted and rebuilt from scratch every run.
