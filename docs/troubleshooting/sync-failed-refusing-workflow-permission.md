# Sync run failed: "refusing to allow a GitHub App to … update workflow … without `workflows` permission"

**Symptom.** The `sync-updates-from-template` run (or any CI push) fails at the
push step with *"! [remote rejected] main -> main (refusing to allow a GitHub
App to create or update workflow `.github/workflows/….yml` without `workflows`
permission)"*.

**Cause.** GitHub forbids the default CI token from pushing changes to files
under `.github/workflows/` — and template updates sometimes change workflow
files. Current template versions of the sync workflow *hold back* workflow-file
changes automatically and tell you in the run summary; seeing this error
usually means the fork is running an **older copy** of the sync workflow that
predates the hold-back logic (a chicken-and-egg: a workflow can't update itself
through the restricted token).

**Fix.** Apply the template's workflow files once with your own credentials
(they have the permission the CI token lacks):

```bash
git fetch https://github.com/DgxSparkLabs/marketplace-template main
git rm -rq .github/workflows && git checkout FETCH_HEAD -- .github/workflows
git commit -m "chore: apply template workflow updates" && git push
```

> Always name the branch (`… main`) in that fetch — a bare `git fetch <remote>`
> can leave `FETCH_HEAD` pointing at a different branch.

**Prevent.** Add a fine-grained PAT (Contents + Workflows write) as the
`SYNC_TOKEN` repository secret — the sync then updates workflow files too, and
this error class disappears. Details: [`../UPDATING.md`](../UPDATING.md).
