# Claude Code Skill Marketplace — fork-ready template

A **template marketplace for Claude Code skills**. Fork it, drop skill folders into `src/skills/`, push — CI packages and publishes them, and anyone can install your skills with two `claude` commands. You never run the generator; everything you own lives in `src/` — add, change, or delete anything there, including the shipped examples.

```
you fork this repo
 └▶ drop a folder into src/skills/<your-skill>/      ← the ONLY thing you touch
     └▶ git commit + push to your fork's main
         └▶ GitHub Actions (in your fork) validates → regenerates → commits
             └▶ users: claude plugin marketplace add <you>/<your-repo>
                 └▶ /plugin install <your-skill>
```

Governance and history: umbrella issue [#18](https://github.com/DgxSparkLabs/marketplace-template/issues/18) (the skills-only, Claude-only scope-down) and [#19](https://github.com/DgxSparkLabs/marketplace-template/issues/19) (the naming standard CI enforces). Other construct types and other agent platforms are deliberately deferred with tracked re-expansion issues — see #18's index.

## Prerequisites

- [Claude Code](https://code.claude.com) (`claude` CLI; behavior below verified on 2.1.220)
- `git`; and [`uv`](https://docs.astral.sh/uv/) for the scaffold command and the optional local gate

## Install skills from this marketplace

```bash
claude plugin marketplace add DgxSparkLabs/marketplace-template
claude plugin install skill-example-multi@dgxsparklabs-marketplace --scope project
```

Install auto-enables the plugin on current CLIs. Two sharp edges worth knowing: `--scope project` writes `.claude/settings.json` in your **current directory** — run it from the project you mean to configure; and uninstalling needs the same flag (`claude plugin uninstall skill-example-multi --scope project`).

Browse what's installable with `claude plugin list --available --json` (the `--available` flag requires `--json`) — or just read the generated list at [`docs/INVENTORY.md`](docs/INVENTORY.md).

Skills invoke as `/<brand>-skill-<plugin-folder>:<skill-name>` (e.g. `/dgxsparklabs-skill-example-multi:notebook`) or via the flat shortcut (`/notebook`) when unambiguous.

## Make it yours (forking checklist, ~5 minutes)

1. **Fork** this repo on GitHub.
2. **Enable Actions** in your fork (Actions tab → enable — one click; forks start with workflows off).
3. **Edit `src/.metadata-MARKETPLACE.toml`**: set `name` (kebab-case, must end in `-marketplace` — e.g. `acme-marketplace`; CI enforces this, and the part before `-marketplace` becomes the brand prefix on every skill), `description`, `owner`, and the repo URL.
4. **Push to main.** CI regenerates every manifest with your identity — nothing else needs renaming; install commands, plugin names, and slash namespaces all derive from that one file plus your repo slug. (`.metadata-*.toml` files are the fork-editable source metadata — dot-prefixed like `.env`: your fork edits them and ships its own values.)
5. Tell users: `claude plugin marketplace add <you>/<your-fork>`.

What you may NOT hand-edit: `_generated/`, `.claude-plugin/`, `docs/INVENTORY.md` — CI owns them and will overwrite (drift is also a CI failure on PRs).

## Add a skill

```bash
uv run scripts/new_construct.py skill my-skill     # scaffold from the example (optional)
# — or just create src/skills/my-skill/SKILL.md by hand —
git add src/skills/my-skill && git commit && git push
```

A skill folder is either **solo** (`src/skills/<plugin>/SKILL.md`) or **multi** (`src/skills/<plugin>/skills/<a>/SKILL.md`, one subfolder per skill — folder name must equal the SKILL.md frontmatter `name:`). Format details: [`docs/SKILL_FORMAT.md`](docs/SKILL_FORMAT.md); the full naming rules CI enforces: issue #19 and `scripts/validate_source.py`.

Working locally and want the full gate before pushing? `uv run scripts/tasks.py verify` runs source validation → drift check → test suites → `claude plugin validate`. If the drift check fails it tells you what's out of sync and leaves your tree untouched; commit only `src/` and let CI regenerate, or run `uv run scripts/generate_manifest.py` and commit everything — both work.

## Template updates — your fork receives them automatically

This template is maintained **as software**: bug fixes, CI improvements, and doc
updates land upstream, and forked marketplaces are *intended* to receive them.
Because everything you own lives in `src/` (and the template never overrides your side of it),
updates merge underneath your content without touching it. The shipped
`sync-template` workflow checks the template **daily** and merges + republishes
on its own — you do nothing. Details, the manual recipe, and the one warning
(never use GitHub's "Sync fork" button on a published fork): [`docs/UPDATING.md`](docs/UPDATING.md).

What is generated vs. what you edit — and how generation works: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).
