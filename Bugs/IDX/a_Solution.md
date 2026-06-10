# Fix: Qdrant "Failed to obtain server version" Warning

## Quickstart

Already patched and installed — just verify and go:

```bash
# Confirm the fixed binary is active
kilo --version
# Expected: 0.0.0-main-202606101332 (or the build date you see)

# That's it — the warning is gone and IDX still works.
```

If you ever need to revert to the stock binary:

```bash
cp ~/.npm-global/lib/node_modules/@kilocode/cli/bin/.kilo.backup \
   ~/.npm-global/lib/node_modules/@kilocode/cli/bin/.kilo
```

---

## Problem

Error / warning printed on every Kilo CLI startup when code indexing is enabled:

> "Failed to obtain server version. Unable to check client-server compatibility. Set checkCompatibility=false to skip version check"

This is **not** a cloud-connectivity issue (`app.kilo.ai`). It comes from the **Qdrant vector-database client** embedded in Kilo, which tries to ping `http://localhost:6333` to check version compatibility on initialization.

## Actual Root Cause

- `packages/kilo-indexing/src/indexing/vector-store/qdrant-client.ts` instantiates `QdrantClient` without passing `checkCompatibility: false`.
- The Qdrant JS client defaults `checkCompatibility` to `true`.
- On construction it fires an async `root({})` call to the server. When no local Qdrant is running, the call fails and `console.warn` emits the message above.

## Solution Applied (Source Patch)

### 1. Modified `qdrant-client.ts`

Added `checkCompatibility: false` to **both** `QdrantClient` constructor invocations:

```typescript
// Primary host-based constructor
this.client = new QdrantClient({
  host: urlObj.hostname,
  https: useHttps,
  port: port,
  prefix: urlObj.pathname === "/" ? undefined : urlObj.pathname.replace(/\/+$/, ""),
  apiKey,
  checkCompatibility: false,   // <-- FIX
  headers: {
    "User-Agent": "Kilo-Code",
  },
})

// Fallback URL-based constructor (catch block)
this.client = new QdrantClient({
  url: parsedUrl,
  apiKey,
  checkCompatibility: false,   // <-- FIX
  headers: {
    "User-Agent": "Kilo-Code",
  },
})
```

### 2. Updated unit tests

File: `packages/kilo-indexing/test/kilocode/indexing/vector-store/qdrant-client.test.ts`

All `toHaveBeenCalledWith` / `toHaveBeenLastCalledWith` expectations that assert on `QdrantClient` constructor arguments were updated to include `checkCompatibility: false`.

**Test result after fix:**
- `425 pass, 0 fail` across the `kilo-indexing` package.

### 3. Built and installed the fixed CLI

| Step | Command / Action |
|------|------------------|
| Clone source | `git clone --depth 1 https://github.com/Kilo-Org/kilocode.git kilo-source` |
| Install deps | `bun install` |
| Build current platform only | `bun run script/build.ts --single` (in `packages/opencode`) |
| Replace binary | Copied `dist/@kilocode/cli-linux-x64/bin/kilo` → `~/.npm-global/lib/node_modules/@kilocode/cli/bin/.kilo` |
| Backup original | Original saved as `.kilo.backup` |

### 4. Verified the fix

- **Smoke test:** `kilo --version` and `kilo --pure models anthropic` both pass.
- **Standalone warning test:** A small script that instantiates `QdrantVectorStore` and captures `console.warn` confirms **zero** compatibility warnings are emitted.

## Why This Is Safe

- `checkCompatibility` only controls a **client-side version-comparison warning**. It does not change any API behavior, search accuracy, or indexing logic.
- LanceDB remains the default vector-store backend for local indexing; Qdrant is only used when explicitly configured.
- Kilo's actual code-indexing functionality (embeddings, collection creation, search, upsert, delete) is completely unaffected.

## Files & Locations

| Path | Purpose |
|------|---------|
| `kilo-source/packages/kilo-indexing/src/indexing/vector-store/qdrant-client.ts` | Source file containing the fix |
| `kilo-source/packages/kilo-indexing/test/kilocode/indexing/vector-store/qdrant-client.test.ts` | Updated unit tests |
| `~/.npm-global/lib/node_modules/@kilocode/cli/bin/.kilo` | Installed fixed binary |
| `~/.npm-global/lib/node_modules/@kilocode/cli/bin/.kilo.backup` | Backup of original stock binary |

## References

- Qdrant JS client source (`qdrant-client.js`, lines 60-72): shows the `checkCompatibility` default and the warning emission logic.
- Kilo Code repository: `https://github.com/Kilo-Org/kilocode`
