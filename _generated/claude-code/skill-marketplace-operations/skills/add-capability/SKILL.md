---
name: add-capability
description: Add a new capability (skill) to the marketplace repo you are working in - one folder, one push, CI packages and publishes it. Use when the user wants to add, contribute, or publish a skill/capability to their marketplace.
allowed-tools:
  - Bash
---

You are working inside a marketplace repo (it has `src/.metadata-MARKETPLACE.toml`).
The contract: contributors touch `src/` only - CI owns everything generated.

## 1. Create the skill folder

Solo layout (one skill per capability - the common case):

```bash
mkdir -p src/skills/<name>          # kebab-case, max 32 chars
```

Write `src/skills/<name>/SKILL.md`:

```markdown
---
name: <name>
description: <one line - what the model can do with this; shown in listings>
allowed-tools:
  - Bash
---

<the instructions the model follows when this skill is invoked>
```

Multi layout (several skills shipped as one capability): one
`src/skills/<plugin>/skills/<skill-name>/SKILL.md` per skill (folder name must
equal its frontmatter `name:`), plus `src/skills/<plugin>/.metadata-SKILL.toml`
with `description = "..."`. Full format: `docs/capabilities/skills.md`.

Rules CI enforces (fix before pushing, or let CI tell you): kebab-case names,
`description:` required, no `.claude-plugin/` directory inside `src/`.

## 2. Optional local preview

```bash
uv run scripts/tasks.py verify     # validate -> drift -> tests -> plugin validate
```

Skippable - CI runs the same gate; contributors need only git.

## 3. Push - CI does the rest

```bash
git add src/skills/<name> && git commit -m "feat: add <name> capability" && git push
```

On main (or a merged PR), CI regenerates the manifests and the catalog and
commits them (~1 minute). Verify:

```bash
git pull    # the "chore(generated): regenerate manifests" commit
claude plugin marketplace update <marketplace-name>   # name: src/.metadata-MARKETPLACE.toml
claude plugin install skill-<name>@<marketplace-name> --scope user
```

The capability's full install/invoke reference appears in
`_generated/CATALOG_AND_INSTALLATION_INSTRUCTIONS.md`.
