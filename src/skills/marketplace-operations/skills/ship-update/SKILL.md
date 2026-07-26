---
name: ship-update
description: Ship changes to the marketplace repo you are working in - branch, commit, PR, merge on green, and verify the published result. Use when the user wants to publish, release, or ship their marketplace changes.
allowed-tools:
  - Bash
---

You are working inside a marketplace repo. Changes ship PR-only to `main`;
pushes to `main` (and merged PRs) trigger CI to regenerate and commit all
generated artifacts.

## 1. Branch and commit

```bash
git checkout -b <short-topic-branch>
git add -A                          # or stage selectively
git commit -m "<what changed and why>"
git push -u origin <short-topic-branch>
```

Never hand-edit `_generated/` or `.claude-plugin/` - CI overwrites them, and
drift fails the PR gate.

## 2. Open the PR

```bash
gh pr create --fill        # title/body auto-filled from the commit message
```

(`--web` instead opens the pre-filled form in the browser - the PR is only
created when the user submits it there.)

## 3. Merge on green

```bash
gh pr checks --watch       # wait until every check shows "pass"
gh pr merge --merge --delete-branch
```

If a check is red, open its link - the common causes are naming-rule
violations (the log names the rule) and drift (someone hand-edited a
generated file).

## 4. Verify the published result

```bash
git checkout main && git pull      # CI's regenerate commit follows the merge
claude plugin marketplace update <marketplace-name>   # name: src/.metadata-MARKETPLACE.toml
```

Consumers now see the update. If this marketplace has forks that sync from it,
they receive the change through their own sync-updates-from-template runs.
