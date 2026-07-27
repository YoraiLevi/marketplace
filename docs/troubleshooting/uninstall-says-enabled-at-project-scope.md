# Uninstall says "enabled at project scope" — but you can't find where

**Symptom.** `claude plugin uninstall <name> --scope user` fails with
*"Plugin … is enabled at project scope (.claude/settings.json, shared with your
team)"* — but running `uninstall --scope project` says it's *not* installed in
project scope, and `disable --scope project` says it's *already disabled*. The
messages seem to contradict each other.

**Cause.** A project-scope install belongs to **the folder it was run in**, and
every project-scope command answers only for **your current directory**. The
plugin was installed with `--scope project` from some *other* folder (often a
test clone or a directory you forgot about). The error message never names that
folder — that's the whole confusion. The commands aren't contradicting each
other; they're answering about different directories.

**Fix.** Look up the owning folder in the CLI's own ledger, then uninstall from
inside it:

```bash
python -c "import json,os;d=json.load(open(os.path.expanduser('~/.claude/plugins/installed_plugins.json'),encoding='utf-8'));print(json.dumps(d,indent=1))" | grep -B2 -A4 "<plugin-name>"
# note the "projectPath" for the plugin, then:
cd <that projectPath>
claude plugin uninstall <name> --scope project
```

**Prevent.** Uninstall project-scope plugins *before* deleting the folder you
installed them from, and run `--scope project` installs only from the project
root you actually mean to configure.
