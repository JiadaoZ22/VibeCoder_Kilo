# Bug Report: Kilo CLI loses sessions for Git submodules

**Product:** Kilo Code CLI  
**Version:** 7.3.0 (confirmed still present in 7.3.1)  
**Platform:** Linux x64 (musl)  
**Date:** 2026-05-18 (last verified 2026-05-21)

---

## Summary

When a project is a **Git submodule** (where `.git` is a file pointing to `.git/modules/<name>` in the parent repo), Kilo stores the **`.git/modules/<path>` directory** as the project's `worktree` in its local SQLite database (`~/.local/share/kilo/kilo.db`). Because the stored `worktree` does not match the actual working directory, Kilo fails to associate previous sessions with the project on restart, making session history appear lost.

---

## Affected Repository Structures

On the reporter's machine, the bug manifests in any submodule under these parent repos:
- `/media/zoujd4/DATA1/Users/zoujd4/Zoujd_IMI/`  
- `/media/zoujd4/DATA1/Users/zoujd4/JDgentLAB/`

Confirmed affected submodules:
- `VibeCoder_Kilo`
- `MyResearchReading`
- `Brain/FreeSurfer`
- `proj_PaperReplication` (not yet used with Kilo, but will trigger the same bug)
- `open-design` (not yet used with Kilo, but will trigger the same bug)

## Steps to Reproduce

1. Create or enter a Git submodule working directory where `.git` is a file, e.g.:
   ```
   /path/to/parent/VibeCoder_Kilo/.git   ← file containing "gitdir: ../.git/modules/VibeCoder_Kilo"
   ```
2. Run `kilo` inside the submodule directory and start a session.
3. Exit Kilo.
4. Run `kilo` again in the same directory.
5. Observe that previous sessions are not found / a new project/session is created.

---

## Observed Behavior

In `~/.local/share/kilo/kilo.db`, the `project` table records:

| project `id` | stored `worktree` | actual working directory | sandboxes |
|---|---|---|---|
| `a31cb1999225cec4110e6e56492c6ec396ab56f1` | `.../JDgentLAB/.git/modules` | `.../JDgentLAB/VibeCoder_Kilo` | `[".../VibeCoder_Kilo"]` |
| `7983312a3bf2a821197f4cdd797662c9ed499fd7` | `.../JDgentLAB/.git/modules/2_KnowledgeBases` | `.../JDgentLAB/2_KnowledgeBases/MyResearchReading` | `[".../MyResearchReading"]` |
| `e7872c4a14c01060bfd2446cee1a4455cd25cdad` | `.../Zoujd_IMI/.git/modules/f1_Code/Brain` | `.../Zoujd_IMI/f1_Code/Brain/FreeSurfer` | `[".../FreeSurfer"]` |

Pattern: Kilo appears to use `dirname(git-dir)` for submodules instead of `git rev-parse --show-toplevel`.

For normal (non-submodule) repos, the `worktree` is recorded correctly.

---

## Expected Behavior

The `worktree` field should contain the actual working directory of the submodule (e.g. `.../VibeCoder_Kilo`), matching the behavior for regular repositories.

---

## Root-Cause Hypothesis

Kilo detects the Git repository by resolving the `.git` file, finds the real gitdir at `.git/modules/<name>`, and then uses the **parent directory of that gitdir** (`dirname(.git/modules/<name>)`) as the project worktree. It should instead resolve the working tree via `git rev-parse --show-toplevel` (or by reading `core.worktree` from the submodule's git config, which correctly points back to the working directory).

---

## Impact

- Users working inside Git submodules lose access to previous sessions on every Kilo restart.
- The bug is silent: no error is shown; sessions simply do not appear.
- Affects any repository layout using Git submodules (common in monorepos, dotfiles, or research-code organizations).

---

## Environment Details

```
$ kilo --version
7.3.0

$ git rev-parse --show-toplevel
/media/zoujd4/DATA1/Users/zoujd4/JDgentLAB/VibeCoder_Kilo

$ git rev-parse --git-dir
/media/zoujd4/DATA1/Users/zoujd4/JDgentLAB/.git/modules/VibeCoder_Kilo

$ cat .git
gitdir: ../.git/modules/VibeCoder_Kilo

$ git config --file .git/config --get core.worktree
../../../VibeCoder_Kilo
```

---

## Suggested Fix (for Kilo upstream)

When resolving a project's `worktree`:
- If `.git` is a **directory**, use the current directory (existing behavior).
- If `.git` is a **file** (submodule / worktree), run `git rev-parse --show-toplevel` or read `core.worktree` from the resolved gitdir to obtain the real working directory, rather than inferring it from the gitdir path.

---

## Playground Reproduction (2026-05-19)

A clean reproduction was performed in a sandbox to confirm the bug mechanics.

### Setup

```
/home/zoujd4/kilo-playground/
├── parent/                    ← parent git repo
│   ├── .git/
│   ├── .gitmodules
│   └── submod-child/          ← submodule (.git is a FILE)
│       ├── .git   → "gitdir: ../.git/modules/submod-child"
│       └── README.md
└── submod-actual/             ← bare repo for submodule origin
```

### Reproduction steps

```bash
cd /home/zoujd4/kilo-playground/parent/submod-child
kilo debug snapshot track
kilo run "test" --title "Playground test session"
kilo debug snapshot track   # simulate restart
```

### Observed results

**1. Project registration (wrong `worktree`)**

DB query after first Kilo access:

| `id` | `worktree` | `sandboxes` |
|---|---|---|
| `795a3cd8af705309f8a1a725d0a76ea0b7e4d3ad` | `/home/zoujd4/kilo-playground/parent/.git/modules` ❌ | `["/home/zoujd4/kilo-playground/parent/submod-child"]` ✅ |

- The `.git/kilo` marker was written into the **gitdir**, not the working tree:
  ```bash
  cat /home/zoujd4/kilo-playground/parent/.git/modules/submod-child/kilo
  # → 795a3cd8af705309f8a1a725d0a76ea0b7e4d3ad
  ```

**2. Session creation (correct `directory`)**

The session was stored with the correct working directory:
- `project_id`: `795a3cd8af705309f8a1a725d0a76ea0b7e4d3ad`
- `directory`: `/home/zoujd4/kilo-playground/parent/submod-child` ✅
- `title`: `Playground test session`

**3. Restart behavior — Kilo overwrites the `worktree` on EVERY access**

Running `kilo debug snapshot track` a second time **re-used** the same project ID (read from `.git/modules/submod-child/kilo`), but **re-wrote the `worktree` back to the wrong value**.

A monitoring script running every 60 seconds captured the overwrite cycle:

```
11:02:02 Fixed 795a3cd8af705309f8a1a725d0a76ea0b7e4d3ad
        from: /home/zoujd4/kilo-playground/parent/.git/modules
        to:   /home/zoujd4/kilo-playground/parent/submod-child
11:03:05 Fixed 795a3cd8af705309f8a1a725d0a76ea0b7e4d3ad   ← overwritten AGAIN by Kilo
        from: /home/zoujd4/kilo-playground/parent/.git/modules
        to:   /home/zoujd4/kilo-playground/parent/submod-child
```

**Key finding:** Kilo does not just set the wrong `worktree` once — it **re-detects and re-writes it on every project access**.

**4. Session visibility**

`kilo session list` still shows the session even when the `worktree` is broken, so the session is **not deleted** from the DB. The failure mode is likely in the TUI startup path: Kilo knows the real `directory` on startup (`INFO service=project directory=... fromDirectory`), but the mismatched `worktree` in the DB probably causes the home screen / auto-resume logic to start a **fresh session** instead of surfacing the previous one.

---

## Personal Verification (2026-05-21)

Re-tested on Kilo **7.3.1** in the actual `VibeCoder_Kilo` submodule:

| Step | `worktree` in DB |
|------|------------------|
| Before `kilo` TUI | `.../JDgentLAB/VibeCoder_Kilo` ✅ |
| After `kilo` TUI  | `.../JDgentLAB/.git/modules` ❌ |

**Key finding:** `kilo debug snapshot track` (used in the original playground repro) **does NOT** trigger the overwrite in 7.3.1, but the **full `kilo` TUI startup DOES**. The bug is specifically in the TUI project-resolution path, not the snapshot/debug path.

Logs confirm Kilo knows the real directory on startup:
```
INFO service=project directory=/media/zoujd4/.../VibeCoder_Kilo fromDirectory
```
…yet the DB `worktree` column is still rewritten to the gitdir parent.

---

## User Workaround

See [`README.md`](./README.md) in this directory for tested fixes:
- One-shot manual repair
- Persistent auto-repair via systemd user timer
- Converting submodules to standalone clones
