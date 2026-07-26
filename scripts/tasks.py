#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""tasks.py — one-verb task runner for the common workflows (NFR-8).

Usage:
    uv run scripts/tasks.py <task>

Tasks:
    regen    regenerate manifests / the catalog doc from src/
    check    drift-check only (no writes; exit 1 on drift)
    test     run all the test suites (SUITES below)
    verify   check + test + `claude plugin validate ./`
             (the validate step is skipped with a warning if the `claude`
             CLI is not on PATH, so `verify` is usable on any dev box)
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # repo root (this file lives in scripts/)

SUITES = ("test_marketplace", "test_tooling")


def run(cmd: list[str]) -> int:
    print(f"\n$ {' '.join(cmd)}", flush=True)
    return subprocess.call(cmd, cwd=ROOT)


def regen() -> int:
    return run(["uv", "run", "scripts/generate_manifest.py"])


def check() -> int:
    return run(["uv", "run", "scripts/generate_manifest.py", "--check"])


def test() -> int:
    rc = 0
    for suite in SUITES:
        # Run via `-m unittest` AND assert a nonzero test count. Direct
        # execution (`uv run tests/<suite>.py`) imports-and-exits-0 when a
        # suite file loses its __main__ block — that turned this gate
        # vacuously green once (PR #38, commit 5078a5a; PITFALLS entry
        # preserved on the project-memory branch).
        cmd = ["uv", "run", "-m", "unittest", "-v", f"tests.{suite}"]
        print(f"\n$ {' '.join(cmd)}", flush=True)
        proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        sys.stdout.write(proc.stdout)
        sys.stderr.write(proc.stderr)
        combined = proc.stdout + proc.stderr
        m = re.search(r"Ran (\d+) tests?", combined)
        if not m or int(m.group(1)) == 0:
            print(f"[test] FAIL: {suite} ran ZERO tests — vacuous green rejected")
            rc |= 1
        rc |= proc.returncode
    return rc


def verify() -> int:
    rc = run(["uv", "run", "scripts/validate_source.py"])
    rc |= check()
    rc |= test()
    if shutil.which("claude"):
        rc |= run(["claude", "plugin", "validate", "./"])
    else:
        print(
            "\n[verify] WARNING: 'claude' CLI not on PATH — "
            "skipping `claude plugin validate ./` (run it in CI / a Claude env)."
        )
    print("\n" + ("VERIFY OK" if rc == 0 else "VERIFY FAILED"))
    return rc


TASKS = {"regen": regen, "check": check, "test": test, "verify": verify}


def main(argv: list[str]) -> int:
    if len(argv) != 1 or argv[0] not in TASKS:
        print(f"usage: uv run scripts/tasks.py <{'|'.join(TASKS)}>", file=sys.stderr)
        return 2
    return TASKS[argv[0]]()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
