# Skill Dependency Resolution Design

## Goal

Enable the Claude-to-Codex skill migrator to handle mutually dependent skills such as
`phase-worker` and `phase-reviewer`, while only migrating plugin-backed dependencies
and runtime assets when they are actually required by migrated skills.

## Problem

The current skill migrator classifies operational skill references in a binary way:

- resolved if the referenced Codex skill already exists locally
- blocked if only a Claude source skill exists

That model fails for:

- same-batch dependencies where multiple Claude skills are being migrated together
- cyclic dependencies where no topological ordering exists
- plugin-backed dependencies that may exist in installed Codex plugins
- Claude plugin skills that should be migrated on demand when no Codex parity exists
- runtime assets such as `notify.sh` that need Codex-side installation and wiring

## Requirements

### Functional

1. A skill dependency is considered satisfiable when it is provided by any of:
   - an existing Codex skill
   - an installed Codex plugin skill
   - another source skill in the current migration batch
   - a Claude plugin skill that can be migrated on demand
2. Cyclic source-skill dependencies must migrate as a unit instead of hard-blocking.
3. Claude plugins must not be migrated eagerly. They are only considered when a
   referenced dependency is otherwise unresolved.
4. Runtime assets such as `notify.sh` must only be installed and wired into Codex
   when a migrated dependency requires them.
5. Codex runtime updates must be idempotent and must be able to modify:
   - `~/.codex/config.toml`
   - `~/.codex/hooks.json`

### Non-Functional

- Do not weaken existing path-containment or symlink safety checks.
- Do not log secrets or copy secret-bearing files into repo artifacts.
- Preserve current behavior for simple one-skill migrations that have no unresolved
  dependencies.
- Keep the dependency resolver deterministic for a given source tree and Codex home.

## Recommended Approach

Implement a demand-driven dependency resolver and batch planner inside the skill
migrator. The resolver upgrades dependency handling from a binary missing/resolved
check to a typed state model and allows migration of strongly connected components.

This keeps the migration surface narrow:

- source skills are still the primary migration unit
- Claude plugin skills are only consulted when needed to satisfy a referenced skill
- runtime assets are only installed when a migrated dependency explicitly requires them

## Dependency Model

Every referenced skill token should resolve to one of these states:

- `codex_skill`
  A matching skill exists in `.codex/skills`.
- `codex_plugin_skill`
  A matching namespaced skill exists in an installed Codex plugin.
- `batch_source_skill`
  A matching source skill exists in `.claude/skills` and is included in the current
  migration batch.
- `claude_plugin_skill`
  A matching dependency exists in a Claude plugin and can be migrated on demand.
- `missing`
  No satisfiable provider exists.
- `ambiguous`
  The reference still requires manual adjudication under existing ambiguity rules.

`missing` remains blocking. `ambiguous` remains manual-review gated. The other four
states are satisfiable.

## Batch Planning

### Batch membership

When the user requests `--all`, batch membership is the full non-archived source
skill set. When the user requests `--skill <name>`, batch membership begins with the
requested skill and expands to any required source skills that are satisfiable via
`batch_source_skill`.

### Cycle handling

Build a directed graph where nodes are source skills and edges represent operational
dependencies between source skills in the batch. Collapse the graph into strongly
connected components.

Migration behavior:

- singleton SCC with no self-loop: migrate in dependency order
- multi-node SCC or self-loop: classify as a cycle batch and migrate the component as
  one unit

The key semantic change is that a source-skill dependency inside the same SCC is not
blocking merely because its Codex artifact does not exist yet.

### Output ordering

Emit deterministic output by sorting SCCs and members by skill name before execution.

## Claude Plugin Dependency Handling

Add discovery for Claude plugin skills from `~/.claude/plugins`, but only consult it
after normal Codex-skill and same-batch resolution fail.

Resolution rules:

1. If Codex parity exists, use it and do nothing else.
2. If a source skill in the batch satisfies the dependency, use the batch.
3. If no Codex parity exists but a Claude plugin skill can satisfy the dependency,
   plan an on-demand plugin migration for that dependency.
4. If none of the above holds, the dependency is `missing`.

This avoids bulk migration of unrelated plugins.

## Runtime Asset Handling

Runtime assets are not treated as generic copied files. They are dependency-owned
installations with explicit Codex wiring.

### Asset model

Each migratable dependency may declare zero or more runtime assets, for example:

- scripts to install under `~/.codex/`
- hook commands to install into `~/.codex/hooks.json`
- plugin/config entries to merge into `~/.codex/config.toml`

### Installation rules

- install only assets required by resolved dependencies
- write files idempotently
- merge TOML/JSON structurally instead of rewriting unrelated user config
- preserve existing user settings outside the owned keys being installed
- never emit secret-bearing asset contents into repo logs or generated migration
  reports

### `notify.sh`

`~/.claude/notify.sh` contains runtime credentials. The migration flow must treat it
as a local runtime asset:

- install into `~/.codex/` only if a migrated dependency needs it
- wire it into `~/.codex/hooks.json` or `~/.codex/config.toml` as appropriate for the
  target runtime behavior
- avoid copying the script into the repo or exposing its contents in artifacts

## Proposed Code Changes

### Shared support

- `tools/migration_support/paths.py`
  Add Claude plugin discovery helpers alongside existing Codex plugin discovery.
- `tools/migration_support/`
  Add a dependency-resolution module for:
  - dependency state classification
  - batch expansion
  - SCC construction
  - plugin dependency planning
  - runtime asset installation planning

### Skill migrator

- `.codex/skills/migrate-to-codex/scripts/migrate_claude_workflows_to_codex.py`
  Replace the current direct `missing_skills` gating with the dependency resolver.
  Preserve ambiguity and orchestration-risk checks.

### Runtime installer

- add support code that can patch:
  - `~/.codex/config.toml`
  - `~/.codex/hooks.json`
  - selected runtime asset files under `~/.codex/`

This may live in shared support or in a dedicated migration helper script, but it
should be reused by the skill migrator rather than embedded inline.

## Data Flow

1. Parse source skill references.
2. Resolve each dependency against:
   - local Codex skills
   - installed Codex plugins
   - same-batch source skills
   - on-demand Claude plugin skills
3. Build the source dependency graph for satisfiable batch skill edges.
4. Collapse SCCs and plan migration order.
5. Migrate required source skills and any required plugin-provided skills.
6. Install and wire any declared runtime assets.
7. Return classification and migration results with explicit provenance for what was
   migrated and what runtime changes were made.

## Error Handling

- Block when a dependency is truly missing.
- Preserve manual-review gating for ambiguous references.
- Fail safely when runtime config files are malformed; do not overwrite invalid user
  config silently.
- If an asset install partially succeeds, report the exact incomplete step and stop
  before claiming completion.
- If a Claude plugin dependency cannot be migrated mechanically, surface that as a
  targeted blocker rather than falling back to broad plugin copying.

## Testing

Add targeted tests for:

1. Two-skill cycle migration succeeds when both skills are in the requested batch.
2. `--skill phase-worker` expands the batch to include `phase-reviewer`.
3. A same-batch dependency does not appear in `missing_skills`.
4. An unresolved external dependency still blocks migration.
5. A Codex plugin skill continues to satisfy namespaced references.
6. A Claude plugin skill is only consulted when no Codex parity exists.
7. On-demand Claude plugin migration only installs the referenced dependency.
8. Runtime asset installation updates `~/.codex/config.toml` idempotently.
9. Runtime hook installation updates `~/.codex/hooks.json` idempotently.
10. Secret-bearing runtime assets are installed without leaking contents into logs or
    migration reports.

## Risks

- Claude plugin formats may not map cleanly to Codex plugin/runtime structures.
- Automatic config merging can damage user state if patch ownership is not narrowly
  defined.
- Over-expanding the batch could surprise users if single-skill migrations silently
  pull in large dependency sets.

## Mitigations

- Keep plugin migration demand-driven and dependency-specific.
- Use explicit ownership boundaries for TOML/JSON merges.
- Report auto-expanded batch membership before writing changes.
- Preserve dry-run and analysis-only modes for dependency planning.

## Success Criteria

The design is successful when:

- `phase-worker` and `phase-reviewer` can migrate without manual hand-authoring
  solely because they depend on each other
- a missing plugin-backed dependency is migrated only when referenced
- Codex runtime wiring occurs automatically when needed
- unrelated Claude plugins and assets are not copied
- deterministic preview output explains batch expansion, cycle grouping, plugin
  dependency handling, and runtime config changes before the live run
