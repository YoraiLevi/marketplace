"""model.py — datatypes and decorators for the lint-rule registry.

A lint rule is ONE object that owns its identity, its explanation, its
severity, the code that enforces it, and input that provokes it. Two
consumers read the same object and nothing else describes a rule anywhere:

    LintRule
     ├─ scripts/lint.py            EXECUTES  rule.check
     └─ scripts/generate_manifest  DESCRIBES rule.requirement / .why and
                                   QUOTES the message produced by running
                                   rule.counterexample

Guarantees that hold by construction, not by test:
  - a rule with no check cannot be declared (the decorator wraps a function)
  - a rule with no counterexample cannot be declared (the decorator raises)
  - an emitted rule id cannot disagree with a declared one — checks yield a
    location and a detail; the reporter alone attaches ``rule.id``
  - ``severity`` is read by the driver, so the published severity IS the
    behaviour

Two axes per rule:
  - ``stage``      WHEN it runs (see Stage — inputs exist at different moments)
  - ``constructs`` WHO it applies to: a set of construct keys, or the ALL
    sentinel meaning "every construct, including ones that do not exist yet"

Rule ids are ``topic/slug`` (e.g. ``naming/folder-kebab-case``) so the error
message itself says what went wrong.
"""

from __future__ import annotations

import json
import re
import tomllib
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Final

from utils import _frontmatter


class Stage(StrEnum):
    IDENTITY = "identity"        # once, pre-generation
    CAPABILITY = "capability"    # per capability folder, pre-generation
    FILE = "file"                # per file under src/, pre-generation
    GENERATED = "generated"     # once, post-generation


class Severity(StrEnum):
    ERROR = "error"              # blocks publishing
    WARNING = "warning"          # advisory; never changes the exit status


# Sentinel: applies to every construct, including future ones. A rule that
# enumerates constructs fails OPEN when a new construct arrives (it silently
# stops covering it); ALL fails closed — new constructs are covered by default
# and must be excluded deliberately.
ALL: Final[frozenset[str]] = frozenset({"*"})

RULE_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*/[a-z0-9]+(?:-[a-z0-9]+)*$")


@dataclass(frozen=True)
class Violation:
    """One failure. Carries NO rule id and NO formatting — the reporter adds both.

    ``detail`` must not embed an absolute path: ``where`` is relativized when
    the docs capture an example, but a path baked into the prose cannot be,
    and would make the generated document differ per machine. Name the other
    location, do not path it.
    """

    where: Path | str
    detail: str


@dataclass
class Context:
    """What a rule is handed. Only the fields for its stage are populated.

    ``root`` is the repository root the driver is operating on — a parameter,
    not a global, precisely so a counterexample can build a throwaway
    repository and have the same rules run against it.

    Accessors are lazy and memoise ONLY in ``self._cache``. They must never
    delegate to utils' module-level caches (``_load_marketplace_toml`` /
    ``_load_plugin_json``): those are keyed to the real repo and would make
    fixture runs read the fork's real identity, breaking the drift gate
    differently on every fork.
    """

    root: Path
    construct: str | None = None   # set for CAPABILITY / FILE stages
    folder: Path | None = None     # CAPABILITY
    file: Path | None = None       # FILE
    _cache: dict = field(default_factory=dict, repr=False)

    # ── lazy accessors ──────────────────────────────────────────────────────

    def _resolve(self, rel: str | Path) -> Path:
        p = Path(rel)
        if p.is_absolute():
            return p
        base = self.folder if self.folder is not None else self.root
        return base / p

    def read_json(self, rel: str | Path) -> dict | list | None:
        """Parsed JSON, or None if missing/unparseable (S-rules that need the
        parse failure itself read the raw text instead)."""
        p = self._resolve(rel)
        key = ("json", p)
        if key not in self._cache:
            try:
                self._cache[key] = json.loads(p.read_text(encoding="utf-8-sig"))
            except (OSError, json.JSONDecodeError, UnicodeDecodeError):
                self._cache[key] = None
        return self._cache[key]

    def read_frontmatter(self, rel: str | Path) -> dict | None:
        """Frontmatter dict, or None if the file is missing. Empty dict means
        the file exists but has no frontmatter block."""
        p = self._resolve(rel)
        key = ("fm", p)
        if key not in self._cache:
            try:
                self._cache[key] = _frontmatter(p)
            except OSError:
                self._cache[key] = None
        return self._cache[key]

    def read_toml(self, rel: str | Path) -> dict | None:
        p = self._resolve(rel)
        key = ("toml", p)
        if key not in self._cache:
            try:
                with open(p, "rb") as f:
                    self._cache[key] = tomllib.load(f)
            except (OSError, tomllib.TOMLDecodeError):
                self._cache[key] = None
        return self._cache[key]

    def files(self, pattern: str) -> list[Path]:
        """Sorted glob under the capability folder — sorted because glob order
        is filesystem-dependent and rule output feeds a byte-identity gate."""
        base = self.folder if self.folder is not None else self.root
        key = ("glob", base, pattern)
        if key not in self._cache:
            self._cache[key] = sorted(p for p in base.glob(pattern) if p.is_file())
        return self._cache[key]

    def identity_path(self) -> Path:
        return self.root / "src" / ".metadata-MARKETPLACE.toml"

    def marketplace_identity(self) -> dict:
        """The identity file under ctx.root — NOT the real repo's."""
        key = ("identity",)
        if key not in self._cache:
            self._cache[key] = self.read_toml(self.identity_path()) or {}
        return self._cache[key]

    def marketplace_name(self) -> str:
        return self.marketplace_identity().get("marketplace", {}).get("name", "")

    def brand(self) -> str:
        name = self.marketplace_name()
        return name.removesuffix("-marketplace") if name.endswith("-marketplace") else name

    def generated_plugin_dirs(self) -> list[Path]:
        key = ("plugin_dirs",)
        if key not in self._cache:
            generated = self.root / "_generated" / "claude-code"
            self._cache[key] = (
                sorted(d for d in generated.iterdir() if d.is_dir())
                if generated.is_dir() else []
            )
        return self._cache[key]


@dataclass(frozen=True)
class LintRule:
    id: str                          # "naming/folder-kebab-case"
    stage: Stage
    constructs: frozenset[str]       # {"skill", ...} or the ALL sentinel
    applies_to: str                  # what a contributor recognizes
    requirement: str                 # what must be true
    why: str                         # the failure it prevents
    check: Callable[[Context], Iterable[Violation]]
    counterexample: Callable[[Path], None]
    severity: Severity = Severity.ERROR

    def applies_to_construct(self, construct: str | None) -> bool:
        # Membership, not identity: a hand-built frozenset({"*"}) that merely
        # EQUALS the sentinel must still match, or the rule silently runs
        # against nothing and the only symptom is a distant counterexample
        # failure pointing nowhere near the cause.
        return "*" in self.constructs or construct in self.constructs

    @property
    def topic(self) -> str:
        return self.id.split("/", 1)[0]


REGISTRY: list[LintRule] = []
_PENDING_COUNTEREXAMPLES: dict[str, Callable[[Path], None]] = {}


def counterexample(rule_id: str):
    """Register the input that must provoke ``rule_id``.

    Mandatory. A rule without one cannot be registered — that is what proves
    every published rule reachable and lets the renderer quote a real failure
    message instead of an invented one.
    """

    def deco(fn: Callable[[Path], None]):
        _PENDING_COUNTEREXAMPLES[rule_id] = fn
        return fn

    return deco


def lint_rule(rule_id: str, *, stage: Stage, constructs: frozenset[str],
              applies_to: str, requirement: str, why: str,
              severity: Severity = Severity.ERROR):
    """Register a check as a lint rule. The decorated function IS the enforcement."""

    def deco(fn: Callable[[Context], Iterable[Violation]]):
        if not RULE_ID.match(rule_id):
            raise ValueError(f"rule id '{rule_id}' is not topic/slug kebab-case")
        if any(r.id == rule_id for r in REGISTRY):
            raise ValueError(f"duplicate rule id '{rule_id}'")
        if "*" in constructs and constructs is not ALL:
            raise ValueError(
                f"rule {rule_id}: pass the ALL sentinel, not a raw {{'*'}} set"
            )
        if stage in (Stage.IDENTITY, Stage.GENERATED) and constructs is not ALL:
            raise ValueError(
                f"rule {rule_id}: {stage} rules must use constructs=ALL — "
                f"ctx.construct is None at that stage, so a narrower set "
                f"would silently never run"
            )
        try:
            example = _PENDING_COUNTEREXAMPLES.pop(rule_id)
        except KeyError:
            raise ValueError(
                f"rule {rule_id} has no @counterexample. Every rule must ship "
                f"input that provokes it, so it can be proven reachable and "
                f"documented with a real message."
            ) from None
        REGISTRY.append(LintRule(
            id=rule_id, stage=stage, constructs=constructs,
            applies_to=applies_to, requirement=requirement, why=why,
            check=fn, counterexample=example, severity=severity,
        ))
        return fn

    return deco
