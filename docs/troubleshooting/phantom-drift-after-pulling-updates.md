# Phantom changes to generated files right after pulling updates

**Symptom.** Immediately after pulling template updates (or checking out a
branch that includes them), `git status` shows modifications to files under
`_generated/` you never touched, and/or the drift gate
(`uv run scripts/generate_manifest.py --check`) reports drift on a tree that
should be clean. Diffs look content-identical.

**Cause.** Line endings. The template ships a `.gitattributes` that normalizes
files to LF, but a checkout that existed **before** that file arrived still has
CRLF copies on disk (Windows default). Git then reports every such file as
modified, and the generator (which writes LF) disagrees with what's on disk —
pure line-ending noise, zero content difference.

**Fix.** Re-normalize the working tree once:

```bash
git add --renormalize .
git status            # the phantom modifications collapse
# or, equivalently: delete the affected paths and `git checkout -- .`
```

A fresh clone never has this problem — cloning applies `.gitattributes` from
the first checkout.

**Prevent.** Nothing to do ongoing; this is a one-time artifact of pulling the
`.gitattributes` introduction into a pre-existing checkout.
