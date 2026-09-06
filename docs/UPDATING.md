---
purpose: how a forked marketplace receives template updates
audience: forkers (marketplace owners)
---

# Updating your marketplace from the template

Your fork is **your content on top of the template's machinery**, and the split is
strict by design:

- **Yours**: everything in `src/` (your skills, your metadata, and the shipped
  examples, which you may edit or delete). You also own the extension zone for your
  marketplace's own scripts, tests, and workflows: `custom/` and
  `.github/workflows/custom-*.yml`.
- **The template's**: everything else. The generator and the rest of `scripts/`,
  the template's own workflows, `tests/`, `docs/`, and all generated output receive
  fixes and improvements upstream, and your fork pulls them in like software updates.

Updates merge underneath your content without touching it, and every conflict
resolves in your favor — so template updates can never resurrect an example you
deleted or overwrite a skill you changed.

## Automatic updates (default — you do nothing)

The `sync-updates-from-template` workflow ships in this repo. In your fork it:

1. Runs **daily** (and on demand: Actions → sync-updates-from-template → Run workflow).
2. Fetches `DgxSparkLabs/marketplace-template` and merges it into your main.
   Any conflict resolves in **your** favor (`-X ours`) — safe because conflicts can
   only occur in generated files (regenerated from source anyway) or your
   metadata file (where your side is correct by definition).
3. Regenerates all manifests **under your identity**, runs the test suites, and
   pushes. (The regeneration happens inside this workflow because pushes made
   with the CI token do not trigger the separate `regen-bot` run.)

**Workflow-file updates — the one GitHub restriction.** The default CI token
may not push changes under `.github/workflows/`. When a template update touches
workflow files, the sync ships everything else and tells you the single command
that completes it — in the sync run's **summary** (Actions → the run) and as a
warning annotation, plus an auto-opened issue **if your fork has Issues enabled**
(GitHub disables Issues on forks by default — enable it in Settings for the
most visible notification). To make even that automatic (fully
zero-touch forever), add a repository secret named **`SYNC_TOKEN`** containing a
fine-grained PAT for your fork with **Contents: write** and **Workflows: write**
— the sync uses it automatically when present.

Two more GitHub platform caveats:

- Scheduled workflows only run in forks after you enable Actions (the same
  one-click as in the README checklist).
- GitHub pauses scheduled workflows after ~60 days without repository activity;
  the Actions tab shows a "Re-enable" button when that happens.

## Manual update (the same thing, by hand)

```bash
git remote add template https://github.com/DgxSparkLabs/marketplace-template  # once
git config merge.ours.driver true                                             # once - honors the fork-owned file list
git fetch template
git merge -X ours --no-edit template/main
git push
```

After pushing, your fork's `regen-bot` regenerates the manifests (your push
triggers it; CI-token pushes don't) — `git pull` a minute later to see its commit.

## Files that become yours on first edit

`.gitattributes` lists **fork-owned** files (`README.md`, `SECURITY.md` by
default): while you leave one untouched it keeps receiving template updates;
the moment you customize it, every sync keeps your version whole-file — no
half-merged text, ever. Claim more files by adding your own `merge=ours`
lines to `.gitattributes`; the sync preserves your additions.

## Extend with your own scripts & workflows

`src/` holds the capabilities you publish. Your marketplace's own machinery lives in
two fork-owned places instead: put scripts, helpers, data, and tests in `custom/`
(tests go in `custom/tests/`), and put your own GitHub Actions workflows in
`.github/workflows/` with a `custom-` prefix, for example `custom-vendor.yml`.

Both are protected by `merge=ours` in `.gitattributes`, so a template sync never
overwrites them. The template ships one hello-world example in each
(`custom/hello_custom.py` and `.github/workflows/custom-hello.yml`); copy it or
delete it, the same way you treat the example skills. Tests you add under
`custom/tests/` run automatically with `uv run scripts/tasks.py test`, so your CI
checks your code and you never edit a template-owned file. You push your own
`custom-*.yml` workflows yourself, with your own credentials; the GitHub rule that
blocks the sync bot from pushing `.github/workflows/` does not apply to you.

Give each workflow you own its own `custom-` name rather than editing the shipped
`custom-hello.yml`. A workflow whose name the template does not ship is yours alone
and survives every sync. If you edit the shipped `custom-hello.yml` in place, the
daily merge keeps your version, but the manual step that finishes a held-back
workflow update replaces it with the template's copy. Copying rather than editing
avoids that surprise.

## What NOT to do

**Do not use GitHub's "Sync fork" button once you have published anything.**
Your fork and the template permanently diverge in the generated files (each
side's CI commits them with its own identity), so the button degrades to two
bad options: a web conflict editor on files you must never hand-edit, or
**"Discard commits" — a hard reset that deletes your skills from the branch.**
The workflow and the recipe above exist precisely so you never face that choice.

## After an update

Nothing to do. Your skills, your identity, and your users' install commands
(`claude plugin install <skill>@<your-marketplace-name>`) are untouched; only
the machinery underneath moved. If an update ever changes something you *do*
interact with (a metadata field, a layout rule), the template's release notes
on the GitHub Releases page will say so.

Something about updating misbehaving? Symptom-indexed fixes: [`troubleshooting/`](troubleshooting/).
