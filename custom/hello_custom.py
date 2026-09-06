#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""hello_custom.py — the smallest possible custom/ script.

A working hello-world for the fork-owned extension zone (docs/UPDATING.md). It
does nothing useful on purpose: it shows where a fork's own scripts live and how
they are written (PEP 723 + `uv run`, standard library only). Copy it, or delete
it — the template treats custom/ as yours.

Run it directly:
    uv run custom/hello_custom.py

Driven by .github/workflows/custom-hello.yml as a manual (workflow_dispatch)
example.
"""
from __future__ import annotations

from datetime import datetime, timezone


def greeting(now: datetime | None = None) -> str:
    """The one line this example prints — factored out so custom/tests/ can assert it."""
    stamp = (now or datetime.now(timezone.utc)).strftime("%Y-%m-%dT%H:%M:%SZ")
    return f"Hello from the custom/ extension zone at {stamp}."


def main() -> int:
    print(greeting())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
