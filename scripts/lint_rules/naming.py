"""naming.py — lint rules about the names people type.

Marketplace identity, capability folder names, skill names, and the composed
identifiers of generated plugins.
"""

from __future__ import annotations

import re
from pathlib import Path

from utils import skill_components

from . import fixtures
from .model import ALL, Context, Severity, Stage, Violation, counterexample, lint_rule

KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

# Probed against the CLI: only {skills-dir, builtin} are hard-rejected by
# `claude plugin validate`; the rest pass there, so this lint is their only gate.
RESERVED_MARKETPLACES = {
    "skills-dir", "builtin",
    "claude-plugins-official",
    "local", "user", "project", "claude", "anthropic",
}

# Built-in slash command names a skill name should avoid. Advisory only —
# the namespaced form always resolves.
BUILTIN_SLASH_NAMES = {
    "config", "theme", "agents", "mcp", "plugin", "help", "init", "clear",
    "compact", "resume", "fast", "code-review", "review", "security-review",
}


# ─── marketplace identity (stage: IDENTITY) ──────────────────────────────────

@counterexample("naming/marketplace-kebab-case")
def _ce_mk(root: Path) -> None:
    fixtures.base(root, fixtures.identity_with("Not_Kebab-marketplace"))


@lint_rule("naming/marketplace-kebab-case", stage=Stage.IDENTITY, constructs=ALL,
           applies_to="marketplace name",
           requirement="Is kebab-case.",
           why="The name appears in the install command users type; mixed case "
               "and underscores are easy to mistype and inconsistent across forks.")
def marketplace_kebab_case(ctx: Context):
    name = ctx.marketplace_name()
    if name and not KEBAB.match(name):
        yield Violation(ctx.identity_path(), f"marketplace name '{name}' is not kebab-case")


@counterexample("naming/marketplace-suffix")
def _ce_ms(root: Path) -> None:
    fixtures.base(root, fixtures.identity_with("example-store"))


@lint_rule("naming/marketplace-suffix", stage=Stage.IDENTITY, constructs=ALL,
           applies_to="marketplace name",
           requirement="Ends in `-marketplace`.",
           why="The brand prefix used throughout generated output is derived by "
               "stripping that suffix; without it there is no brand to derive.")
def marketplace_suffix(ctx: Context):
    name = ctx.marketplace_name()
    if name and not name.endswith("-marketplace"):
        yield Violation(
            ctx.identity_path(), f"marketplace name '{name}' must end in '-marketplace'"
        )


@counterexample("naming/marketplace-brand")
def _ce_mb(root: Path) -> None:
    fixtures.base(root, fixtures.identity_with("-marketplace"))


@lint_rule("naming/marketplace-brand", stage=Stage.IDENTITY, constructs=ALL,
           applies_to="marketplace name",
           requirement="The name with `-marketplace` removed is non-empty and kebab-case.",
           why="That remainder becomes the brand prefix on every published plugin.")
def marketplace_brand(ctx: Context):
    name = ctx.marketplace_name()
    if name and name.endswith("-marketplace"):
        brand = name.removesuffix("-marketplace")
        if not brand or not KEBAB.match(brand):
            yield Violation(
                ctx.identity_path(),
                f"marketplace name '{name}' leaves brand '{brand}', which is "
                f"empty or not kebab-case",
            )


@counterexample("naming/marketplace-not-reserved")
def _ce_mr(root: Path) -> None:
    fixtures.base(root, fixtures.identity_with("builtin"))


@lint_rule("naming/marketplace-not-reserved", stage=Stage.IDENTITY, constructs=ALL,
           applies_to="marketplace name",
           requirement="Is not a reserved identity.",
           why="Some names are rejected outright by the CLI and others collide "
               "with built-in scopes; either way the marketplace fails to register.")
def marketplace_not_reserved(ctx: Context):
    name = ctx.marketplace_name()
    if name in RESERVED_MARKETPLACES:
        yield Violation(ctx.identity_path(), f"marketplace name '{name}' is reserved")


@counterexample("naming/marketplace-length")
def _ce_ml(root: Path) -> None:
    fixtures.base(root, fixtures.identity_with("a" * 60 + "-marketplace"))


@lint_rule("naming/marketplace-length", stage=Stage.IDENTITY, constructs=ALL,
           applies_to="marketplace name",
           requirement="Is 3 to 64 characters.",
           why="Keeps the install command a user types readable and typo-resistant.")
def marketplace_length(ctx: Context):
    name = ctx.marketplace_name()
    if name and not (3 <= len(name) <= 64):
        yield Violation(
            ctx.identity_path(),
            f"marketplace name '{name}' is {len(name)} characters, outside 3-64",
        )


# ─── capability folder names (stage: CAPABILITY, all constructs) ─────────────

@counterexample("naming/folder-kebab-case")
def _ce_fk(root: Path) -> None:
    fixtures.skill(fixtures.base(root), "My_Skill")


@lint_rule("naming/folder-kebab-case", stage=Stage.CAPABILITY, constructs=ALL,
           applies_to="capability folder name",
           requirement="Is kebab-case.",
           why="The folder name flows into the published plugin name and the "
               "install command; it has to survive being typed by hand.")
def folder_kebab_case(ctx: Context):
    if not KEBAB.match(ctx.folder.name):
        yield Violation(ctx.folder, "folder name is not kebab-case")


@counterexample("naming/folder-length")
def _ce_fl(root: Path) -> None:
    fixtures.skill(fixtures.base(root), "a" * 40)


@lint_rule("naming/folder-length", stage=Stage.CAPABILITY, constructs=ALL,
           applies_to="capability folder name",
           requirement="Is at most 32 characters.",
           why="It is only one segment of a longer composed name; an overlong "
               "folder makes the full identifier unwieldy.")
def folder_length(ctx: Context):
    if len(ctx.folder.name) > 32:
        yield Violation(
            ctx.folder,
            f"folder name is {len(ctx.folder.name)} characters, over the 32 limit",
        )


# ─── skill names (stage: CAPABILITY, skills only) ────────────────────────────

@counterexample("naming/skill-name-kebab-case")
def _ce_sk(root: Path) -> None:
    fixtures.skill(fixtures.base(root), "ok-skill", "name: Bad_Name\ndescription: x")


@lint_rule("naming/skill-name-kebab-case", stage=Stage.CAPABILITY,
           constructs=frozenset({"skill"}),
           applies_to="skill name",
           requirement="Is kebab-case.",
           why="It is the last segment of what a user types to invoke the skill.")
def skill_name_kebab_case(ctx: Context):
    for c in skill_components(ctx.folder):
        if not KEBAB.match(c["name"]):
            yield Violation(ctx.folder, f"skill name '{c['name']}' is not kebab-case")


@counterexample("naming/skill-name-length")
def _ce_sl(root: Path) -> None:
    fixtures.skill(fixtures.base(root), "ok-skill", f"name: {'n' * 40}\ndescription: x")


@lint_rule("naming/skill-name-length", stage=Stage.CAPABILITY,
           constructs=frozenset({"skill"}),
           applies_to="skill name",
           requirement="Is 1 to 32 characters.",
           why="Keeps the invocation typeable and the listing scannable.")
def skill_name_length(ctx: Context):
    for c in skill_components(ctx.folder):
        if not (1 <= len(c["name"]) <= 32):
            yield Violation(
                ctx.folder,
                f"skill name '{c['name']}' is {len(c['name'])} characters, outside 1-32",
            )


@counterexample("naming/skill-name-unique")
def _ce_su(root: Path) -> None:
    src = fixtures.base(root)
    fixtures.multi_skill(src, "dupes", "alpha", "name: same\ndescription: x")
    fixtures.multi_skill(src, "dupes", "beta", "name: same\ndescription: x")


@lint_rule("naming/skill-name-unique", stage=Stage.CAPABILITY,
           constructs=frozenset({"skill"}),
           applies_to="skill name",
           requirement="Is unique within its plugin.",
           why="Two skills with one name inside a single plugin cannot both be "
               "addressed; one wins silently.")
def skill_name_unique(ctx: Context):
    seen: set[str] = set()
    for c in skill_components(ctx.folder):
        if c["name"] in seen:
            yield Violation(ctx.folder, f"skill name '{c['name']}' appears more than once")
        seen.add(c["name"])


@counterexample("naming/avoids-builtin-name")
def _ce_bn(root: Path) -> None:
    fixtures.skill(fixtures.base(root), "ok-skill", "name: compact\ndescription: x")


@lint_rule("naming/avoids-builtin-name", stage=Stage.CAPABILITY,
           constructs=frozenset({"skill"}),
           applies_to="skill name",
           severity=Severity.WARNING,
           requirement="Does not shadow a built-in command name.",
           why="A shadowing name may resolve to the built-in instead of the "
               "skill, depending on what else is installed. Advisory, because "
               "the namespaced form always resolves correctly.")
def avoids_builtin_name(ctx: Context):
    for c in skill_components(ctx.folder):
        if c["name"] in BUILTIN_SLASH_NAMES:
            yield Violation(ctx.folder, f"skill name '{c['name']}' shadows a built-in command")


# ─── generated identifiers (stage: GENERATED) ────────────────────────────────

@counterexample("naming/plugin-id-unique")
def _ce_pu(root: Path) -> None:
    fixtures.base(root)
    fixtures.generated_plugin(root, "skill-alpha", "example-skill-alpha")
    fixtures.generated_plugin(root, "skill-beta", "example-skill-alpha")  # duplicate


@lint_rule("naming/plugin-id-unique", stage=Stage.GENERATED, constructs=ALL,
           applies_to="generated plugin identifier",
           requirement="Is unique across the marketplace.",
           why="Two plugins sharing an identifier means one is unreachable "
               "after install, with no error to explain why.")
def plugin_id_unique(ctx: Context):
    seen: dict[str, Path] = {}
    for d in ctx.generated_plugin_dirs():
        data = ctx.read_json(d / ".claude-plugin" / "plugin.json")
        if not isinstance(data, dict):
            continue
        name = data.get("name", "")
        if name in seen:
            # Name the other location, do not path it — an absolute path here
            # would leak the fixture root into the docs' captured example.
            yield Violation(
                d / ".claude-plugin" / "plugin.json",
                f"plugin identifier '{name}' is already used by '{seen[name].name}'",
            )
        seen[name] = d


@counterexample("naming/plugin-id-composed")
def _ce_pc(root: Path) -> None:
    fixtures.base(root)
    fixtures.generated_plugin(root, "skill-alpha", "wrong-prefix-alpha")


@lint_rule("naming/plugin-id-composed", stage=Stage.GENERATED, constructs=ALL,
           applies_to="generated plugin identifier",
           requirement="Is composed as `<brand>-<type>-<folder>`.",
           why="The composed shape is what users see and type; a deviation "
               "silently changes the documented invocation.")
def plugin_id_composed(ctx: Context):
    for d in ctx.generated_plugin_dirs():
        data = ctx.read_json(d / ".claude-plugin" / "plugin.json")
        if not isinstance(data, dict):
            continue
        name = data.get("name", "")
        expected = f"{ctx.brand()}-{d.name}"
        if name != expected:
            yield Violation(
                d / ".claude-plugin" / "plugin.json",
                f"plugin identifier '{name}' should be '{expected}'",
            )
