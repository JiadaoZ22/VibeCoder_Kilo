# New build loses previous sessions/cache; doubao-search MCP fails

**Product:** Kilo Code CLI (local build)
**Source tree:** `/media/zoujd4/DATA1/Users/zoujd4/JDgentLAB/VibeCoder_Kilo/kilo-source`
**Observed in build:** `0.0.0-dev-zoujd-mainline-202608200243` (first build after the branch rename)
**Date:** 2026-08-20
**Status:** ✅ Fixed 2026-08-20 — data migration + uv mirror config; no source change needed.

---

## Issue 1 — previous sessions and cache "gone" in the new build

### Root cause

The session database filename is **channel-derived**, and the channel is the sanitized git branch name at build time:

- `packages/opencode/src/storage/db.ts:33` `getChannelPath()` and `packages/core/src/database/database.ts:48` `path()`:
  - release channels (`latest`/`beta`/`prod`) or `KILO_DISABLE_CHANNEL_DB=1` → `~/.local/share/kilo/kilo.db`
  - otherwise → `kilo-<channel>.db`, falling back to a pre-existing `opencode-<channel>.db` **of the same channel only**

Renaming the branch `fix/qdrant-check-compatibility` → `dev/zoujd-mainline` (2026-08-19) changed the channel, so the new build created a fresh empty `kilo-dev-zoujd-mainline.db` while all real sessions stayed in `opencode-fix-qdrant-check-compatibility.db` (481 MB, still being written by the old build's running processes).

Observed files in `~/.local/share/kilo/`: `kilo.db` (release, stale), `opencode-main.db`, `opencode-fix-qdrant-check-compatibility.db` (all recent sessions), `kilo-dev-zoujd-mainline.db` (fresh, empty).

### Fix applied

One-time online backup into the new channel name (safe while the old build keeps the source DB open — SQLite backup API):

```
cd ~/.local/share/kilo
mv kilo-dev-zoujd-mainline.db kilo-dev-zoujd-mainline.db.fresh-20260820.bak   # today's fresh db kept aside
rm -f kilo-dev-zoujd-mainline.db-shm kilo-dev-zoujd-mainline.db-wal
python3 -c 'import sqlite3; s=sqlite3.connect("file:opencode-fix-qdrant-check-compatibility.db?mode=ro",uri=True); d=sqlite3.connect("kilo-dev-zoujd-mainline.db"); s.backup(d)'
```

Since the branch name is now stable (`dev/zoujd-mainline`), the channel — and therefore the DB — is stable going forward; this will not recur unless the branch is renamed again.

### Prevention notes

- Do not rename the working branch casually; the channel DB name follows it. (This regression was an unintended side effect of the 2026-08-19 branch rename.)
- Escape hatch if ever needed: `KILO_DB=<absolute path>` pins the DB explicitly, or `KILO_DISABLE_CHANNEL_DB=1` forces the shared `kilo.db`.

## Issue 2 — doubao-search MCP fails to start

### Root cause

The MCP (`~/.config/kilo/opencode.json` → `mcp.doubao-search`) launches via `uvx --from git+https://github.com/volcengine/mcp-server#…`. The git fetch worked, but dependency resolution hit `https://pypi.org/simple/…` → **TLS handshake EOF** — the same local-proxy interference documented in `Bugs/Balance-Fetch/Problem.md` (pypi.org joins the blocked list: npmjs, plugins.gradle.org, packages.jetbrains.team, cdn.sheetjs.com).

Not related to the new binary; any fresh uvx resolve would have failed the same way.

### Fix applied

`~/.config/uv/uv.toml` (user-level, applies to every uv/uvx invocation including MCP subprocesses):

```toml
[[index]]
url = "https://pypi.tuna.tsinghua.edu.cn/simple"
default = true
```

Verified 2026-08-20: `uvx --from git+https://github.com/volcengine/mcp-server#subdirectory=server/mcp_server_askecho_search_infinity mcp-server-askecho-search-infinity --help` installs 37 packages via the mirror and prints usage. The uvx environment is now cached, so later MCP starts do not depend on the network at all.
