# Issue Report: `/remote` is unavailable in Kilo Code CLI

**Product:** Kilo Code CLI (local build)
**Version:** 7.4.22 / binary `0.0.0-fix-qdrant-check-compatibility-202608170357`
**Source tree:** `/media/zoujd4/DATA1/Users/zoujd4/JDgentLAB/VibeCoder_Kilo/kilo-source` (branch `fix/qdrant-check-compatibility`, merged upstream v7.4.22)
**Platform:** Linux x64
**Date:** 2026-08-18
**Verdict:** Not a code bug — a **configuration/authentication precondition** that is not communicated in the TUI.

---

## Summary

`/remote` never appears in the TUI slash-command list, and `kilo remote` fails from the shell. The cause is that **no `kilo` credential exists** in `~/.local/share/kilo/auth.json`. This machine is authenticated only against third-party providers (`openrouter`, `ark`), never against the Kilo Gateway account, and the remote session relay is a Kilo-account service.

Two independent gates therefore fail:

1. **TUI gate** — the command is registered with `enabled: isKiloConnected()` / `hidden: !isKiloConnected()`, so it is filtered out of the palette entirely.
2. **Runtime gate** — `KiloSessions.enableRemote()` throws when no Kilo token can be resolved.

---

## Evidence

### 1. Auth state on this machine

`~/.local/share/kilo/account.json`:

| account id | serviceID | credential |
|---|---|---|
| `f6f15fb48001rXlJK6UaG6MZDn` | `openrouter` | api key |
| `f6f15fb48002EtM5v5WOWBRQdr` | `ark` | api key |

`kilo auth list` reports exactly two credentials (OpenRouter, ark). **No `kilo` entry.**

### 2. Reproduction from the shell

```console
$ kilo remote
Error: Unexpected error

Unable to enable remote: no Kilo credentials found. Run `kilo auth login`.
```

The subcommand itself exists and is registered correctly:

```console
$ kilo remote --help
kilo remote
enable remote connection for real-time session relay
```

So `kilo remote` is wired up (`packages/opencode/src/kilocode/cli/setup.ts:57`, `packages/opencode/src/kilocode/commands.ts:72`); only the credential is missing.

---

## Root Cause Analysis (code path)

### A. TUI visibility gate

`packages/opencode/src/kilocode/kilo-commands.tsx:44`

```ts
const isKiloConnected = createMemo(() => {
  return sync.data.provider_next.connected.includes("kilo")
})
```

`packages/opencode/src/kilocode/kilo-commands.tsx:89-123` — the `/remote` registration:

```ts
{
  name: "remote.toggle",
  title: "Toggle remote",
  desc: "Enable or disable remote session relay",
  category: "Kilo",
  slashName: "remote",
  enabled: isKiloConnected(),
  hidden: !isKiloConnected(),
  run: async () => { /* sdk.client.remote.status() / enable() / disable() */ },
}
```

`provider_next.connected` is produced by the provider HTTP handler
(`packages/opencode/src/server/routes/instance/httpapi/handlers/provider.ts:83`):

```ts
connected: Object.keys(connected),   // connected = yield* provider.list()
```

`provider.list()` only returns providers that have **resolved credentials and a non-empty model list**. With no `kilo` credential, `"kilo"` is absent from `connected`, so `isKiloConnected()` is `false`.

The palette/slash filter then drops the entry — `packages/tui/src/keymap.tsx:49`:

```ts
function isVisiblePaletteCommand(command: Command) {
  return command.hidden !== true && command.name !== COMMAND_PALETTE_COMMAND
}
```

and `useCommandSlashes()` (`packages/tui/src/keymap.tsx:260-289`) builds `/…` entries only from that filtered set. Result: **`/remote` is not merely disabled, it is invisible** — no error, no hint, no "requires Kilo login" message. This is the real usability defect.

### B. Runtime gate

`packages/opencode/src/kilo-sessions/kilo-sessions.ts:624-648`:

```ts
export async function enableRemote() {
  if (ingestDisabled) return
  ensureDefaultInstanceAdvertisement()
  if (remote) return
  if (enabling) return enabling
  ...
  const token = await kilocodeToken()
  if (!token) {
    throw new Error("Unable to enable remote: no Kilo credentials found. Run `kilo auth login`.")
  }
  const valid = await authValid(token)
  if (valid === false) throw new Error("... invalid or expired Kilo credentials. Run `kilo auth login`.")
  if (valid === undefined) throw new Error("... failed to verify Kilo credentials.")
  ...
}
```

Token resolution (`kilo-sessions.ts:155-166`) accepts, in order:

1. `auth.get("kilo")` of type `api` (`key`), `oauth` (`access`), or `wellknown` (`token`)
2. env var `KILO_API_KEY`

Neither is present here, so the throw at step 1 is hit.

Validation calls `GET ${KILO_API_BASE}/api/user` (`kilo-sessions.ts:141`), with
`KILO_API_BASE = process.env.KILO_API_URL || https://api.kilo.ai`
(`packages/kilo-gateway/src/api/constants.ts:13`).

The relay websocket target is
`KILO_SESSION_INGEST_URL || https://ingest.kilosessions.ai` → upgraded to `wss://`
(`kilo-sessions.ts:645-647`).

### C. Additional kill switches (not active here, but worth knowing)

`kilo-sessions.ts:232`:

```ts
const ingestDisabled =
  process.env["KILO_DISABLE_SESSION_INGEST"] === "true" || process.env["KILO_DISABLE_SESSION_INGEST"] === "1"
```

If set, `enableRemote()` returns silently — remote appears to "succeed" but nothing is advertised or relayed.

---

## Precondition Checklist for `/remote`

| # | Requirement | Status here |
|---|---|---|
| 1 | A `kilo` credential in `~/.local/share/kilo/auth.json` (or `KILO_API_KEY`) | ❌ missing |
| 2 | `"kilo"` present in `provider_next.connected` (⇒ Kilo provider models resolved) | ❌ false |
| 3 | `GET https://api.kilo.ai/api/user` returns 2xx for the token | ⛔ untestable (no token) |
| 4 | `KILO_DISABLE_SESSION_INGEST` unset / not `true`/`1` | ✅ unset |
| 5 | Outbound `wss://ingest.kilosessions.ai` reachable (proxy/firewall) | ⚠️ unverified |

---

## Solution

### Primary fix — authenticate the Kilo account

```bash
kilo auth login          # choose the Kilo / Kilo Gateway provider (not OpenRouter, not ark)
kilo auth list           # must now show a `kilo` credential
```

Then, in an **already-running TUI**, the `/remote` entry is still hidden until
`provider_next.connected` is refreshed — restart the TUI:

```bash
# exit the TUI, then
kilo
/remote                  # should now appear under the "Kilo" category
```

Verify from the shell instead of the TUI (headless relay host, blocks until Ctrl-C):

```bash
kilo remote
# expected: "Remote connection enabled."
```

### Alternative — env-var token (CI / headless)

```bash
export KILO_API_KEY="<kilo-account-token>"
kilo remote
```

`kilocodeToken()` falls back to `KILO_API_KEY` (`kilo-sessions.ts:162-164`). Note this only satisfies gate **B**; the TUI `/remote` entry stays hidden because gate **A** reads the provider list, not the env var. Use `kilo remote` for this path.

### Self-hosted / staging endpoints

```bash
export KILO_API_URL="https://api.kilo.ai"                    # auth validation base
export KILO_SESSION_INGEST_URL="https://ingest.kilosessions.ai"  # relay (auto-upgraded to wss://)
```

### Diagnostics if it still fails after login

```bash
# 1. token present?
python3 -c "import json;print(list(json.load(open('$HOME/.local/share/kilo/auth.json')).keys()))"

# 2. token accepted by the API? (expect HTTP 200)
curl -s -o /dev/null -w '%{http_code}\n' -H "Authorization: Bearer $KILO_API_KEY" https://api.kilo.ai/api/user

# 3. relay reachable?
curl -s -o /dev/null -w '%{http_code}\n' https://ingest.kilosessions.ai

# 4. kill switch off?
env | grep -E 'KILO_DISABLE_SESSION_INGEST|KILO_API_URL|KILO_SESSION_INGEST_URL'

# 5. verbose CLI logs
kilo remote --print-logs --log-level DEBUG
```

Map the error text to the failing gate:

| Message | Failing gate | Action |
|---|---|---|
| `no Kilo credentials found` | no token at all | `kilo auth login` (Kilo provider) |
| `invalid or expired Kilo credentials` | `/api/user` → non-2xx | re-login; token revoked/expired |
| `failed to verify Kilo credentials` | `/api/user` unreachable | network/proxy/DNS to `api.kilo.ai` |
| silent no-op, remote never connects | `ingestDisabled` | `unset KILO_DISABLE_SESSION_INGEST` |
| `/remote` absent from slash list | `provider_next.connected` lacks `kilo` | login **and** restart TUI |

---

## Upstream Improvement Request

The hard-hidden gate is user-hostile: a user with no Kilo credential gets **zero feedback** that `/remote` exists at all, and there is no in-TUI path to discover the requirement.

Suggested change in `packages/opencode/src/kilocode/kilo-commands.tsx:89-123`:

```ts
// instead of hidden: !isKiloConnected()
enabled: isKiloConnected(),
hidden: false,
run: async () => {
  if (!isKiloConnected()) {
    dialog.replace(() => (
      <DialogAlert
        title="Kilo login required"
        message="Remote session relay requires a Kilo account. Run `kilo auth login` and restart the CLI."
      />
    ))
    return
  }
  /* existing toggle logic */
},
```

This keeps the functional gate while making the precondition discoverable — matching how `/kiloclaw` already routes unprovisioned users into `DialogClawSetup` instead of hiding itself.

---

## Affected / Referenced Files

| File | Relevance |
|---|---|
| `packages/opencode/src/kilocode/kilo-commands.tsx:44,89-123` | `/remote` TUI registration + `isKiloConnected` gate |
| `packages/tui/src/keymap.tsx:49,260-289` | `hidden` filter that removes it from the slash list |
| `packages/opencode/src/kilo-sessions/kilo-sessions.ts:141,155-166,232,624-648` | token resolution, `/api/user` validation, `ingestDisabled`, `enableRemote()` |
| `packages/opencode/src/cli/cmd/remote.ts` | headless `kilo remote` command |
| `packages/opencode/src/kilocode/cli/setup.ts:57`, `packages/opencode/src/kilocode/commands.ts:72` | CLI registration (confirmed correct) |
| `packages/opencode/src/server/routes/instance/httpapi/handlers/provider.ts:58-83` | source of `provider_next.connected` |
| `packages/kilo-gateway/src/api/constants.ts:13` | `KILO_API_BASE` default `https://api.kilo.ai` |
| `~/.local/share/kilo/auth.json`, `~/.local/share/kilo/account.json` | local credential state (only `openrouter`, `ark`) |
