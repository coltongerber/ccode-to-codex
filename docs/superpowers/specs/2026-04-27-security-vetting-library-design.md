# Broad Repo Security Vetting Library Design

## Goal

Extract the portable security-vetting work from `ccode-to-codex` into a new
sibling repository that becomes a general Python library for auditing and
remediating security issues across GitHub-hosted packages and repositories.

The first version should work for broad repository surfaces, not just
Claude/Codex migration packages, while preserving any already-implemented deep
checks that can be cleanly isolated behind optional adapters.

## Product Direction

- Primary surface: Python library
- Secondary surface: no required CLI in v1
- Operating mode: read findings, generate remediations, and write governance
  artifacts
- Repository placement: new sibling repo next to `ccode-to-codex`
- Scope target: common repository artifacts first; deeper runtime/dependency
  inspection only when reusable logic already exists in extracted code

## Non-Goals

- Building a CLI-first tool before the library contract stabilizes
- Tying the package identity to Claude/Codex migration workflows
- Solving full dependency-graph or package-runtime security analysis in v1
- Auto-applying destructive fixes without explicit caller intent

## Why This Exists

The current repo already contains reusable security-hardening patterns:

- identifier validation and root containment
- provenance/comment escaping for generated artifacts
- host-path redaction for reports and diagnostics
- GitHub Actions pinning checks
- adversarial regressions for traversal, symlinks, injection, and privacy leaks
- findings, remediation-plan, and audit-ledger structures

Those pieces are currently embedded in migration-specific scripts. The new repo
should turn them into reusable library contracts that can scan and remediate
other repositories without assuming `.claude/` or `.codex/` layouts.

## Design Options Considered

### Option 1: Modular library with pluggable rule packs

Create a small engine, typed finding/remediation models, rule-pack modules, and
adapter modules for specialized ecosystems.

Pros:

- clean separation between general framework and package-specific logic
- easy to extend to new repo surfaces without reworking the core
- preserves extracted logic without letting it define the whole product

Cons:

- slightly more design work up front

### Option 2: Monolithic package

Keep all checks, remediations, and artifact generation in one package surface.

Pros:

- fastest initial scaffold

Cons:

- weak boundaries
- harder to maintain as non-agent use cases grow

### Option 3: Mostly declarative rule engine

Represent most findings and remediations as data-driven policy specs.

Pros:

- high portability in the long run

Cons:

- poor fit for the imperative Python logic being extracted now
- higher initial complexity

## Chosen Approach

Option 1: modular library with pluggable rule packs.

This keeps the extracted security primitives portable, allows generic GitHub
repo scanning from day one, and provides a controlled place for migration- or
agent-specific checks to live as optional adapters instead of core identity.

## Repository Shape

The sibling repo should be initialized as a normal Python project with a `src/`
layout and tests.

### Proposed top-level layout

```text
<new-repo>/
  pyproject.toml
  README.md
  LICENSE
  .gitignore
  .github/workflows/
  docs/
    findings-taxonomy.md
    remediation-artifacts.md
  src/
    repo_security_vetting/
      __init__.py
      engine/
      models/
      rules/
      remediation/
      artifacts/
      adapters/
      extracted/
  tests/
    unit/
    integration/
    fixtures/
```

### Package responsibilities

- `engine/`
  - repo traversal
  - rule execution
  - remediation orchestration
  - artifact generation coordination
- `models/`
  - finding, severity, evidence, remediation plan, ledger row, patch proposal
- `rules/`
  - general checks grouped by repo surface
- `remediation/`
  - reusable fixers and patch builders
- `artifacts/`
  - audit ledger, findings report, remediation plan, regression scaffold writers
- `adapters/`
  - optional ecosystem-specific logic for agent or migration packages
- `extracted/`
  - thin compatibility layer around imported logic from this repo until it is
    normalized into stable framework modules

## Core Library Contract

The main public API should be library-oriented and structured around explicit
analysis and remediation phases.

### Primary API

- `analyze_repo(path, rule_packs=..., adapters=..., config=...) -> AuditResult`
- `plan_remediation(audit_result, policy=...) -> RemediationPlan`
- `apply_remediation(path, remediation_plan, mode=...) -> ApplyResult`
- `write_governance_artifacts(output_dir, audit_result, remediation_plan) -> ArtifactBundle`

### API expectations

- analysis is read-only
- remediation planning is deterministic for the same input/config
- apply mode supports dry-run and write modes
- governance artifacts are generated from structured finding data, not separate
  handwritten paths
- callers can run rule packs independently or as a composed profile

## First-Version Rule Packs

Version 1 should cover common GitHub repository surfaces first.

### `github_actions`

- detect unpinned GitHub Actions
- flag unsafe action source patterns
- propose commit-SHA pinning remediations

### `paths`

- validate identifiers used in path construction
- enforce root containment for joined paths
- detect traversal-style inputs in repo tooling

### `symlinks`

- detect copy-or-transform flows that follow symlinks
- flag possible exfiltration of out-of-root content

### `generated_artifacts`

- detect unescaped provenance/comment/banner emission
- flag generated TOML/Markdown/HTML/JSON that can be structurally altered by
  attacker-controlled names

### `report_privacy`

- detect absolute local-path leakage in generated text, JSON, and reports
- generate redacted display-path remediations

### `operator_guidance`

- detect filesystem-absolute paths in operational docs/config where repo-local
  or package-local references are required

### `shell_and_scripts`

- detect broad shell execution patterns relevant to the extracted rule set
- start with path- and file-handling risk patterns rather than full shell
  security analysis

### `python_packaging`

- include already-available reusable checks that fit broad Python package
  scanning
- avoid inventing deep dependency analysis in v1 unless existing extracted code
  already supports it cleanly

## Extracted Specialized Layer

The new repo should preserve extracted logic from `ccode-to-codex`, but isolate
it so the general framework does not depend on migration semantics.

### Specialized adapter targets

- migration-tooling path hardening
- migration-tooling report redaction
- migration-validator path policy checks
- package-specific governance artifact generation patterns

### Rule for inclusion

If a check assumes `.claude/`, `.codex/`, or migration-specific workflows, it
belongs behind an adapter or extracted compatibility layer until it is proven to
be generally reusable.

## Remediation Model

The library must support more than finding generation.

### Remediation outputs

- code or config patch proposals
- safe write-mode application for approved fixes
- findings register
- remediation plan
- audit coverage ledger
- regression test scaffold suggestions or generated skeletons

### Remediation safety constraints

- default mode is dry-run
- write mode only edits files explicitly targeted by remediation steps
- destructive or ambiguous fixes remain plan-only unless the caller opts in
- governance artifacts clearly distinguish confirmed findings from queued review

## Governance Artifacts

The extracted audit documents in this repo are a good template and should become
library outputs rather than one-off docs.

### Standard artifact set

- `security-audit-ledger.md`
- `security-findings.md`
- `security-remediation-plan.md`
- optional machine-readable JSON companion for findings and remediation state

### Artifact requirements

- structured around reviewed units and finding IDs
- include severity, impact, evidence, remediation, and verification fields
- designed to be shareable without leaking host-specific absolute paths

## Testing Strategy

The extracted repo should preserve the adversarial testing style because it is
the main evidence that the security logic is real rather than aspirational.

### Test layers

- unit tests for helpers and finding classification
- integration tests for repo scans across fixture repositories
- remediation tests for generated patches and governance artifacts
- regression fixtures for previously confirmed attack patterns

### Required adversarial fixtures

- path traversal identifiers
- path separators and dot-segment names
- newline-bearing provenance inputs
- comment terminator injection cases
- symlinked files escaping source roots
- absolute-path leakage in reports
- unpinned GitHub Actions workflows

## Initial Extraction Plan

The scaffolding work should proceed in this order:

1. create the sibling repo with Python packaging, tests, CI, and docs skeleton
2. extract reusable safety primitives into framework-owned modules
3. define stable finding/remediation/artifact models
4. port generic rule packs first
5. port governance artifact generation
6. port specialized migration logic behind adapters
7. add adversarial test fixtures mirroring the original findings
8. verify the new repo independently of `ccode-to-codex`

## Risks

### Risk: overfitting to current repo structure

Mitigation:

- keep repo-specific semantics behind adapters
- design core rules against general file surfaces, not `.claude/` or `.codex/`

### Risk: remediation becomes unsafe

Mitigation:

- dry-run by default
- typed remediation plans
- limited file target sets

### Risk: governance docs drift from actual findings

Mitigation:

- generate artifacts from structured finding records
- keep evidence and remediation IDs in code and artifact writers

## Success Criteria

The first version is successful when:

- it exists as an independent sibling repo
- it installs as a Python library
- it can analyze an arbitrary GitHub repo for the initial rule packs
- it can generate remediation plans and governance artifacts
- it preserves adversarial regressions for the extracted finding classes
- migration-specific logic is available without defining the core architecture
