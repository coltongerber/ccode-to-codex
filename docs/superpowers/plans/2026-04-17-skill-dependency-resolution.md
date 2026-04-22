# Skill Dependency Resolution Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Teach the skill migrator to resolve same-batch and cyclic skill dependencies, fall back to Claude plugins only when required, and automatically wire required Codex runtime assets.

**Architecture:** Add two shared support modules: one for dependency graph planning and one for Codex runtime installation. Integrate them into the existing skill migrator so classification, dry-run, and live migration all use the same dependency model. Keep existing ambiguity, safety, and redaction behavior intact.

**Tech Stack:** Python 3, `unittest`, `pathlib`, JSON/TOML parsing, existing migration support helpers under `tools/migration_support/`

---

## File Structure

- Create: `tools/migration_support/skill_dependencies.py`
- Create: `tools/migration_support/codex_runtime.py`
- Modify: `tools/migration_support/paths.py`
- Modify: `tools/migration_support/__init__.py`
- Modify: `.codex/skills/migrate-to-codex/scripts/migrate_claude_workflows_to_codex.py`
- Modify: `.codex/skills/migrate-to-codex/tests/test_migrate_claude_workflows_to_codex.py`
- Create: `.codex/skills/migrate-to-codex/tests/test_codex_runtime_installation.py`

### Task 1: Lock In Resolver Expectations With Failing Tests

**Files:**
- Modify: `.codex/skills/migrate-to-codex/tests/test_migrate_claude_workflows_to_codex.py`
- Create: `.codex/skills/migrate-to-codex/tests/test_codex_runtime_installation.py`
- Test: `.codex/skills/migrate-to-codex/tests/test_migrate_claude_workflows_to_codex.py`
- Test: `.codex/skills/migrate-to-codex/tests/test_codex_runtime_installation.py`

- [x] **Step 1: Write the failing dependency-resolution tests**

```python
    def test_same_batch_cycle_does_not_block_missing_skills(self) -> None:
        skill_packages = {
            "phase-worker": {
                "SKILL.md": make_skill(
                    """
                    Use Skill('phase-reviewer') before continuing.
                    """,
                    name="phase-worker",
                )
            },
            "phase-reviewer": {
                "SKILL.md": make_skill(
                    """
                    Return to Skill('phase-worker') after review.
                    """,
                    name="phase-reviewer",
                )
            },
        }

        with temporary_repo(skill_packages):
            plan = MODULE.plan_skill_batch(["phase-worker"])

        self.assertEqual(plan.requested_skills, ["phase-worker"])
        self.assertEqual(plan.expanded_skills, ["phase-reviewer", "phase-worker"])
        self.assertEqual(plan.blocked_skills, [])
        self.assertEqual(plan.cycles, [["phase-reviewer", "phase-worker"]])

    def test_single_skill_request_expands_to_required_source_dependencies(self) -> None:
        skill_packages = {
            "phase-worker": {
                "SKILL.md": make_skill(
                    """
                    Use Skill('phase-reviewer') before continuing.
                    """,
                    name="phase-worker",
                )
            },
            "phase-reviewer": {
                "SKILL.md": make_skill("# review", name="phase-reviewer")
            },
        }

        with temporary_repo(skill_packages):
            plan = MODULE.plan_skill_batch(["phase-worker"])

        self.assertEqual(plan.expanded_skills, ["phase-reviewer", "phase-worker"])
```

- [x] **Step 2: Run the resolver tests to verify they fail**

Run: `python3 .codex/skills/migrate-to-codex/tests/test_migrate_claude_workflows_to_codex.py`

Expected: `AttributeError` for missing `plan_skill_batch` or assertion failures showing same-batch dependencies still land in `missing_skills`.

- [x] **Step 3: Write the failing runtime-installation tests**

```python
class CodexRuntimeInstallationTests(unittest.TestCase):
    def test_install_runtime_assets_writes_hook_and_script(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            codex_home = Path(tmpdir) / ".codex"
            claude_home = Path(tmpdir) / ".claude"
            codex_home.mkdir()
            claude_home.mkdir()
            (claude_home / "notify.sh").write_text("#!/bin/bash\necho notify\n", encoding="utf-8")

            runtime_plan = MODULE.RuntimeInstallPlan(
                files=[MODULE.RuntimeFileCopy(source=claude_home / "notify.sh", relative_target=Path("notify.sh"))],
                hook_commands=["bash ~/.codex/notify.sh"],
                config_plugins={"superpowers@openai-curated": {"enabled": True}},
            )

            MODULE.install_runtime_assets(runtime_plan, codex_home=codex_home, dry_run=False)

            self.assertTrue((codex_home / "notify.sh").exists())
            self.assertTrue((codex_home / "hooks.json").exists())
            self.assertIn("superpowers@openai-curated", (codex_home / "config.toml").read_text(encoding="utf-8"))
```

- [x] **Step 4: Run the runtime tests to verify they fail**

Run: `python3 .codex/skills/migrate-to-codex/tests/test_codex_runtime_installation.py`

Expected: import failure or missing symbol errors for `RuntimeInstallPlan` and `install_runtime_assets`.

- [x] **Step 5: Commit the failing-test baseline**

```bash
git add .codex/skills/migrate-to-codex/tests/test_migrate_claude_workflows_to_codex.py \
        .codex/skills/migrate-to-codex/tests/test_codex_runtime_installation.py
git commit -m "test: cover cyclic skill dependencies and runtime installation"
```

### Task 2: Build Shared Dependency Discovery And Batch Planning

**Files:**
- Create: `tools/migration_support/skill_dependencies.py`
- Modify: `tools/migration_support/paths.py`
- Modify: `tools/migration_support/__init__.py`
- Test: `.codex/skills/migrate-to-codex/tests/test_migrate_claude_workflows_to_codex.py`

- [x] **Step 1: Add the failing support-module imports**

```python
from migration_support.skill_dependencies import (
    BatchPlan,
    DependencyResolution,
    expand_skill_batch,
    plan_dependency_graph,
)
from migration_support.paths import discover_claude_plugin_skill_names
```

- [x] **Step 2: Implement Claude plugin discovery in `paths.py`**

```python
@lru_cache(maxsize=None)
def discover_claude_plugin_skill_names(*, claude_home: Path | None = None) -> tuple[str, ...]:
    root = (claude_home or Path.home() / ".claude") / "plugins"
    manifest_path = root / "installed_plugins.json"
    if not manifest_path.exists():
        return ()

    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ()

    discovered: set[str] = set()
    for plugin in payload.get("installed_plugins", []):
        slug = plugin.get("slug")
        if not isinstance(slug, str) or not slug:
            continue
        plugin_root = root / slug
        skills_root = plugin_root / "skills"
        if not skills_root.exists():
            continue
        for skill_dir in sorted(path for path in skills_root.iterdir() if path.is_dir()):
            if (skill_dir / "SKILL.md").is_file():
                discovered.add(f"{slug}:{skill_dir.name}")
    return tuple(sorted(discovered))
```

- [x] **Step 3: Implement batch and graph planning in `skill_dependencies.py`**

```python
@dataclass(frozen=True)
class BatchPlan:
    requested_skills: list[str]
    expanded_skills: list[str]
    cycles: list[list[str]]
    blocked_skills: list[str]

def expand_skill_batch(requested_skills: list[str], source_skill_names: set[str], edges: dict[str, set[str]]) -> list[str]:
    queue = list(requested_skills)
    seen = set(requested_skills)
    while queue:
        skill = queue.pop(0)
        for dependency in sorted(edges.get(skill, set())):
            if dependency in source_skill_names and dependency not in seen:
                seen.add(dependency)
                queue.append(dependency)
    return sorted(seen)

def strongly_connected_components(edges: dict[str, set[str]]) -> list[list[str]]:
    order: list[str] = []
    visited: set[str] = set()
    reverse_edges: dict[str, set[str]] = {node: set() for node in edges}
    for node, neighbors in edges.items():
        for neighbor in neighbors:
            reverse_edges.setdefault(neighbor, set()).add(node)

    def visit(node: str) -> None:
        if node in visited:
            return
        visited.add(node)
        for neighbor in sorted(edges.get(node, set())):
            visit(neighbor)
        order.append(node)

    for node in sorted(edges):
        visit(node)

    components: list[list[str]] = []
    assigned: set[str] = set()

    def collect(node: str, component: list[str]) -> None:
        if node in assigned:
            return
        assigned.add(node)
        component.append(node)
        for neighbor in sorted(reverse_edges.get(node, set())):
            collect(neighbor, component)

    for node in reversed(order):
        if node in assigned:
            continue
        component: list[str] = []
        collect(node, component)
        components.append(sorted(component))
    return components
```

- [x] **Step 4: Re-run the dependency tests to verify the shared planner satisfies them**

Run: `python3 .codex/skills/migrate-to-codex/tests/test_migrate_claude_workflows_to_codex.py`

Expected: the new planner tests pass, while integration tests still fail because the migrator has not adopted the planner yet.

- [x] **Step 5: Commit the shared dependency planner**

```bash
git add tools/migration_support/paths.py \
        tools/migration_support/skill_dependencies.py \
        tools/migration_support/__init__.py \
        .codex/skills/migrate-to-codex/tests/test_migrate_claude_workflows_to_codex.py
git commit -m "feat: add shared skill dependency planner"
```

### Task 3: Build Idempotent Codex Runtime Installation Support

**Files:**
- Create: `tools/migration_support/codex_runtime.py`
- Modify: `tools/migration_support/__init__.py`
- Create: `.codex/skills/migrate-to-codex/tests/test_codex_runtime_installation.py`
- Test: `.codex/skills/migrate-to-codex/tests/test_codex_runtime_installation.py`

- [x] **Step 1: Add the runtime data structures and merge helpers**

```python
@dataclass(frozen=True)
class RuntimeFileCopy:
    source: Path
    relative_target: Path

@dataclass(frozen=True)
class RuntimeInstallPlan:
    files: list[RuntimeFileCopy]
    hook_commands: list[str]
    config_plugins: dict[str, dict[str, object]]

def merge_plugin_config(existing: dict[str, object], plugin_updates: dict[str, dict[str, object]]) -> dict[str, object]:
    plugins = dict(existing.get("plugins", {})) if isinstance(existing.get("plugins"), dict) else {}
    for plugin_name, payload in plugin_updates.items():
        current = dict(plugins.get(plugin_name, {})) if isinstance(plugins.get(plugin_name), dict) else {}
        current.update(payload)
        plugins[plugin_name] = current
    updated = dict(existing)
    updated["plugins"] = plugins
    return updated
```

- [x] **Step 2: Implement file copy, hook merge, and TOML write paths**

```python
def install_runtime_assets(plan: RuntimeInstallPlan, *, codex_home: Path, dry_run: bool) -> None:
    if dry_run:
        return

    codex_home.mkdir(parents=True, exist_ok=True)
    for file_copy in plan.files:
        target = resolve_within_root(codex_home, codex_home / file_copy.relative_target, kind="runtime asset target")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file_copy.source, target)

    hooks_path = codex_home / "hooks.json"
    hooks_payload = _read_json_file(hooks_path) if hooks_path.exists() else {}
    hooks_payload = merge_hook_commands(hooks_payload, plan.hook_commands)
    hooks_path.write_text(json.dumps(hooks_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    config_path = codex_home / "config.toml"
    config_payload = _read_toml_file(config_path) if config_path.exists() else {}
    config_payload = merge_plugin_config(config_payload, plan.config_plugins)
    config_path.write_text(_dump_simple_toml(config_payload), encoding="utf-8")
```

- [x] **Step 3: Add redaction-safe assertions to the runtime tests**

```python
    def test_install_runtime_assets_is_idempotent(self) -> None:
        plan = MODULE.RuntimeInstallPlan(
            files=[MODULE.RuntimeFileCopy(source=claude_home / "notify.sh", relative_target=Path("notify.sh"))],
            hook_commands=["bash ~/.codex/notify.sh"],
            config_plugins={"superpowers@openai-curated": {"enabled": True}},
        )
        MODULE.install_runtime_assets(plan, codex_home=codex_home, dry_run=False)
        first = (codex_home / "hooks.json").read_text(encoding="utf-8")
        MODULE.install_runtime_assets(plan, codex_home=codex_home, dry_run=False)
        second = (codex_home / "hooks.json").read_text(encoding="utf-8")
        self.assertEqual(first, second)

    def test_runtime_plan_repr_does_not_include_secret_script_contents(self) -> None:
        plan = MODULE.RuntimeInstallPlan(
            files=[MODULE.RuntimeFileCopy(source=claude_home / "notify.sh", relative_target=Path("notify.sh"))],
            hook_commands=["bash ~/.codex/notify.sh"],
            config_plugins={"superpowers@openai-curated": {"enabled": True}},
        )
        self.assertNotIn("audpbr25", repr(plan))
```

- [x] **Step 4: Run the runtime tests to verify they pass**

Run: `python3 .codex/skills/migrate-to-codex/tests/test_codex_runtime_installation.py`

Expected: `OK`

- [x] **Step 5: Commit the runtime installer support**

```bash
git add tools/migration_support/codex_runtime.py \
        tools/migration_support/__init__.py \
        .codex/skills/migrate-to-codex/tests/test_codex_runtime_installation.py
git commit -m "feat: add codex runtime asset installer"
```

### Task 4: Integrate Batch Planning, Claude Plugin Fallback, And Runtime Wiring Into The Migrator

**Files:**
- Modify: `.codex/skills/migrate-to-codex/scripts/migrate_claude_workflows_to_codex.py`
- Modify: `.codex/skills/migrate-to-codex/tests/test_migrate_claude_workflows_to_codex.py`
- Test: `.codex/skills/migrate-to-codex/tests/test_migrate_claude_workflows_to_codex.py`

- [x] **Step 1: Add migrator-facing planner hooks**

```python
from migration_support.codex_runtime import RuntimeInstallPlan, install_runtime_assets
from migration_support.skill_dependencies import BatchPlan, build_skill_batch_plan

CLAUDE_HOME = Path.home() / ".claude"

def plan_skill_batch(requested_skills: list[str]) -> BatchPlan:
    source_skill_names = _known_claude_skill_names()
    dependency_edges = collect_operational_skill_edges(source_skill_names)
    return build_skill_batch_plan(
        requested_skills=requested_skills,
        source_skill_names=source_skill_names,
        dependency_edges=dependency_edges,
        available_codex_skills=_known_codex_skill_names(),
        available_claude_plugin_skills=discover_claude_plugin_skill_names(claude_home=CLAUDE_HOME),
    )
```

- [x] **Step 2: Replace direct `missing_skills` gating with dependency resolution states**

```python
if candidate.context == SKILL_CALL_CONTEXT_OPERATIONAL:
    resolution = dependency_resolver.resolve(token)
    if resolution.state == "missing":
        missing_skills.add(token)
        _append_finding(
            findings,
            seen_findings,
            category=f"missing-skill:{token}",
            file=f"{relative_file}:{line_number}",
            trigger=f"hard skill dependency: {token}",
            next_action="migrate or install the missing dependency before rerunning",
        )
    elif resolution.state == "batch_source_skill":
        planned_source_dependencies.add(token)
    elif resolution.state == "claude_plugin_skill":
        planned_plugin_dependencies.add(token)
```

- [x] **Step 3: Apply batch migration and runtime installation during live runs**

```python
batch_plan = plan_skill_batch([skill] if skill else [path.name for path in iter_source_skill_dirs()])
for component in batch_plan.execution_groups:
    for member in component:
        migrate_path(src_root / member, dst_root / member, dry_run=dry_run)

runtime_plan = build_runtime_install_plan(batch_plan.planned_plugin_dependencies, claude_home=CLAUDE_HOME)
install_runtime_assets(runtime_plan, codex_home=USER_CODEX_HOME, dry_run=dry_run)
```

- [x] **Step 4: Add integration tests for plugin fallback and batch preview output**

```python
    def test_claude_plugin_dependency_only_used_when_codex_parity_is_missing(self) -> None:
        skill_packages = {
            "main-skill": {
                "SKILL.md": make_skill(
                    """
                    Use Skill('superpowers:requesting-code-review') before continuing.
                    """,
                    name="main-skill",
                )
            }
        }
        with temporary_repo(skill_packages, plugin_skills={}):
            plan = MODULE.plan_skill_batch(["main-skill"])
        self.assertEqual(plan.plugin_dependencies, ["superpowers:requesting-code-review"])

    def test_dry_run_reports_batch_expansion_and_cycles(self) -> None:
        with temporary_repo(skill_packages):
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                MODULE.migrate_skill("phase-worker", dry_run=True, analysis_only=False)
        output = stdout.getvalue()
        self.assertIn("expanded batch", output)
        self.assertIn("cycle group", output)
```

- [x] **Step 5: Run the migrator test suite to verify integration**

Run: `python3 .codex/skills/migrate-to-codex/tests/test_migrate_claude_workflows_to_codex.py`

Expected: `OK`

- [x] **Step 6: Commit the migrator integration**

```bash
git add .codex/skills/migrate-to-codex/scripts/migrate_claude_workflows_to_codex.py \
        .codex/skills/migrate-to-codex/tests/test_migrate_claude_workflows_to_codex.py
git commit -m "feat: resolve cyclic and plugin-backed skill dependencies"
```

### Task 5: Verify End-To-End Behavior And Guard Existing Reporting

**Files:**
- Modify: `.codex/skills/migrate-to-codex/tests/test_run_migration_workflow.py`
- Modify: `.codex/skills/migrate-to-codex/tests/test_reporting_redaction.py`
- Test: `.codex/skills/migrate-to-codex/tests/test_run_migration_workflow.py`
- Test: `.codex/skills/migrate-to-codex/tests/test_reporting_redaction.py`
- Test: `.codex/skills/migrate-to-codex/tests/test_validate_skill_migration.py`

- [x] **Step 1: Add workflow assertions for dependency planning summaries**

```python
    def test_workflow_json_includes_cycle_and_runtime_changes(self) -> None:
        payload = json.loads(
            run_workflow_json(
                skill_packages={
                    "phase-worker": {"SKILL.md": make_skill("Use Skill('phase-reviewer').", name="phase-worker")},
                    "phase-reviewer": {"SKILL.md": make_skill("Return to Skill('phase-worker').", name="phase-reviewer")},
                },
                preview=True,
            )
        )
        self.assertEqual(payload["expanded_skills"], ["phase-reviewer", "phase-worker"])
        self.assertEqual(payload["cycles"], [["phase-reviewer", "phase-worker"]])
        self.assertEqual(payload["runtime_changes"]["files"], ["notify.sh"])
```

- [x] **Step 2: Add redaction assertions so runtime asset paths and secrets stay hidden**

```python
    def test_reporting_redacts_runtime_asset_paths(self) -> None:
        report = render_report(
            files=["/u/af/cf/cgerber/.claude/notify.sh"],
            display_files=["<codex-home>/notify.sh"],
            secret_tokens=["audpbr25"],
        )
        self.assertNotIn("/u/af/cf/cgerber/.claude/notify.sh", report)
        self.assertIn("<codex-home>/notify.sh", report)
        self.assertNotIn("audpbr25", report)
```

- [x] **Step 3: Run the reporting and validator tests**

Run: `python3 .codex/skills/migrate-to-codex/tests/test_run_migration_workflow.py`

Expected: `OK`

Run: `python3 .codex/skills/migrate-to-codex/tests/test_reporting_redaction.py`

Expected: `OK`

Run: `python3 .codex/skills/migrate-to-codex/tests/test_validate_skill_migration.py`

Expected: `OK`

- [x] **Step 4: Run the full migration-skill test suite**

Run: `python3 -m unittest discover -s .codex/skills/migrate-to-codex/tests -p 'test_*.py'`

Expected: all tests pass with no redaction regressions.

- [x] **Step 5: Commit the verification updates**

```bash
git add .codex/skills/migrate-to-codex/tests/test_run_migration_workflow.py \
        .codex/skills/migrate-to-codex/tests/test_reporting_redaction.py \
        .codex/skills/migrate-to-codex/tests/test_validate_skill_migration.py
git commit -m "test: verify dependency planning and runtime redaction"
```

## Self-Review

- Spec coverage:
  - same-batch and cyclic dependency handling is covered in Tasks 1, 2, and 4
  - demand-driven Claude plugin fallback is covered in Tasks 2 and 4
  - automatic runtime config and hook wiring is covered in Tasks 1, 3, and 5
  - secret-safe reporting and idempotence are covered in Tasks 3 and 5
- Placeholder scan:
  - no `TBD`, `TODO`, or deferred “implement later” language remains
  - each code-touching step includes concrete paths, commands, and starter code
- Type consistency:
  - shared types are introduced before migrator integration uses them
  - `RuntimeInstallPlan` and `BatchPlan` are defined in shared support before tests and migrator steps reference them
