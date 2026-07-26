#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""validate_source.py — fast, friendly checks on construct sources (FR-13).

Runs at author time (and as a pre-commit hook) so a malformed source is caught
before the slower generate / --check / `claude plugin validate` cycle. Checks,
for each given path (default: all of src/):

  - every *.md with YAML frontmatter has a non-empty `description:`
  - every *.json parses
  - every ${CLAUDE_PLUGIN_ROOT}/<file> reference inside a *.json points at a
    file that exists in the plugin dir (catches the "config references a missing
    script" class — e.g. an lsp-config.json pointing at an untracked .py)
  - construct instance directory names are kebab-case

Usage:
    uv run scripts/validate_source.py [path ...]
Exit 0 if clean, 1 if any problem is found.
"""
from __future__ import annotations

import json
import re
import tomllib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils import SRC, _frontmatter, _marketplace_name, skill_components  # noqa: E402

KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
PLUGIN_ROOT_REF = re.compile(r"\$\{CLAUDE_PLUGIN_ROOT\}/([^\"'\s]+)")
CONSTRUCT_DIRS = {
    "skills",
}

# ─── naming standard (issue #19, rules N1/N2/N4; probed on CLI 2.1.220) ──────
# The CLI hard-rejects only {skills-dir, builtin} as marketplace names; every
# other reserved word below passed `claude plugin validate` in live probes, so
# CI is the ONLY gate for them. Composition invariants (N3/N5) live in
# tests/test_marketplace.py next to the drift check.
RESERVED_MARKETPLACES = {
    "skills-dir", "builtin",                      # CLI-enforced (exact errors probed)
    "claude-plugins-official",                    # preinstalled official marketplace
    "local", "user", "project", "claude", "anthropic",  # scope words / vendor
}
# Built-in slash commands a component name SHOULD not shadow (warning only —
# components always surface as /<plugin>:<component>, never bare).
BUILTIN_SLASH_NAMES = {
    "config", "theme", "agents", "mcp", "plugin", "help", "init", "clear",
    "compact", "resume", "fast", "code-review", "review", "security-review",
}


def _check_marketplace_identity(problems: list[str]) -> None:
    """N1 — marketplace identity rules on src/.metadata-MARKETPLACE.toml [marketplace] name."""
    name = _marketplace_name()
    if not KEBAB.match(name):
        problems.append(f".metadata-MARKETPLACE.toml name '{name}': not kebab-case (N1.1)")
    if not name.endswith("-marketplace"):
        problems.append(
            f".metadata-MARKETPLACE.toml name '{name}': must end in '-marketplace' — the "
            f"brand prefix is derived by stripping that suffix (N1.2)"
        )
    else:
        brand = name.removesuffix("-marketplace")
        if not brand or not KEBAB.match(brand):
            problems.append(
                f".metadata-MARKETPLACE.toml name '{name}': stripped brand '{brand}' is "
                f"empty or not kebab-case (N1.3)"
            )
    if name in RESERVED_MARKETPLACES:
        problems.append(
            f".metadata-MARKETPLACE.toml name '{name}': reserved marketplace identity (N1.4)"
        )
    if not (3 <= len(name) <= 64):
        problems.append(
            f".metadata-MARKETPLACE.toml name '{name}': length {len(name)} outside 3-64 (N1.5)"
        )


def _check_component_names(plugin_dir: Path, problems: list[str]) -> None:
    """N4 — component names: kebab, 1-32 chars, unique within the plugin."""
    seen: dict[str, Path] = {}
    for entry in skill_components(plugin_dir):
        comp = entry["name"]
        src_file = plugin_dir / (entry["dir"] or "") if entry["dir"] else plugin_dir
        src_file = (plugin_dir / "skills" / entry["dir"] / "SKILL.md") if entry["dir"] else (plugin_dir / "SKILL.md")
        if not KEBAB.match(comp):
            problems.append(f"{src_file}: component name '{comp}' not kebab-case (N4.1)")
        if not (1 <= len(comp) <= 32):
            problems.append(
                f"{src_file}: component name '{comp}' length {len(comp)} outside 1-32 (N4.2)"
            )
        if comp in seen:
            problems.append(
                f"{src_file}: component name '{comp}' duplicates {seen[comp]} "
                f"within the same plugin (N4.3)"
            )
        seen[comp] = src_file
        if comp in BUILTIN_SLASH_NAMES:
            print(
                f"  WARN: {src_file}: component name '{comp}' shadows a "
                f"built-in slash command (N4.4 — warning only)",
                file=sys.stderr,
            )


def _check_source_metadata(plugin_dir: Path, problems: list[str]) -> None:
    """R6 — source metadata hygiene.

    Source trees carry intent, not platform shapes: the generator alone
    writes ``.claude-plugin/`` (into ``_generated/``). Two checks:

    1. A source ``.claude-plugin/`` directory must NOT exist at all — it is
       always dead weight wearing a generated file's costume (the pre-refactor
       key-allowlist version of this rule caught a stale ``name`` that had
       misled readers for two months).
    2. ``.metadata-SKILL.toml``, if present, must parse as TOML and contain
       only the keys the generator reads (``description``, non-empty string).
    """
    stray = plugin_dir / ".claude-plugin"
    if stray.exists():
        problems.append(
            f"{stray}: source trees must not contain .claude-plugin/ — plugin "
            f"metadata belongs in .metadata-SKILL.toml; the generator emits "
            f".claude-plugin/ under _generated/ (R6)"
        )
    meta = plugin_dir / ".metadata-SKILL.toml"
    if not meta.exists():
        return
    try:
        with open(meta, "rb") as f:
            data = tomllib.load(f)
    except tomllib.TOMLDecodeError as exc:
        problems.append(f"{meta}: invalid TOML ({exc}) (R6)")
        return
    except OSError as exc:
        problems.append(f"{meta}: unreadable ({exc}) (R6)")
        return
    extra = set(data) - {"description"}
    if extra:
        problems.append(
            f"{meta}: keys {sorted(extra)} are not read by the generator — "
            f"only 'description' is allowed (R6)"
        )
    desc = data.get("description")
    if desc is not None and (not isinstance(desc, str) or not desc):
        problems.append(f"{meta}: 'description' must be a non-empty string (R6)")


def _check_multi_layout_folder_names(plugin_dir: Path, problems: list[str]) -> None:
    """R8 — multi-layout skill folder name must equal its frontmatter name.

    Mirrors are keyed by folder name while the CLI surfaces the frontmatter
    name; they agree by convention only, and drift would give the same skill
    two user-visible names. Multi-layout only: a solo plugin's dir names the
    PLUGIN, its frontmatter names the component — those differ by design.
    """
    subdir = plugin_dir / "skills"
    if not subdir.is_dir():
        return
    for d in sorted(subdir.iterdir()):
        sk = d / "SKILL.md"
        if not sk.exists():
            continue
        fm_name = _frontmatter(sk).get("name")
        if fm_name and fm_name != d.name:
            problems.append(
                f"{sk}: frontmatter name '{fm_name}' != folder name "
                f"'{d.name}' (R8 — they must match)"
            )


def _check_md(path: Path, problems: list[str]) -> None:
    fm = _frontmatter(path)
    if not fm:
        return  # plain markdown (e.g. README) - nothing to check
    # Require 'description' (the marketplace-listing one-liner). 'name' is NOT
    # required: commands derive their name from the filename stem, so requiring
    # it would false-positive on every command .md.
    if not fm.get("description"):
        problems.append(f"{path}: frontmatter missing or empty 'description'")


def _check_json(path: Path, problems: list[str]) -> None:
    try:
        text = path.read_text(encoding="utf-8-sig")
        json.loads(text)
    except (json.JSONDecodeError, UnicodeDecodeError, OSError) as exc:
        problems.append(f"{path}: invalid JSON ({exc})")
        return
    for m in PLUGIN_ROOT_REF.finditer(text):
        ref = m.group(1)
        if not (path.parent / ref).exists():
            problems.append(
                f"{path}: references ${{CLAUDE_PLUGIN_ROOT}}/{ref} "
                f"but {path.parent / ref} does not exist"
            )


def _iter_files(root: Path):
    if root.is_file():
        yield root
    elif root.is_dir():
        yield from (p for p in root.rglob("*") if p.is_file())


def _iter_instance_dirs(root: Path):
    """Yield directories that are an instance under a construct dir (.../<construct>/<name>)."""
    candidates = [root] if root.is_dir() else []
    if root.is_dir():
        candidates += [d for d in root.rglob("*") if d.is_dir()]
    for d in candidates:
        if d.parent.name in CONSTRUCT_DIRS:
            yield d


def validate(paths: list[Path]) -> list[str]:
    problems: list[str] = []
    for root in paths:
        if not root.exists():
            problems.append(f"{root}: path does not exist")
            continue
        for f in _iter_files(root):
            if f.name == "__pycache__" or f.suffix == ".pyc":
                continue
            if f.suffix == ".md":
                _check_md(f, problems)
            elif f.suffix == ".json":
                _check_json(f, problems)
        for d in _iter_instance_dirs(root):
            if not KEBAB.match(d.name):
                problems.append(f"{d}: instance directory name is not kebab-case (N2.1)")
            if len(d.name) > 32:
                problems.append(
                    f"{d}: instance directory name length {len(d.name)} exceeds 32 (N2.2)"
                )
            _check_component_names(d, problems)
            _check_source_metadata(d, problems)
            _check_multi_layout_folder_names(d, problems)
    _check_marketplace_identity(problems)
    return problems


def main(argv: list[str]) -> int:
    paths = [Path(a).resolve() for a in argv] if argv else [SRC]
    problems = validate(paths)
    if problems:
        for p in problems:
            print(f"  FAIL: {p}", file=sys.stderr)
        print(f"\n{len(problems)} problem(s) found.", file=sys.stderr)
        return 1
    scanned = ", ".join(p.name for p in paths)
    print(f"source OK ({scanned})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
