---
name: sync-updates-from-template
description: Pull the marketplace-template's latest machinery updates into the forked marketplace you are working in - automatic and manual paths, plus completing held-back workflow updates. Use when the user wants to update, upgrade, or sync their marketplace from the template.
allowed-tools:
  - Bash
---

You are working inside a marketplace forked from the template. Updates merge
underneath the fork's content: everything in `src/` and any customized
fork-owned file (see `.gitattributes`, e.g. README.md) always wins - template
updates can never overwrite the fork's capabilities or storefront.

## The automatic path (usually nothing to do)

The `sync-updates-from-template` workflow runs daily and on demand
(**Actions → sync-updates-from-template → Run workflow**, or):

```bash
gh workflow run sync-updates-from-template.yml
gh run watch $(gh run list --workflow=sync-updates-from-template --limit 1 --json databaseId -q '.[0].databaseId')
```

Green run = merged, regenerated under this fork's identity, pushed. Then
`git pull` locally.

## The manual path (same thing by hand)

```bash
git remote add template https://github.com/DgxSparkLabs/marketplace-template  # once
git config merge.ours.driver true                                             # once per clone
git fetch template
git merge -X ours --no-edit template/main
git push          # this push triggers CI to regenerate under the fork's identity
```

## Held-back workflow updates

GitHub forbids the CI token from pushing `.github/workflows/` changes, so when
a template update touches workflow files the sync ships everything else and
says so in the run summary (and an issue, if Issues are enabled). Complete it
with the user's own credentials:

```bash
git fetch https://github.com/DgxSparkLabs/marketplace-template main
git rm -rq .github/workflows && git checkout FETCH_HEAD -- .github/workflows
git commit -m "chore: apply template workflow updates" && git push
```
> **Always name the branch in the fetch** (`... main`): a bare `git fetch <remote>` can leave `FETCH_HEAD` pointing at a different branch of the template (observed live: it briefly restored pre-cleanup workflows from an archive branch).


Fully hands-off alternative: a fine-grained PAT (Contents + Workflows write)
saved as the `SYNC_TOKEN` repository secret - the sync then updates workflow
files too.

## Never

Never use GitHub's "Sync fork" button on a published fork - its "Discard
commits" option hard-resets the branch and deletes the fork's capabilities.
Full semantics: `docs/UPDATING.md`.
