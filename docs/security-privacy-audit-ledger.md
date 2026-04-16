# Security & Privacy Audit Ledger

Inventory date: 2026-04-16

This document is Phase 0 of an exhaustive security/privacy review for this repository.
It is a coverage ledger, not a findings report.

Scope rules:

- Every tracked file outside `.git/` must appear exactly once in this ledger.
- Audit and remediation artifacts created during the review are also listed once they exist so the review record and resulting fixes are covered.
- Review status starts at `queued` unless the file is inventory-only placeholder data.
- Human ownership is not derivable from repo metadata, so this ledger tracks `stream` instead of `owner`.
- Markdown, TOML, YAML, and JSON artifacts are treated as operational policy when they influence tool use, generated outputs, or environment behavior.

Status legend:

- `queued`: not yet reviewed line by line for security/privacy issues
- `placeholder-only`: no functional logic; confirm no sensitive content and move on
- `in_review`: currently under manual review
- `reviewed`: manual review complete
- `fixed`: findings were remediated and rechecked

## Phased Review Plan

### Phase 0: Inventory and coverage control

- Freeze the audit surface and maintain this ledger.
- Group files by review stream so the review can proceed without omissions.
- Record status transitions in this file during the audit.

### Phase 1: Threat model and review criteria

- Define trust boundaries between `.claude/` source inputs, Python migration logic, `.codex/` generated outputs, CI, and local operator environment.
- Define issue classes: path traversal, unsafe writes, subprocess injection, unsafe parsing, overbroad tool guidance, secret leakage, privacy leaks in logs/reports, dependency and CI exposure.

### Phase 2: High-risk executable Python review

- Review write-capable migration scripts first.
- Review validation, tracker, and reporting code next.
- Verify input validation, canonical paths, temp/report handling, subprocess safety, and output sanitization.

### Phase 3: Operational instruction review

- Review `SKILL.md`, reference markdown, TOML agent artifacts, and config files as executable policy.
- Check for overbroad permissions, unsafe delegation guidance, destructive command patterns, and hidden exfiltration paths.

### Phase 4: Security regression coverage review

- Review tests as evidence for safety guarantees.
- Add missing negative tests for malicious inputs, malformed frontmatter, weird paths, and hostile config values.

### Phase 5: CI, dependency, and publication hygiene

- Review workflow behavior, dependency pinning, ignore patterns, and docs/examples that may normalize unsafe operator behavior.

### Phase 6: Data-flow and privacy audit

- Trace what content is read, generated, persisted, logged, or displayed.
- Focus on tracker state, reports, environment-readiness output, SHAs, timestamps, and absolute path leakage.

### Phase 7: Findings triage and verification

- Record findings with file, line, impact, exploit path, remediation, and test gap.
- Re-review changed files and close the ledger only after coverage is complete.

## Review Order

1. `.codex/skills/migrate-agents-to-codex/scripts/migrate_claude_agents_to_codex.py`
2. `.codex/skills/migrate-to-codex/scripts/migrate_claude_workflows_to_codex.py`
3. Workflow runners under `.codex/skills/*/scripts/run_*`
4. `.codex/skills/verify-skill-migration/scripts/validate_skill_migration.py`
5. `.codex/skills/migration-dashboard/scripts/analyze_migration.py`
6. `tools/migration_support/*.py`
7. Tests under `.codex/skills/*/tests/`
8. Operational markdown/TOML/config artifacts
9. CI, root docs, examples, and state files

## Ledger

### Root Governance, State, and Packaging

| Path | Stream | Type | Execution Role | Primary Security/Privacy Focus | Status |
| --- | --- | --- | --- | --- | --- |
| `CHANGELOG.md` | governance | documentation | published change history | sensitive detail leakage, unsafe guidance normalization | reviewed |
| `CONTRIBUTING.md` | governance | documentation | contributor instructions | unsafe contributor workflows, secret handling guidance | reviewed |
| `LICENSE` | governance | legal text | none | placeholder legal text only | placeholder-only |
| `README.md` | governance | documentation | operator entrypoint | unsafe usage guidance, trust-boundary claims, secret/logging guidance | reviewed |
| `migration-state.json` | state | json | persistent tracker data | privacy leakage, stale review metadata, absolute paths, identifiers, integrity assumptions | reviewed |
| `requirements.txt` | packaging | dependency manifest | install-time input | pinning strength, supply-chain exposure, unexpected dependency surface | reviewed |
| `.gitignore` | governance | ignore policy | publication boundary | accidental secret/state publication, missing generated-output ignores | reviewed |

### CI and Automation

| Path | Stream | Type | Execution Role | Primary Security/Privacy Focus | Status |
| --- | --- | --- | --- | --- | --- |
| `.github/workflows/ci.yml` | ci | workflow | hosted CI execution | dependency install trust, secret exposure, unreviewed publish/exec behavior | reviewed |

### Source and Output Placeholders

| Path | Stream | Type | Execution Role | Primary Security/Privacy Focus | Status |
| --- | --- | --- | --- | --- | --- |
| `.claude/agents/.gitkeep` | source-input | placeholder | keeps source tree shape | confirm no hidden payload or misleading assumptions | placeholder-only |
| `.claude/skills/.gitkeep` | source-input | placeholder | keeps source tree shape | confirm no hidden payload or misleading assumptions | placeholder-only |
| `.codex/agents/.gitkeep` | generated-output | placeholder | keeps output tree shape | confirm no hidden payload or misleading assumptions | placeholder-only |
| `example-service/src/testing/.gitkeep` | example-service | placeholder | keeps example tree shape | confirm no hidden payload or misleading assumptions | placeholder-only |

### Codex Runtime Config

| Path | Stream | Type | Execution Role | Primary Security/Privacy Focus | Status |
| --- | --- | --- | --- | --- | --- |
| `.codex/config.toml` | config | toml | local Codex runtime configuration | agent enablement, hook/tool behavior, environment assumptions, privacy-sensitive local config | reviewed |

### Shared Python Support

| Path | Stream | Type | Execution Role | Primary Security/Privacy Focus | Status |
| --- | --- | --- | --- | --- | --- |
| `tools/migration_support/__init__.py` | support-python | python | package export surface | unexpected imports, trust-boundary assumptions | reviewed |
| `tools/migration_support/safety.py` | support-python | python | shared safety helpers | identifier policy drift, path containment consistency, privacy-redaction consistency | fixed |
| `tools/migration_support/nativeness.py` | support-python | python | tracker handoff and subprocess helper | subprocess safety, output leakage, command trust boundary | reviewed |
| `tools/migration_support/paths.py` | support-python | python | repo root and state path resolution | path canonicalization, traversal, incorrect root discovery | reviewed |
| `tools/migration_support/primitives.py` | support-python | python | primitive name normalization | unsafe tool mapping, overbroad primitive translation | reviewed |
| `tools/migration_support/tracker.py` | support-python | python | CLI/module entrypoint | import path manipulation, execution boundary assumptions | reviewed |
| `tools/migration_support/tracker_cli.py` | support-python | python | tracker core logic | subprocess usage, file scanning, metadata persistence, output leakage | reviewed |
| `tools/migration_support/tracker_state.py` | support-python | python | tracker state merge and archival logic | state integrity, stale review carryover, privacy of archived metadata | reviewed |
| `tools/migration_support/validate_names.py` | support-python | python | validation shim entrypoint | runpy loading, path trust, boundary between wrapper and validator | reviewed |

### Skill Package: `example-commit-helper`

| Path | Stream | Type | Execution Role | Primary Security/Privacy Focus | Status |
| --- | --- | --- | --- | --- | --- |
| `.codex/skills/example-commit-helper/SKILL.md` | skill-policy | markdown | operational skill instructions | command safety, git hygiene guidance, destructive action normalization | reviewed |

### Skill Package: `example-skill`

| Path | Stream | Type | Execution Role | Primary Security/Privacy Focus | Status |
| --- | --- | --- | --- | --- | --- |
| `.codex/skills/example-skill/SKILL.md` | skill-policy | markdown | operational skill instructions | tool permission scope, unsafe workflow guidance | reviewed |
| `.codex/skills/example-skill/references/workflow-mode.md` | skill-policy | markdown | referenced operator contract | unsafe operational assumptions, privacy leakage in examples | reviewed |

### Skill Package: `migrate-agents-to-codex`

| Path | Stream | Type | Execution Role | Primary Security/Privacy Focus | Status |
| --- | --- | --- | --- | --- | --- |
| `.codex/skills/migrate-agents-to-codex/SKILL.md` | agent-migration-skill | markdown | operator workflow contract | overbroad permissions, unsafe migration guidance, report leakage | reviewed |
| `.codex/skills/migrate-agents-to-codex/references/agent-complexity-classifier.md` | agent-migration-skill | markdown | classification reference | unsafe classification heuristics affecting review depth | reviewed |
| `.codex/skills/migrate-agents-to-codex/references/agent-field-mapping.md` | agent-migration-skill | markdown | field mapping reference | insecure field translation, privilege expansion during mapping | reviewed |
| `.codex/skills/migrate-agents-to-codex/references/architectural-patterns.md` | agent-migration-skill | markdown | design reference | unsafe orchestration patterns normalized as valid | reviewed |
| `.codex/skills/migrate-agents-to-codex/references/codebase-verification-prompt.md` | agent-migration-skill | markdown | review prompt artifact | prompt leakage, unsafe verification instructions, privacy-sensitive context collection | reviewed |
| `.codex/skills/migrate-agents-to-codex/references/codex-agent-template.md` | agent-migration-skill | markdown | output template guidance | privilege overgrant, unsafe defaults, hidden tool access assumptions | reviewed |
| `.codex/skills/migrate-agents-to-codex/references/legacy-subagent-roi.md` | agent-migration-skill | markdown | delegation policy reference | unsafe delegation incentives, privacy boundary dilution | reviewed |
| `.codex/skills/migrate-agents-to-codex/references/primitive-mapping.md` | agent-migration-skill | markdown | primitive conversion reference | unsafe primitive substitutions, silent behavior changes | reviewed |
| `.codex/skills/migrate-agents-to-codex/references/subagent-migration-guide.md` | agent-migration-skill | markdown | migration decision guidance | overuse of delegation, unsafe concurrency/tool assumptions | reviewed |
| `.codex/skills/migrate-agents-to-codex/scripts/migrate_claude_agents_to_codex.py` | agent-migration-skill | python | core migration writer | parser safety, path handling, output sanitization, privilege mapping, generated artifact safety | fixed |
| `.codex/skills/migrate-agents-to-codex/scripts/run_agent_migration_workflow.py` | agent-migration-skill | python | orchestration runner | temp/report handling, subprocess trust, write targets, output leakage | reviewed |
| `.codex/skills/migrate-agents-to-codex/tests/test_migrate_claude_agents_to_codex.py` | agent-migration-skill | python-test | regression evidence | missing adversarial tests, unsupported negative cases | fixed |

### Skill Package: `migrate-to-codex`

| Path | Stream | Type | Execution Role | Primary Security/Privacy Focus | Status |
| --- | --- | --- | --- | --- | --- |
| `.codex/skills/migrate-to-codex/SKILL.md` | skill-migration-skill | markdown | operator workflow contract | overbroad permissions, unsafe migration instructions, privacy leakage in review flow | reviewed |
| `.codex/skills/migrate-to-codex/references/architectural-patterns.md` | skill-migration-skill | markdown | design reference | unsafe orchestration guidance, misleading trust claims | reviewed |
| `.codex/skills/migrate-to-codex/references/codex-skill-template.md` | skill-migration-skill | markdown | output template guidance | unsafe defaults, hidden permission scope, exfiltration-prone examples | reviewed |
| `.codex/skills/migrate-to-codex/references/complexity-classifier.md` | skill-migration-skill | markdown | classification reference | under-classification of risky workflows | reviewed |
| `.codex/skills/migrate-to-codex/references/conversational-migration-contract.md` | skill-migration-skill | markdown | behavior contract | unsafe prompt contract, privacy-sensitive context retention | reviewed |
| `.codex/skills/migrate-to-codex/references/embedded-agent-taxonomy.md` | skill-migration-skill | markdown | taxonomy reference | unsafe delegation or runtime flattening guidance | reviewed |
| `.codex/skills/migrate-to-codex/references/primitive-mapping.md` | skill-migration-skill | markdown | primitive conversion reference | unsafe primitive substitutions, silent privilege changes | reviewed |
| `.codex/skills/migrate-to-codex/scripts/migrate_claude_workflows_to_codex.py` | skill-migration-skill | python | core migration writer | yaml parsing safety, copy/write safety, path rewriting, output sanitization, prompt/tool mapping correctness | fixed |
| `.codex/skills/migrate-to-codex/scripts/migration_doctor.py` | skill-migration-skill | python | preflight assessment and reporting | environment disclosure, dynamic loading, report privacy, path trust | fixed |
| `.codex/skills/migrate-to-codex/scripts/run_migration_workflow.py` | skill-migration-skill | python | orchestration runner | temp/report handling, write targets, subprocess trust, evidence leakage | fixed |
| `.codex/skills/migrate-to-codex/scripts/validate_codex_workflow_names.py` | skill-migration-skill | python | validation shim | dynamic execution boundary, path trust | reviewed |
| `.codex/skills/migrate-to-codex/tests/test_migrate_claude_workflows_to_codex.py` | skill-migration-skill | python-test | regression evidence | missing adversarial tests, malformed input cases, path edge cases | fixed |
| `.codex/skills/migrate-to-codex/tests/test_reporting_redaction.py` | skill-migration-skill | python-test | regression evidence | consumer redaction preservation, privacy regression coverage | fixed |
| `.codex/skills/migrate-to-codex/tests/test_run_migration_workflow.py` | skill-migration-skill | python-test | regression evidence | workflow report-path privacy regression coverage | fixed |
| `.codex/skills/migrate-to-codex/tests/test_validate_skill_migration.py` | skill-migration-skill | python-test | regression evidence | validator host-path policy and privacy regression coverage | fixed |

### Skill Package: `migration-dashboard`

| Path | Stream | Type | Execution Role | Primary Security/Privacy Focus | Status |
| --- | --- | --- | --- | --- | --- |
| `.codex/skills/migration-dashboard/SKILL.md` | dashboard-skill | markdown | operator workflow contract | unsafe dashboard guidance, over-trust of tracker outputs | reviewed |
| `.codex/skills/migration-dashboard/scripts/analyze_migration.py` | dashboard-skill | python | tracker analysis and reporting | subprocess safety, data aggregation leakage, stale integrity assumptions, privacy of displayed metadata | fixed |

### Skill Package: `verify-skill-migration`

| Path | Stream | Type | Execution Role | Primary Security/Privacy Focus | Status |
| --- | --- | --- | --- | --- | --- |
| `.codex/skills/verify-skill-migration/SKILL.md` | validator-skill | markdown | operator workflow contract | unsafe validator guidance, privacy-sensitive environment checks | reviewed |
| `.codex/skills/verify-skill-migration/scripts/validate_skill_migration.py` | validator-skill | python | migration validator | parser safety, environment probing, path trust, false trust signals, privacy leakage in diagnostics | fixed |

### Examples and Walkthroughs

| Path | Stream | Type | Execution Role | Primary Security/Privacy Focus | Status |
| --- | --- | --- | --- | --- | --- |
| `docs/how-to/claude-to-codex-agentic-migration.md` | docs | documentation | operator walkthrough | unsafe workflow normalization, missing safety prerequisites, privacy leakage in examples | reviewed |
| `docs/security-privacy-audit-ledger.md` | docs | documentation | audit coverage ledger | audit drift, missing-file risk, inaccurate status tracking | reviewed |
| `docs/security-privacy-findings.md` | docs | documentation | audit findings register | findings accuracy, severity consistency, evidence traceability | reviewed |
| `docs/security-privacy-remediation-plan.md` | docs | documentation | remediation backlog | prioritization accuracy, fix-sequencing clarity, test-gap tracking | reviewed |
| `examples/hello-world-agent/hello-world-agent.toml` | examples | toml | example custom agent artifact | unsafe default permissions, misleading minimal example behavior | reviewed |
| `examples/hello-world-skill/SKILL.md` | examples | markdown | example skill artifact | unsafe example patterns that could be copied into production | reviewed |

## Audit Notes

- Phase 0 inventory capture is complete as of 2026-04-16.
- First completed review unit: `.codex/skills/migrate-agents-to-codex/` core writer, workflow wrapper, test file, and skill contract.
- Second completed review unit: `.codex/skills/migrate-to-codex/` core writer, workflow wrapper, test file, and skill contract.
- Third completed review unit: validator/dashboard/reporting path, shared support Python, and reviewed root config/examples/docs called by those flows.
- Fourth completed review unit: remaining reference/policy markdown plus `migration-state.json`.
- Confirmed findings for this unit are tracked in `docs/security-privacy-findings.md`.
- Remediation backlog is tracked in `docs/security-privacy-remediation-plan.md`.
- Remediation implementation is complete through P2, including shared helper consolidation and adversarial regression coverage.
- Findings 1-9 are now marked fixed and were rechecked against the touched codepaths on 2026-04-16.
- The current working tree contains 62 files outside `.git/` represented in this ledger: 55 tracked repo files plus 7 audit/remediation artifacts added during this review.
- Placeholder files are intentionally listed so they are not silently skipped during the audit.
