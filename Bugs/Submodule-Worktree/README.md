# Kilo Submodule Worktree Fix

**Bug:** Kilo CLI corrupts the `worktree` path for Git submodules in its SQLite database on every TUI startup, making session history appear lost.  
**Affected:** Kilo ≤ 7.4.5 (verified up to 7.3.1; not re-tested on newer releases).  
**Scope:** Any Git repo where `.git` is a file pointing to a parent `.git/modules/` directory.

---

## Quick Apply

### Persistent fix (recommended)

One command installs the auto-repair timer that runs every minute:

```bash
cd Bugs/Submodule-Worktree
./install.sh
```

This copies the repair script to `~/.local/bin/` and enables a systemd user timer so Kilo can never keep the wrong value for long.

### One-shot manual repair

If you prefer not to install a timer, run the script directly:

```bash
python3 kilo-fix-submodules.py
```

---

## Recovery: Your sessions are NOT lost

Even when the `worktree` is wrong, `kilo session list` still shows your sessions because Kilo queries by `project_id`. The failure is only in the **TUI startup / auto-resume logic**, which uses `worktree` to match the current directory.

After repairing the DB, resume with:

```bash
kilo -c                    # continue the most recent session
kilo --session <id>        # resume a specific session
```

---

## Files

| File | Purpose |
|------|---------|
| `install.sh` | One-command installer (persistent timer) |
| `kilo-fix-submodules.py` | Repair script — scans entire DB and fixes all affected projects |
| `systemd/kilo-fix-submodules.service` | systemd oneshot service definition |
| `systemd/kilo-fix-submodules.timer` | systemd timer (every 60 seconds) |
| `Problem.md` | Full technical bug report, reproduction, and root-cause analysis |

---

## Verification

Check the timer is active:

```bash
systemctl --user status kilo-fix-submodules.timer
```

View the most recent repair run:

```bash
journalctl --user -u kilo-fix-submodules.service --no-pager
```

---

## How the script works

1. Opens `~/.local/share/kilo/kilo.db` (SQLite).
2. Finds every `project` row where `worktree` contains `/.git/modules`.
3. Restores the correct path from the `sandboxes` column (which Kilo still records correctly).
4. Commits the fix.

The script is **idempotent** — running it on a clean database produces no changes and does no harm.
