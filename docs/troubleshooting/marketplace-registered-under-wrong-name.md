# Marketplace registered under an old or wrong name

**Symptom.** `claude plugin marketplace add <owner>/<repo>` succeeds, but the
registered name (shown in the ✔ line and in `claude plugin marketplace list`)
is an old identity — e.g. the name from *before* you edited
`src/.metadata-MARKETPLACE.toml`, or the template's name instead of your fork's.
Installs against the expected `@<your-name>` then fail.

**Cause.** The CLI registers whatever `name` it finds in the repo's published
`.claude-plugin/marketplace.json` at fetch time. Two ways that goes stale:
(1) CI hasn't finished regenerating after your identity change (its
"chore(generated): regenerate manifests" commit isn't on `main` yet), or
(2) GitHub's raw-content cache served a copy from a few minutes ago.

**Fix.**

```bash
# 1. confirm the published manifest is current (look at the "name" field):
#    https://github.com/<owner>/<repo>/blob/main/.claude-plugin/marketplace.json
# 2. drop the stale registration and re-add:
claude plugin marketplace remove <wrong-name>
claude plugin marketplace add <owner>/<repo>
```

If the manifest itself still shows the old name, wait for CI to finish (watch
the repo's Actions tab), `git pull`, then re-add. Cache staleness resolves
itself within ~5 minutes.

**Prevent.** After changing marketplace identity, wait for the CI regeneration
commit to appear on `main` before registering anywhere.
