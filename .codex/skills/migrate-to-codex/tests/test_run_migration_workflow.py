# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Sergejs Sušinskis
# See LICENSE file in the repository root for full license text.

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "run_migration_workflow.py"
SPEC = importlib.util.spec_from_file_location("run_migration_workflow", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def make_doctor_report() -> dict[str, object]:
    return {
        "summary": {
            "readiness": "ready",
            "score": 92,
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
        "environment_readiness": {
            "state": "warnings",
            "failures": 0,
            "warnings": 1,
            "codex_home": ".codex",
            "checks": [
                {
                    "name": "codex-config",
                    "status": "warn",
                    "detail": ".codex/config.toml: config not found",
                }
            ],
        },
        "risks": [],
    }


class RunMigrationWorkflowTests(unittest.TestCase):
    def test_write_report_redacts_preview_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            preview_root = Path(tmpdir) / "preview-root"
            report_path = MODULE._write_report(
                doctor_report=make_doctor_report(),
                results=[],
                validation_results=[],
                preview=True,
                preview_root=preview_root,
                report_dir=Path(tmpdir) / "reports",
                tracker_updated=False,
                tracker_output="",
                dashboard_text=None,
                nativeness_review={
                    "state": "not_required",
                    "required": False,
                    "instructions": [],
                    "record_review_examples": [],
                },
            )

            text = report_path.read_text(encoding="utf-8")

        self.assertIn("`<preview-root>`", text)
        self.assertIn("`<preview-root>/.codex/skills`", text)
        self.assertNotIn(str(preview_root), text)

    def test_run_workflow_preview_result_redacts_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            preview_root = Path(tmpdir) / "preview-root"
            result_object = SimpleNamespace(
                skill="demo-skill",
                action="migrated",
                status="MECHANICAL_SAFE",
            )

            with (
                patch.object(MODULE.doctor, "build_doctor_report", return_value=make_doctor_report()),
                patch.object(MODULE.migrator, "migrate_skill", return_value=result_object),
                patch.object(
                    MODULE.migrator,
                    "_serialize_result",
                    return_value={"skill": "demo-skill", "status": "MECHANICAL_SAFE", "action": "migrated"},
                ),
                patch.object(
                    MODULE,
                    "_validate_scan_dir",
                    return_value={"passed": True, "errors": [], "warnings": []},
                ),
                patch.object(
                    MODULE.nativeness,
                    "build_nativeness_review_handoff",
                    return_value={
                        "state": "not_required",
                        "required": False,
                        "instructions": [],
                        "record_review_examples": [],
                    },
                ),
            ):
                result = MODULE.run_workflow(
                    skill="demo-skill",
                    preview=True,
                    preview_dir=preview_root,
                )

        serialized = json.dumps(result, indent=2)
        self.assertEqual(result["preview"]["root"], "<preview-root>")
        self.assertEqual(result["preview"]["skills_root"], "<preview-root>/.codex/skills")
        self.assertEqual(result["report_path"], "<preview-root>/migration-evidence.md")
        self.assertNotIn(str(preview_root), serialized)


if __name__ == "__main__":
    unittest.main()
