#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""new_construct.py — scaffold a new construct source dir from the example (FR-11).

Usage:
    uv run scripts/new_construct.py <type> <name> [--multi]

<type> is one of the construct types (skill, rule, command, agent, hook, mcp,
lsp, monitor, output-style, theme). <name> is kebab-case. The chosen example
(example-single by default, example-multi with --multi; rule has a single
'example') is copied to src/<construct>/<name>/. Then edit the copied files,
push (CI regenerates all manifests; running the generator locally is optional), and
the plugin <prefix>-<name> becomes installable. No marketplace-metadata edit needed.
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from constructs import CONSTRUCTS  # noqa: E402
from utils import REPO_ROOT, scan_source_dir  # noqa: E402

KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def _pick_example(src_dir: Path, multi: bool) -> str | None:
    """Choose the example template to copy from a construct's source dir."""
    available = set(scan_source_dir(src_dir))
    preferred = "example-multi" if multi else "example-single"
    for cand in (preferred, "example", "example-single", "example-multi"):
        if cand in available:
            return cand
    return None


def _builtin_template(name: str) -> str:
    """Minimal solo-layout SKILL.md used when no example exists to copy.

    Forks own src/ entirely and may delete the shipped examples; scaffolding
    must keep working from this built-in template afterwards.
    """
    lines = [
        "---",
        "name: " + name,
        "description: TODO - one-line description shown in the marketplace listing.",
        "allowed-tools:",
        "  - Bash",
        "---",
        "",
        "TODO: instructions the model follows when this skill is invoked.",
        "",
    ]
    return chr(10).join(lines)


def main() -> int:
    p = argparse.ArgumentParser(
        description="Scaffold a new construct source dir from the example template."
    )
    p.add_argument("type", choices=sorted(CONSTRUCTS), help="construct type")
    p.add_argument("name", help="new construct name (kebab-case)")
    p.add_argument(
        "--multi", action="store_true",
        help="copy example-multi instead of example-single",
    )
    args = p.parse_args()

    if not KEBAB.match(args.name):
        print(
            f"error: name '{args.name}' must be kebab-case "
            f"(lowercase letters/digits, hyphen-separated)",
            file=sys.stderr,
        )
        return 2

    construct = CONSTRUCTS[args.type]
    src_dir = construct.source_directory
    example = _pick_example(src_dir, args.multi)

    dest = src_dir / args.name
    if dest.exists():
        print(f"error: {dest} already exists", file=sys.stderr)
        return 1

    if example is None:
        # Examples deleted (fork-owned src/) - scaffold from the built-in
        # minimal solo-layout template instead of copying.
        dest.mkdir(parents=True)
        (dest / "SKILL.md").write_text(
            _builtin_template(args.name), encoding="utf-8", newline=""
        )
        example = "built-in template"
    else:
        shutil.copytree(
            src_dir / example, dest,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )

    plugin = f"{construct.prefix}-{args.name}"
    rel = dest.relative_to(REPO_ROOT).as_posix()
    print(f"Created {rel}/ (from {example})")
    print("Next:")
    print(f"  1. Edit the copied files - set name:/description: and the body.")
    print(f"  2. uv run scripts/validate_source.py {rel}")
    print(f"  3. git add/commit/push - CI regenerates all manifests for you")
    print(f"     (optional local preview: uv run scripts/tasks.py verify)")
    print(f"  -> plugin '{plugin}' appears in the marketplace; no marketplace-metadata edit needed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
