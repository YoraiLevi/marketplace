"""content.py — lint rules about the contents of individual source files.

FILE-stage rules run once per file under the scanned tree, regardless of
which capability folder it sits in — all three are constructs=ALL, because a
markdown or JSON file of the NEXT construct type needs these checks exactly
as much as a skill's does.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from utils import _frontmatter

from . import fixtures
from .model import ALL, Context, Stage, Violation, counterexample, lint_rule

PLUGIN_ROOT_REF = re.compile(r"\$\{CLAUDE_PLUGIN_ROOT\}/([^\"'\s]+)")


@counterexample("content/description-required")
def _ce_dr(root: Path) -> None:
    fixtures.skill(fixtures.base(root), "ok-skill", "name: ok-skill")


@lint_rule("content/description-required", stage=Stage.FILE, constructs=ALL,
           applies_to="any markdown file with frontmatter",
           requirement="Declares a non-empty `description`.",
           why="It is both the relevance hint the agent reads and the "
               "marketplace catalog line; an entry without one is unusable "
               "in a listing.")
def description_required(ctx: Context):
    if ctx.file.suffix != ".md":
        return
    fm = _frontmatter(ctx.file)
    if fm and not fm.get("description"):
        yield Violation(ctx.file, "frontmatter is missing or has an empty 'description'")


@counterexample("content/json-parses")
def _ce_jp(root: Path) -> None:
    d = fixtures.skill(fixtures.base(root), "ok-skill")
    (d / "config.json").write_text("{not json", encoding="utf-8")


@lint_rule("content/json-parses", stage=Stage.FILE, constructs=ALL,
           applies_to="any JSON file in a source folder",
           requirement="Parses as valid JSON.",
           why="A malformed config is skipped at load time with the reason "
               "visible only in debug output.")
def json_parses(ctx: Context):
    if ctx.file.suffix != ".json":
        return
    try:
        json.loads(ctx.file.read_text(encoding="utf-8-sig"))
    except (json.JSONDecodeError, UnicodeDecodeError, OSError) as exc:
        yield Violation(ctx.file, f"invalid JSON ({exc})")


@counterexample("content/bundled-file-exists")
def _ce_bf(root: Path) -> None:
    d = fixtures.skill(fixtures.base(root), "ok-skill")
    (d / "config.json").write_text(
        '{"args": ["${CLAUDE_PLUGIN_ROOT}/missing.py"]}', encoding="utf-8"
    )


@lint_rule("content/bundled-file-exists", stage=Stage.FILE, constructs=ALL,
           applies_to="bundled-file references in JSON",
           requirement="Every `${CLAUDE_PLUGIN_ROOT}/<path>` reference resolves "
                       "to a file that exists in the folder.",
           why="Catches the 'config points at a script nobody committed' "
               "failure, which otherwise surfaces only when a user runs the "
               "capability.")
def bundled_file_exists(ctx: Context):
    if ctx.file.suffix != ".json":
        return
    try:
        text = ctx.file.read_text(encoding="utf-8-sig")
        json.loads(text)
    except (json.JSONDecodeError, UnicodeDecodeError, OSError):
        return  # content/json-parses owns unparseable JSON
    for m in PLUGIN_ROOT_REF.finditer(text):
        ref = m.group(1)
        if not (ctx.file.parent / ref).exists():
            yield Violation(
                ctx.file,
                f"references ${{CLAUDE_PLUGIN_ROOT}}/{ref} but that file does not exist",
            )
