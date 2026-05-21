#!/usr/bin/env python3
"""
Kilo Submodule Worktree Auto-Repair Script
============================================

Kilo CLI (up to at least v7.3.1) has a bug where Git submodules get their
`worktree` field corrupted in `~/.local/share/kilo/kilo.db` on every TUI
startup. The stored path becomes the parent of the gitdir
(e.g. `.../.git/modules`) instead of the actual working directory.

This script scans the entire Kilo database and repairs ALL affected projects
by restoring the correct path from the `sandboxes` column (which Kilo still
records correctly).

Usage:
    python3 kilo-fix-submodules.py           # one-shot repair
    systemctl --user start kilo-fix-submodules.service   # via systemd
"""

import sqlite3
import json
import os


def fix_submodule_worktrees():
    db_path = os.path.expanduser("~/.local/share/kilo/kilo.db")

    if not os.path.exists(db_path):
        print(f"kilo-fix: database not found at {db_path}")
        return 0

    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Find every project whose worktree points into a .git/modules directory
    c.execute(
        "SELECT id, worktree, sandboxes FROM project WHERE worktree LIKE '%/.git/modules%'"
    )
    rows = c.fetchall()
    fixed_count = 0

    for proj_id, worktree, sandboxes_raw in rows:
        sandboxes = json.loads(sandboxes_raw) if sandboxes_raw else []
        if sandboxes:
            fixed_path = sandboxes[0]  # Kilo always records the real cwd here
        else:
            # Fallback heuristic: infer from gitdir path
            parts = worktree.split("/.git/modules/")
            if len(parts) == 2:
                fixed_path = parts[0] + "/" + parts[1]
            else:
                continue

        c.execute(
            "UPDATE project SET worktree = ? WHERE id = ?",
            (fixed_path, proj_id),
        )
        fixed_count += 1
        print(f"kilo-fix: repaired {proj_id}\n  from: {worktree}\n  to:   {fixed_path}")

    conn.commit()
    conn.close()

    if fixed_count > 0:
        print(f"kilo-fix: total repaired = {fixed_count}")
    else:
        print("kilo-fix: no broken worktrees found")

    return fixed_count


if __name__ == "__main__":
    fix_submodule_worktrees()
