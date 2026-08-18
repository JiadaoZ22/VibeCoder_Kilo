# Fix: `/remote` is now visible and explains its Kilo-account precondition

**Product:** Kilo Code CLI (local build)
**Source tree:** `/media/zoujd4/DATA1/Users/zoujd4/JDgentLAB/VibeCoder_Kilo/kilo-source`
**Branch:** `fix/qdrant-check-compatibility`
**Build date:** 2026-08-18

---

## Change

`packages/opencode/src/kilocode/kilo-commands.tsx:44-123`

The `/remote` slash command no longer hides itself when no Kilo credential is configured. Instead it stays visible in the command palette and shows a clear dialog when invoked.

The original gate used `sync.data.provider_next.connected.includes("kilo")`, but that is **not** a credential check: the Kilo provider autoloads with an anonymous key when no real credential is stored, so `"kilo"` is always in `connected`. The command therefore called `sdk.client.remote.enable()`, the server returned a generic `Unauthorized` error, and the TUI showed the unhelpful fallback `Failed to enable remote.`

The fix adds a real credential check via the existing `/kilo/auth-status` endpoint:

```ts
import { createMemo, createResource } from "solid-js"

// provider_next.connected includes the kilo provider even with an anonymous key,
// so check the actual stored credential before allowing remote relay.
const [kiloAuthStatus] = createResource(() => sdk.client.kilo.authStatus())
const isKiloAuthenticated = createMemo(() => {
  return kiloAuthStatus()?.data?.authenticated === true
})

// /remote command
{
  name: "remote.toggle",
  title: "Toggle remote",
  desc: "Enable or disable remote session relay",
  category: "Kilo",
  slashName: "remote",
  enabled: isKiloConnected(),   // stays visible because kilo is "connected" via anonymous key
  hidden: false,
  run: async () => {
    if (!isKiloAuthenticated()) {
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
}
```

This matches the `/kiloclaw` pattern: keep the functional gate, but route unprovisioned users to a discoverable setup message instead of silently removing the command.

---

## Build artifacts

Per the repo's immutable-build policy, previous binaries were kept and a new artifact was produced:

| Artifact | Path | Active? |
|---|---|---|
| Pre-fix (frozen from live `dist/`) | `~/.npm-global/lib/node_modules/@kilocode/cli/bin/versions/kilo-7.4.22-ccd56a5-20260817` | ❌ |
| First attempt (visible `/remote`, but still used `provider_next.connected` gate) | `~/.npm-global/lib/node_modules/@kilocode/cli/bin/versions/kilo-7.4.22-ccd56a518b-20260818` | ❌ |
| Second attempt (`auth-status` gate, but `enabled` was tied to it so the command stayed hidden) | `~/.npm-global/lib/node_modules/@kilocode/cli/bin/versions/kilo-7.4.22-ccd56a518b-20260818-080606` | ❌ |
| Final corrected build (visible + `auth-status` runtime gate) | `~/.npm-global/lib/node_modules/@kilocode/cli/bin/versions/kilo-7.4.22-ccd56a518b-20260818-100505` | ✅ |

The active binary is selected by the `.kilo` symlink:

```bash
readlink -f ~/.npm-global/lib/node_modules/@kilocode/cli/bin/.kilo
# -> .../kilo-7.4.22-ccd56a518b-20260818-100505
```

`~/.npm-global/bin/kilo` now points to the npm launcher shim (`.../bin/kilo`) rather than directly into `kilo-source/packages/opencode/dist/`, so future rebuilds cannot silently mutate the installed CLI.

---

## Verification

1. Confirm the active version:

```bash
kilo --version
# 0.0.0-fix-qdrant-check-compatibility-202608181005
```

2. Start the TUI in a project without a Kilo credential. Type `/remote` — it now appears under the "Kilo" category. Selecting it shows:

```
Kilo login required
Remote session relay requires a Kilo account. Run `kilo auth login` and restart the CLI.
```

3. After `kilo auth login` with the Kilo provider and a TUI restart, `/remote` toggles remote relay as before.

---

## Roll back

```bash
BIN=~/.npm-global/lib/node_modules/@kilocode/cli/bin
ln -sfn "$(cat ~/.kilo-active-previous)" "$BIN/.kilo"
kilo --version
```

---

## Notes

- Pre-existing Kilo TUI sessions were running against the `dist/` binary during the builds, so those directories were renamed to `dist-old-running` and `dist-old-running-2` to allow builds to proceed without killing those sessions. Once those sessions exit, remove the leftover directories manually:

```bash
rm -rf /media/zoujd4/DATA1/Users/zoujd4/JDgentLAB/VibeCoder_Kilo/kilo-source/packages/opencode/dist-old-running
rm -rf /media/zoujd4/DATA1/Users/zoujd4/JDgentLAB/VibeCoder_Kilo/kilo-source/packages/opencode/dist-old-running-2
```

- `packages/opencode/src/kilocode/` already contains `kilocode` in its path, so no `kilocode_change` markers were needed for this edit.
- Package-level `bun run typecheck` in `packages/opencode/` reports pre-existing errors unrelated to this change (missing `defaultLayer` / `layer` properties in `bootstrap.ts` and a benchmark test). The edited file compiled cleanly.
