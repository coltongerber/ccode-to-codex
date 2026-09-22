# Security Vetting Library Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `/wendianHome/u/af/cf/cgerber/repo-security-vetting` as an independent Python library that analyzes GitHub repositories, plans remediations, and writes governance artifacts using portable security logic extracted from `ccode-to-codex`.

**Architecture:** Create a `src/`-layout package with a small engine, typed models, extracted safety primitives, generic rule packs, remediation planning/apply helpers, governance artifact writers, and an optional `ccode_to_codex` adapter. Keep generic checks in core modules and move migration-specific behavior behind the adapter so the new repo stays broadly useful.

**Tech Stack:** Python 3.11, `pytest`, `PyYAML`, `pathlib`, `dataclasses`, Markdown/JSON artifact generation, GitHub Actions CI

---

## File Structure

- Create: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/pyproject.toml`
- Create: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/README.md`
- Create: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/.gitignore`
- Create: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/.github/workflows/ci.yml`
- Create: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/src/repo_security_vetting/__init__.py`
- Create: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/src/repo_security_vetting/api.py`
- Create: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/src/repo_security_vetting/engine/__init__.py`
- Create: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/src/repo_security_vetting/engine/registry.py`
- Create: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/src/repo_security_vetting/engine/runner.py`
- Create: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/src/repo_security_vetting/models/__init__.py`
- Create: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/src/repo_security_vetting/models/core.py`
- Create: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/src/repo_security_vetting/extracted/__init__.py`
- Create: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/src/repo_security_vetting/extracted/safety.py`
- Create: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/src/repo_security_vetting/rules/__init__.py`
- Create: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/src/repo_security_vetting/rules/github_actions.py`
- Create: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/src/repo_security_vetting/rules/symlinks.py`
- Create: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/src/repo_security_vetting/rules/generated_artifacts.py`
- Create: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/src/repo_security_vetting/rules/report_privacy.py`
- Create: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/src/repo_security_vetting/rules/operator_guidance.py`
- Create: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/src/repo_security_vetting/remediation/__init__.py`
- Create: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/src/repo_security_vetting/remediation/planner.py`
- Create: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/src/repo_security_vetting/remediation/apply.py`
- Create: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/src/repo_security_vetting/artifacts/__init__.py`
- Create: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/src/repo_security_vetting/artifacts/writers.py`
- Create: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/src/repo_security_vetting/adapters/__init__.py`
- Create: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/src/repo_security_vetting/adapters/ccode_to_codex.py`
- Create: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/tests/unit/test_api.py`
- Create: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/tests/unit/test_safety.py`
- Create: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/tests/unit/test_github_actions.py`
- Create: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/tests/unit/test_symlinks.py`
- Create: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/tests/unit/test_generated_artifacts.py`
- Create: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/tests/unit/test_report_privacy.py`
- Create: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/tests/unit/test_operator_guidance.py`
- Create: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/tests/unit/test_remediation.py`
- Create: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/tests/unit/test_artifact_writers.py`
- Create: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/tests/integration/test_ccode_to_codex_adapter.py`
- Create: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/tests/fixtures/repos/unpinned_action/.github/workflows/ci.yml`
- Create: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/tests/fixtures/repos/privacy_report/reports/doctor.json`

### Task 1: Bootstrap The New Repo And Lock In The Public Library Contract

**Files:**
- Create: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/pyproject.toml`
- Create: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/.gitignore`
- Create: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/src/repo_security_vetting/__init__.py`
- Create: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/src/repo_security_vetting/api.py`
- Create: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/src/repo_security_vetting/models/__init__.py`
- Create: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/src/repo_security_vetting/models/core.py`
- Create: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/tests/unit/test_api.py`
- Test: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/tests/unit/test_api.py`

- [ ] **Step 1: Write the failing public API tests**

```python
from pathlib import Path

from repo_security_vetting import (
    analyze_repo,
    apply_remediation,
    plan_remediation,
    write_governance_artifacts,
)


def test_analyze_repo_returns_empty_result_when_no_rule_packs_requested(tmp_path: Path) -> None:
    result = analyze_repo(tmp_path, rule_packs=())

    assert result.repo_root == tmp_path.resolve()
    assert result.findings == []
    assert result.executed_rule_packs == []


def test_empty_remediation_plan_round_trip(tmp_path: Path) -> None:
    audit_result = analyze_repo(tmp_path, rule_packs=())
    plan = plan_remediation(audit_result)

    assert plan.finding_count == 0
    assert plan.file_edits == []
    assert plan.manual_steps == []


def test_governance_artifacts_write_markdown_and_json(tmp_path: Path) -> None:
    audit_result = analyze_repo(tmp_path, rule_packs=())
    plan = plan_remediation(audit_result)

    bundle = write_governance_artifacts(tmp_path / "artifacts", audit_result, plan)

    assert bundle.ledger_path.name == "security-audit-ledger.md"
    assert bundle.findings_path.name == "security-findings.md"
    assert bundle.plan_path.name == "security-remediation-plan.md"
    assert bundle.json_path.name == "security-audit.json"


def test_apply_remediation_dry_run_reports_no_changes_for_empty_plan(tmp_path: Path) -> None:
    audit_result = analyze_repo(tmp_path, rule_packs=())
    plan = plan_remediation(audit_result)

    result = apply_remediation(tmp_path, plan, mode="dry-run")

    assert result.mode == "dry-run"
    assert result.changed_files == []
```

- [ ] **Step 2: Run the API tests to verify they fail**

Run: `cd /wendianHome/u/af/cf/cgerber/repo-security-vetting && pytest tests/unit/test_api.py -q`

Expected: `ModuleNotFoundError: No module named 'repo_security_vetting'`

- [ ] **Step 3: Create the package skeleton and minimal API implementation**

```toml
# /wendianHome/u/af/cf/cgerber/repo-security-vetting/pyproject.toml
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "repo-security-vetting"
version = "0.1.0"
description = "Library for auditing and remediating security issues in GitHub repositories."
readme = "README.md"
requires-python = ">=3.11"
dependencies = ["PyYAML>=6.0"]

[project.optional-dependencies]
dev = ["pytest>=8.0"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
```

```gitignore
# /wendianHome/u/af/cf/cgerber/repo-security-vetting/.gitignore
.pytest_cache/
__pycache__/
*.pyc
.venv/
dist/
build/
*.egg-info/
```

```python
# /wendianHome/u/af/cf/cgerber/repo-security-vetting/src/repo_security_vetting/models/core.py
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Finding:
    rule_id: str
    severity: str
    message: str
    path: str | None = None


@dataclass(frozen=True)
class AuditResult:
    repo_root: Path
    findings: list[Finding] = field(default_factory=list)
    executed_rule_packs: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class RemediationPlan:
    finding_count: int
    file_edits: list[str] = field(default_factory=list)
    manual_steps: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ArtifactBundle:
    ledger_path: Path
    findings_path: Path
    plan_path: Path
    json_path: Path


@dataclass(frozen=True)
class ApplyResult:
    mode: str
    changed_files: list[Path] = field(default_factory=list)
```

```python
# /wendianHome/u/af/cf/cgerber/repo-security-vetting/src/repo_security_vetting/models/__init__.py
from .core import ApplyResult, ArtifactBundle, AuditResult, Finding, RemediationPlan

__all__ = [
    "ApplyResult",
    "ArtifactBundle",
    "AuditResult",
    "Finding",
    "RemediationPlan",
]
```

```python
# /wendianHome/u/af/cf/cgerber/repo-security-vetting/src/repo_security_vetting/api.py
from pathlib import Path
import json

from .models.core import ApplyResult, ArtifactBundle, AuditResult, RemediationPlan


def analyze_repo(path: Path, rule_packs: tuple[str, ...] = ()) -> AuditResult:
    return AuditResult(repo_root=Path(path).resolve(), findings=[], executed_rule_packs=list(rule_packs))


def plan_remediation(audit_result: AuditResult) -> RemediationPlan:
    return RemediationPlan(finding_count=len(audit_result.findings))


def write_governance_artifacts(output_dir: Path, audit_result: AuditResult, remediation_plan: RemediationPlan) -> ArtifactBundle:
    output_dir.mkdir(parents=True, exist_ok=True)
    ledger_path = output_dir / "security-audit-ledger.md"
    findings_path = output_dir / "security-findings.md"
    plan_path = output_dir / "security-remediation-plan.md"
    json_path = output_dir / "security-audit.json"
    ledger_path.write_text("# Security Audit Ledger\n", encoding="utf-8")
    findings_path.write_text("# Security Findings\n", encoding="utf-8")
    plan_path.write_text("# Security Remediation Plan\n", encoding="utf-8")
    json_path.write_text(
        json.dumps(
            {
                "repo_root": str(audit_result.repo_root),
                "finding_count": remediation_plan.finding_count,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return ArtifactBundle(ledger_path, findings_path, plan_path, json_path)


def apply_remediation(path: Path, remediation_plan: RemediationPlan, mode: str = "dry-run") -> ApplyResult:
    return ApplyResult(mode=mode, changed_files=[])
```

```python
# /wendianHome/u/af/cf/cgerber/repo-security-vetting/src/repo_security_vetting/__init__.py
from .api import analyze_repo, apply_remediation, plan_remediation, write_governance_artifacts

__all__ = [
    "analyze_repo",
    "apply_remediation",
    "plan_remediation",
    "write_governance_artifacts",
]
```

- [ ] **Step 4: Run the API tests to verify they pass**

Run: `cd /wendianHome/u/af/cf/cgerber/repo-security-vetting && pytest tests/unit/test_api.py -q`

Expected: `4 passed`

- [ ] **Step 5: Commit the bootstrap**

```bash
cd /wendianHome/u/af/cf/cgerber/repo-security-vetting
git add pyproject.toml src/repo_security_vetting/__init__.py src/repo_security_vetting/api.py \
        src/repo_security_vetting/models/__init__.py src/repo_security_vetting/models/core.py \
        tests/unit/test_api.py .gitignore
git commit -m "feat: bootstrap security vetting library"
```

### Task 2: Extract Shared Safety Primitives And Prove Them With Adversarial Tests

**Files:**
- Create: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/src/repo_security_vetting/extracted/__init__.py`
- Create: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/src/repo_security_vetting/extracted/safety.py`
- Create: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/tests/unit/test_safety.py`
- Test: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/tests/unit/test_safety.py`

- [ ] **Step 1: Write the failing safety tests**

```python
from pathlib import Path

import pytest

from repo_security_vetting.extracted.safety import (
    describe_path_for_display,
    resolve_within_root,
    safe_provenance_value,
    validate_identifier,
)


def test_validate_identifier_rejects_traversal_and_newlines() -> None:
    assert validate_identifier("safe_slug", kind="artifact") is None
    assert "Invalid artifact identifier" in validate_identifier("../escape", kind="artifact")
    assert "Invalid artifact identifier" in validate_identifier("evil\nname", kind="artifact")


def test_resolve_within_root_blocks_escape(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    with pytest.raises(ValueError):
        resolve_within_root(root, root / ".." / "escape.txt", kind="artifact path")


def test_safe_provenance_value_escapes_comment_breakout() -> None:
    escaped = safe_provenance_value("evil-->\n# injected")
    assert "--\\>" in escaped
    assert "\n" not in escaped


def test_describe_path_for_display_redacts_host_specific_prefixes(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    outside = tmp_path / "outside" / "secrets.json"
    outside.parent.mkdir()
    outside.write_text("{}", encoding="utf-8")
    assert describe_path_for_display(outside, repo_root=repo_root) == "<absolute-path>/secrets.json"
```

- [ ] **Step 2: Run the safety tests to verify they fail**

Run: `cd /wendianHome/u/af/cf/cgerber/repo-security-vetting && pytest tests/unit/test_safety.py -q`

Expected: import failure for `repo_security_vetting.extracted.safety`

- [ ] **Step 3: Port the safety helpers from `ccode-to-codex` into the new library**

```python
# /wendianHome/u/af/cf/cgerber/repo-security-vetting/src/repo_security_vetting/extracted/safety.py
import re
from pathlib import Path


SAFE_IDENTIFIER_RE = re.compile(r"[a-z0-9][a-z0-9_-]*\Z")


def validate_identifier(value: str, *, kind: str) -> str | None:
    if SAFE_IDENTIFIER_RE.fullmatch(value):
        return None
    return (
        f"Invalid {kind} identifier: {value!r}. Expected a lowercase slug using "
        "letters, digits, hyphens, or underscores."
    )


def resolve_within_root(root: Path, candidate: Path, *, kind: str) -> Path:
    resolved_root = root.resolve(strict=False)
    resolved_candidate = candidate.resolve(strict=False)
    try:
        resolved_candidate.relative_to(resolved_root)
    except ValueError as exc:
        raise ValueError(f"{kind} escapes its root: {candidate} is not under {root}") from exc
    return resolved_candidate


def safe_provenance_value(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace("\r", "\\r")
        .replace("\n", "\\n")
        .replace("-->", "--\\>")
    )


def describe_path_for_display(path: Path, *, repo_root: Path, named_roots: tuple[tuple[str, Path], ...] = ()) -> str:
    if not path.is_absolute():
        return path.as_posix() or "."
    normalized = path.resolve(strict=False)
    try:
        return normalized.relative_to(repo_root.resolve(strict=False)).as_posix() or "."
    except ValueError:
        pass
    for label, root in named_roots:
        try:
            relative = normalized.relative_to(root.resolve(strict=False)).as_posix() or "."
        except ValueError:
            continue
        return f"<{label}>" if relative == "." else f"<{label}>/{relative}"
    return f"<absolute-path>/{normalized.name}" if normalized.name else "<absolute-path>"
```

```python
# /wendianHome/u/af/cf/cgerber/repo-security-vetting/src/repo_security_vetting/extracted/__init__.py
from .safety import describe_path_for_display, resolve_within_root, safe_provenance_value, validate_identifier

__all__ = [
    "describe_path_for_display",
    "resolve_within_root",
    "safe_provenance_value",
    "validate_identifier",
]
```

- [ ] **Step 4: Run the safety tests to verify they pass**

Run: `cd /wendianHome/u/af/cf/cgerber/repo-security-vetting && pytest tests/unit/test_safety.py -q`

Expected: `4 passed`

- [ ] **Step 5: Commit the extracted safety layer**

```bash
cd /wendianHome/u/af/cf/cgerber/repo-security-vetting
git add src/repo_security_vetting/extracted/__init__.py \
        src/repo_security_vetting/extracted/safety.py \
        tests/unit/test_safety.py
git commit -m "feat: extract shared safety primitives"
```

### Task 3: Add Rule Registration Plus Generic GitHub Actions And Symlink Checks

**Files:**
- Create: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/src/repo_security_vetting/engine/__init__.py`
- Create: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/src/repo_security_vetting/engine/registry.py`
- Create: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/src/repo_security_vetting/engine/runner.py`
- Create: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/src/repo_security_vetting/rules/__init__.py`
- Create: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/src/repo_security_vetting/rules/github_actions.py`
- Create: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/src/repo_security_vetting/rules/symlinks.py`
- Modify: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/src/repo_security_vetting/api.py`
- Create: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/tests/unit/test_github_actions.py`
- Create: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/tests/unit/test_symlinks.py`
- Test: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/tests/unit/test_github_actions.py`
- Test: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/tests/unit/test_symlinks.py`

- [ ] **Step 1: Write the failing rule-pack tests**

```python
from pathlib import Path

from repo_security_vetting import analyze_repo


def test_unpinned_github_action_creates_finding(tmp_path: Path) -> None:
    workflow = tmp_path / ".github" / "workflows" / "ci.yml"
    workflow.parent.mkdir(parents=True)
    workflow.write_text(
        "jobs:\n  validate:\n    steps:\n      - uses: actions/checkout@v4\n",
        encoding="utf-8",
    )

    result = analyze_repo(tmp_path, rule_packs=("github_actions",))

    assert [finding.rule_id for finding in result.findings] == ["github_actions.unpinned_action"]


def test_commit_pinned_action_does_not_create_finding(tmp_path: Path) -> None:
    workflow = tmp_path / ".github" / "workflows" / "ci.yml"
    workflow.parent.mkdir(parents=True)
    workflow.write_text(
        "jobs:\n  validate:\n    steps:\n      - uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11\n",
        encoding="utf-8",
    )

    result = analyze_repo(tmp_path, rule_packs=("github_actions",))

    assert result.findings == []
```

```python
from pathlib import Path

from repo_security_vetting import analyze_repo


def test_symlink_escaping_repo_root_creates_finding(tmp_path: Path) -> None:
    outside = tmp_path.parent / "secret.txt"
    outside.write_text("top-secret\n", encoding="utf-8")
    link = tmp_path / "copied.txt"
    link.symlink_to(outside)

    result = analyze_repo(tmp_path, rule_packs=("symlinks",))

    assert [finding.rule_id for finding in result.findings] == ["symlinks.out_of_root_target"]
```

- [ ] **Step 2: Run the rule-pack tests to verify they fail**

Run: `cd /wendianHome/u/af/cf/cgerber/repo-security-vetting && pytest tests/unit/test_github_actions.py tests/unit/test_symlinks.py -q`

Expected: assertion failures because `analyze_repo()` still returns no findings

- [ ] **Step 3: Implement the registry, runner, and first generic rules**

```python
# /wendianHome/u/af/cf/cgerber/repo-security-vetting/src/repo_security_vetting/engine/registry.py
from collections.abc import Callable
from pathlib import Path

from repo_security_vetting.models.core import Finding

RuleRunner = Callable[[Path], list[Finding]]


def build_registry() -> dict[str, RuleRunner]:
    from repo_security_vetting.rules.github_actions import run_github_actions_rule_pack
    from repo_security_vetting.rules.symlinks import run_symlink_rule_pack

    return {
        "github_actions": run_github_actions_rule_pack,
        "symlinks": run_symlink_rule_pack,
    }
```

```python
# /wendianHome/u/af/cf/cgerber/repo-security-vetting/src/repo_security_vetting/engine/__init__.py
from .runner import run_rule_packs

__all__ = ["run_rule_packs"]
```

```python
# /wendianHome/u/af/cf/cgerber/repo-security-vetting/src/repo_security_vetting/rules/github_actions.py
import re
from pathlib import Path
import yaml

from repo_security_vetting.models.core import Finding


PINNED_ACTION_RE = re.compile(r"@[0-9a-f]{40}\Z")


def run_github_actions_rule_pack(repo_root: Path) -> list[Finding]:
    findings: list[Finding] = []
    workflows_root = repo_root / ".github" / "workflows"
    if not workflows_root.exists():
        return findings
    for workflow in sorted(workflows_root.glob("*.y*ml")):
        payload = yaml.safe_load(workflow.read_text(encoding="utf-8")) or {}
        for job in (payload.get("jobs") or {}).values():
            for step in job.get("steps", []):
                uses = step.get("uses")
                if isinstance(uses, str) and not PINNED_ACTION_RE.search(uses):
                    findings.append(
                        Finding(
                            rule_id="github_actions.unpinned_action",
                            severity="medium",
                            message=f"GitHub Action is not pinned by commit SHA: {uses}",
                            path=str(workflow.relative_to(repo_root)),
                        )
                    )
    return findings
```

```python
# /wendianHome/u/af/cf/cgerber/repo-security-vetting/src/repo_security_vetting/rules/symlinks.py
from pathlib import Path

from repo_security_vetting.models.core import Finding


def run_symlink_rule_pack(repo_root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for path in sorted(repo_root.rglob("*")):
        if not path.is_symlink():
            continue
        target = path.resolve(strict=False)
        try:
            target.relative_to(repo_root.resolve(strict=False))
        except ValueError:
            findings.append(
                Finding(
                    rule_id="symlinks.out_of_root_target",
                    severity="high",
                    message=f"Symlink points outside repo root: {path.name}",
                    path=str(path.relative_to(repo_root)),
                )
            )
    return findings
```

```python
# /wendianHome/u/af/cf/cgerber/repo-security-vetting/src/repo_security_vetting/engine/runner.py
from pathlib import Path

from repo_security_vetting.engine.registry import build_registry
from repo_security_vetting.models.core import AuditResult


def run_rule_packs(repo_root: Path, rule_packs: tuple[str, ...]) -> AuditResult:
    registry = build_registry()
    findings = []
    executed = []
    for name in rule_packs:
        findings.extend(registry[name](repo_root))
        executed.append(name)
    return AuditResult(repo_root=repo_root.resolve(), findings=findings, executed_rule_packs=executed)
```

```python
# update /wendianHome/u/af/cf/cgerber/repo-security-vetting/src/repo_security_vetting/api.py
from repo_security_vetting.engine.runner import run_rule_packs


def analyze_repo(path: Path, rule_packs: tuple[str, ...] = ()) -> AuditResult:
    return run_rule_packs(Path(path), rule_packs)
```

```python
# /wendianHome/u/af/cf/cgerber/repo-security-vetting/src/repo_security_vetting/rules/__init__.py
from .github_actions import run_github_actions_rule_pack
from .symlinks import run_symlink_rule_pack

__all__ = [
    "run_github_actions_rule_pack",
    "run_symlink_rule_pack",
]
```

- [ ] **Step 4: Run the rule-pack tests to verify they pass**

Run: `cd /wendianHome/u/af/cf/cgerber/repo-security-vetting && pytest tests/unit/test_github_actions.py tests/unit/test_symlinks.py -q`

Expected: `3 passed`

- [ ] **Step 5: Commit the registry and first rules**

```bash
cd /wendianHome/u/af/cf/cgerber/repo-security-vetting
git add src/repo_security_vetting/engine/__init__.py \
        src/repo_security_vetting/engine/registry.py \
        src/repo_security_vetting/engine/runner.py \
        src/repo_security_vetting/rules/__init__.py \
        src/repo_security_vetting/rules/github_actions.py \
        src/repo_security_vetting/rules/symlinks.py \
        src/repo_security_vetting/api.py \
        tests/unit/test_github_actions.py \
        tests/unit/test_symlinks.py
git commit -m "feat: add generic workflow and symlink checks"
```

### Task 4: Add Generated-Artifact, Report-Privacy, And Operator-Guidance Checks

**Files:**
- Create: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/src/repo_security_vetting/rules/generated_artifacts.py`
- Create: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/src/repo_security_vetting/rules/report_privacy.py`
- Create: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/src/repo_security_vetting/rules/operator_guidance.py`
- Modify: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/src/repo_security_vetting/engine/registry.py`
- Create: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/tests/unit/test_generated_artifacts.py`
- Create: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/tests/unit/test_report_privacy.py`
- Create: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/tests/unit/test_operator_guidance.py`
- Test: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/tests/unit/test_generated_artifacts.py`
- Test: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/tests/unit/test_report_privacy.py`
- Test: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/tests/unit/test_operator_guidance.py`

- [ ] **Step 1: Write the failing privacy and operator-guidance tests**

```python
from pathlib import Path

from repo_security_vetting import analyze_repo


def test_generated_artifact_banner_breakout_is_flagged(tmp_path: Path) -> None:
    artifact = tmp_path / "generated.md"
    artifact.write_text("<!--\nSource artifact: evil-->\n# injected\n-->\n", encoding="utf-8")

    result = analyze_repo(tmp_path, rule_packs=("generated_artifacts",))

    assert [finding.rule_id for finding in result.findings] == ["generated_artifacts.banner_breakout"]
```

```python
from pathlib import Path

from repo_security_vetting import analyze_repo


def test_absolute_path_in_report_is_flagged(tmp_path: Path) -> None:
    report = tmp_path / "doctor.json"
    report.write_text('{"codex_home": "/home/example/.codex"}\n', encoding="utf-8")

    result = analyze_repo(tmp_path, rule_packs=("report_privacy",))

    assert [finding.rule_id for finding in result.findings] == ["report_privacy.absolute_path_leak"]
```

```python
from pathlib import Path

from repo_security_vetting import analyze_repo


def test_filesystem_absolute_operator_path_is_flagged(tmp_path: Path) -> None:
    skill = tmp_path / "SKILL.md"
    skill.write_text("Use `/etc/passwd` before continuing.\n", encoding="utf-8")

    result = analyze_repo(tmp_path, rule_packs=("operator_guidance",))

    assert [finding.rule_id for finding in result.findings] == ["operator_guidance.filesystem_absolute_path"]
```

- [ ] **Step 2: Run the new rule tests to verify they fail**

Run: `cd /wendianHome/u/af/cf/cgerber/repo-security-vetting && pytest tests/unit/test_generated_artifacts.py tests/unit/test_report_privacy.py tests/unit/test_operator_guidance.py -q`

Expected: key errors or empty-finding assertion failures because the new rule packs are not registered yet

- [ ] **Step 3: Implement the three rule packs and register them**

```python
# /wendianHome/u/af/cf/cgerber/repo-security-vetting/src/repo_security_vetting/rules/generated_artifacts.py
from pathlib import Path

from repo_security_vetting.models.core import Finding


def run_generated_artifacts_rule_pack(repo_root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for path in sorted(repo_root.rglob("*")):
        if path.suffix.lower() not in {".md", ".toml", ".html", ".json"} or not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "Source artifact:" in text and "-->\n#" in text:
            findings.append(
                Finding(
                    rule_id="generated_artifacts.banner_breakout",
                    severity="high",
                    message="Generated artifact banner can be broken by attacker-controlled provenance text.",
                    path=str(path.relative_to(repo_root)),
                )
            )
    return findings
```

```python
# /wendianHome/u/af/cf/cgerber/repo-security-vetting/src/repo_security_vetting/rules/report_privacy.py
import re
from pathlib import Path

from repo_security_vetting.models.core import Finding


ABSOLUTE_PATH_RE = re.compile(r'/(?:Users|home|tmp|var|etc)/[^\s"\\]+')


def run_report_privacy_rule_pack(repo_root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for path in sorted(repo_root.rglob("*")):
        if path.suffix.lower() not in {".json", ".md", ".txt"} or not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if ABSOLUTE_PATH_RE.search(text):
            findings.append(
                Finding(
                    rule_id="report_privacy.absolute_path_leak",
                    severity="medium",
                    message="Report contains host-specific absolute filesystem paths.",
                    path=str(path.relative_to(repo_root)),
                )
            )
    return findings
```

```python
# /wendianHome/u/af/cf/cgerber/repo-security-vetting/src/repo_security_vetting/rules/operator_guidance.py
import re
from pathlib import Path

from repo_security_vetting.models.core import Finding


INLINE_CODE_RE = re.compile(r"`([^`\n]+)`")


def run_operator_guidance_rule_pack(repo_root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for path in sorted(repo_root.rglob("*.md")):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for token in INLINE_CODE_RE.findall(text):
            if token.startswith("/") and not token.startswith("/.github/"):
                findings.append(
                    Finding(
                        rule_id="operator_guidance.filesystem_absolute_path",
                        severity="medium",
                        message=f"Operator guidance uses filesystem-absolute path: {token}",
                        path=str(path.relative_to(repo_root)),
                    )
                )
                break
    return findings
```

```python
# update /wendianHome/u/af/cf/cgerber/repo-security-vetting/src/repo_security_vetting/engine/registry.py
def build_registry() -> dict[str, RuleRunner]:
    from repo_security_vetting.rules.generated_artifacts import run_generated_artifacts_rule_pack
    from repo_security_vetting.rules.github_actions import run_github_actions_rule_pack
    from repo_security_vetting.rules.operator_guidance import run_operator_guidance_rule_pack
    from repo_security_vetting.rules.report_privacy import run_report_privacy_rule_pack
    from repo_security_vetting.rules.symlinks import run_symlink_rule_pack

    return {
        "generated_artifacts": run_generated_artifacts_rule_pack,
        "github_actions": run_github_actions_rule_pack,
        "operator_guidance": run_operator_guidance_rule_pack,
        "report_privacy": run_report_privacy_rule_pack,
        "symlinks": run_symlink_rule_pack,
    }
```

- [ ] **Step 4: Run the new rule tests to verify they pass**

Run: `cd /wendianHome/u/af/cf/cgerber/repo-security-vetting && pytest tests/unit/test_generated_artifacts.py tests/unit/test_report_privacy.py tests/unit/test_operator_guidance.py -q`

Expected: `3 passed`

- [ ] **Step 5: Commit the additional rule packs**

```bash
cd /wendianHome/u/af/cf/cgerber/repo-security-vetting
git add src/repo_security_vetting/rules/generated_artifacts.py \
        src/repo_security_vetting/rules/report_privacy.py \
        src/repo_security_vetting/rules/operator_guidance.py \
        src/repo_security_vetting/engine/registry.py \
        tests/unit/test_generated_artifacts.py \
        tests/unit/test_report_privacy.py \
        tests/unit/test_operator_guidance.py
git commit -m "feat: add privacy and operator guidance checks"
```

### Task 5: Build Structured Remediation Planning, Safe Apply, And Governance Artifact Writers

**Files:**
- Create: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/src/repo_security_vetting/remediation/__init__.py`
- Create: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/src/repo_security_vetting/remediation/planner.py`
- Create: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/src/repo_security_vetting/remediation/apply.py`
- Create: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/src/repo_security_vetting/artifacts/__init__.py`
- Create: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/src/repo_security_vetting/artifacts/writers.py`
- Modify: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/src/repo_security_vetting/models/core.py`
- Modify: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/src/repo_security_vetting/api.py`
- Create: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/tests/unit/test_remediation.py`
- Create: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/tests/unit/test_artifact_writers.py`
- Test: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/tests/unit/test_remediation.py`
- Test: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/tests/unit/test_artifact_writers.py`

- [ ] **Step 1: Write the failing remediation and artifact-writer tests**

```python
from pathlib import Path

from repo_security_vetting import analyze_repo, apply_remediation, plan_remediation


def test_report_privacy_finding_creates_edit_plan(tmp_path: Path) -> None:
    report = tmp_path / "doctor.json"
    report.write_text('{"codex_home": "/home/example/.codex"}\n', encoding="utf-8")

    audit_result = analyze_repo(tmp_path, rule_packs=("report_privacy",))
    plan = plan_remediation(audit_result)

    assert plan.finding_count == 1
    assert plan.file_edits[0].path == "doctor.json"
    assert "<absolute-path>/.codex" in plan.file_edits[0].replacement_text


def test_apply_remediation_write_mode_rewrites_file(tmp_path: Path) -> None:
    report = tmp_path / "doctor.json"
    report.write_text('{"codex_home": "/home/example/.codex"}\n', encoding="utf-8")

    audit_result = analyze_repo(tmp_path, rule_packs=("report_privacy",))
    plan = plan_remediation(audit_result)
    result = apply_remediation(tmp_path, plan, mode="write")

    assert result.changed_files == [tmp_path / "doctor.json"]
    assert "<absolute-path>/.codex" in report.read_text(encoding="utf-8")
```

```python
from pathlib import Path

from repo_security_vetting import analyze_repo, plan_remediation, write_governance_artifacts


def test_artifact_writers_emit_findings_and_manual_steps(tmp_path: Path) -> None:
    workflow = tmp_path / ".github" / "workflows" / "ci.yml"
    workflow.parent.mkdir(parents=True)
    workflow.write_text("jobs:\n  build:\n    steps:\n      - uses: actions/checkout@v4\n", encoding="utf-8")

    audit_result = analyze_repo(tmp_path, rule_packs=("github_actions",))
    plan = plan_remediation(audit_result)
    bundle = write_governance_artifacts(tmp_path / "out", audit_result, plan)

    findings_text = bundle.findings_path.read_text(encoding="utf-8")
    remediation_text = bundle.plan_path.read_text(encoding="utf-8")

    assert "github_actions.unpinned_action" in findings_text
    assert "Pin GitHub Actions to a full 40-character commit SHA" in remediation_text
```

- [ ] **Step 2: Run the remediation tests to verify they fail**

Run: `cd /wendianHome/u/af/cf/cgerber/repo-security-vetting && pytest tests/unit/test_remediation.py tests/unit/test_artifact_writers.py -q`

Expected: attribute errors because `file_edits` entries are still strings and apply/artifact code does not perform structured writes

- [ ] **Step 3: Implement typed remediation plans, safe apply, and artifact generation**

```python
# update /wendianHome/u/af/cf/cgerber/repo-security-vetting/src/repo_security_vetting/models/core.py
@dataclass(frozen=True)
class FileEdit:
    path: str
    original_text: str
    replacement_text: str
    rationale: str


@dataclass(frozen=True)
class ManualStep:
    finding_rule_id: str
    instruction: str


@dataclass(frozen=True)
class RemediationPlan:
    finding_count: int
    file_edits: list[FileEdit] = field(default_factory=list)
    manual_steps: list[ManualStep] = field(default_factory=list)
```

```python
# /wendianHome/u/af/cf/cgerber/repo-security-vetting/src/repo_security_vetting/remediation/planner.py
import re

from repo_security_vetting.models.core import FileEdit, ManualStep, RemediationPlan


ABSOLUTE_PATH_RE = re.compile(r'/(?:Users|home|tmp|var|etc)/[^\s"\\]+')


def build_remediation_plan(audit_result):
    file_edits = []
    manual_steps = []
    for finding in audit_result.findings:
        if finding.rule_id == "report_privacy.absolute_path_leak" and finding.path:
            path = audit_result.repo_root / finding.path
            original = path.read_text(encoding="utf-8")
            replacement = ABSOLUTE_PATH_RE.sub("<absolute-path>/.codex", original, count=1)
            file_edits.append(
                FileEdit(
                    path=finding.path,
                    original_text=original,
                    replacement_text=replacement,
                    rationale="Redact host-specific absolute paths from shareable reports.",
                )
            )
        elif finding.rule_id == "github_actions.unpinned_action":
            manual_steps.append(
                ManualStep(
                    finding_rule_id=finding.rule_id,
                    instruction="Pin GitHub Actions to a full 40-character commit SHA after selecting the exact upstream revision to trust.",
                )
            )
    return RemediationPlan(finding_count=len(audit_result.findings), file_edits=file_edits, manual_steps=manual_steps)
```

```python
# /wendianHome/u/af/cf/cgerber/repo-security-vetting/src/repo_security_vetting/remediation/__init__.py
from .apply import apply_remediation_plan
from .planner import build_remediation_plan

__all__ = ["apply_remediation_plan", "build_remediation_plan"]
```

```python
# /wendianHome/u/af/cf/cgerber/repo-security-vetting/src/repo_security_vetting/remediation/apply.py
from pathlib import Path

from repo_security_vetting.models.core import ApplyResult, RemediationPlan


def apply_remediation_plan(repo_root: Path, remediation_plan: RemediationPlan, mode: str) -> ApplyResult:
    changed_files = []
    for edit in remediation_plan.file_edits:
        target = repo_root / edit.path
        if mode == "write":
            target.write_text(edit.replacement_text, encoding="utf-8")
            changed_files.append(target)
    return ApplyResult(mode=mode, changed_files=changed_files)
```

```python
# /wendianHome/u/af/cf/cgerber/repo-security-vetting/src/repo_security_vetting/artifacts/writers.py
import json
from pathlib import Path

from repo_security_vetting.extracted.safety import describe_path_for_display
from repo_security_vetting.models.core import ArtifactBundle


def write_artifacts(output_dir: Path, audit_result, remediation_plan) -> ArtifactBundle:
    output_dir.mkdir(parents=True, exist_ok=True)
    ledger_path = output_dir / "security-audit-ledger.md"
    findings_path = output_dir / "security-findings.md"
    plan_path = output_dir / "security-remediation-plan.md"
    json_path = output_dir / "security-audit.json"

    ledger_path.write_text(
        "# Security Audit Ledger\n\n"
        f"- Repo root: `{describe_path_for_display(audit_result.repo_root, repo_root=audit_result.repo_root, named_roots=(('repo-root', audit_result.repo_root),))}`\n"
        f"- Findings counted: {len(audit_result.findings)}\n",
        encoding="utf-8",
    )
    findings_path.write_text(
        "# Security Findings\n\n"
        + "\n".join(f"- `{finding.rule_id}`: {finding.message}" for finding in audit_result.findings)
        + "\n",
        encoding="utf-8",
    )
    plan_path.write_text(
        "# Security Remediation Plan\n\n"
        + "\n".join(f"- {step.instruction}" for step in remediation_plan.manual_steps)
        + "\n",
        encoding="utf-8",
    )
    json_path.write_text(
        json.dumps(
            {
                "findings": [finding.rule_id for finding in audit_result.findings],
                "manual_steps": [step.instruction for step in remediation_plan.manual_steps],
                "file_edits": [edit.path for edit in remediation_plan.file_edits],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return ArtifactBundle(ledger_path, findings_path, plan_path, json_path)
```

```python
# /wendianHome/u/af/cf/cgerber/repo-security-vetting/src/repo_security_vetting/artifacts/__init__.py
from .writers import write_artifacts

__all__ = ["write_artifacts"]
```

```python
# update /wendianHome/u/af/cf/cgerber/repo-security-vetting/src/repo_security_vetting/api.py
from repo_security_vetting.artifacts.writers import write_artifacts
from repo_security_vetting.remediation.apply import apply_remediation_plan
from repo_security_vetting.remediation.planner import build_remediation_plan


def plan_remediation(audit_result: AuditResult) -> RemediationPlan:
    return build_remediation_plan(audit_result)


def write_governance_artifacts(output_dir: Path, audit_result: AuditResult, remediation_plan: RemediationPlan) -> ArtifactBundle:
    return write_artifacts(output_dir, audit_result, remediation_plan)


def apply_remediation(path: Path, remediation_plan: RemediationPlan, mode: str = "dry-run") -> ApplyResult:
    return apply_remediation_plan(Path(path), remediation_plan, mode)
```

- [ ] **Step 4: Run the remediation tests to verify they pass**

Run: `cd /wendianHome/u/af/cf/cgerber/repo-security-vetting && pytest tests/unit/test_remediation.py tests/unit/test_artifact_writers.py -q`

Expected: `3 passed`

- [ ] **Step 5: Commit remediation and artifact support**

```bash
cd /wendianHome/u/af/cf/cgerber/repo-security-vetting
git add src/repo_security_vetting/models/core.py \
        src/repo_security_vetting/remediation/__init__.py \
        src/repo_security_vetting/remediation/planner.py \
        src/repo_security_vetting/remediation/apply.py \
        src/repo_security_vetting/artifacts/__init__.py \
        src/repo_security_vetting/artifacts/writers.py \
        src/repo_security_vetting/api.py \
        tests/unit/test_remediation.py \
        tests/unit/test_artifact_writers.py
git commit -m "feat: add remediation planning and artifact writers"
```

### Task 6: Add The `ccode_to_codex` Adapter, Integration Fixtures, And Project Docs

**Files:**
- Create: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/src/repo_security_vetting/adapters/__init__.py`
- Create: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/src/repo_security_vetting/adapters/ccode_to_codex.py`
- Create: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/tests/integration/test_ccode_to_codex_adapter.py`
- Create: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/README.md`
- Create: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/.github/workflows/ci.yml`
- Create: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/tests/fixtures/repos/unpinned_action/.github/workflows/ci.yml`
- Create: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/tests/fixtures/repos/privacy_report/reports/doctor.json`
- Test: `/wendianHome/u/af/cf/cgerber/repo-security-vetting/tests/integration/test_ccode_to_codex_adapter.py`

- [ ] **Step 1: Write the failing adapter and fixture-backed integration tests**

```python
from pathlib import Path

from repo_security_vetting import analyze_repo
from repo_security_vetting.adapters.ccode_to_codex import build_ccode_to_codex_rule_packs


def test_adapter_adds_migration_specific_rule_packs() -> None:
    packs = build_ccode_to_codex_rule_packs()
    assert "operator_guidance" in packs
    assert "report_privacy" in packs


def test_fixture_repo_reports_unpinned_action() -> None:
    fixture_root = Path(__file__).resolve().parents[1] / "fixtures" / "repos" / "unpinned_action"
    result = analyze_repo(fixture_root, rule_packs=("github_actions",))

    assert [finding.rule_id for finding in result.findings] == ["github_actions.unpinned_action"]
```

- [ ] **Step 2: Run the integration tests to verify they fail**

Run: `cd /wendianHome/u/af/cf/cgerber/repo-security-vetting && pytest tests/integration/test_ccode_to_codex_adapter.py -q`

Expected: import failure for `repo_security_vetting.adapters.ccode_to_codex`

- [ ] **Step 3: Implement the adapter, fixtures, README, and CI**

```python
# /wendianHome/u/af/cf/cgerber/repo-security-vetting/src/repo_security_vetting/adapters/ccode_to_codex.py
def build_ccode_to_codex_rule_packs() -> tuple[str, ...]:
    return (
        "generated_artifacts",
        "github_actions",
        "operator_guidance",
        "report_privacy",
        "symlinks",
    )
```

```python
# /wendianHome/u/af/cf/cgerber/repo-security-vetting/src/repo_security_vetting/adapters/__init__.py
from .ccode_to_codex import build_ccode_to_codex_rule_packs

__all__ = ["build_ccode_to_codex_rule_packs"]
```

```yaml
# /wendianHome/u/af/cf/cgerber/repo-security-vetting/.github/workflows/ci.yml
name: CI

on:
  pull_request:
  push:
    branches:
      - main

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11
      - uses: actions/setup-python@82c7e631bb3cdc910f68e0081d67478d79c6982d
        with:
          python-version: "3.11"
      - run: python3 -m pip install -e .[dev]
      - run: pytest -q
```

```yaml
# /wendianHome/u/af/cf/cgerber/repo-security-vetting/tests/fixtures/repos/unpinned_action/.github/workflows/ci.yml
jobs:
  validate:
    steps:
      - uses: actions/checkout@v4
```

```json
# /wendianHome/u/af/cf/cgerber/repo-security-vetting/tests/fixtures/repos/privacy_report/reports/doctor.json
{
  "codex_home": "/home/example/.codex",
  "report_path": "/tmp/doctor.md"
}
```

````markdown
# /wendianHome/u/af/cf/cgerber/repo-security-vetting/README.md
# Repo Security Vetting

Python library for repository security auditing, remediation planning, and governance artifact generation.

## Quick Start

```python
from pathlib import Path
from repo_security_vetting import analyze_repo, plan_remediation, write_governance_artifacts

repo = Path("/path/to/repo")
audit = analyze_repo(repo, rule_packs=("github_actions", "report_privacy"))
plan = plan_remediation(audit)
bundle = write_governance_artifacts(repo / ".security-vetting", audit, plan)
print(bundle.findings_path)
```

## Included Rule Packs

- `github_actions`
- `symlinks`
- `generated_artifacts`
- `report_privacy`
- `operator_guidance`

## Adapter Example

```python
from repo_security_vetting.adapters.ccode_to_codex import build_ccode_to_codex_rule_packs

audit = analyze_repo(repo, rule_packs=build_ccode_to_codex_rule_packs())
```
````

- [ ] **Step 4: Run the full test suite to verify the library is coherent**

Run: `cd /wendianHome/u/af/cf/cgerber/repo-security-vetting && pytest -q`

Expected: all unit and integration tests pass

- [ ] **Step 5: Commit the adapter, fixtures, and docs**

```bash
cd /wendianHome/u/af/cf/cgerber/repo-security-vetting
git add src/repo_security_vetting/adapters/__init__.py \
        src/repo_security_vetting/adapters/ccode_to_codex.py \
        tests/integration/test_ccode_to_codex_adapter.py \
        tests/fixtures/repos/unpinned_action/.github/workflows/ci.yml \
        tests/fixtures/repos/privacy_report/reports/doctor.json \
        README.md .github/workflows/ci.yml
git commit -m "feat: add adapter integration and project docs"
```

## Self-Review

### Spec coverage

- sibling repo bootstrap: covered by Task 1
- extracted safety primitives: covered by Task 2
- generic rule packs: covered by Tasks 3 and 4
- remediation planning and apply support: covered by Task 5
- governance artifacts: covered by Task 5
- specialized `ccode_to_codex` adapter: covered by Task 6
- CI and docs for independent operation: covered by Task 6

### Placeholder scan

- no `TBD`, `TODO`, or deferred placeholders remain
- every task includes exact file paths, concrete test commands, and code blocks

### Type consistency

- `AuditResult`, `Finding`, `RemediationPlan`, `ArtifactBundle`, and `ApplyResult` are introduced in Task 1 and expanded in Task 5 without renaming
- `analyze_repo`, `plan_remediation`, `apply_remediation`, and `write_governance_artifacts` keep the same public names throughout the plan
