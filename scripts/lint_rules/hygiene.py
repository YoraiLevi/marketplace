"""hygiene.py — lint rules about repository shape.

Source trees carry intent; packaging is produced by the generator. These
rules keep the two from bleeding into each other.
"""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

from utils import _frontmatter

from . import fixtures
from .model import ALL, Context, Stage, Violation, counterexample, lint_rule


@counterexample("hygiene/no-packaging-in-source")
def _ce_np(root: Path) -> None:
    d = fixtures.skill(fixtures.base(root), "ok-skill")
    (d / ".claude-plugin").mkdir()
    (d / ".claude-plugin" / "plugin.json").write_text("{}", encoding="utf-8")


@lint_rule("hygiene/no-packaging-in-source", stage=Stage.CAPABILITY, constructs=ALL,
           applies_to="capability folder",
           requirement="Contains no generated-packaging directory (`.claude-plugin/`).",
           why="Packaging is generated; a hand-written packaging file looks "
               "authoritative while being ignored, which has misled readers "
               "for months at a time.")
def no_packaging_in_source(ctx: Context):
    stray = ctx.folder / ".claude-plugin"
    if stray.exists():
        yield Violation(
            stray,
            "source folders must not contain .claude-plugin/ — plugin metadata "
            "belongs in .metadata-SKILL.toml and packaging is generated",
        )


@counterexample("hygiene/metadata-keys")
def _ce_mk(root: Path) -> None:
    d = fixtures.skill(fixtures.base(root), "ok-skill")
    (d / ".metadata-SKILL.toml").write_text(
        'description = "ok"\nname = "sneaky"\n', encoding="utf-8"
    )


@lint_rule("hygiene/metadata-keys", stage=Stage.CAPABILITY,
           constructs=frozenset({"skill"}),
           applies_to="`.metadata-SKILL.toml`",
           requirement="Parses as TOML and declares only `description` (a non-empty string).",
           why="Only `description` is read by the generator; any other key is "
               "dead weight that a reader will assume does something.")
def metadata_keys(ctx: Context):
    meta = ctx.folder / ".metadata-SKILL.toml"
    if not meta.exists():
        return
    try:
        with open(meta, "rb") as f:
            data = tomllib.load(f)
    except tomllib.TOMLDecodeError as exc:
        yield Violation(meta, f"invalid TOML ({exc})")
        return
    except OSError as exc:
        yield Violation(meta, f"unreadable ({exc})")
        return
    extra = sorted(set(data) - {"description"})
    if extra:
        yield Violation(meta, f"keys {extra} are not read by the generator")
    desc = data.get("description")
    if desc is not None and (not isinstance(desc, str) or not desc):
        yield Violation(meta, "'description' must be a non-empty string")


@counterexample("hygiene/folder-matches-name")
def _ce_fm(root: Path) -> None:
    fixtures.multi_skill(
        fixtures.base(root), "multi", "alpha", "name: renamed\ndescription: x"
    )


@lint_rule("hygiene/folder-matches-name", stage=Stage.CAPABILITY,
           constructs=frozenset({"skill"}),
           applies_to="skill folder in the multi layout",
           requirement="The folder name equals the frontmatter `name`, when one is set.",
           why="Packaging is keyed by folder name while the agent surfaces the "
               "frontmatter name; if they disagree the same skill has two "
               "user-visible names.")
def folder_matches_name(ctx: Context):
    subdir = ctx.folder / "skills"
    if not subdir.is_dir():
        return
    for d in sorted(subdir.iterdir()):
        sk = d / "SKILL.md"
        if not sk.exists():
            continue
        fm_name = _frontmatter(sk).get("name")
        if fm_name and fm_name != d.name:
            yield Violation(
                sk, f"frontmatter name '{fm_name}' does not match folder '{d.name}'"
            )


@counterexample("hygiene/no-self-referential-skills-path")
def _ce_sr(root: Path) -> None:
    fixtures.base(root)
    d = fixtures.generated_plugin(root, "skill-alpha", "example-skill-alpha")
    pj = d / ".claude-plugin" / "plugin.json"
    data = json.loads(pj.read_text(encoding="utf-8"))
    data["skills"] = ["./"]
    pj.write_text(json.dumps(data), encoding="utf-8")


# ``"./"`` resolves to the plugin root, so a consumer that stages each declared
# path into a directory *under* that root copies the plugin into itself. Claude
# Code tolerates it; portable consumers do not. Measured: `apm install` dies
# with `maximum recursion depth exceeded` (microsoft/apm#2556). ``""``, ``"."``
# and ``"/"`` all normalise to the same place, so all four are refused.
@lint_rule("hygiene/no-self-referential-skills-path", stage=Stage.GENERATED,
           constructs=ALL,
           applies_to="generated plugin manifest `skills` path",
           requirement="Points at a subdirectory, never at the plugin root.",
           why="A path resolving to the plugin root makes a consumer copy the "
               "plugin into itself; one such consumer crashes outright rather "
               "than warning, so the skill silently never installs.")
def no_self_referential_skills_path(ctx: Context):
    for d in ctx.generated_plugin_dirs():
        data = ctx.read_json(d / ".claude-plugin" / "plugin.json")
        if not isinstance(data, dict):
            continue
        declared = data.get("skills")
        paths = declared if isinstance(declared, list) else [declared]
        for p in paths:
            if isinstance(p, str) and p.strip().strip("/").strip() in ("", "."):
                yield Violation(
                    d / ".claude-plugin" / "plugin.json",
                    f"skills path '{p}' resolves to the plugin root — declare a "
                    f"subdirectory such as './skills/' instead",
                )
