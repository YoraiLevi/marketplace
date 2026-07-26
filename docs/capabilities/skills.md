# SKILL.md format reference

The format for skills in this marketplace, as the toolchain actually enforces and Claude Code actually consumes it. Everything here is checkable against `scripts/validate_source.py` (the CI gate) and the shipped examples under `src/skills/`.

> **You never write `plugin.json` for the marketplace** — the generator derives the plugin wrapper at `_generated/claude-code/skill-<name>/` from your `SKILL.md` + `src/.metadata-MARKETPLACE.toml`. See [CONTRIBUTING](../CONTRIBUTING.md) for the workflow.

## Layouts

A skill plugin folder under `src/skills/<plugin>/` is one of exactly two shapes:

```
solo                                multi
src/skills/<plugin>/                src/skills/<plugin>/
├── SKILL.md                        ├── .claude-plugin/plugin.json
└── .claude-plugin/plugin.json      └── skills/
    (optional in BOTH layouts; "description" is the ONLY allowed key — rule R6)
                                            ├── <skill-a>/SKILL.md
                                            └── <skill-b>/SKILL.md
```

Having both a root `SKILL.md` and a `skills/` subdir is a generator error — pick one. Supporting files (scripts, references) may sit next to any `SKILL.md` and are copied into the plugin verbatim.

## Frontmatter

```markdown
---
name: my-skill
description: One sentence saying when Claude should use this skill.
allowed-tools: Bash
---

The skill body: the instructions Claude follows when the skill is invoked.
```

| Field | Required? | Rules (CI-enforced where marked) |
|---|---|---|
| `description` | **Yes**, whenever frontmatter is present (CI) | Non-empty; this is both the model's invocation hint and the marketplace listing line. Keep it one sentence. |
| `name` | Optional | Defaults to the folder name (solo: the plugin folder; multi: the skill folder). If set: kebab-case, 1–32 chars (CI); in the multi layout it must equal the skill folder name (CI, rule R8). Avoid names of built-in slash commands (CI warns). |
| `allowed-tools` | Optional | Claude Code tool names (e.g. `Bash`, `Read`). Claude-only — this marketplace targets no other platform. |

Other Claude Code SKILL.md fields (e.g. `disable-model-invocation`) pass through untouched; the validator neither requires nor rejects them. The authoritative field list is Claude Code's own skills documentation: https://code.claude.com/docs/en/skills

## Referencing bundled files

Use `${CLAUDE_PLUGIN_ROOT}` for paths to files shipped with the skill — Claude Code sets it to the installed plugin's root at runtime:

```markdown
Run: uv run ${CLAUDE_PLUGIN_ROOT}/scripts/helper.py
```

The validator checks every `${CLAUDE_PLUGIN_ROOT}/<file>` reference in bundled JSON actually resolves to a file in the plugin (the "config references a missing script" class). There is **no** other substitution mechanism — nothing rewrites paths at install time.

## How a skill surfaces after install

- Slash form: `/<brand>-skill-<plugin>:<name>` (e.g. `/dgxsparklabs-skill-example-multi:notebook`)
- Flat shortcut: `/<name>` when unambiguous
- The model can also invoke the skill autonomously based on `description`.

Naming chain and rules in full: [ARCHITECTURE](../ARCHITECTURE.md) "The name chain" + issue #19.
