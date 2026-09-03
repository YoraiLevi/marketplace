#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""lint.py — the lint driver.

This file contains no rules. It builds the context each stage needs, runs
every rule in ``scripts/lint_rules/`` against it, and formats the results.
The rules — ids, severities, explanations, checks, counterexamples — live in
the registry, which ``generate_manifest.py`` also renders into
``_generated/LINTING_RULES.md``. One declaration, two consumers.

The driver is deliberately construct-ignorant: it derives folder→construct
from the CONSTRUCTS registry and applies one filter
(``rule.stage`` matches AND ``rule.applies_to_construct(construct)``).
Adding a construct type adds a rules module, never a driver edit.

Stages run when their inputs exist:

    IDENTITY / CAPABILITY / FILE   before generation (this CLI)
    GENERATED                       after generation (generate_manifest.py)

Usage:
    uv run scripts/lint.py [path ...]
Exit 0 if clean, 1 if any ERROR-severity rule fired. Warnings print to
stderr and never change the exit status.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from constructs import CONSTRUCTS  # noqa: E402
from lint_rules import (  # noqa: E402
    LINT_RULES,
    Context,
    LintRule,
    Severity,
    Stage,
    Violation,
)
from utils import REPO_ROOT, SRC  # noqa: E402

# Folder-name → construct key, derived from the one registry that already
# knows (e.g. {"skills": "skill"}). No hand-kept duplicate list.
_DIR_TO_CONSTRUCT: dict[str, str] = {
    c.source_directory.name: key for key, c in CONSTRUCTS.items()
}

SOURCE_STAGES = {Stage.IDENTITY, Stage.CAPABILITY, Stage.FILE}


@dataclass(frozen=True)
class Finding:
    """A violation with the rule that produced it — the only place the two meet."""

    rule: LintRule
    violation: Violation

    def message(self, relative_to: Path | None = None) -> str:
        where = self.violation.where
        if relative_to is not None and isinstance(where, Path):
            try:
                where = where.relative_to(relative_to).as_posix()
            except ValueError:
                pass
        return f"{where}: {self.violation.detail} ({self.rule.id})"


# ─── discovery ───────────────────────────────────────────────────────────────

def construct_of(folder: Path) -> str | None:
    """The construct a capability folder belongs to (by its parent dir name)."""
    return _DIR_TO_CONSTRUCT.get(folder.parent.name)


def _capability_dirs(targets: list[Path]) -> list[Path]:
    """Capability instance dirs among the targets and their descendants.

    Candidates are ``[target, *target.rglob("*")]`` — the target ITSELF
    included, because tests and the CLI pass instance dirs directly
    (``lint.py <dir>``). Sorted for deterministic order.
    """
    out: set[Path] = set()
    for root in targets:
        if not root.is_dir():
            continue
        for d in [root, *(p for p in root.rglob("*") if p.is_dir())]:
            if d.parent.name in _DIR_TO_CONSTRUCT:
                out.add(d)
    return sorted(out)


def _files(targets: list[Path]) -> list[Path]:
    out: set[Path] = set()
    for root in targets:
        if root.is_file():
            out.add(root)
        elif root.is_dir():
            out.update(p for p in root.rglob("*") if p.is_file())
    return sorted(
        p for p in out if p.name != "__pycache__" and p.suffix != ".pyc"
    )


def _nearest_construct(path: Path) -> str | None:
    """Construct membership for a file: the nearest ancestor that IS a
    capability instance (its parent is a construct dir) determines it.

    ``src/skills/README.md`` sits in no instance → None → matched only by
    constructs=ALL rules, which is the intended semantics.
    """
    for ancestor in path.parents:
        if ancestor.parent.name in _DIR_TO_CONSTRUCT:
            return _DIR_TO_CONSTRUCT[ancestor.parent.name]
    return None


# ─── the driver ──────────────────────────────────────────────────────────────

def run(root: Path, stages: set[Stage],
        paths: list[Path] | None = None) -> list[Finding]:
    """Run every registered rule in ``stages`` against ``root``.

    ``paths`` narrows the CAPABILITY and FILE stages to a subtree (the CLI's
    ``lint.py <path>`` form). IDENTITY and GENERATED always consider the
    whole repository — they are not per-file concerns.
    """
    findings: list[Finding] = []
    targets = list(paths) if paths else [root / "src"]
    by_stage = {s: [r for r in LINT_RULES if r.stage is s] for s in Stage}

    def fire(rules: list[LintRule], ctx: Context) -> None:
        for r in rules:
            if not r.applies_to_construct(ctx.construct):
                continue
            for v in r.check(ctx):
                findings.append(Finding(r, v))

    if Stage.IDENTITY in stages:
        fire(by_stage[Stage.IDENTITY], Context(root=root))

    if Stage.CAPABILITY in stages:
        for folder in _capability_dirs(targets):
            fire(
                by_stage[Stage.CAPABILITY],
                Context(root=root, construct=construct_of(folder), folder=folder),
            )

    if Stage.FILE in stages:
        for f in _files(targets):
            fire(
                by_stage[Stage.FILE],
                Context(root=root, construct=_nearest_construct(f), file=f),
            )

    if Stage.GENERATED in stages:
        fire(by_stage[Stage.GENERATED], Context(root=root))

    return findings


def lint(paths: list[Path]) -> list[str]:
    """Source-stage findings as ERROR-severity message strings.

    The module's stable entry point: warnings are excluded so a caller can
    treat a non-empty result as "this does not publish".
    """
    return [
        f.message()
        for f in run(REPO_ROOT, SOURCE_STAGES, list(paths) or None)
        if f.rule.severity is Severity.ERROR
    ]


def main(argv: list[str]) -> int:
    paths = [Path(a).resolve() for a in argv] if argv else [SRC]
    missing = [p for p in paths if not p.exists()]
    for p in missing:
        print(f"  FAIL: {p}: path does not exist", file=sys.stderr)

    findings = run(REPO_ROOT, SOURCE_STAGES, [p for p in paths if p.exists()] or None)
    errors = [f for f in findings if f.rule.severity is Severity.ERROR]
    warnings = [f for f in findings if f.rule.severity is Severity.WARNING]

    for f in warnings:
        print(f"  WARN: {f.message()}", file=sys.stderr)
    for f in errors:
        print(f"  FAIL: {f.message()}", file=sys.stderr)

    if errors or missing:
        print(f"\n{len(errors) + len(missing)} problem(s) found.", file=sys.stderr)
        return 1
    scanned = ", ".join(p.name for p in paths)
    print(f"source OK ({scanned})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
