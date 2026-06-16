# Fix: Failed to obtain server version. Unable to check client-server compatibility.

## Problem
Error message: "Failed to obtain server version. Unable to check client-server compatibility. Set checkCompatibility=false to skip version check"

## Actual Root Cause
This warning comes from the **Qdrant vector database client** embedded within Kilo. When Kilo starts code indexing, it initializes a Qdrant client that tries to connect to a local Qdrant server (default: `http://localhost:6333`) to check version compatibility.

**This is NOT related to Kilo cloud connectivity (`app.kilo.ai`) - that was a misunderstanding.**

The Qdrant client has a `checkCompatibility` parameter that defaults to `true`, but Kilo doesn't expose this configuration option.

## IMPORTANT: What Does NOT Work
1. **`checkCompatibility: false` in kilo.json** - This is a Qdrant client parameter, not a Kilo config option. Kilo doesn't pass this to the Qdrant client internally.
2. **Changing API keys or base URLs** - Unrelated to this Qdrant client warning.
3. **Network fixes for `app.kilo.ai`** - The warning is about Qdrant (port 6333), not Kilo's cloud.

## Working Solutions

### Solution 1 (Recommended)
**Ignore the warning** - It does NOT affect Kilo functionality. Code indexing uses LanceDB (file-based vector DB) by default, not Qdrant. The Qdrant client initialization failure is harmless.

### Solution 2 (Disable Code Indexing)
If you want to completely eliminate the warning, disable code indexing in your `kilo.json`:

```json
{
  "$schema": "https://app.kilo.ai/config.json",
  "indexing": {
    "enabled": false
  }
}
```

This will disable all vector database initialization, including the Qdrant client check.

### Solution 3 (Run a Local Qdrant Server - Eliminate Warning)
If you want the warning gone AND keep indexing enabled, run a local Qdrant server:

```bash
# Using Docker
docker run -p 6333:6333 qdrant/qdrant

# Or using Qdrant binary (if installed)
qdrant
```

The Qdrant client will successfully connect and the warning will disappear.

### Solution 4 (Upgrade Kilo)
Newer versions of Kilo may have fixed this by either:
1. Disabling the Qdrant version check by default
2. Using only LanceDB without initializing Qdrant

```bash
# Check current version
kilo --version

# Upgrade Kilo to latest version
npm install -g @kilocode/cli

# Verify upgrade
kilo --version
```

## Related Issue: ENOSPC Error
If you also see "ENOSPC: no space left on device" errors, this is caused by inotify watcher limit being exceeded. Fix with:

```bash
# Kill all existing Kilo processes
pkill -f "kilo\|.kilo"

# Increase inotify watcher limit (until reboot)
sudo sysctl -w fs.inotify.max_user_watches=524288

# Make it permanent (survives reboot)
echo 'fs.inotify.max_user_watches=524288' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

## Configuration Location
Global Kilo configuration: `~/.config/kilo/kilo.json` or `/home/<user>/.config/kilo/kilo.json`

Project-level configuration: `.kilo/kilo.json` in your project directory

## Kilo Version Tested
7.3.41

## Date
2026-06-10

---

# Fix: Doubao/Ark Embedding "max 10, got 60" Batch Error

## Problem
During code indexing the scan fails with:

```text
Failed during initial scan: Indexing failed: Failed to process batch after 3 retries:
Embedding request failed after 3 attempts with status 400:
400 The parameter `input` specified in the request are not valid:
Embeddings API input limit exceeded: max 10, got 60.
```

Progress appears stuck at `0% (0/N files)` and then errors out.

## Root Cause
The configured OpenAI-compatible embedding provider (Volcano Ark / Doubao) caps the number of `input` strings per `/embeddings` request at **10**. Kilo's default embedding batch size is **60**, so every batch was rejected.

## Solution Applied
Patched the OpenAI-compatible embedder to cap request input length at the provider limit.

### Files changed
| File | Change |
|---|---|
| `kilo-source/packages/kilo-indexing/src/indexing/constants/index.ts` | Added `OPENAI_COMPATIBLE_MAX_BATCH_INPUTS = 10` |
| `kilo-source/packages/kilo-indexing/src/indexing/embedders/openai-compatible.ts` | Batches are now split once they reach 10 inputs, regardless of the higher-level `embeddingBatchSize` setting |
| `kilo-source/packages/kilo-indexing/test/kilocode/indexing/embedders/openai-compatible.test.ts` | Regression test verifying a 15-item batch is split into 10 + 5 |

### Immediate workaround (before patch)
Set the top-level `indexing.embeddingBatchSize` option to `10` in your Kilo config:

```json
{
  "indexing": {
    "enabled": true,
    "provider": "openai-compatible",
    "model": "doubao-embedding-vision",
    "dimension": 2048,
    "vectorStore": "lancedb",
    "embeddingBatchSize": 10,
    "openai-compatible": {
      "apiKey": "{env:ARK_API_KEY}",
      "baseUrl": "https://ark.cn-beijing.volces.com/api/plan/v3"
    }
  }
}
```

### Build & install (already done)
```bash
cd /media/zoujd4/DATA1/Users/zoujd4/JDgentLAB/VibeCoder_Kilo/kilo-source
PATH="$HOME/.bun/bin:$PATH" bun run --cwd packages/opencode script/build.ts --single --skip-install

cp packages/opencode/dist/@kilocode/cli-linux-x64/bin/kilo /tmp/kilo.new
chmod +x /tmp/kilo.new
mv -f /tmp/kilo.new ~/.npm-global/lib/node_modules/@kilocode/cli/bin/.kilo
```

### Clear stale index and restart
```bash
rm -rf ~/.local/share/kilo/indexing
kilo --version
```

Then start Kilo and run `/indexing`.

## Date
2026-06-16
