# Fix: mobile app shows "not found" when opening a desktop `/remote` session

**Product:** Kilo Code CLI (local build)
**Source tree:** `/media/zoujd4/DATA1/Users/zoujd4/JDgentLAB/VibeCoder_Kilo/kilo-source`
**Branch:** `fix/qdrant-check-compatibility`
**Fixed in build:** `0.0.0-fix-qdrant-check-compatibility-202608190324`
**Date:** 2026-08-19
**Status:** ✅ Confirmed fixed by user on 2026-08-19

---

## Symptom

- Desktop session `E2E_DK_Parcellation:main` (`ses_05970ac10ffe3hCzb1IxEqy6zw`) runs with `/remote` enabled.
- The Kilo mobile app **lists** the session correctly (title shows the running build version).
- Tapping the session in the mobile app shows **"not found"** — the session can never be opened from mobile.

## Initial (wrong) hypothesis

The preview version string `0.0.0-fix-qdrant-check-compatibility-<date>` was suspected of breaking relay version-gating. A version-compat layer was built (see "Related change" below) — but logs disproved it as the cause of "not found".

## Diagnosis (from logs)

`~/.local/share/kilo/log/dev.log`:

- `remote-ws` connected fine (connectionId `768d2bbd`, gen=1), `heartbeat_ack` every ~10 s → the mobile **session list** comes from the live relay heartbeat. This is why the session appears at all.
- **Zero** "creating session" / bootstrap log lines for the session.
- `~/.local/share/kilo/storage/session_share/` had **no record** for `ses_05970ac10ffe3hCzb1IxEqy6zw` (only five old `ses_fe84…`/`ses_feb9…` records with `{id, ingestPath}`).

## Root cause

`KiloSessions.bootstrap()` (POST `/api/session`, which creates the cloud content record) was only triggered by the `watch(Session.Event.Created)` handler in `packages/opencode/src/kilo-sessions/kilo-sessions.ts`.

A **resumed** session — created by an earlier process (this one dated 2026-07-28 per `time.created`) — never fires `Session.Event.Created` in the current process, so:

1. it is never bootstrapped to the ingest service,
2. the cloud has no content record for it,
3. the mobile app lists it (via heartbeat) but shows "not found" on open.

## Fix

`packages/opencode/src/kilo-sessions/kilo-sessions.ts`:

- New `ensureShared(sessionId)`: when the heartbeat's `getSessions()` advertises a session, check its `session_share` storage record; if missing (NotFoundError treated as "never bootstrapped"), run the existing `create()` bootstrap (POST `/api/session` + `fullSync()`), coalesced via `bootstrapInflight`.
- A module-level `ensured: Set<string>` guarantees **once per process per session**; failures remove the mark so the next heartbeat retries.
- Fire-and-forget — a slow ingest POST never delays the heartbeat payload.

Regression test: `test/kilocode/kilo-sessions.test.ts` — "bootstraps an advertised session whose share record is missing (resumed session)" creates a session, waits for the Created-path bootstrap, **deletes** the share record to reproduce the resumed-session state, then asserts the next advertised heartbeat re-POSTs `/api/session`.

Changeset: `.changeset/remote-resumed-session-bootstrap.md` (patch, `@kilocode/cli`).

## Related change (kept, but orthogonal)

Preview-version compatibility layer, still in the tree:

- `packages/opencode/src/kilo-sessions/remote-version.ts` — `RemoteVersion.resolve(version, base) → {protocol, build?}`; `current = resolve(InstallationVersion, InstallationBaseVersion)`.
- `packages/core/src/installation/version.ts` — `KILO_BASE_VERSION` global + `InstallationBaseVersion`.
- `remote-ws.ts` / `remote-protocol.ts` / `instance-advertisement.ts` — heartbeat/advertisement send `protocolVersion: 7.4.22` (base) plus optional `buildVersion: 0.0.0-…` (preview string).
- Tests: `test/kilocode/sessions/remote-version.test.ts`, `test/kilocode/cli/cmd/remote.test.ts`. Changeset: `.changeset/remote-preview-version-compat.md`.

## Verification

- `bun test test/kilocode/kilo-sessions.test.ts` → 22/22 pass.
- `bun test test/kilocode/sessions/remote-ws.test.ts test/kilocode/sessions/remote-version.test.ts test/kilocode/cli/cmd/remote.test.ts` → 51/51 pass.
- `bun run typecheck` in `packages/opencode/` → only the two known pre-existing errors (`bootstrap.ts` `defaultLayer`, `session-compaction-chunks-benchmark.test.ts` layers) — unchanged by this fix.
- `bun run script/check-opencode-annotations.ts --worktree` → clean (all edits carry `kilocode_change` markers).
- New binary built with smoke tests passed: `kilo-source/packages/opencode/dist/@kilocode/cli-linux-x64/bin/kilo`, `--version` = `0.0.0-fix-qdrant-check-compatibility-202608190324`, fix string confirmed inside the binary.
- **User confirmed on 2026-08-19:** mobile can now open the desktop session.

## Deployment note

The fix only applies to processes started from the new binary. Previously running sessions kept using deleted FUSE inodes until exited. Required steps (done 2026-08-19):

1. Exit the old desktop session(s).
2. Start fresh via `kilo` (see updated install layout in `a_Solution.md`).
3. Open/resume the project session, run `/remote`.
4. On mobile, tap the session — the first advertising heartbeat bootstraps it; allow a few seconds before tapping.

## Install layout after 2026-08-19 cleanup

- Old npm-global `@kilocode/cli` v7.3.41 **uninstalled**; the `bin/versions/` artifact scheme described in `a_Solution.md` no longer exists.
- `~/.npm-global/bin/kilo` → symlink directly to `kilo-source/packages/opencode/dist/@kilocode/cli-linux-x64/bin/kilo`.
- Removed: `dist-old-running-2`, `dist-old-running-3`, and the stale `~/.kilo-active-previous` rollback marker.
- Pending removal (still held open by running old processes at cleanup time): `.dist-old-running.deleted`, `.dist-old-running-4.deleted` — safe to `rm -rf` once no old `kilo` processes remain.
