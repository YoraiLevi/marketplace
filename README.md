# Example Marketplace
<!-- This README is yours on first edit — template updates never overwrite it (see .gitattributes + docs/UPDATING.md). -->

Install **agentic capabilities** for your AI tooling — every capability, every install path, copy-pasteable:
**[Catalog & installation instructions →](_generated/CATALOG_AND_INSTALLATION_INSTRUCTIONS.md)**

## Contributing a capability — [`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md)

One folder, one push — CI does everything else:

```bash
mkdir -p src/skills/my-skill        # or scaffold: uv run scripts/new_construct.py skill my-skill
$EDITOR src/skills/my-skill/SKILL.md
git add src/skills/my-skill && git commit && git push   # or open a PR
```

Capability types and their format guides live under [`docs/capabilities/`](docs/capabilities/) — skills today, more types planned.

---

## Run your own marketplace (this repo is a template)

This marketplace is built on the fork-ready **marketplace-template** — fork it and
you own one too, in ~5 minutes:

1. Fork → enable Actions (one click in the Actions tab)
2. Edit [`src/.metadata-MARKETPLACE.toml`](src/.metadata-MARKETPLACE.toml) — your name, your URLs
3. Push. CI republishes everything under your identity — commands, namespaces, catalog.
4. Rewrite everything above the divider — it's your storefront, and it's yours forever
   on first edit ([how updates respect that](docs/UPDATING.md)).

Template updates then arrive automatically — your content always wins:
[`docs/UPDATING.md`](docs/UPDATING.md) · what's generated vs. yours:
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)

**Roadmap** — skills on Claude Code today; more capability types (commands, agents, hooks,
MCP servers, …) and more platforms (Codex, Gemini, Cursor, …) are planned and tracked in
[governed re-expansion issues](https://github.com/DgxSparkLabs/marketplace-template/issues/18).
