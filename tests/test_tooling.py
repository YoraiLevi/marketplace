#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Tests for the contributor tooling scripts (scripts/new_construct.py,
scripts/lint.py).

Validates:
  - lint flags missing description, invalid JSON, a missing
    ${CLAUDE_PLUGIN_ROOT} reference, and a non-kebab instance dir; passes on
    well-formed sources AND on the real src/ tree.
  - new_construct's kebab guard and example-template selection.
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import lint  # noqa: E402
import new_construct  # noqa: E402
from constructs import CONSTRUCTS  # noqa: E402
from utils import SRC  # noqa: E402

class TestLintCli(unittest.TestCase):
    def test_good_skill_passes(self):
        with tempfile.TemporaryDirectory() as t:
            d = Path(t) / "skills" / "good"
            d.mkdir(parents=True)
            (d / "SKILL.md").write_text(
                "---\nname: good\ndescription: A good skill.\n---\nbody\n", encoding="utf-8"
            )
            self.assertEqual(lint.lint([d]), [])

    def test_bad_component_name_flagged(self):
        with tempfile.TemporaryDirectory() as t:
            d = Path(t) / "skills" / "bad-comp"
            d.mkdir(parents=True)
            (d / "SKILL.md").write_text(
                "---\nname: My Bad Skill\ndescription: x\n---\nbody\n",
                encoding="utf-8",
            )

            self.assertTrue(any("naming/skill-name-kebab-case" in p for p in lint.lint([d])))

    def test_duplicate_component_names_flagged(self):
        with tempfile.TemporaryDirectory() as t:
            d = Path(t) / "skills" / "dup"
            for sub in ("a", "b"):
                sd = d / "skills" / sub
                sd.mkdir(parents=True)
                (sd / "SKILL.md").write_text(
                    "---\nname: same\ndescription: x\n---\nbody\n",
                    encoding="utf-8",
                )

            self.assertTrue(any("naming/skill-name-unique" in p for p in lint.lint([d])))

    def test_overlong_instance_dir_flagged(self):
        with tempfile.TemporaryDirectory() as t:
            d = Path(t) / "skills" / ("x" * 33)
            d.mkdir(parents=True)
            (d / "SKILL.md").write_text(
                "---\nname: x\ndescription: x\n---\nbody\n",
                encoding="utf-8",
            )

            self.assertTrue(any("naming/folder-length" in p for p in lint.lint([d])))

    def test_source_claude_plugin_dir_flagged(self):
        with tempfile.TemporaryDirectory() as t:
            d = Path(t) / "skills" / "strayshape"
            (d / ".claude-plugin").mkdir(parents=True)
            (d / "SKILL.md").write_text(
                "---\nname: strayshape\ndescription: x\n---\nbody\n",
                encoding="utf-8",
            )
            (d / ".claude-plugin" / "plugin.json").write_text(
                '{"description": "x"}', encoding="utf-8"
            )
            self.assertTrue(
                any("hygiene/no-packaging-in-source" in p for p in lint.lint([d]))
            )

    def test_metadata_toml_stray_key_flagged(self):
        with tempfile.TemporaryDirectory() as t:
            d = Path(t) / "skills" / "straykey"
            d.mkdir(parents=True)
            (d / "SKILL.md").write_text(
                "---\nname: straykey\ndescription: x\n---\nbody\n",
                encoding="utf-8",
            )
            (d / ".metadata-SKILL.toml").write_text(
                'description = "x"\nname = "stale-name"\n', encoding="utf-8"
            )
            self.assertTrue(
                any("hygiene/metadata-keys" in p for p in lint.lint([d]))
            )

    def test_metadata_toml_invalid_flagged(self):
        with tempfile.TemporaryDirectory() as t:
            d = Path(t) / "skills" / "badtoml"
            d.mkdir(parents=True)
            (d / "SKILL.md").write_text(
                "---\nname: badtoml\ndescription: x\n---\nbody\n",
                encoding="utf-8",
            )
            (d / ".metadata-SKILL.toml").write_text("not = = toml", encoding="utf-8")
            self.assertTrue(
                any("hygiene/metadata-keys" in p for p in lint.lint([d]))
            )

    def test_multi_layout_name_mismatch_flagged(self):
        with tempfile.TemporaryDirectory() as t:
            sd = Path(t) / "skills" / "mismatch" / "skills" / "folder-name"
            sd.mkdir(parents=True)
            (sd / "SKILL.md").write_text(
                "---\nname: other-name\ndescription: x\n---\nbody\n",
                encoding="utf-8",
            )
            self.assertTrue(
                any("hygiene/folder-matches-name" in p for p in lint.lint([sd.parent.parent]))
            )

    def test_real_marketplace_identity_passes(self):
        # The identity rules run against the repo's real
        # .metadata-MARKETPLACE.toml in every lint() call. Filter by RULE ID,
        # not by message prefix — messages start with a path, so a prefix
        # filter would match nothing and pass vacuously.
        self.assertFalse(
            [p for p in lint.lint([]) if "naming/marketplace-" in p]
        )

    def test_missing_description_flagged(self):
        with tempfile.TemporaryDirectory() as t:
            d = Path(t) / "skills" / "bad"
            d.mkdir(parents=True)
            (d / "SKILL.md").write_text("---\nname: bad\n---\nbody\n", encoding="utf-8")
            self.assertTrue(any("description" in p for p in lint.lint([d])))

    def test_missing_plugin_root_ref_flagged(self):
        with tempfile.TemporaryDirectory() as t:
            d = Path(t) / "lsp-servers" / "x"
            d.mkdir(parents=True)
            (d / "lsp-config.json").write_text(
                '{"args": ["${CLAUDE_PLUGIN_ROOT}/nope.py"]}', encoding="utf-8"
            )
            self.assertTrue(any("nope.py" in p for p in lint.lint([d])))

    def test_present_plugin_root_ref_ok(self):
        with tempfile.TemporaryDirectory() as t:
            d = Path(t) / "lsp-servers" / "x"
            d.mkdir(parents=True)
            (d / "server.py").write_text("# server\n", encoding="utf-8")
            (d / "lsp-config.json").write_text(
                '{"args": ["${CLAUDE_PLUGIN_ROOT}/server.py"]}', encoding="utf-8"
            )
            self.assertEqual(lint.lint([d]), [])

    def test_invalid_json_flagged(self):
        with tempfile.TemporaryDirectory() as t:
            d = Path(t) / "mcp-servers" / "x"
            d.mkdir(parents=True)
            (d / "mcp-config.json").write_text("{not json", encoding="utf-8")
            self.assertTrue(any("invalid JSON" in p for p in lint.lint([d])))

    def test_non_kebab_instance_dir_flagged(self):
        with tempfile.TemporaryDirectory() as t:
            d = Path(t) / "skills" / "Bad_Name"
            d.mkdir(parents=True)
            (d / "SKILL.md").write_text("---\ndescription: x\n---\n", encoding="utf-8")
            self.assertTrue(any("kebab-case" in p for p in lint.lint([d])))

    def test_real_src_is_clean(self):
        # The shipped sources must pass their own validator.
        self.assertEqual(lint.lint([SRC]), [])

class TestDriftGateReadOnly(unittest.TestCase):
    """Regression: --check must be read-only and deterministic (fail twice).

    Three independent newcomer walkthroughs hit the old behavior where a
    failing --check regenerated the tree in place, so the SECOND run passed
    with zero user action (fail-once-then-pass). The fix restores the
    pre-check tree on drift; this test injects drift and asserts BOTH runs
    fail and the tampered byte survives the check untouched.
    """

    def test_check_fails_twice_and_restores_tree(self):
        import subprocess

        inv = REPO_ROOT / "_generated" / "CATALOG_AND_INSTALLATION_INSTRUCTIONS.md"
        original = inv.read_bytes()
        try:
            inv.write_bytes(original + b"tampered\n")
            for run_no in (1, 2):
                proc = subprocess.run(
                    ["uv", "run", "scripts/generate_manifest.py", "--check"],
                    cwd=REPO_ROOT, capture_output=True, text=True,
                )
                self.assertEqual(
                    proc.returncode, 1,
                    f"run {run_no}: --check must fail on drift every time "
                    f"(got {proc.returncode}); fail-once-then-pass means the "
                    f"check wrote to the tree",
                )
            self.assertEqual(
                inv.read_bytes(), original + b"tampered\n",
                "--check must leave the drifted file exactly as it found it",
            )
        finally:
            inv.write_bytes(original)

class TestNewConstruct(unittest.TestCase):
    def test_kebab_regex(self):
        self.assertTrue(new_construct.KEBAB.match("telegram-notify"))
        self.assertFalse(new_construct.KEBAB.match("Bad_Name"))
        self.assertFalse(new_construct.KEBAB.match("UPPER"))

    def test_pick_example_prefers_single_or_multi(self):
        # Forks may delete the shipped examples (they own src/ entirely);
        # the preference order is only testable while examples exist.
        src = CONSTRUCTS["skill"].source_directory
        available = {d.name for d in src.iterdir() if d.is_dir()}
        if "example-single" not in available or "example-multi" not in available:
            self.skipTest("shipped examples not present (fork-owned src/)")
        self.assertEqual(new_construct._pick_example(src, multi=False), "example-single")
        self.assertEqual(new_construct._pick_example(src, multi=True), "example-multi")

    def test_scaffold_falls_back_without_examples(self):
        # A fork that deleted the examples must still be able to scaffold.
        with tempfile.TemporaryDirectory() as t:
            empty = Path(t)
            self.assertIsNone(new_construct._pick_example(empty, multi=False))
            content = new_construct._builtin_template("my-skill")
            self.assertIn("name: my-skill", content)
            self.assertIn("description:", content)

if __name__ == "__main__":
    unittest.main(verbosity=2)
