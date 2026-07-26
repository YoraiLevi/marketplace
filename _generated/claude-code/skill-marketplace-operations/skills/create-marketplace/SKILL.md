---
name: create-marketplace
description: Create your own capability marketplace from the marketplace-template - forks the template, asks you for your marketplace identity, applies it, and verifies the first publish end to end. Use when the user wants to start, fork, or set up their own marketplace.
allowed-tools:
  - Bash
---

Guide the user through creating their own marketplace from the template. Ask for
inputs conversationally; never invent values for them.

## 1. Collect the identity (ask the user)

Ask for, with these constraints:
- **Marketplace name** - kebab-case, MUST end in `-marketplace` (e.g. `acme-marketplace`).
  The part before `-marketplace` becomes the brand prefix on every capability.
- **Display name** - human title (e.g. "Acme Marketplace").
- **One-line description** - shown in marketplace listings.
- **GitHub owner** (user or org) and the **repository name** for the new fork.

## 2. Fork and clone

```bash
gh repo fork DgxSparkLabs/marketplace-template --fork-name <repo-name> --clone
cd <repo-name>
```

If `gh` is missing or unauthenticated, have the user fork in the browser
(github.com/DgxSparkLabs/marketplace-template → Fork) and `git clone` their fork.

## 3. Enable Actions (the one manual click)

Forks start with workflows disabled. Have the user open their fork's **Actions**
tab in the browser and click enable. Without this, nothing publishes.

## 4. Apply the identity

Edit `src/.metadata-MARKETPLACE.toml` with the collected values: `[marketplace]`
`name`, `display_name`, `description`; `[owner]` `name`, `url`; `[repository]`
`url`, `homepage`. Then:

```bash
git add src/.metadata-MARKETPLACE.toml
git commit -m "chore: marketplace identity"
git push
```

## 5. Verify the first publish

CI regenerates and commits everything under the new identity (~1 minute). Then:

```bash
git pull   # shows the CI commit "chore(generated): regenerate manifests"
claude plugin marketplace add <owner>/<repo-name>
claude plugin install skill-example-single@<marketplace-name> --scope user
```

Success = `✔ Successfully installed`. The marketplace is live. Point the user at
`_generated/CATALOG_AND_INSTALLATION_INSTRUCTIONS.md` (their commands, their
identity) and the `add-capability` skill for their first real capability.

## Troubleshooting

- CI red on the identity push → almost always a name-rule violation; the log
  names the rule (kebab-case, `-marketplace` suffix, reserved words).
- `claude plugin marketplace add` says already exists → a marketplace with that
  `name` is registered; `claude plugin marketplace remove <name>` first.
