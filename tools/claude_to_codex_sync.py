#!/usr/bin/env python3
# SPDX-License-Identifier: MIT

"""
Careful automation for Claude → Codex migration.

This script is intentionally conservative:
- Default is plan-only (no writes). Use --apply to perform changes.
- Sync operations are root-scoped (only the intended subtrees are touched).
- Tooling install/update into a target repo is opt-in / minimal by default.

Two primary modes:
1) global: mirror ~/.claude/{skills,agents} into a dedicated migration repo,
   run migrations there, then mirror resulting .codex/{skills,agents} into
   ~/.codex/{skills,agents}.
2) repo: run migrations inside an existing project repo that already contains
   .claude/{skills,agents}, updating .codex/{skills,agents} in place.

Notes on CLAUDE.md:
- This toolkit does not natively migrate CLAUDE.md.
- Optionally, we can generate a Codex-facing instructions file (AGENTS.md and/or
  CODEX.md) while leaving CLAUDE.md untouched for Claude.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Iterable


def _toolkit_root() -> Path:
    # This file lives at <toolkit>/tools/claude_to_codex_sync.py
    return Path(__file__).resolve().parents[1]


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except Exception:
        return False


def _sha256_file(path: Path) -> str:
    h = sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _same_file(a: Path, b: Path) -> bool:
    if not a.exists() or not b.exists():
        return False
    if a.stat().st_size != b.stat().st_size:
        return False
    # Cheap fast-path: mtime match. If mismatch, fall back to content hash.
    if int(a.stat().st_mtime) == int(b.stat().st_mtime):
        return True
    return _sha256_file(a) == _sha256_file(b)


@dataclass(frozen=True)
class MirrorPlan:
    copies: tuple[tuple[Path, Path], ...]
    deletes: tuple[Path, ...]


def plan_mirror_tree(
    *,
    src: Path,
    dst: Path,
    delete: bool,
    refuse_symlinks: bool,
) -> MirrorPlan:
    src = src.expanduser().resolve()
    dst = dst.expanduser().resolve()
    if not src.exists():
        return MirrorPlan(copies=(), deletes=())
    if not src.is_dir():
        raise ValueError(f"Source is not a directory: {src}")

    src_files: dict[Path, Path] = {}
    for p in src.rglob("*"):
        if p.is_dir():
            continue
        if refuse_symlinks and p.is_symlink():
            raise ValueError(f"Refusing to mirror symlinked file: {p}")
        rel = p.relative_to(src)
        src_files[rel] = p

    dst_files: dict[Path, Path] = {}
    if dst.exists():
        if not dst.is_dir():
            raise ValueError(f"Destination is not a directory: {dst}")
        for p in dst.rglob("*"):
            if p.is_dir():
                continue
            if refuse_symlinks and p.is_symlink():
                raise ValueError(f"Refusing to mirror into symlinked file: {p}")
            rel = p.relative_to(dst)
            dst_files[rel] = p

    copies: list[tuple[Path, Path]] = []
    for rel, src_file in sorted(src_files.items(), key=lambda kv: kv[0].as_posix()):
        dst_file = dst / rel
        if dst_file.exists() and _same_file(src_file, dst_file):
            continue
        copies.append((src_file, dst_file))

    deletes: list[Path] = []
    if delete and dst.exists():
        for rel, dst_file in sorted(dst_files.items(), key=lambda kv: kv[0].as_posix()):
            if rel not in src_files:
                deletes.append(dst_file)

    return MirrorPlan(copies=tuple(copies), deletes=tuple(deletes))


def apply_mirror_plan(
    plan: MirrorPlan,
    *,
    trash_root: Path | None,
    apply: bool,
) -> None:
    if not plan.copies and not plan.deletes:
        return

    if not apply:
        return

    trash_dir: Path | None = None
    if plan.deletes and trash_root is not None:
        trash_dir = trash_root.expanduser().resolve() / f"trash-{_utc_stamp()}"
        trash_dir.mkdir(parents=True, exist_ok=True)

    for src_file, dst_file in plan.copies:
        dst_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_file, dst_file)

    for doomed in plan.deletes:
        if trash_dir is not None:
            doomed = doomed.resolve()
            rel = doomed.name
            target = trash_dir / rel
            # Best-effort unique name to avoid collisions.
            if target.exists():
                target = trash_dir / f"{rel}.{_utc_stamp()}"
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(doomed), str(target))
        else:
            doomed.unlink(missing_ok=True)


def _repo_root_from(start: Path) -> Path:
    p = start.expanduser().resolve()
    if p.is_file():
        p = p.parent
    while p != p.parent:
        if (p / ".git").exists() or (p / "package.json").exists():
            return p
        p = p.parent
    raise RuntimeError(f"Unable to find repo root from: {start}")


def _ensure_repo_sentinel(repo_root: Path, *, apply: bool) -> None:
    # The migration scripts look for .git or package.json to define REPO_ROOT.
    if (repo_root / ".git").exists() or (repo_root / "package.json").exists():
        return
    if not apply:
        return
    (repo_root / "package.json").write_text(
        json.dumps({"name": "claude-to-codex-migration-workspace", "private": True}, indent=2)
        + "\n",
        encoding="utf-8",
    )


def _copy_tree_minimal(
    *,
    src: Path,
    dst: Path,
    apply: bool,
) -> None:
    if not src.exists():
        raise FileNotFoundError(str(src))
    if not apply:
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        # Minimal install is "install if missing" by default, so reaching here means update path.
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def ensure_tooling_installed(
    *,
    toolkit_root: Path,
    target_repo_root: Path,
    apply: bool,
    update: bool,
) -> list[str]:
    """Install migration tooling into a target repo (minimal set)."""
    actions: list[str] = []
    toolkit_root = toolkit_root.expanduser().resolve()
    target_repo_root = target_repo_root.expanduser().resolve()

    src_support = toolkit_root / "tools" / "migration_support"
    dst_support = target_repo_root / "tools" / "migration_support"

    needed_skills = (
        "migrate-to-codex",
        "migrate-agents-to-codex",
        "verify-skill-migration",
        "migration-dashboard",
    )
    for skill in needed_skills:
        src = toolkit_root / ".codex" / "skills" / skill
        dst = target_repo_root / ".codex" / "skills" / skill
        if dst.exists() and not update:
            continue
        actions.append(f"install tooling skill: .codex/skills/{skill}")
        _copy_tree_minimal(src=src, dst=dst, apply=apply)

    if (dst_support.exists() and not update) is False:
        # Install or update support library.
        actions.append("install tooling support lib: tools/migration_support")
        _copy_tree_minimal(src=src_support, dst=dst_support, apply=apply)

    return actions


def _run(
    argv: list[str],
    *,
    cwd: Path,
    env: dict[str, str],
    apply: bool,
) -> None:
    if not apply:
        return
    proc = subprocess.run(argv, cwd=str(cwd), env=env)
    if proc.returncode != 0:
        raise SystemExit(proc.returncode)


def discover_claude_md_chain(start_dir: Path, *, stop_at: Path | None) -> list[Path]:
    """Return CLAUDE.md files found from start_dir up to stop_at (inclusive)."""
    start_dir = start_dir.expanduser().resolve()
    stop_at_resolved = stop_at.expanduser().resolve() if stop_at else None
    found: list[Path] = []
    p = start_dir
    while True:
        candidate = p / "CLAUDE.md"
        if candidate.is_file():
            found.append(candidate)
        if stop_at_resolved is not None and p == stop_at_resolved:
            break
        if p == p.parent:
            break
        p = p.parent
    return found


def render_instructions_md_from_claude_md(
    *,
    sources: Iterable[Path],
    output_filename: str,
) -> str:
    sources = [p.expanduser().resolve() for p in sources]
    header = [
        f"# {output_filename} (Generated)",
        "",
        "This file is generated from one or more `CLAUDE.md` files to provide a Codex-facing",
        "instruction surface while leaving Claude’s `CLAUDE.md` files untouched.",
        "",
        "Sources (nearest-first):",
    ]
    for p in sources:
        header.append(f"- `{p}`")
    header.append("")

    parts: list[str] = ["\n".join(header)]
    for p in sources:
        try:
            body = p.read_text(encoding="utf-8").rstrip()
        except OSError:
            continue
        parts.append(f"## From `{p}`\n\n{body}\n")
    return "\n".join(parts).rstrip() + "\n"


def write_instructions_md(
    *,
    repo_root: Path,
    start_dir: Path,
    stop_at: Path | None,
    filename: str,
    apply: bool,
) -> str | None:
    sources = discover_claude_md_chain(start_dir, stop_at=stop_at)
    if not sources:
        return None
    out_path = repo_root / filename
    rendered = render_instructions_md_from_claude_md(
        sources=sources,
        output_filename=filename,
    )
    if apply:
        out_path.write_text(rendered, encoding="utf-8")
    return str(out_path)


def global_mode(args: argparse.Namespace) -> int:
    toolkit_root = _toolkit_root()
    claude_home = Path(args.claude_home).expanduser()
    codex_home = Path(args.codex_home).expanduser()
    migration_repo = Path(args.migration_repo).expanduser()

    apply = bool(args.apply)
    run_skills = not bool(args.agents_only)
    run_agents = not bool(args.skills_only)

    # Minimal, explicit root for global work so we don't pollute the toolkit repo.
    migration_repo.mkdir(parents=True, exist_ok=True)
    _ensure_repo_sentinel(migration_repo, apply=apply)

    tooling_actions = ensure_tooling_installed(
        toolkit_root=toolkit_root,
        target_repo_root=migration_repo,
        apply=apply,
        update=bool(args.update_tooling),
    )

    input_plans: list[tuple[str, MirrorPlan, Path | None]] = []
    if run_skills:
        # Mirror ~/.claude skills into migration repo's .claude.
        src_skills = claude_home / "skills"
        dst_skills = migration_repo / ".claude" / "skills"
        input_plans.append(
            (
                f"mirror inputs: {src_skills} -> {dst_skills}",
                plan_mirror_tree(src=src_skills, dst=dst_skills, delete=True, refuse_symlinks=True),
                migration_repo / ".claude" / ".trash",
            )
        )
    if run_agents:
        # Mirror ~/.claude agents into migration repo's .claude.
        src_agents = claude_home / "agents"
        dst_agents = migration_repo / ".claude" / "agents"
        input_plans.append(
            (
                f"mirror inputs: {src_agents} -> {dst_agents}",
                plan_mirror_tree(src=src_agents, dst=dst_agents, delete=True, refuse_symlinks=True),
                migration_repo / ".claude" / ".trash",
            )
        )

    # Run migrations in migration repo.
    env = os.environ.copy()
    env["CLAUDE_HOME"] = str(claude_home)
    env["CODEX_HOME"] = str(codex_home)

    skill_cmd = [
        sys.executable,
        ".codex/skills/migrate-to-codex/scripts/run_migration_workflow.py",
        "--all",
    ]
    agent_cmd = [
        sys.executable,
        ".codex/skills/migrate-agents-to-codex/scripts/run_agent_migration_workflow.py",
        "--all",
        "--format",
        "toml",
        "--force",
    ]

    tracker_cmd = [sys.executable, "tools/migration_support/tracker.py", "--write"]

    # Mirror outputs into CODEX_HOME.
    out_skill_src = migration_repo / ".codex" / "skills"
    out_agent_src = migration_repo / ".codex" / "agents"
    out_skill_dst = codex_home / "skills"
    out_agent_dst = codex_home / "agents"

    output_plans: list[tuple[str, MirrorPlan, Path | None]] = []
    if args.publish_outputs and run_skills:
        output_plans.append(
            (
                f"publish skills: {out_skill_src} -> {out_skill_dst}",
                plan_mirror_tree(
                    src=out_skill_src,
                    dst=out_skill_dst,
                    delete=bool(args.delete_outputs),
                    refuse_symlinks=True,
                ),
                codex_home / ".trash",
            )
        )
    if args.publish_outputs and run_agents:
        output_plans.append(
            (
                f"publish agents: {out_agent_src} -> {out_agent_dst}",
                plan_mirror_tree(
                    src=out_agent_src,
                    dst=out_agent_dst,
                    delete=bool(args.delete_outputs),
                    refuse_symlinks=True,
                ),
                codex_home / ".trash",
            )
        )

    written_instruction_paths: list[str] = []
    if args.write_agents_md:
        p = write_instructions_md(
            repo_root=migration_repo,
            start_dir=migration_repo,
            stop_at=Path.home() if args.instructions_include_parents else migration_repo,
            filename="AGENTS.md",
            apply=apply,
        )
        if p:
            written_instruction_paths.append(p)
    if args.write_codex_md:
        p = write_instructions_md(
            repo_root=migration_repo,
            start_dir=migration_repo,
            stop_at=Path.home() if args.instructions_include_parents else migration_repo,
            filename="CODEX.md",
            apply=apply,
        )
        if p:
            written_instruction_paths.append(p)

    # Render plan.
    print("Mode: global")
    print(f"- toolkit_root: {toolkit_root}")
    print(f"- migration_repo: {migration_repo}")
    print(f"- CLAUDE_HOME: {claude_home}")
    print(f"- CODEX_HOME: {codex_home}")
    print(f"- run_skills: {run_skills}")
    print(f"- run_agents: {run_agents}")
    if tooling_actions:
        print("- tooling:")
        for a in tooling_actions:
            print(f"  - {a}")

    for label, plan, _trash in input_plans:
        print(f"- {label}")
        print(f"  - copies: {len(plan.copies)}")
        print(f"  - deletes: {len(plan.deletes)}")

    print("- would run:")
    if run_skills:
        print(f"  - {' '.join(skill_cmd)} (cwd={migration_repo})")
    if run_agents:
        print(f"  - {' '.join(agent_cmd)} (cwd={migration_repo})")
    print(f"  - {' '.join(tracker_cmd)} (cwd={migration_repo})")

    if args.publish_outputs:
        for label, plan, _trash in output_plans:
            print(f"- {label}")
            print(f"  - copies: {len(plan.copies)}")
            print(f"  - deletes: {len(plan.deletes)}")

    for p in written_instruction_paths:
        print(f"- would write: {p}")

    if not apply:
        print("\nDry-run only. Re-run with --apply to perform these actions.")
        return 0

    # Apply.
    for _label, plan, trash in input_plans:
        apply_mirror_plan(plan, trash_root=trash, apply=True)
    if run_skills:
        _run(skill_cmd, cwd=migration_repo, env=env, apply=True)
    if run_agents:
        _run(agent_cmd, cwd=migration_repo, env=env, apply=True)
    _run(tracker_cmd, cwd=migration_repo, env=env, apply=True)
    for _label, plan, trash in output_plans:
        apply_mirror_plan(plan, trash_root=trash, apply=True)
    return 0


def repo_mode(args: argparse.Namespace) -> int:
    toolkit_root = _toolkit_root()
    repo_root = _repo_root_from(Path(args.repo_root))
    apply = bool(args.apply)

    _ensure_repo_sentinel(repo_root, apply=apply)

    tooling_actions = ensure_tooling_installed(
        toolkit_root=toolkit_root,
        target_repo_root=repo_root,
        apply=apply,
        update=bool(args.update_tooling),
    )

    env = os.environ.copy()
    if args.claude_home:
        env["CLAUDE_HOME"] = str(Path(args.claude_home).expanduser())
    if args.codex_home:
        env["CODEX_HOME"] = str(Path(args.codex_home).expanduser())

    run_skills = not bool(args.agents_only) and (bool(args.all) or bool(args.skill))
    run_agents = not bool(args.skills_only) and (bool(args.all) or bool(args.agent))

    skill_cmd: list[str] | None = None
    if run_skills:
        skill_cmd = [
            sys.executable,
            ".codex/skills/migrate-to-codex/scripts/run_migration_workflow.py",
            "--all" if args.all else "--skill",
        ]
        if not args.all:
            if not args.skill:
                raise SystemExit("--skill is required unless --all is set")
            skill_cmd.append(args.skill)

    agent_cmd: list[str] | None = None
    if run_agents:
        agent_cmd = [
            sys.executable,
            ".codex/skills/migrate-agents-to-codex/scripts/run_agent_migration_workflow.py",
            "--all" if args.all else "--agent",
        ]
        if not args.all:
            if not args.agent:
                raise SystemExit("--agent is required unless --all is set")
            agent_cmd.append(args.agent)
        agent_cmd.extend(["--format", "toml", "--force"])

    tracker_cmd = [sys.executable, "tools/migration_support/tracker.py", "--write"]

    written_instruction_paths: list[str] = []
    if args.write_agents_md:
        p = write_instructions_md(
            repo_root=repo_root,
            start_dir=repo_root,
            stop_at=Path.home() if args.instructions_include_parents else repo_root,
            filename="AGENTS.md",
            apply=apply,
        )
        if p:
            written_instruction_paths.append(p)
    if args.write_codex_md:
        p = write_instructions_md(
            repo_root=repo_root,
            start_dir=repo_root,
            stop_at=Path.home() if args.instructions_include_parents else repo_root,
            filename="CODEX.md",
            apply=apply,
        )
        if p:
            written_instruction_paths.append(p)

    print("Mode: repo")
    print(f"- repo_root: {repo_root}")
    print(f"- run_skills: {run_skills}")
    print(f"- run_agents: {run_agents}")
    if tooling_actions:
        print("- tooling:")
        for a in tooling_actions:
            print(f"  - {a}")
    print("- would run:")
    if skill_cmd:
        print(f"  - {' '.join(skill_cmd)} (cwd={repo_root})")
    if agent_cmd:
        print(f"  - {' '.join(agent_cmd)} (cwd={repo_root})")
    print(f"  - {' '.join(tracker_cmd)} (cwd={repo_root})")
    for p in written_instruction_paths:
        print(f"- would write: {p}")

    if not apply:
        print("\nDry-run only. Re-run with --apply to perform these actions.")
        return 0

    if skill_cmd:
        _run(skill_cmd, cwd=repo_root, env=env, apply=True)
    if agent_cmd:
        _run(agent_cmd, cwd=repo_root, env=env, apply=True)
    _run(tracker_cmd, cwd=repo_root, env=env, apply=True)
    return 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Careful automation for Claude → Codex migration (global and repo modes)."
    )
    sub = parser.add_subparsers(dest="mode", required=True)

    p_global = sub.add_parser("global", help="Mirror ~/.claude to ~/.codex via a dedicated migration repo.")
    p_global.add_argument("--apply", action="store_true", help="Perform changes (default is dry-run).")
    p_global.add_argument("--claude-home", default=str(Path.home() / ".claude"))
    p_global.add_argument("--codex-home", default=str(Path.home() / ".codex"))
    p_global.add_argument(
        "--migration-repo",
        default=str(Path.home() / ".claude-to-codex-migrate"),
        help="Dedicated repo/workspace holding mirrored inputs + generated outputs.",
    )
    p_global.add_argument("--update-tooling", action="store_true", help="Overwrite tooling in the migration repo.")
    p_global.add_argument(
        "--publish-outputs",
        action="store_true",
        help="Mirror generated .codex/{skills,agents} into CODEX_HOME/{skills,agents}.",
    )
    p_global.add_argument(
        "--delete-outputs",
        action="store_true",
        help="When publishing, delete files in CODEX_HOME/{skills,agents} that are not in generated outputs (moved to trash).",
    )
    p_global.add_argument(
        "--write-agents-md",
        action="store_true",
        help="Generate AGENTS.md from discovered CLAUDE.md files (leaves CLAUDE.md untouched).",
    )
    p_global.add_argument(
        "--write-codex-md",
        action="store_true",
        help="Generate CODEX.md from discovered CLAUDE.md files (leaves CLAUDE.md untouched).",
    )
    p_global.add_argument(
        "--instructions-include-parents",
        action="store_true",
        help="Include parent-directory CLAUDE.md files up to $HOME when generating instructions.",
    )
    global_group = p_global.add_mutually_exclusive_group()
    global_group.add_argument(
        "--skills-only",
        action="store_true",
        help="Only sync/migrate/publish skills (skip agents).",
    )
    global_group.add_argument(
        "--agents-only",
        action="store_true",
        help="Only sync/migrate/publish agents (skip skills).",
    )

    p_repo = sub.add_parser("repo", help="Run migrations in an existing project repo.")
    p_repo.add_argument("--apply", action="store_true", help="Perform changes (default is dry-run).")
    p_repo.add_argument("--repo-root", default=".", help="Path inside the repo; root is auto-detected.")
    p_repo.add_argument("--update-tooling", action="store_true", help="Overwrite tooling in the repo.")
    p_repo.add_argument("--all", action="store_true", help="Migrate all skills/agents.")
    p_repo.add_argument("--skill", help="Migrate one skill (implies --all false).")
    p_repo.add_argument("--agent", help="Migrate one agent (implies --all false).")
    p_repo.add_argument("--claude-home", help="Optional CLAUDE_HOME override for runtime/plugin discovery.")
    p_repo.add_argument("--codex-home", help="Optional CODEX_HOME override for runtime/plugin installs.")
    repo_group = p_repo.add_mutually_exclusive_group()
    repo_group.add_argument(
        "--skills-only",
        action="store_true",
        help="Only migrate skills (skip agents).",
    )
    repo_group.add_argument(
        "--agents-only",
        action="store_true",
        help="Only migrate agents (skip skills).",
    )
    p_repo.add_argument(
        "--write-agents-md",
        action="store_true",
        help="Generate AGENTS.md from discovered CLAUDE.md files (leaves CLAUDE.md untouched).",
    )
    p_repo.add_argument(
        "--write-codex-md",
        action="store_true",
        help="Generate CODEX.md from discovered CLAUDE.md files (leaves CLAUDE.md untouched).",
    )
    p_repo.add_argument(
        "--instructions-include-parents",
        action="store_true",
        help="Include parent-directory CLAUDE.md files up to $HOME when generating instructions.",
    )

    args = parser.parse_args(argv)
    if args.mode == "repo":
        # Default to --all if neither a specific skill nor agent is provided.
        if not args.all and not args.skill and not args.agent:
            args.all = True
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    if args.mode == "global":
        return global_mode(args)
    if args.mode == "repo":
        return repo_mode(args)
    raise SystemExit(f"Unknown mode: {args.mode}")


if __name__ == "__main__":
    raise SystemExit(main())
