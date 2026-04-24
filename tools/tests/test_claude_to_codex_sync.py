# SPDX-License-Identifier: MIT

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path


def _import_sync_module():
    repo_root = Path(__file__).resolve().parents[2]
    tools_dir = repo_root / "tools"
    sys.path.insert(0, str(tools_dir))
    try:
        import claude_to_codex_sync  # type: ignore

        return claude_to_codex_sync
    finally:
        # Best-effort cleanup to avoid path pollution across tests.
        try:
            sys.path.remove(str(tools_dir))
        except ValueError:
            pass


class MirrorPlanningTests(unittest.TestCase):
    def test_plan_mirror_tree_detects_copies_and_deletes(self) -> None:
        mod = _import_sync_module()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src = root / "src"
            dst = root / "dst"
            src.mkdir()
            dst.mkdir()

            (src / "a.txt").write_text("a", encoding="utf-8")
            (src / "nested").mkdir()
            (src / "nested" / "b.txt").write_text("b", encoding="utf-8")

            (dst / "stale.txt").write_text("stale", encoding="utf-8")

            plan = mod.plan_mirror_tree(src=src, dst=dst, delete=True, refuse_symlinks=True)
            copy_rels = sorted([d.relative_to(dst).as_posix() for _s, d in plan.copies])
            delete_rels = sorted([p.relative_to(dst).as_posix() for p in plan.deletes])

            self.assertEqual(copy_rels, ["a.txt", "nested/b.txt"])
            self.assertEqual(delete_rels, ["stale.txt"])

    def test_apply_mirror_plan_copies_and_trashes_deletes(self) -> None:
        mod = _import_sync_module()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src = root / "src"
            dst = root / "dst"
            trash_root = root / "trash"
            src.mkdir()
            dst.mkdir()
            trash_root.mkdir()

            (src / "a.txt").write_text("a", encoding="utf-8")
            (dst / "stale.txt").write_text("stale", encoding="utf-8")

            plan = mod.plan_mirror_tree(src=src, dst=dst, delete=True, refuse_symlinks=True)
            mod.apply_mirror_plan(plan, trash_root=trash_root, apply=True)

            self.assertTrue((dst / "a.txt").is_file())
            self.assertFalse((dst / "stale.txt").exists())
            self.assertTrue(any(p.is_file() for p in trash_root.rglob("stale.txt*")))

    def test_plan_mirror_tree_refuses_symlink(self) -> None:
        mod = _import_sync_module()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src = root / "src"
            dst = root / "dst"
            src.mkdir()
            dst.mkdir()

            target = src / "target.txt"
            target.write_text("x", encoding="utf-8")
            link = src / "link.txt"
            try:
                os.symlink(str(target), str(link))
            except (OSError, NotImplementedError):
                self.skipTest("symlink not supported in this environment")

            with self.assertRaises(ValueError):
                mod.plan_mirror_tree(src=src, dst=dst, delete=False, refuse_symlinks=True)


class ClaudeMdInstructionTests(unittest.TestCase):
    def test_discover_chain_and_render(self) -> None:
        mod = _import_sync_module()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "CLAUDE.md").write_text("root", encoding="utf-8")
            sub = root / "a" / "b"
            sub.mkdir(parents=True)
            (root / "a" / "CLAUDE.md").write_text("a", encoding="utf-8")

            chain = mod.discover_claude_md_chain(sub, stop_at=root)
            self.assertEqual([p.name for p in chain], ["CLAUDE.md", "CLAUDE.md"])
            # Nearest-first (a/CLAUDE.md then root/CLAUDE.md).
            self.assertEqual(chain[0].parent.name, "a")
            self.assertEqual(chain[1], root / "CLAUDE.md")

            rendered = mod.render_instructions_md_from_claude_md(
                sources=chain,
                output_filename="AGENTS.md",
            )
            self.assertIn("# AGENTS.md (Generated)", rendered)
            self.assertIn("## From", rendered)
            self.assertIn("root", rendered)
            self.assertIn("a", rendered)


if __name__ == "__main__":
    unittest.main()

