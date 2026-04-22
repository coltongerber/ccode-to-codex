# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Sergejs Sušinskis
# See LICENSE file in the repository root for full license text.

import importlib.util
import json
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import tempfile
import textwrap


DOCTOR_PATH = Path(__file__).resolve().parents[1] / "scripts" / "migration_doctor.py"
DOCTOR_SPEC = importlib.util.spec_from_file_location("migration_doctor", DOCTOR_PATH)
DOCTOR = importlib.util.module_from_spec(DOCTOR_SPEC)
assert DOCTOR_SPEC.loader is not None
sys.modules[DOCTOR_SPEC.name] = DOCTOR
DOCTOR_SPEC.loader.exec_module(DOCTOR)

DASHBOARD_PATH = (
    Path(__file__).resolve().parents[2]
    / "migration-dashboard"
    / "scripts"
    / "analyze_migration.py"
)
DASHBOARD_SPEC = importlib.util.spec_from_file_location("analyze_migration", DASHBOARD_PATH)
DASHBOARD = importlib.util.module_from_spec(DASHBOARD_SPEC)
assert DASHBOARD_SPEC.loader is not None
sys.modules[DASHBOARD_SPEC.name] = DASHBOARD
DASHBOARD_SPEC.loader.exec_module(DASHBOARD)


class ReportingRedactionTests(unittest.TestCase):
    def test_doctor_report_keeps_redacted_environment_readiness(self) -> None:
        environment_readiness = {
            "state": "warnings",
            "failures": 0,
            "warnings": 1,
            "codex_home": "<codex-home>",
            "checks": [
                {
                    "name": "hook-command",
                    "status": "warn",
                    "detail": "hook executable path is missing: <absolute-path>/hook.sh",
                }
            ],
        }
        summary = {
            "readiness": "ready",
            "score": 90,
            "recommended_action": "Preview migration",
            "skills_considered": 1,
            "mechanical_safe": 1,
            "blocked": 0,
            "manual_review_required": 0,
            "refactor_required": 0,
            "validator_failures": 0,
            "drifted": 0,
            "pending_native_review": 0,
            "oversized": 0,
        }
        classification = SimpleNamespace(
            status="MECHANICAL_SAFE",
            findings=[],
            missing_agents=[],
            missing_skills=[],
            ambiguous_references=[],
        )

        with (
            patch.object(DOCTOR, "_resolve_skill_scope", return_value=["demo-skill"]),
            patch.object(DOCTOR, "_safe_load_tracker", return_value=(None, None)),
            patch.object(DOCTOR.migrator, "classify_skill", return_value=classification),
            patch.object(DOCTOR, "_build_summary", return_value=summary),
            patch.object(DOCTOR.validator, "build_environment_readiness_report", return_value=environment_readiness),
        ):
            report = DOCTOR.build_doctor_report(skill="demo-skill")

        serialized = json.dumps(report, indent=2)
        text = DOCTOR.format_doctor_report(report)
        self.assertIn("<codex-home>", serialized)
        self.assertIn("<absolute-path>/hook.sh", serialized)
        self.assertIn("<absolute-path>/hook.sh", text)

    def test_dashboard_validate_output_preserves_redacted_environment_readiness(self) -> None:
        environment_readiness = {
            "state": "warnings",
            "output": (
                "Warnings (2):\n"
                "  ⚠ codex-config: <codex-home>/config.toml: config not found\n"
                "  ⚠ hook-command: hook script path is missing: <absolute-path>/hook.sh"
            ),
        }

        text = DASHBOARD.format_validate([], environment_readiness=environment_readiness)
        result = DASHBOARD.build_validate_result(
            {"summary": {}},
            [],
            environment_readiness=environment_readiness,
        )

        self.assertIn("<codex-home>/config.toml", text)
        self.assertIn("<absolute-path>/hook.sh", text)
        serialized = json.dumps(result, indent=2)
        self.assertIn("<codex-home>/config.toml", serialized)
        self.assertIn("<absolute-path>/hook.sh", serialized)

    def test_workflow_runtime_change_paths_are_redacted(self) -> None:
        workflow_path = (
            Path(__file__).resolve().parents[1] / "scripts" / "run_migration_workflow.py"
        )
        spec = importlib.util.spec_from_file_location("run_migration_workflow", workflow_path)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)

        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir) / "repo"
            repo_root.mkdir(parents=True)
            source_skills_dir = repo_root / ".claude" / "skills"
            source_skills_dir.mkdir(parents=True)
            (repo_root / ".claude" / "notify.sh").write_text("#!/bin/bash\necho notify\n", encoding="utf-8")

            skill_dir = source_skills_dir / "demo-skill"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                textwrap.dedent(
                    """\
                    ---
                    name: demo-skill
                    description: demo
                    ---

                    Use Skill('demo-skill') before continuing.
                    """
                ),
                encoding="utf-8",
            )

            doctor_report = {
                "summary": {
                    "readiness": "ready",
                    "score": 100,
                    "recommended_action": "Preview migration",
                    "skills_considered": 1,
                    "mechanical_safe": 1,
                    "blocked": 0,
                    "manual_review_required": 0,
                    "refactor_required": 0,
                    "validator_failures": 0,
                    "drifted": 0,
                    "pending_native_review": 0,
                    "environment_readiness_state": "warnings",
                },
                "risks": [],
                "environment_readiness": {
                    "state": "warnings",
                    "failures": 0,
                    "warnings": 0,
                    "codex_home": "<codex-home>",
                    "checks": [],
                },
            }

            with (
                patch.object(module, "REPO_ROOT", repo_root),
                patch.object(module.migrator, "REPO_ROOT", repo_root),
                patch.object(module.migrator, "SOURCE_SKILLS_DIR", source_skills_dir),
                patch.object(module.migrator, "TARGET_SKILLS_DIR", repo_root / ".codex" / "skills"),
                patch.object(module.migrator, "USER_CLAUDE_HOME", repo_root / ".claude"),
                patch.object(module.migrator, "USER_CODEX_HOME", repo_root / "private-codex-home"),
                patch.object(module.doctor, "build_doctor_report", return_value=doctor_report),
            ):
                payload = module.run_workflow(skill="demo-skill", preview=True, preview_dir=repo_root / "preview")

            serialized = json.dumps(payload, indent=2)
            self.assertIn("<codex-home>/notify.sh", serialized)
            self.assertNotIn(str(repo_root / "private-codex-home"), serialized)


if __name__ == "__main__":
    unittest.main()
