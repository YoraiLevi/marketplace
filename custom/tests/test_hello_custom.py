#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Example custom test — proof that custom/tests/ runs.

Forks put their own tests here; `uv run scripts/tasks.py test` discovers and runs
them next to the template's own suites (a fork never edits a template-owned file
to get its tests run). Delete or replace this file freely.
"""
from __future__ import annotations

import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

# custom/tests/ -> custom/ on the path, so the example script imports cleanly.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import hello_custom  # noqa: E402


class TestHelloCustom(unittest.TestCase):
    def test_greeting_is_stable_and_stamped(self):
        fixed = datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc)
        self.assertEqual(
            hello_custom.greeting(fixed),
            "Hello from the custom/ extension zone at 2026-01-02T03:04:05Z.",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
