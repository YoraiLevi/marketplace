# DgxSparkLabs Marketplace Template

<!-- This README is yours on first edit — template updates never overwrite it (see .gitattributes + docs/UPDATING.md). -->

**This is the template** — fork it to run your own marketplace of agentic
capabilities; it automates all the packaging, publishing, and updating for you.
Its published capabilities are working references (and the `marketplace-operations`
suite). Looking for DgxSparkLabs' official capabilities? They ship from
[DgxSparkLabs/marketplace](https://github.com/DgxSparkLabs/marketplace).

**New here? Pick your path:**

| You want to… | Start here |
|---|---|
| **Install** a capability from this marketplace | [Install a capability](#install-a-capability) — two commands |
| **Contribute** a capability to this marketplace | [Contribute a capability](#contribute-a-capability) — one folder, one push |
| **Run your own** marketplace | [Run your own marketplace](#run-your-own-marketplace) — fork it, ~5 minutes |

## Install a capability

```bash
claude plugin marketplace add DgxSparkLabs/marketplace-template     # register (once)
claude plugin install skill-example-single@dgxsparklabs-template-marketplace
```

Browse everything this marketplace publishes — every capability, every install
and invocation path, copy-pasteable:
**[Catalog & installation instructions →](_generated/CATALOG_AND_INSTALLATION_INSTRUCTIONS.md)**

Featured: **`marketplace-operations`** — skills that teach your AI assistant to
run a marketplace like this one (create your own, add capabilities, ship
updates, pull template upgrades).

## Contribute a capability

One folder, one push — CI validates, packages, and publishes; you never run the
generator:

```bash
mkdir -p src/skills/my-skill
$EDITOR src/skills/my-skill/SKILL.md     # name + description + instructions
git add src/skills/my-skill && git commit && git push    # or open a PR
```

Start from the guide: [`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md) — the
capability types and their format references live under
[`docs/capabilities/`](docs/capabilities/) (skills today, more types planned).

## Run your own marketplace

This whole repo is a template — fork it and you own a marketplace with the same
automation, in about 5 minutes:

1. **Fork** this repo on GitHub.
2. **Enable Actions** in your fork (Actions tab → enable — one click).
3. **Set your identity**: edit [`src/.metadata-MARKETPLACE.toml`](src/.metadata-MARKETPLACE.toml)
   — your marketplace name, your URLs — and push.
4. **Done.** CI republishes everything under your identity: install commands,
   namespaces, the catalog. Tell users: `claude plugin marketplace add <you>/<your-fork>`.

Or let your AI assistant drive it: install the `marketplace-operations`
capability above and ask for a new marketplace — its `create-marketplace` skill
walks through these steps interactively.

Then make it yours: **this README is your storefront** — rewrite it freely; it
becomes permanently yours on first edit, and template updates will never
overwrite it. Everything else keeps improving underneath you automatically:
the template ships updates like software (daily sync, your content always
wins) — [`docs/UPDATING.md`](docs/UPDATING.md) · what's generated vs. what you
edit: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Roadmap

Skills on Claude Code ship today. More capability types (commands, agents,
hooks, MCP servers, …) and more platforms (Codex, Gemini, Cursor, …) are
planned and tracked in
[governed re-expansion issues](https://github.com/DgxSparkLabs/marketplace-template/issues/18).
