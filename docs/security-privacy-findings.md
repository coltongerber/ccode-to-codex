# Security & Privacy Findings

Review date: 2026-04-16

This file records confirmed findings from the ongoing repository-wide security/privacy audit.
Only reviewed units should appear here.

Remediation status: all 9 confirmed findings were fixed and reverified on 2026-04-16.

## Review Unit 1

Reviewed files:

- `.codex/skills/migrate-agents-to-codex/SKILL.md`
- `.codex/skills/migrate-agents-to-codex/scripts/migrate_claude_agents_to_codex.py`
- `.codex/skills/migrate-agents-to-codex/scripts/run_agent_migration_workflow.py`
- `.codex/skills/migrate-agents-to-codex/tests/test_migrate_claude_agents_to_codex.py`

### Finding 1

- Severity: high
- Status: fixed on 2026-04-16
- File: `.codex/skills/migrate-agents-to-codex/scripts/migrate_claude_agents_to_codex.py`
- Lines: 936-937, 993, 1081-1083
- Issue: agent names are used as raw path components, so `--agent ../escape` can read from outside `.claude/agents/` and write outside `.codex/agents/`.
- Why it matters: this is a direct path traversal on both the input and output side. An operator or upstream automation that passes an untrusted agent name can cause the migration to consume arbitrary repo-adjacent markdown and overwrite files outside the intended output directory.
- Evidence: local proof confirmed `prepare_migration('../escape', ...)` read `.claude/escape.md`, and `write_migration(...)` wrote `.codex/escape.toml` instead of `.codex/agents/escape.toml`.
- Fix: reject agent names containing path separators, dot-segments, control characters, or anything outside a strict slug pattern before any path construction. After joining paths, resolve and enforce containment under the intended root.
- Remediation: strict identifier validation and root-containment checks now come from `tools/migration_support/safety.py` and are enforced by the agent migrator before any file read/write.
- Verification: direct regressions cover `../escape` and path-separator names in `.codex/skills/migrate-agents-to-codex/tests/test_migrate_claude_agents_to_codex.py`.

### Finding 2

- Severity: high
- Status: fixed on 2026-04-16
- File: `.codex/skills/migrate-agents-to-codex/scripts/migrate_claude_agents_to_codex.py`
- Lines: 810-818, 848-895, 898-926
- Issue: agent names are interpolated unescaped into the TOML provenance banner, so newline-bearing names inject arbitrary top-level TOML keys that survive validation.
- Why it matters: a crafted source filename such as `evil\napproval_policy = "never".md` causes the generated agent artifact to contain attacker-controlled runtime config outside the intended migration mapping. Validation does not reject this because it only checks for required keys and structural shape.
- Evidence: local proof confirmed generated TOML containing `approval_policy = "never"` parsed successfully and preserved the injected key.
- Fix: treat agent names as untrusted data everywhere. Escape or comment-prefix every emitted line derived from `name`, and validate source names against a safe filename pattern before generation.
- Remediation: provenance/banner escaping is now shared and applied before TOML banner emission, while invalid source names are rejected before generation.
- Verification: regression coverage now asserts hostile newline-bearing names cannot inject top-level TOML keys.

### Finding 3

- Severity: medium
- Status: fixed on 2026-04-16
- File: `.codex/skills/migrate-agents-to-codex/scripts/migrate_claude_agents_to_codex.py`
- Lines: 518-525, 886-892
- Issue: skill references from source frontmatter are accepted as raw relative paths, allowing traversal outside `.codex/skills/` when a matching `SKILL.md` exists.
- Why it matters: a malicious source agent can cause generated `skills.config.path` entries to point at arbitrary local skill directories instead of staying inside the intended migration output tree.
- Evidence: local proof confirmed a source `skills: ../../shared-skill` produced `path = ".codex/skills/../../shared-skill"` in generated TOML.
- Fix: validate skill identifiers as slugs, resolve candidate paths, and reject any reference whose resolved target escapes `TARGET_SKILLS_DIR`.
- Remediation: frontmatter `skills:` entries are now slug-validated and rejected before any `skills.config.path` emission.
- Verification: regression coverage asserts traversal-style skill references are surfaced as invalid and never emitted.

## Coverage Notes

- Dedicated regressions now cover adversarial agent names, hostile provenance values, and traversal-style skill references.
- Review unit 1 is complete; all findings from this unit are fixed.

## Review Unit 2

Reviewed files:

- `.codex/skills/migrate-to-codex/SKILL.md`
- `.codex/skills/migrate-to-codex/scripts/migrate_claude_workflows_to_codex.py`
- `.codex/skills/migrate-to-codex/scripts/run_migration_workflow.py`
- `.codex/skills/migrate-to-codex/tests/test_migrate_claude_workflows_to_codex.py`

### Finding 4

- Severity: high
- Status: fixed on 2026-04-16
- File: `.codex/skills/migrate-to-codex/scripts/migrate_claude_workflows_to_codex.py`
- Lines: 954-956, 1001-1002
- Issue: skill names are used as raw path components, so `--skill ../escape` migrates directories outside `.claude/skills/` and writes outside `.codex/skills/`.
- Why it matters: this is the same path traversal class as the agent migrator, but here it applies to whole directory trees. An untrusted skill name can cause arbitrary repo-adjacent content to be transformed and written into an unintended destination.
- Evidence: local proof confirmed `migrate_skill('../escape', ...)` wrote `.codex/escape/SKILL.md` instead of `.codex/skills/escape/SKILL.md`.
- Fix: validate skill identifiers against a strict slug pattern and enforce resolved-path containment for both source and destination roots before any migration work runs.
- Remediation: the skill migrator now uses the shared slug/containment helper and rejects invalid skill identifiers before source or destination path construction.
- Verification: regressions now cover traversal and path-separator skill names.

### Finding 5

- Severity: high
- Status: fixed on 2026-04-16
- File: `.codex/skills/migrate-to-codex/scripts/migrate_claude_workflows_to_codex.py`
- Lines: 880-886, 901-910
- Issue: recursive migration follows symlinked source files and copies their target contents into the generated Codex package.
- Why it matters: a source skill package can exfiltrate arbitrary local files by placing symlinks inside `.claude/skills/<name>/`. Non-markdown symlinks are copied verbatim via `shutil.copy2`, and markdown symlinks are read and transformed via `read_text`.
- Evidence: local proof confirmed a symlink to an external `secret.txt` was migrated into `.codex/skills/demo-skill/references-link.txt` with the secret contents copied into a regular file.
- Fix: reject symlinks during traversal or resolve each file and enforce containment under the source skill root before reading or copying.
- Remediation: migration now blocks when any source file is a symlink, including markdown files under nested `references/`.
- Verification: regressions now cover both non-markdown and markdown symlink cases.

### Finding 6

- Severity: high
- Status: fixed on 2026-04-16
- File: `.codex/skills/migrate-to-codex/scripts/migrate_claude_workflows_to_codex.py`
- Lines: 811-824, 871-877
- Issue: crafted skill names are embedded into the generated HTML provenance banner without escaping, so `-->` and newlines can break out of the comment and inject arbitrary markdown into the migrated skill.
- Why it matters: this allows attacker-controlled source directory names to alter the effective instructions of the generated Codex skill without modifying the source `SKILL.md` body itself.
- Evidence: local proof confirmed a source skill named `evil-->\n# injected` produced a migrated `SKILL.md` whose banner was terminated early and emitted `# injected` as live markdown.
- Fix: treat skill names as untrusted data in banners, escape comment terminators and line breaks, or avoid embedding raw source names in generated content altogether.
- Remediation: shared provenance escaping now defuses comment terminators and newline-bearing source names before banner generation.
- Verification: banner regression coverage asserts hostile source names remain inert comment text.

### Finding 7

- Severity: medium
- Status: fixed on 2026-04-16
- File: `.codex/skills/migrate-to-codex/scripts/run_migration_workflow.py`
- Lines: 272, 315-317, 339-340, 463-472
- Issue: generated evidence reports and JSON output include unsanitized absolute local paths such as `codex_home`, preview roots, and report locations.
- Why it matters: these artifacts are designed to be saved and potentially shared as review evidence. Emitting absolute home-directory and temp-path details leaks operator environment structure unnecessarily.
- Evidence: local proof confirmed `_write_report(...)` wrote both `/home/example/.codex` and the absolute preview root into the report body.
- Fix: redact or relativize local filesystem paths in evidence/report output unless the user explicitly requests full host-path diagnostics.
- Remediation: workflow report, JSON, and text output now render preview/report paths via shared redaction helpers and never emit raw default absolute locations.
- Verification: regressions assert preview/report paths are rendered as `<preview-root>/...` instead of absolute host paths.

## Coverage Notes

- Dedicated regressions now cover adversarial skill names, path traversal, symlinked source-package contents, workflow report redaction, and validator-facing privacy checks.
- Review unit 1 is complete.
- Review unit 2 is complete; all findings from this unit are fixed.

## Review Unit 3

Reviewed files:

- `.codex/skills/migrate-to-codex/scripts/migration_doctor.py`
- `.codex/skills/migrate-to-codex/scripts/validate_codex_workflow_names.py`
- `.codex/skills/migration-dashboard/SKILL.md`
- `.codex/skills/migration-dashboard/scripts/analyze_migration.py`
- `.codex/skills/verify-skill-migration/SKILL.md`
- `.codex/skills/verify-skill-migration/scripts/validate_skill_migration.py`
- `tools/migration_support/__init__.py`
- `tools/migration_support/nativeness.py`
- `tools/migration_support/paths.py`
- `tools/migration_support/primitives.py`
- `tools/migration_support/tracker.py`
- `tools/migration_support/tracker_cli.py`
- `tools/migration_support/tracker_state.py`
- `tools/migration_support/validate_names.py`

### Finding 8

- Severity: medium
- Status: fixed on 2026-04-16
- File: `.codex/skills/verify-skill-migration/scripts/validate_skill_migration.py`
- Lines: 552-580, 583-620
- Issue: operator-path validation probes arbitrary absolute host paths and treats them as valid guidance when they exist.
- Why it matters: migration-family docs can contain host-specific absolute paths such as `/etc/passwd`, and the validator will silently accept them on machines where those paths exist. That turns the validator into a filesystem-existence oracle and normalizes non-portable host-path references in checked-in operational guidance.
- Evidence: local proof confirmed `validate_operator_guidance()` returned no errors or warnings for a migration-family `SKILL.md` containing `` `/etc/passwd` `` once the file existed on the host.
- Fix: reject absolute host paths in migration-family operator guidance by policy, or restrict validation to repo-relative and skill-local paths only. Do not probe arbitrary host files during validation.
- Remediation: validator policy is now repo-local/skill-local only and no longer probes arbitrary absolute host paths.
- Verification: regressions cover both rejection of `/etc/passwd`-style paths and acceptance of repo-relative or skill-local operator paths.

### Finding 9

- Severity: medium
- Status: fixed on 2026-04-16
- Files:
  - `.codex/skills/verify-skill-migration/scripts/validate_skill_migration.py`
  - `.codex/skills/migration-dashboard/scripts/analyze_migration.py`
  - `.codex/skills/migrate-to-codex/scripts/migration_doctor.py`
- Lines:
  - `validate_skill_migration.py`: 871-1024
  - `analyze_migration.py`: 549-579
  - `migration_doctor.py`: 345-362, 437-446, 497-501
- Issue: environment-readiness diagnostics include absolute local paths, and both the dashboard and migration doctor republish those details in text and JSON output.
- Why it matters: these tools are intended to generate shareable review/status artifacts. Emitting absolute `codex_home`, config, hooks, instruction, and plugin-manifest paths leaks local workstation structure that is not needed for migration review.
- Evidence: local proof confirmed `build_environment_readiness_report()` returned an absolute `codex_home` and absolute config-path detail; code review showed the dashboard truncates and republishes validator output, while the migration doctor embeds the full environment-readiness payload directly in its report.
- Fix: redact or relativize host paths before serializing diagnostics, and keep raw absolute paths behind an explicit debug mode only.
- Remediation: environment-readiness serialization is now sanitized at the validator source via shared display-path logic, and the dashboard/doctor consumers were rechecked against that sanitized contract.
- Verification: regressions cover sanitized `codex_home`, redacted hook/config paths, and redaction preservation in doctor/dashboard output.

## Coverage Notes

- Dedicated regressions now cover validator host-path handling, environment-readiness redaction, workflow report redaction, and doctor/dashboard consumer output.
- Review unit 1 is complete.
- Review unit 2 is complete.
- Review unit 3 is complete; all findings from this unit are fixed.

## Review Unit 4

Reviewed files:

- `migration-state.json`
- `.codex/skills/migrate-agents-to-codex/references/agent-complexity-classifier.md`
- `.codex/skills/migrate-agents-to-codex/references/agent-field-mapping.md`
- `.codex/skills/migrate-agents-to-codex/references/architectural-patterns.md`
- `.codex/skills/migrate-agents-to-codex/references/codebase-verification-prompt.md`
- `.codex/skills/migrate-agents-to-codex/references/codex-agent-template.md`
- `.codex/skills/migrate-agents-to-codex/references/legacy-subagent-roi.md`
- `.codex/skills/migrate-agents-to-codex/references/primitive-mapping.md`
- `.codex/skills/migrate-agents-to-codex/references/subagent-migration-guide.md`
- `.codex/skills/migrate-to-codex/references/architectural-patterns.md`
- `.codex/skills/migrate-to-codex/references/codex-skill-template.md`
- `.codex/skills/migrate-to-codex/references/complexity-classifier.md`
- `.codex/skills/migrate-to-codex/references/conversational-migration-contract.md`
- `.codex/skills/migrate-to-codex/references/embedded-agent-taxonomy.md`
- `.codex/skills/migrate-to-codex/references/primitive-mapping.md`

No confirmed security or privacy findings were identified in this review unit.

## Coverage Notes

- Review unit 1 is complete.
- Review unit 2 is complete.
- Review unit 3 is complete.
- Review unit 4 is complete.
- All 9 confirmed findings are fixed and now have direct negative regression coverage or consumer-level redaction coverage.
- Policy/reference markdown remains enforced indirectly through migration behavior and validator expectations rather than a dedicated standalone markdown test suite.
