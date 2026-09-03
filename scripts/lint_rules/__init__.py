"""lint_rules — the authoritative lint-rule registry.

Topic modules are imported EXPLICITLY, in a fixed order — registration order
is generated-document order, and auto-discovery would make that depend on
filesystem enumeration. Add a topic module, add its import here.

Cross-registry validation happens at import time, so a broken registry
cannot be partially used: a counterexample without a rule fails the import —
not some later run.
"""

from __future__ import annotations

from . import model
from .model import (  # noqa: F401 — re-exported for consumers
    ALL,
    Context,
    LintRule,
    Severity,
    Stage,
    Violation,
    counterexample,
    lint_rule,
)

# Registration order = doc order.
from . import naming, hygiene, content  # noqa: E402, F401

LINT_RULES: tuple[LintRule, ...] = tuple(model.REGISTRY)
LINT_RULES_BY_ID: dict[str, LintRule] = {r.id: r for r in LINT_RULES}

if model._PENDING_COUNTEREXAMPLES:
    raise ValueError(
        "counterexamples registered for rules that were never declared: "
        f"{sorted(model._PENDING_COUNTEREXAMPLES)}"
    )

