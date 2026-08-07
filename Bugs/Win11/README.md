# Kilo Code CLI Setup Guide for Windows 11

This guide documents how to set up Kilo Code CLI on Windows 11, migrating from a WSL Ubuntu environment. It covers installation, configuration, IDXing setup, authentication, and common pitfalls.

---

## 1. Prerequisites

- Windows 11
- Node.js / npm installed (Kilo CLI is distributed via npm)
- Optional: WSL2 Ubuntu if migrating configs from a Linux environment
- Optional: Qdrant vector database if using Qdrant for indexing (LanceDB is embedded)

---

## 2. Install Kilo Code CLI

```powershell
npm install -g kilo
```

Verify installation:

```powershell
kilo --version
# Expected: 7.4.1 (or later)
```

The binary will be installed to (for global npm packages):

```text
C:\Program Files\nodejs\kilo
```

Make sure this directory is in your system `PATH`. If `kilo` is not recognized in a fresh CMD or PowerShell window, add `C:\Program Files\nodejs` to your user or system `PATH` environment variable.

---

## 3. Install Kimi Code CLI (optional, co-existing with Kilo)

Kimi Code CLI is a separate tool. The installer places it in:

```text
C:\Users\<YourUser>\.kimi-code\bin\kimi
```

Verify:

```powershell
kimi --version
```

Ensure `C:\Users\<YourUser>\.kimi-code\bin` is in your `PATH`.

---

## 4. Configuration Directory Layout

Kilo Code CLI reads configuration from multiple locations. On Windows it loads from (in order observed in logs):

1. `C:\Users\<YourUser>\.kilocode\`
2. `C:\Users\<YourUser>\.kilo\`

Note: It **does not** automatically prefer `~/.config/kilo/` on Windows. If you migrate from WSL, place the same files in **both** `.kilocode/` and `.kilo/` on Windows.

Expected structure:

```text
C:\Users\Jiadao
├── .kilocode
│   ├── auth.json          # API keys for providers
│   └── opencode.json      # Main configuration (model, indexing, providers, permissions)
├── .kilo
│   ├── .kiloindexignore   # Global indexing ignore patterns
│   ├── kilo.json          # Optional global defaults
│   └── opencode.json      # Mirror of .kilocode/opencode.json
├── .local
│   └── share
│       └── kilo
│           └── auth.json  # Where Kilo actually reads credentials
```

---

## 5. Migrate Configs from WSL

If you have a working setup in WSL, copy the relevant files:

```bash
# Inside WSL
mkdir -p /mnt/c/Users/<YourUser>/.kilocode
mkdir -p /mnt/c/Users/<YourUser>/.kilo
mkdir -p /mnt/c/Users/<YourUser>/.local/share/kilo

cp /home/<wsl_user>/.config/kilo/opencode.json /mnt/c/Users/<YourUser>/.kilocode/opencode.json
cp /home/<wsl_user>/.config/kilo/opencode.json /mnt/c/Users/<YourUser>/.kilo/opencode.json
cp /home/<wsl_user>/.local/share/kilo/auth.json /mnt/c/Users/<YourUser>/.local/share/kilo/auth.json

cp /home/<wsl_user>/JDgentLAB/VibeCoder_Kilo/Config/kiloindexignore /mnt/c/Users/<YourUser>/.kilo/.kiloindexignore
```

Replace `<YourUser>` and `<wsl_user>` with your actual Windows and WSL usernames.

---

## 6. Provider Authentication

Create or copy `C:\Users\<YourUser>\.local\share\kilo\auth.json`:

```json
{
  "openrouter": {
    "type": "api",
    "key": ""
  },
  "ark": {
    "type": "api",
    "key": "ark-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx-xxxxx"
  }
}
```

Verify credentials are loaded:

```powershell
kilo auth list
```

Expected output:

```text
Credentials ~\.local\share\kilo\auth.json

● OpenRouter api
● ark api

2 credentials
```

---

## 7. Main Configuration (opencode.json)

This file controls model selection, indexing, and permissions. Below is a working configuration for Volcano Ark (豆包 / Doubao) provider with Qdrant vector store.

`C:\Users\<YourUser>\.kilocode\opencode.json` and `C:\Users\<YourUser>\.kilo\opencode.json`:

```json
{
  "$schema": "https://app.kilo.ai/config.json",
  "model": "ark/ark-code-latest",
  "agent": {
    "compaction": {
      "model": "ark/doubao-seed-2.0-mini",
      "options": {
        "reasoningEffort": "minimal"
      }
    }
  },
  "indexing": {
    "enabled": true,
    "provider": "openai-compatible",
    "model": "doubao-embedding-vision",
    "dimension": 2048,
    "embeddingBatchSize": 10,
    "vectorStore": "qdrant",
    "qdrantUrl": "http://localhost:6333",
    "openai-compatible": {
      "apiKey": "ark-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx-xxxxx",
      "baseUrl": "https://ark.cn-beijing.volces.com/api/plan/v3"
    }
  },
  "watcher": {
    "ignore": [
      "Data/**",
      ".venv*",
      ".dataprep_status/**",
      "**/*.nii.gz",
      "**/*.nii",
      "__pycache__",
      ".kilo/**",
      "node_modules/**",
      "0_Logs/**",
      "2_QuickStart/**/runs/**/data_roots/**",
      "**/*.pth",
      "**/*.ckpt",
      "**/*.safetensors",
      "**/*.h5",
      "**/*.npz",
      "**/*.pkl",
      "**/*.pt",
      "**/*.bin",
      "**/*.onnx",
      "**/*.log",
      "**/*.out"
    ]
  },
  "provider": {
    "ark": {
      "name": "Volcano Ark (Exclusive API Key)",
      "npm": "@ai-sdk/openai-compatible",
      "options": {
        "apiKey": "ark-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx-xxxxx",
        "baseURL": "https://ark.cn-beijing.volces.com/api/plan/v3"
      },
      "models": {
        "ark-code-latest": { "name": "Ark(VolcanoEngine) Auto: effect+speed" },
        "doubao-seed-2.0-code": { "name": "Doubao Seed 2.0 Code" },
        "doubao-seed-2.0-pro": { "name": "Doubao Seed 2.0 Pro" },
        "doubao-seed-2.0-lite": { "name": "Doubao Seed 2.0 Lite" },
        "doubao-seed-2.0-mini": { "name": "Doubao Seed 2.0 Mini" },
        "doubao-seed-code": { "name": "Doubao Seed Code" },
        "doubao-seed-evolving": { "name": "Doubao Seed Evolving (Coding & Agent, weekly upgrade)" },
        "minimax-latest": { "name": "MiniMax M2.7" },
        "glm-5.2": { "name": "GLM 5.2" },
        "deepseek-v4-pro": { "name": "DeepSeek V4 Pro" },
        "deepseek-v4-flash": { "name": "DeepSeek V4 Flash" },
        "kimi-k2.6": { "name": "Kimi K2.6" },
        "doubao-seedance-2.0": { "name": "Doubao Seedance 2.0 (Vision)" },
        "doubao-seedance-2.0-fast": { "name": "Doubao Seedance 2.0 Fast (Vision)" },
        "doubao-seedance-1.5-pro": { "name": "Doubao Seedance 1.5 Pro (Vision)" },
        "doubao-seedream-5.0-lite": { "name": "Doubao Seedream 5.0 Lite (Vision)" }
      }
    }
  },
  "permission": {
    "bash": "allow",
    "*": { "*": "allow" }
  }
}
```

**Critical details:**

- The **embedding model's `baseUrl` must be `https://ark.cn-beijing.volces.com/api/plan/v3`** (note the `/plan` path). Using `/api/v3` will cause an `Authentication failed` error during indexing.
- The **chat/completion provider's `baseURL`** (inside `provider.ark.options`) uses the same `/plan/v3` endpoint.
- `embeddingBatchSize: 10` is recommended for Ark embedding endpoints.

---

## 8. Project-Level IDXing Configuration

In each project you want to index, create `.kilo/kilo.json`:

```json
{
  "$schema": "https://app.kilo.ai/config.json",
  "indexing": {
    "enabled": true
  }
}
```

Example for this repo:

```text
C:\Users\Jiadao\OneDrive\2_ProjBackup\JDgent\VibeCoder_Kilo
├── .kilo
│   └── kilo.json
├── Config
│   ├── auth.json
│   ├── kiloindexignore
│   └── opencode.json
└── README.md
```

---

## 9. Global Indexing Ignore Patterns

Create `C:\Users\<YourUser>\.kilo\.kiloindexignore` to exclude large/binary files from indexing. Example:

```text
# === Common data / output directories ===
Data/
data/
data_roots/
datasets/
checkpoints/
weights/
runs/
logs/

# === Medical / neuroimaging ===
*.nii
*.nii.gz
*.mgz
*.mgh
*.mgh.gz
*.dcm
*.dicom
*.vtk
*.vti
*.trk
*.tck

# === Model weights / serialized tensors ===
*.pth
*.pt
*.ckpt
*.safetensors
*.bin
*.onnx
*.h5
*.hdf5
*.npy
*.npz
*.pkl
*.pickle
*.joblib

# === Python data formats ===
*.feather
*.orc
*.parquet
*.csv
*.tsv
*.jsonl
*.db
*.sqlite
*.sqlite3
*.zarr
*.tfrecord

# === Binary media / archives / documents ===
*.png
*.jpg
*.jpeg
*.gif
*.bmp
*.webp
*.pdf
*.zip
*.tar
*.gz
*.rar
*.7z

# === Tool caches / environments ===
node_modules/
__pycache__/
.venv*/
.venv.*/
.cache/
*.egg-info/
```

---

## 10. Qdrant Vector Store Setup

If you use `vectorStore: "qdrant"`, Qdrant must be running locally.

### Option A: Docker

```powershell
docker run -p 6333:6333 -v "${PWD}/qdrant_storage:/qdrant/storage" qdrant/qdrant
```

### Option B: Download Windows binary

1. Download the Qdrant Windows binary from the [Qdrant releases page](https://github.com/qdrant/qdrant/releases).
2. Extract and run `qdrant.exe`.

Verify Qdrant is running:

```powershell
curl http://localhost:6333
```

Expected response:

```json
{"title":"qdrant - vector search engine","version":"1.13.4",...}
```

### Option B: Use LanceDB instead

If you do not want to run Qdrant, change `opencode.json`:

```json
"indexing": {
  "enabled": true,
  "provider": "openai-compatible",
  "model": "doubao-embedding-vision",
  "dimension": 2048,
  "vectorStore": "lancedb",
  "openai-compatible": {
    "apiKey": "ark-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx-xxxxx",
    "baseUrl": "https://ark.cn-beijing.volces.com/api/plan/v3"
  }
}
```

LanceDB is embedded and requires no external service, but performance and behavior may differ from Qdrant.

---

## 11. Verify the Setup

Run these commands in CMD or PowerShell:

```powershell
kilo --version
kilo auth list
kilo config check
kilo models ark
```

Expected:

- Version prints.
- Both OpenRouter and Ark credentials appear.
- `No config warnings.`
- Ark models are listed, including `ark/ark-code-latest`.

Then test in a project directory:

```powershell
cd C:\Users\Jiadao\OneDrive\2_ProjBackup\JDgent\VibeCoder_Kilo
kilo
```

If indexing succeeds, the TUI will open without an authentication error.

---

## 12. Troubleshooting

### 12.1 `Authentication failed. Please check your API key.` during indexing

Likely causes:

1. Wrong `baseUrl` in `indexing.openai-compatible.baseUrl`. Must end with `/api/plan/v3` for Ark.
2. Wrong config directory. Kilo on Windows loads `~/.kilocode/opencode.json` and `~/.kilo/opencode.json`. Make sure both files have the correct values.
3. The `apiKey` is missing or wrong.

Debug:

```powershell
kilo config check
Get-Content ~\.kilocode\opencode.json | Select-String "baseUrl"
```

### 12.2 Kilo cannot find credentials

Ensure `auth.json` is at:

```text
C:\Users\<YourUser>\.local\share\kilo\auth.json
```

Not only in `~/.kilocode/` or `~/.config/kilo/`.

### 12.3 Model not available

Check that the model exists:

```powershell
kilo models ark
```

If your custom model is missing, add it under `provider.ark.models` in `opencode.json`.

### 12.4 Different behavior in Git Bash vs CMD

Git Bash may translate paths differently. For debugging, always test directly in CMD or PowerShell. Kilo's logs are located at:

```text
C:\Users\<YourUser>\.local\share\kilo\log\
```

Read the most recent `.log` file to see which config paths were loaded and any errors.

### 12.5 `.kilocode/` vs `.config/kilo/` confusion

On WSL, Kilo may use `~/.config/kilo/opencode.json`. On Windows, it uses `~/.kilocode/opencode.json` and `~/.kilo/opencode.json`. Keep all three in sync if you switch between platforms, or maintain one source of truth and copy after changes.

### 12.6 Crash on startup: `panic(main thread): Segmentation fault at address ...` (Bun v1.3.14)

**Symptom:**
Running `kilo` immediately crashes with a Bun stack trace similar to:

```text
============================================================
Bun v1.3.14 (0d9b296a) Windows x64 (baseline)
Windows v.win11_dt
CPU: sse42 avx avx2
Args: "C:\Users\Jiadao\AppData\Roaming\nvm\v20.18.3\node_modules\@kilocode\cli\node_modules\@kilocode\cli-windows-x64\bin\kilo.exe"
Elapsed: 5ms | User: 15ms | Sys: 0ms
RSS: 8.35MB | Peak: 8.35MB | Commit: 15.73MB | Faults: 2183

panic(main thread): Segmentation fault at address 0x7FF68B7CEB49
oh no: Bun has crashed. This indicates a bug in Bun, not your code.
```

**Root cause:**
Kilo CLI ships two Windows x64 binaries inside `@kilocode/cli`:

- `@kilocode/cli-windows-x64` — AVX2-optimized build (selected automatically on modern CPUs).
- `@kilocode/cli-windows-x64-baseline` — baseline build without AVX2-specific code.

On affected systems (observed with `@kilocode/cli` **7.4.3** and the bundled Bun **v1.3.14**), the AVX2-optimized `cli-windows-x64\bin\kilo.exe` crashes with a segmentation fault during process startup. The baseline binary starts normally. This is a Bun runtime/compilation issue in the optimized Windows build, not a configuration problem on the user side.

**Immediate workaround — force the baseline binary:**

Set the `KILO_BIN_PATH` environment variable to point at the baseline executable. The Kilo wrapper honors this variable and bypasses CPU-feature detection.

PowerShell (persistent, user-level):

```powershell
[Environment]::SetEnvironmentVariable(
  "KILO_BIN_PATH",
  "C:\Users\$env:USERNAME\AppData\Roaming\nvm\v20.18.3\node_modules\@kilocode\cli\node_modules\@kilocode\cli-windows-x64-baseline\bin\kilo.exe",
  "User"
)
```

If you installed Node/Kilo through a different path, locate your baseline binary with:

```powershell
Get-ChildItem -Path "$env:APPDATA\nvm" -Recurse -Filter "cli-windows-x64-baseline" -Directory |
  ForEach-Object { Join-Path $_.FullName "bin\kilo.exe" }
```

Then verify in a **new** terminal:

```powershell
kilo --version
# Expected: 7.4.3 (or your installed version)
```

**One-off verification (no persistence):**

```powershell
$env:KILO_BIN_PATH = "C:\Users\$env:USERNAME\AppData\Roaming\nvm\v20.18.3\node_modules\@kilocode\cli\node_modules\@kilocode\cli-windows-x64-baseline\bin\kilo.exe"
kilo --version
```

**Longer-term fixes:**

1. **Upgrade Kilo CLI** once a patched release is available:

   ```powershell
   npm install -g @kilocode/cli@latest
   ```

   After upgrading, remove the `KILO_BIN_PATH` override and test `kilo --version`. If the optimized binary still crashes, re-apply the workaround.

2. **Downgrade** to the last known-good version (e.g., 7.4.1) if the baseline workaround is not acceptable:

   ```powershell
   npm install -g @kilocode/cli@7.4.1
   ```

**References:**

- Bun issue discussing similar OpenCode/Kilo Bun v1.3.14 segfaults on Windows 11: [oven-sh/bun#32691](https://github.com/oven-sh/bun/issues/32691)
- Kilo CLI Windows binary selection logic: `@kilocode/cli/bin/kilo` (selects `cli-windows-x64` when AVX2 is detected).

---

## 13. Shell Integration (Optional)

Both `kilo` and `kimi` are already usable from CMD and PowerShell once their directories are in `PATH`.

For convenience, you can add PowerShell aliases by editing your profile:

```powershell
notepad $PROFILE
```

Add:

```powershell
# Aliases
Set-Alias -Name k -Value kilo
Set-Alias -Name km -Value kimi
```

For tab completion, Kilo ships with:

```powershell
kilo completion >> $PROFILE
```

Reload the profile:

```powershell
. $PROFILE
```

---

## 14. Summary of Critical Paths

| Purpose | Windows Path |
|---------|--------------|
| Kilo binary | `C:\Program Files\nodejs\kilo` |
| Kimi binary | `C:\Users\<YourUser>\.kimi-code\bin\kimi` |
| Main config | `C:\Users\<YourUser>\.kilocode\opencode.json` |
| Mirror config | `C:\Users\<YourUser>\.kilo\opencode.json` |
| Credentials | `C:\Users\<YourUser>\.local\share\kilo\auth.json` |
| Global ignores | `C:\Users\<YourUser>\.kilo\.kiloindexignore` |
| Project IDX | `<Project>\.kilo\kilo.json` |
| Logs | `C:\Users\<YourUser>\.local\share\kilo\log\` |
| Project root (this guide) | `C:\Users\Jiadao\OneDrive\2_ProjBackup\JDgent\VibeCoder_Kilo` |

---

## 15. References

- Kilo Code CLI docs: https://kilo.ai/docs/code-with-ai/platforms/cli
- Ark / Volcano Engine: https://www.volcengine.com/
- Qdrant: https://qdrant.tech/
- LanceDB: https://lancedb.github.io/lancedb/
