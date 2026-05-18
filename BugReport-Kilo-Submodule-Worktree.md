# Bug Report: Kilo CLI loses sessions for Git submodules

**Product:** Kilo Code CLI  
**Version:** 7.3.0  
**Platform:** Linux x64 (musl)  
**Date:** 2026-05-18

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

## Suggested Fix

When resolving a project's `worktree`:
- If `.git` is a **directory**, use the current directory (existing behavior).
- If `.git` is a **file** (submodule / worktree), run `git rev-parse --show-toplevel` or read `core.worktree` from the resolved gitdir to obtain the real working directory, rather than inferring it from the gitdir path.

---

## Workaround (for users)

Manually correct the `worktree` column in `~/.local/share/kilo/kilo.db` for affected submodule projects, or avoid submodules by converting them to standalone clones.
