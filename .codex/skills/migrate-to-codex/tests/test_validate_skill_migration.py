# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Sergejs Sušinskis
# See LICENSE file in the repository root for full license text.

import importlib.util
import json
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT_PATH = (
    Path(__file__).resolve().parents[2]
    / "verify-skill-migration"
    / "scripts"
    / "validate_skill_migration.py"
)
SPEC = importlib.util.spec_from_file_location("validate_skill_migration", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class ValidateSkillMigrationTests(unittest.TestCase):
    def test_operator_guidance_accepts_repo_relative_and_skill_local_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            skill_root = repo_root / ".codex" / "skills" / "migrate-to-codex"
            references_dir = skill_root / "references"
            references_dir.mkdir(parents=True)
            (repo_root / ".codex" / "config.toml").parent.mkdir(parents=True, exist_ok=True)
            (repo_root / ".codex" / "config.toml").write_text("", encoding="utf-8")
            (references_dir / "guide.md").write_text("# Guide", encoding="utf-8")
            skill_path = skill_root / "SKILL.md"
            skill_path.write_text(
                textwrap.dedent(
                    """\
                    See `.codex/config.toml` and `references/guide.md`.
                    """
                ),
                encoding="utf-8",
            )

            with patch.object(MODULE, "REPO_ROOT", repo_root):
                errors, warnings = MODULE.validate_operator_guidance([skill_path])

        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_operator_guidance_rejects_absolute_host_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            skill_path = repo_root / ".codex" / "skills" / "migrate-to-codex" / "SKILL.md"
            skill_path.parent.mkdir(parents=True)
            skill_path.write_text(
                textwrap.dedent(
                    """\
                    # Migration Skill

                    Open `/etc/passwd` before migrating.
                    """
                ),
                encoding="utf-8",
            )

            with patch.object(MODULE, "REPO_ROOT", repo_root):
                errors, warnings = MODULE.validate_operator_guidance([skill_path])

        self.assertEqual(warnings, [])
        self.assertEqual(len(errors), 1)
        self.assertIn("must be repo-relative or skill-local", errors[0])
        self.assertIn("`/etc/passwd`", errors[0])

    def test_environment_readiness_redacts_external_paths(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmpdir, tempfile.TemporaryDirectory() as home_tmpdir:
            repo_root = Path(repo_tmpdir)
            codex_home = Path(home_tmpdir) / "private-codex-home"
            codex_home.mkdir(parents=True)
            (codex_home / "config.toml").write_text(
                textwrap.dedent(
                    """\
                    [mcp_servers.private]
                    command = "/very/private/tool"
                    """
                ),
                encoding="utf-8",
            )

            with patch.object(MODULE, "REPO_ROOT", repo_root):
                report = MODULE.build_environment_readiness_report(codex_home)

        serialized = json.dumps(report, indent=2)
        self.assertEqual(report["codex_home"], "<codex-home>")
        self.assertNotIn(str(codex_home), serialized)
        self.assertNotIn("/very/private/tool", serialized)

        details = "\n".join(str(check["detail"]) for check in report["checks"])
        self.assertIn("<codex-home>/config.toml: TOML parsed", details)
        self.assertIn("private: command not found: <absolute-path>/tool", details)


if __name__ == "__main__":
    unittest.main()
