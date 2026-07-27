# Troubleshooting

Common issues, indexed by **what you see**. Every file follows the same shape:
Symptom (the exact message) → Cause → Fix (copy-paste) → Prevent.

| What you see | Open |
|---|---|
| `plugin uninstall` fails: *"enabled at project scope"* — but disable says it's already disabled | [uninstall-says-enabled-at-project-scope.md](uninstall-says-enabled-at-project-scope.md) |
| The sync run fails: *"refusing to allow a GitHub App to create or update workflow … without `workflows` permission"* | [sync-failed-refusing-workflow-permission.md](sync-failed-refusing-workflow-permission.md) |
| `marketplace add` registered your marketplace under an old/wrong name | [marketplace-registered-under-wrong-name.md](marketplace-registered-under-wrong-name.md) |
| `git status` / the drift gate shows changes to generated files you never touched, right after pulling updates | [phantom-drift-after-pulling-updates.md](phantom-drift-after-pulling-updates.md) |

Hit something new? Add a file here following the same four-field shape — this
folder syncs from the template to every fork, so a fix written once helps every
marketplace.
