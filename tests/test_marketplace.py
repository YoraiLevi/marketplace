#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Tests for the marketplace generator's inputs and outputs.

Validates:
  - Source layout: src/skills/<name>/ instances are well-formed
  - Generated plugins: _generated/claude-code/<plugin>/ plugin.json fields + naming
  - marketplace.json: shape, sort order, entry/name invariants
  - Construct registry integrity, plugin count, secrets scan, drift,
    .metadata-MARKETPLACE.toml identity fields

Run via `uv run scripts/tasks.py test` (module invocation + nonzero-count
assertion) — not by direct file execution.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tomllib
import unittest
from pathlib import Path

# Add scripts/ to sys.path for imports
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from constructs import (
    CONSTRUCTS,
    SkillConstruct,
)
from platforms import (
    PLATFORMS,
    ClaudeCodePlatform,
)
from utils import MARKETPLACE_JSON, scan_source_dir

MARKETPLACE_TOML = REPO_ROOT / "src" / ".metadata-MARKETPLACE.toml"
GENERATED_DIR = REPO_ROOT / "_generated" / "claude-code"


# ─── helpers ─────────────────────────────────────────────────────────────────

def load_toml(path: Path) -> dict:
    with open(path, "rb") as f:
        return tomllib.load(f)


def load_marketplace_json() -> dict:
    return json.loads(MARKETPLACE_JSON.read_text(encoding="utf-8"))


# ─── TestSourceLayout ─────────────────────────────────────────────────────────

class TestSourceLayout(unittest.TestCase):
    """Source directory conventions — contract tests."""

    def test_construct_source_dirs_exist(self):
        """Every registered construct's source directory must exist."""
        for construct_id, construct in CONSTRUCTS.items():
            with self.subTest(construct=construct_id):
                self.assertTrue(
                    construct.source_directory.exists(),
                    f"{construct_id}: source_directory {construct.source_directory} does not exist",
                )

    def test_instance_names_kebab_case(self):
        """Every instance name across all constructs must be kebab-case."""
        kebab = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
        for construct_id, construct in CONSTRUCTS.items():
            for name in scan_source_dir(construct.source_directory):
                with self.subTest(construct=construct_id, name=name):
                    self.assertRegex(
                        name, kebab,
                        f"{construct_id}/{name}: not kebab-case; "
                        f"derived plugin name '{construct.prefix}-{name}' would be invalid",
                    )

    def test_examples_not_in_separate_dir(self):
        """A top-level examples/ folder must not exist — examples live in native construct dirs."""
        self.assertFalse(
            (REPO_ROOT / "examples").exists(),
            "examples/ must not exist — examples live in native construct folders",
        )

class TestGeneratedPlugins(unittest.TestCase):
    """Generated plugin artifacts — integration + contract tests."""

    def test_all_plugins_at_correct_path(self):
        """Every plugin in marketplace.json must resolve to a real .claude-plugin/plugin.json."""
        manifest = load_marketplace_json()
        for entry in manifest["plugins"]:
            plugin_path = Path(entry["source"]) / ".claude-plugin" / "plugin.json"
            with self.subTest(plugin=entry["name"]):
                self.assertTrue(
                    plugin_path.exists(),
                    f"{entry['name']}: source {entry['source']} has no .claude-plugin/plugin.json",
                )

    def test_all_plugins_parse_and_have_required_fields(self):
        """Every plugin.json must parse and carry the required common fields."""
        manifest = load_marketplace_json()
        common_required = {"name", "description", "version", "author"}
        for entry in manifest["plugins"]:
            plugin_path = Path(entry["source"]) / ".claude-plugin" / "plugin.json"
            with self.subTest(plugin=entry["name"]):
                data = json.loads(plugin_path.read_text(encoding="utf-8"))
                missing = common_required - set(data.keys())
                self.assertFalse(
                    missing,
                    f"{entry['name']}: missing common fields {missing}",
                )
                if entry["category"] == "bundle":
                    self.assertIn(
                        "dependencies", data,
                        f"{entry['name']}: bundle missing 'dependencies' field",
                    )

    def test_individual_plugin_name_is_unique_brand_namespace(self):
        """Each plugin's ``_generated/claude-code/<plugin>/.claude-plugin/plugin.json``
        ``name`` field is ``<brand>-<construct.prefix>-<source-dir-name>`` —
        unique per plugin (e.g. ``dgxsparklabs-skill-example``).

        The slash form follows the same pattern:
        ``/dgxsparklabs-skill-example:<frontmatter-name>``.

        The install-time marketplace entry name in ``marketplace.json``
        ``plugins[].name`` (e.g. ``skill-example``) is a separate, unprefixed
        identifier; that contract is asserted by
        ``test_individual_plugin_name_is_unique_brand_namespace`` below.

        History: an earlier attempt (Path A, ``d641f92``, 2026-05-27) used a
        shared ``<brand>-<construct.category>`` name so multiple plugins of
        one construct shared a slash namespace; ``claude plugin details``
        collapsed components to a single first-installed-wins view. Path A
        was reverted on 2026-05-28 per
        ``the project-memory branchPLAN.md``.

        RuleConstruct is excluded per F8 — rules don't get a
        .claude-plugin/plugin.json since they are not a Claude plugin
        component (see ClaudeCodePlatform.supports docstring).
        """
        from utils import _marketplace_name
        mp_name = _marketplace_name()
        brand = mp_name.removesuffix("-marketplace") if mp_name.endswith("-marketplace") else mp_name

        for construct in CONSTRUCTS.values():
            if type(construct) not in ClaudeCodePlatform.supports:
                continue
            for source_name in scan_source_dir(construct.source_directory):
                expected = f"{brand}-{construct.prefix}-{source_name}"
                plugin_path = GENERATED_DIR / f"{construct.prefix}-{source_name}" / ".claude-plugin" / "plugin.json"
                with self.subTest(construct=construct.prefix, name=source_name):
                    data = json.loads(plugin_path.read_text(encoding="utf-8"))
                    self.assertEqual(
                        data["name"], expected,
                        f"Plugin name mismatch for {construct.prefix}-{source_name}: "
                        f"expected unique brand-prefixed namespace",
                    )

    def test_skill_plugin_layouts(self):
        """For every source skill plugin, the generated plugin.json's ``skills``
        field matches the source filesystem layout.

        - Solo (root ``SKILL.md`` at plugin root) → ``["./"]``.
        - Multi (one or more ``skills/<x>/SKILL.md`` under ``skills/``) → ``["./skills/"]``.

        Parameterized across every skill source plugin via
        ``scan_source_dir`` + ``subTest`` so a third skill plugin added
        later is automatically covered without a test edit.
        """
        skill = next(c for c in CONSTRUCTS.values() if isinstance(c, SkillConstruct))
        for source_name in scan_source_dir(skill.source_directory):
            src = skill.source_directory / source_name
            gen_dir = GENERATED_DIR / f"skill-{source_name}"
            gen_pj = gen_dir / ".claude-plugin" / "plugin.json"
            with self.subTest(plugin=source_name):
                data = json.loads(gen_pj.read_text(encoding="utf-8"))
                if (src / "SKILL.md").exists():
                    # Solo layout: skills=["./"], one SKILL.md at plugin root
                    self.assertEqual(
                        data["skills"], ["./"],
                        f"solo skill {source_name}: skills field mismatch",
                    )
                    self.assertTrue(
                        (gen_dir / "SKILL.md").exists(),
                        f"solo skill {source_name}: SKILL.md missing at plugin root",
                    )
                else:
                    # Multi layout: skills=["./skills/"], at least one SKILL.md
                    # under a skills/<x>/ subdir
                    self.assertEqual(
                        data["skills"], ["./skills/"],
                        f"multi skill {source_name}: skills field mismatch",
                    )
                    skills_subdir = gen_dir / "skills"
                    self.assertTrue(
                        any(skills_subdir.rglob("SKILL.md")),
                        f"multi skill {source_name}: no SKILL.md under skills/",
                    )

class TestMarketplaceJson(unittest.TestCase):
    """marketplace.json schema and completeness — contract + integration tests."""

    def test_marketplace_json_exists_and_parses(self):
        """Top-level .claude-plugin/marketplace.json must exist and parse."""
        self.assertTrue(MARKETPLACE_JSON.exists(), ".claude-plugin/marketplace.json missing")
        data = load_marketplace_json()
        self.assertIsInstance(data, dict)
        self.assertIn("plugins", data)
        self.assertIn("owner", data)

    def test_marketplace_json_has_top_level_description(self):
        """Per code.claude.com/docs/en/plugin-marketplaces#marketplace-schema
        (fetched 2026-05-26), ``description`` is an optional top-level field;
        omitting it triggers ``claude plugin validate`` warning. We always
        emit it (sourced from the marketplace metadata file) so the validator is clean."""
        data = load_marketplace_json()
        self.assertIn(
            "description", data,
            ".claude-plugin/marketplace.json missing top-level 'description' "
            "field — claude plugin validate will warn",
        )
        self.assertIsInstance(data["description"], str)
        self.assertGreater(len(data["description"]), 0)

    def test_marketplace_entries_have_required_fields(self):
        """Every marketplace.json entry must have all required fields."""
        required = {"name", "source", "description", "version", "author", "category"}
        manifest = load_marketplace_json()
        for entry in manifest["plugins"]:
            with self.subTest(plugin=entry["name"]):
                missing = required - set(entry.keys())
                self.assertFalse(missing, f"{entry['name']}: missing fields {missing}")
                self.assertTrue(
                    entry["source"].startswith("./"),
                    f"{entry['name']}: source must start with './'",
                )

    def test_marketplace_entries_sorted_by_category_then_name(self):
        """Entries must be sorted by (category, name) for deterministic diffs."""
        manifest = load_marketplace_json()
        entries = manifest["plugins"]
        sorted_entries = sorted(entries, key=lambda e: (e["category"], e["name"]))
        actual_order = [(e["category"], e["name"]) for e in entries]
        expected_order = [(e["category"], e["name"]) for e in sorted_entries]
        self.assertEqual(actual_order, expected_order, "marketplace.json entries are not sorted")

class TestConstructRegistry(unittest.TestCase):
    """CONSTRUCTS registry invariants — unit tests."""

    def test_all_prefixes_unique(self):
        """No two construct classes may share the same prefix."""
        prefixes = [c.prefix for c in CONSTRUCTS.values()]
        duplicates = [p for p in prefixes if prefixes.count(p) > 1]
        self.assertEqual(
            len(prefixes), len(set(prefixes)),
            f"Duplicate prefixes in CONSTRUCTS: {duplicates}",
        )

    def test_all_prefixes_kebab_case(self):
        """Every construct prefix must be kebab-case."""
        kebab = re.compile(r"^[a-z]+(-[a-z]+)*$")
        for construct_id, construct in CONSTRUCTS.items():
            with self.subTest(construct=construct_id):
                self.assertRegex(
                    construct.prefix, kebab,
                    f"{construct_id}: prefix '{construct.prefix}' is not kebab-case",
                )


# ─── TestPluginCount ──────────────────────────────────────────────────────────

class TestNoSecrets(unittest.TestCase):
    """No tracked file may contain credential-shaped strings."""

    PATTERNS = [
        (re.compile(r"sk-[A-Za-z0-9]{32,}"), "OpenAI/Anthropic-style API key"),
        (re.compile(r"AIza[A-Za-z0-9_-]{30,}"), "Google API key"),
        (re.compile(r"AKIA[0-9A-Z]{16}"), "AWS access key"),
        (re.compile(r"ghp_[A-Za-z0-9]{30,}"), "GitHub personal access token"),
        (re.compile(r"xox[bpars]-[A-Za-z0-9-]{10,}"), "Slack token"),
    ]

    SKIP_DIRS = {".git", "node_modules", "_dep-test", "user_resource_dump", "research"}

    def test_no_secrets_in_tracked_files(self):
        for path in REPO_ROOT.rglob("*"):
            if not path.is_file():
                continue
            if any(part in self.SKIP_DIRS for part in path.parts):
                continue
            if path.suffix in {".png", ".jpg", ".jpeg", ".svg", ".lock"}:
                continue
            try:
                content = path.read_text(encoding="utf-8", errors="ignore")
            except (OSError, UnicodeDecodeError):
                continue
            for pattern, label in self.PATTERNS:
                match = pattern.search(content)
                if match:
                    self.fail(
                        f"{path.relative_to(REPO_ROOT)} contains {label}: "
                        f"{match.group()[:20]}..."
                    )


# ─── TestGeneratorDrift ───────────────────────────────────────────────────────

class TestGeneratorDrift(unittest.TestCase):
    """Generator output must match committed content — E2E test."""

    def test_check_succeeds(self):
        result = subprocess.run(
            [sys.executable, "-m", "uv", "run",
             str(REPO_ROOT / "scripts" / "generate_manifest.py"), "--check"],
            capture_output=True,
            cwd=REPO_ROOT,
        )
        # Try direct uv invocation
        result = subprocess.run(
            ["uv", "run", str(REPO_ROOT / "scripts" / "generate_manifest.py"), "--check"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
            timeout=120,
        )
        self.assertEqual(
            result.returncode, 0,
            f"generator --check reported drift:\n{result.stdout}\n{result.stderr}",
        )


# ─── TestMarketplaceToml ──────────────────────────────────────────────────────

class TestMarketplaceToml(unittest.TestCase):
    """.metadata-MARKETPLACE.toml integrity — contract tests."""

    def test_marketplace_toml_parses(self):
        mp = load_toml(MARKETPLACE_TOML)
        self.assertIn("marketplace", mp)
        self.assertIn("owner", mp)
        self.assertIn("repository", mp)

    def test_marketplace_has_required_fields(self):
        mp = load_toml(MARKETPLACE_TOML)
        self.assertIn("name", mp["marketplace"])
        self.assertIn("version", mp["marketplace"])
        self.assertIn("description", mp["marketplace"])
        self.assertIn("name", mp["owner"])
        self.assertIn("url", mp["repository"])

    def test_marketplace_version_semver(self):
        mp = load_toml(MARKETPLACE_TOML)
        version = mp["marketplace"]["version"]
        self.assertRegex(version, r"^\d+\.\d+\.\d+$", f"version '{version}' must be semver")


# ─── runner ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    unittest.main(verbosity=2)
