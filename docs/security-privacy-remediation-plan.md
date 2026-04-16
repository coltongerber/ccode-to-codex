# Security & Privacy Remediation Plan

Date: 2026-04-16

This plan converts the confirmed audit findings into a fix sequence that reduces
the largest exploit surface first, then closes privacy leaks, then adds
regression coverage.

Current status: complete on 2026-04-16. All work items below were implemented and reverified.

## Priority Order

### P0: Block arbitrary path control and generated-artifact injection

Fix these first because they enable writes outside the intended target tree,
unexpected reads of repo-adjacent content, or attacker-controlled instructions
inside generated outputs.

#### Work item P0.1: agent migrator input and output containment

- Status: completed on 2026-04-16
- Findings: 1, 2, 3
- Primary files:
  - `.codex/skills/migrate-agents-to-codex/scripts/migrate_claude_agents_to_codex.py`
  - `.codex/skills/migrate-agents-to-codex/tests/test_migrate_claude_agents_to_codex.py`
- Required changes:
  - Reject agent names unless they match a strict slug policy.
  - Resolve constructed paths and enforce containment under `.claude/agents/` and `.codex/agents/`.
  - Treat emitted agent names as untrusted data in TOML comments or banners.
  - Validate source `skills:` entries as safe skill identifiers before building `skills.config.path`.
- Acceptance criteria:
  - `--agent ../escape` fails before any file read or write.
  - newline-bearing or control-character-bearing names cannot alter generated TOML structure.
  - traversal-style `skills:` entries are rejected.
- Tests to add:
  - reject `../escape`
  - reject names containing newline or carriage return
  - reject names containing path separators
  - reject `skills: ../../shared-skill`
  - assert generated TOML contains no injected top-level keys
- Implemented outcome:
  - shared slug/path containment and provenance escaping are now enforced by the agent migrator
  - direct regressions cover traversal, path separators, hostile banner values, and invalid skill references

#### Work item P0.2: skill migrator containment, symlink, and banner safety

- Status: completed on 2026-04-16
- Findings: 4, 5, 6
- Primary files:
  - `.codex/skills/migrate-to-codex/scripts/migrate_claude_workflows_to_codex.py`
  - `.codex/skills/migrate-to-codex/tests/test_migrate_claude_workflows_to_codex.py`
- Required changes:
  - Reject skill names unless they match a strict slug policy.
  - Resolve source and destination paths and enforce containment under `.claude/skills/` and `.codex/skills/`.
  - Refuse to read or copy symlinks during recursive migration, or resolve and reject any target outside the source skill root.
  - Escape or remove raw skill names from HTML provenance comments.
- Acceptance criteria:
  - `--skill ../escape` fails before any migration write.
  - symlinked source files do not copy external file contents into generated output.
  - crafted skill names cannot terminate provenance comments or inject markdown.
- Tests to add:
  - reject `../escape`
  - reject or skip symlinked markdown and non-markdown files
  - reject names containing `-->` plus newline
  - assert migrated `SKILL.md` cannot contain injected heading text from source dir names
- Implemented outcome:
  - shared slug/path containment and provenance escaping are now enforced by the skill migrator
  - direct regressions cover traversal, path separators, symlinked markdown/non-markdown files, and hostile banner values

### P1: Remove privacy leaks and host-path probing from reporting flows

Fix these next because they expose workstation structure and normalize
machine-specific guidance, but they do not currently enable arbitrary writes.

#### Work item P1.1: redact filesystem details from migration workflow reports

- Status: completed on 2026-04-16
- Finding: 7
- Primary files:
  - `.codex/skills/migrate-to-codex/scripts/run_migration_workflow.py`
- Required changes:
  - Redact or relativize `codex_home`, preview roots, temp paths, and report paths in human-readable and JSON outputs.
  - Keep raw absolute paths behind an explicit debug flag only if they are still needed.
- Acceptance criteria:
  - default report output contains repo-relative or redacted paths only.
- Tests to add:
  - report writer returns redacted/relative values for `codex_home`
  - preview/report paths are not absolute in default mode
- Implemented outcome:
  - workflow markdown, JSON, and plain-text outputs now use redacted display paths
  - direct regressions cover preview/report redaction

#### Work item P1.2: make validator operator-path checks repo-local only

- Status: completed on 2026-04-16
- Finding: 8
- Primary files:
  - `.codex/skills/verify-skill-migration/scripts/validate_skill_migration.py`
- Required changes:
  - Stop probing arbitrary absolute host paths.
  - Limit accepted operator-path tokens to repo-relative and skill-local forms.
  - Emit an error or warning when migration-family guidance references absolute host paths.
- Acceptance criteria:
  - `` `/etc/passwd` `` is rejected even if it exists on the current machine.
- Tests to add:
  - absolute host path in migration-family `SKILL.md` fails validation
  - repo-relative `.codex/...` and skill-local `references/...` paths still pass
- Implemented outcome:
  - validator policy now rejects filesystem-absolute operator guidance and accepts only repo-relative or skill-local forms
  - direct regressions cover both rejection and allowed repo-local cases

#### Work item P1.3: redact environment-readiness output everywhere it is republished

- Status: completed on 2026-04-16
- Finding: 9
- Primary files:
  - `.codex/skills/verify-skill-migration/scripts/validate_skill_migration.py`
  - `.codex/skills/migration-dashboard/scripts/analyze_migration.py`
  - `.codex/skills/migrate-to-codex/scripts/migration_doctor.py`
- Required changes:
  - Normalize environment-readiness output at the source before any consumer formats it.
  - Ensure dashboard and doctor output do not reintroduce absolute paths.
- Acceptance criteria:
  - validator, dashboard, and doctor outputs are consistent and sanitized by default.
- Tests to add:
  - `build_environment_readiness_report()` does not return absolute `codex_home`
  - dashboard output truncation still preserves redaction
  - doctor JSON/text output contains no absolute local paths in default mode
- Implemented outcome:
  - environment-readiness serialization is sanitized at the validator source and reused by the doctor/dashboard/workflow surfaces
  - direct regressions cover sanitized validator output plus doctor/dashboard consumer preservation

### P2: Hardening follow-through and regression coverage

These items are lower urgency than the direct write/exfiltration/privacy issues
above, but they are needed to keep the fixes from regressing.

#### Work item P2.1: common validation helpers

- Status: completed on 2026-04-16
- Scope:
  - consider adding one shared slug/path containment helper used by both migration writers and validator/reporting code
- Goal:
  - prevent the same traversal and injection class from being fixed differently in parallel codepaths
- Implemented outcome:
  - `tools/migration_support/safety.py` now provides the shared identifier, containment, provenance-escaping, and display-path helpers

#### Work item P2.2: adversarial fixture coverage

- Status: completed on 2026-04-16
- Scope:
  - extend both migration test suites with malicious names, traversal strings, and symlink fixtures
  - extend validator/reporting coverage with host-path and privacy-redaction fixtures
- Goal:
  - make every confirmed finding correspond to at least one negative regression test
- Implemented outcome:
  - dedicated adversarial tests were added for agent migration, skill migration, validator path policy, workflow redaction, and doctor/dashboard redaction preservation

## Closeout Sequence

1. P0.1 agent migrator containment/injection fixes and tests completed.
2. P0.2 skill migrator containment/symlink/banner fixes and tests completed.
3. P1 validator/reporting redaction fixes and tests completed.
4. P2 helper consolidation and adversarial coverage completed.
5. Audit findings and ledger closeout are the remaining documentation step.

## Verification Checklist

- Verified: no migration entrypoint accepts path traversal via user-provided names.
- Verified: no recursive migration path follows symlinks outside the source root.
- Verified: generated TOML or markdown artifacts are not structurally altered by crafted source names in the covered attack cases.
- Verified: default validator, dashboard, doctor, and workflow report outputs do not expose raw absolute local paths in the covered default flows.
- Verified: every finding from `docs/security-privacy-findings.md` now has direct regression coverage or consumer-level redaction coverage.
