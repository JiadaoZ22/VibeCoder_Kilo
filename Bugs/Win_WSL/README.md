# Win + WSL Kilo Setup Notes

Environment: WSL2 (Ubuntu 24.04) on Windows, projects moved from `C:\Users\Jiadao\OneDrive\2_ProjBackup` to `/home/jiadao/` for WSL-native I/O performance.

---

## 1. Move Projects to WSL Filesystem

Per Microsoft guidance, cross-OS file access is slow. Projects were copied/cloned to WSL native paths:

```text
/home/jiadao/Zoujd_IMI
/home/jiadao/JDgentLAB
```

Access from Windows Explorer via:

```text
\\wsl$\Ubuntu\home\jiadao
```

---

## 2. Build Kilo from Source in WSL

### 2.1 Install Bun

`unzip` was missing, so Bun was installed manually:

```bash
mkdir -p ~/.bun/bin /tmp/bun-install
cd /tmp/bun-install
curl -fsSL -o bun.zip "https://bun.sh/download/latest/linux/x64"
python3 -c "import zipfile; zipfile.ZipFile('bun.zip').extractall('.')"
cp /tmp/bun-install/bun-linux-x64-baseline/bun ~/.bun/bin/bun
chmod +x ~/.bun/bin/bun
export PATH="$HOME/.bun/bin:$PATH"
bun --version   # 1.3.14
```

### 2.2 Clone `JDgentLAB` and Initialize Submodules

```bash
git clone https://github.com/JiadaoZ22/JDgentLAB.git /home/jiadao/JDgentLAB
cd /home/jiadao/JDgentLAB
```

`VibeCoder_Kilo/kilo-source` submodule pointed to a deleted commit (`eea5267...`). Workaround: clone the branch tip manually.

```bash
cd /home/jiadao/JDgentLAB/VibeCoder_Kilo
rm -rf kilo-source
git clone --branch fix/qdrant-check-compatibility --single-branch \
  https://github.com/JiadaoZ22/kilocode.git kilo-source
```

### 2.3 Install Dependencies

Native module postinstall scripts fail because `build-essential` cannot be installed (Ubuntu repo timeouts). Use `--ignore-scripts`:

```bash
cd /home/jiadao/JDgentLAB/VibeCoder_Kilo/kilo-source
export PATH="$HOME/.bun/bin:$PATH"
bun install --ignore-scripts
```

One package (`@opentui/solid`) was missing and had to be added manually:

```bash
bun add @opentui/solid@0.2.10 --ignore-scripts
```

### 2.4 Install `patchelf` and Rebuild

The first build skipped `patchelf`, causing the runtime binary to crash with **Bus error (core dumped)** when LanceDB/indexing initialized.

Download static `patchelf`:

```bash
mkdir -p /tmp/patchelf && cd /tmp/patchelf
curl -fsSL -o patchelf.tar.gz \
  "https://github.com/NixOS/patchelf/releases/download/0.18.0/patchelf-0.18.0-x86_64.tar.gz"
tar -xzf patchelf.tar.gz
sudo cp /tmp/patchelf/bin/patchelf /usr/local/bin/patchelf
patchelf --version   # 0.18.0
```

Rebuild Kilo:

```bash
cd /home/jiadao/JDgentLAB/VibeCoder_Kilo/kilo-source
export PATH="$HOME/.bun/bin:$PATH"
bun run --cwd packages/opencode script/build.ts --single --skip-install
```

Verify the build log includes:

```text
patched interpreter for @kilocode/cli-linux-x64 -> /lib64/ld-linux-x86-64.so.2
```

### 2.5 Install the Binary

Use atomic `mv` to avoid `Text file busy`:

```bash
cp packages/opencode/dist/@kilocode/cli-linux-x64/bin/kilo /tmp/kilo.new
chmod +x /tmp/kilo.new
mv -f /tmp/kilo.new ~/.local/bin/kilo
kilo --version
```

Expected output:

```text
0.0.0-fix-qdrant-check-compatibility-202607081323
```

---

## 3. Kilo Configuration

### 3.1 Copy Config Files

```bash
mkdir -p ~/.config/kilo ~/.local/share/kilo
cp /home/jiadao/JDgentLAB/VibeCoder_Kilo/Config/opencode.json ~/.config/kilo/opencode.json
cp /home/jiadao/JDgentLAB/VibeCoder_Kilo/Config/auth.json    ~/.local/share/kilo/auth.json
```

### 3.2 Fill API Keys

Edit `~/.local/share/kilo/auth.json`:

```json
{
  "openrouter": { "type": "api", "key": "" },
  "ark":        { "type": "api", "key": "your-ark-key" }
}
```

Edit `~/.config/kilo/opencode.json`:

- `indexing.openai-compatible.apiKey`
- `provider.ark.options.apiKey`

### 3.3 Important: Use `/api/plan/v3` for Ark Coding Plan Key

For the exclusive Coding Plan API key, the indexing endpoint must be:

```json
"baseUrl": "https://ark.cn-beijing.volces.com/api/plan/v3"
```

Using `/api/v3` returns **401 Authentication failed**.

Also confirm:

```json
"model": "doubao-embedding-vision",
"dimension": 2048,
"vectorStore": "lancedb"
```

### 3.4 Corrupted Config File Fix

If `~/.config/kilo/opencode.json` accidentally has the source path prepended to line 1, e.g.:

```text
/home/jiadao/JDgentLAB/VibeCoder_Kilo/Config/opencode.json{
  ...
}
```

remove the stray path prefix so the file starts with `{`.

---

## 4. Clear Stale Index After Config Changes

```bash
rm -rf ~/.local/share/kilo/indexing
```

Then start Kilo and run `/indexing` in the TUI.

---

## 5. Avoid Over-Indexing Large/Binary Directories

Create `~/.kilocode/.kiloindexignore` for global indexing-only exclusions:

```text
Data/
*.nii.gz
*.nii
.venv*
.venv.*/
.dataprep_status/
__pycache__/
```

This keeps IDX from scanning huge files while still allowing the agent to read them on request.

---

## 6. Verified Test Directory

Kilo starts and indexing initializes without crash in:

```text
/home/jiadao/Zoujd_IMI/f1_Code/Brain/FreeSurfer/Substitute_aparc+aseg/2_Code/E2E_DK_Parcellation
```

Stability test (with proper pseudo-terminal):

```bash
cd /home/jiadao/Zoujd_IMI/f1_Code/Brain/FreeSurfer/Substitute_aparc+aseg/2_Code/E2E_DK_Parcellation
timeout 120 script -q -c "kilo" /dev/null
```

Result: ran 2 minutes without crash; only killed by `timeout`.

Latest verified version:

```text
7.4.1 (npm @kilocode/cli) — see Section 12 for the current install method.
```

> Historical: the source-built version `0.0.0-fix-qdrant-check-compatibility-202607081323` was verified stable for TUI launch but is no longer the recommended install method.

---

## 7. Indexing Embedder Patches Applied

The checked-out `fix/qdrant-check-compatibility` branch (commit `f8b5c1c9`) only included the dimension fix. It was missing the later robustness patches described in `Bugs/Indexing/a_Solution.md`. The following source patches were applied manually:

| Patch | File |
|---|---|
| 120-second request timeout on OpenAI-compatible embedding calls | `packages/kilo-indexing/src/indexing/embedders/openai-compatible.ts` |
| Cap embedding batch to 10 inputs (Doubao/Ark limit) | `packages/kilo-indexing/src/indexing/embedders/openai-compatible.ts` |
| Added constants `REMOTE_EMBEDDER_REQUEST_TIMEOUT_MS` and `OPENAI_COMPATIBLE_MAX_BATCH_INPUTS` | `packages/kilo-indexing/src/indexing/constants/index.ts` |

---

## 8. Current Status: TUI Opens, Indexing Worker Still Crashes

> **Update:** This crash was resolved by the fix documented in [Section 11](#11-fix-applied-apt-proxy--build-toolchain--full-source-rebuild). The historical diagnosis is preserved below for context.

After all patches, Kilo's main process opens and the TUI is stable. However, the **indexing worker still crashes with SIGBUS** in the background (visible in `dmesg`):

```text
WSL (9753 - CaptureCrash): Capturing crash for pid: 9001, executable: !home!jiadao!.local!bin!kilo, signal: 7, port: 50005
```

This means:

- Kilo CLI launches and is usable for chat/commands.
- Code indexing (`/indexing`) initializes but never progresses because the worker dies.
- The root cause is an incompatible prebuilt native module (most likely LanceDB) that cannot be recompiled because `build-essential` is unavailable.

---

## 9. Terminal / TTY Requirement

Kilo is a TUI application. Running it **without a real terminal** (e.g., piping `/dev/null` to stdin) can cause it to dump core after a short time:

```text
timeout: the monitored command dumped core
```

This is an artifact of the test harness, not a Kilo bug. For non-interactive verification, use `script` to provide a pseudo-terminal:

```bash
timeout 120 script -q -c "kilo" /dev/null
```

In normal interactive use inside Windows Terminal, VS Code terminal, or any Linux terminal emulator, Kilo runs stably.

---

## 10. Known Limitations and Next Steps

- `build-essential` / `make` / `gcc` are not installed because Ubuntu package repos time out in this network.
- Native dependencies run with prebuilt `.node` binaries and `--ignore-scripts`.
- `patchelf` is installed manually so the bundled binary gets the correct ELF interpreter.
- **Code indexing does not progress** because the indexing worker crashes with SIGBUS due to an incompatible prebuilt LanceDB/native module.

To fully fix indexing, one of the following is needed:

1. **Install `build-essential` and recompile native modules from source.** Blocked here because `apt` cannot reach Ubuntu repos.
2. **Build Kilo in an environment with working compilers** (another WSL instance, a Linux VM, or CI) and copy the resulting binary back.
3. **Use Kilo without indexing** — chat and tool use still work; you just won't have semantic code search.

To disable indexing globally, set in `~/.config/kilo/opencode.json`:

```json
{
  "indexing": {
    "enabled": false
  }
}
```

---

## 11. Fix Applied: APT Proxy + Build Toolchain + Full Source Rebuild

**Date:** 2026-07-08

**Status:** ❌ Failed / Superseded by [Section 12](#12-ultimate-solution-official-npm-release--embeddingbatchsize-config). The source build eliminated the SIGBUS crash, but the resulting binary still sent embedding batches of 60 inputs against the Ark/Doubao 10-input limit, causing `Embedding API input limit exceeded: max 10, got 60`. It also required maintaining local source patches that are lost on reinstall.

### Root Cause of the APT Blocker

`apt` could not download Ubuntu repository metadata because the WSL network uses a transparent proxy/DNS interception that breaks apt's native HTTP method when it tries to connect "directly". `curl`/`wget` worked, but apt hung at `Waiting for headers` or reported `Connection failed`.

### Fix Steps

1. **Configured apt to use the local HTTP proxy explicitly.**

   The local proxy is already running on `127.0.0.1:7897` (Clash/V2Ray). Pointing apt at it directly restores reliable package downloads:

   ```bash
   echo '123456' | sudo -S bash -c 'cat > /etc/apt/apt.conf.d/80proxy <<"EOF"
   Acquire::http::Proxy "http://127.0.0.1:7897";
   Acquire::https::Proxy "http://127.0.0.1:7897";
   EOF'
   ```

2. **Installed the build toolchain.**

   ```bash
   echo '123456' | sudo -S bash -c 'apt-get update && apt-get install -y build-essential gcc g++ make unzip python3 python3-pip pkg-config libssl-dev libc6-dev linux-libc-dev'
   ```

   Verified:

   ```text
   gcc (Ubuntu 13.3.0-6ubuntu2~24.04) 13.3.0
   g++ (Ubuntu 13.3.0-6ubuntu2~24.04) 13.3.0
   GNU Make 4.3
   ```

3. **Reinstalled Kilo dependencies with native postinstall scripts enabled.**

   Previously `bun install --ignore-scripts` skipped native module compilation. With compilers available, dependencies were reinstalled normally:

   ```bash
   cd /home/jiadao/JDgentLAB/VibeCoder_Kilo/kilo-source
   export PATH="$HOME/.bun/bin:$PATH"
   rm -rf node_modules packages/*/node_modules
   bun install
   ```

4. **Rebuilt the Kilo CLI binary from source.**

   ```bash
   cd /home/jiadao/JDgentLAB/VibeCoder_Kilo/kilo-source
   export PATH="$HOME/.bun/bin:$PATH"
   bun run --cwd packages/opencode script/build.ts --single --skip-install
   ```

   Build output:

   ```text
   patched interpreter for @kilocode/cli-linux-x64 -> /lib64/ld-linux-x86-64.so.2
   Smoke test passed: 0.0.0-fix-qdrant-check-compatibility-202607081323
   Models snapshot smoke test passed
   ```

5. **Installed the rebuilt binary atomically.**

   ```bash
   cp packages/opencode/dist/@kilocode/cli-linux-x64/bin/kilo /tmp/kilo.new
   chmod +x /tmp/kilo.new
   mv -f /tmp/kilo.new ~/.local/bin/kilo
   kilo --version
   # 0.0.0-fix-qdrant-check-compatibility-202607081323
   ```

### Verification

- **CLI stability:** `kilo` starts in the test directory and runs for minutes without `Bus error (core dumped)`.
- **Indexing initialization:** Log shows `project indexing initialized` and `state=In Progress` without worker crash.
- **End-to-end indexing engine test:** A direct `CodeIndexManager` scan of the test directory discovered 1025 files (259 candidates), created a LanceDB vector store, and indexed files successfully:

  ```text
  [telemetry] {"discovered":1025,"candidate":259,"type":"file_count","source":"scan","mode":"full"}
  [progress] {"systemStatus":"Indexing","message":"Indexed 4 / 84 files (5%).",...}
  ```

  LanceDB files were written to `~/.local/share/kilo/indexing-test/lancedb/...`.

- **No SIGBUS in `dmesg`:** The previous `signal: 7` crash no longer occurs during indexing initialization.

### Notes

- Indexing progress is intentionally slow with the Ark/Doubao embedding provider because it enforces a 10-input-per-request limit. The scanner still discovers files quickly; the bottleneck is remote embedding latency, not a local crash.
- If the local proxy (`127.0.0.1:7897`) is not running, apt will fail again. Keep `/etc/apt/apt.conf.d/80proxy` in place as long as that proxy is the normal network path.

---

## 12. Ultimate Solution: Official npm Release + `embeddingBatchSize` Config

**Date:** 2026-07-08

**Status:** ✅ Current / Working

The source-build approach in [Section 11](#11-fix-applied-apt-proxy--build-toolchain--full-source-rebuild) fixed the SIGBUS crash but was fragile: it relied on local source patches that are lost on reinstall, and the rebuilt binary still defaulted to batch size 60, causing:

```text
Embedding request failed after 3 attempts with status 400: 400 The parameter `input` specified in the request are not valid: Embeddings API input limit exceeded: max 10, got 60.
```

The robust, reproducible fix is to use the published npm package and configure the embedding batch size in JSON.

### Steps

1. **Remove the old source-built binary.**

   ```bash
   rm -f ~/.local/bin/kilo
   ```

2. **Install the official Kilo Code CLI from npm.**

   Official command (requires sudo if npm prefix is `/usr/local`):

   ```bash
   npm install -g @kilocode/cli
   ```

   If you cannot use sudo and your user prefix is already on `PATH`, install locally under `~/.local`:

   ```bash
   npm install -g @kilocode/cli --prefix ~/.local
   ```

3. **Keep your existing config** in `~/.config/kilo/opencode.json` (or `kilo.jsonc`). Add `embeddingBatchSize: 10` under the `indexing` block:

   ```json
   {
     "indexing": {
       "enabled": true,
       "provider": "openai-compatible",
       "model": "doubao-embedding-vision",
       "dimension": 2048,
       "embeddingBatchSize": 10,
       "vectorStore": "qdrant",
       "qdrantUrl": "http://localhost:6333",
       "openai-compatible": {
         "apiKey": "ark-...",
         "baseUrl": "https://ark.cn-beijing.volces.com/api/plan/v3"
       }
     }
   }
   ```

4. **Clear the stale index and restart Kilo.**

   ```bash
   rm -rf ~/.local/share/kilo/indexing
   kilo
   ```

   Then run `/indexing` in the TUI.

### Verification

- `kilo --version` returns the published npm version (e.g., `7.4.1`), not a source branch name like `0.0.0-fix-qdrant-check-compatibility-...`.
- Indexing initializes and progresses without `Embedding API input limit exceeded`.
- No SIGBUS / `signal: 7` crash appears in `dmesg`.

### Why This Replaces Section 11

- **Reproducible:** `npm install -g @kilocode/cli` pulls a published artifact instead of a one-off source build.
- **No source patches needed:** `embeddingBatchSize` is a supported config option; it survives updates and does not require maintaining a fork.
- **APT proxy / build toolchain still useful:** Keep the environment from Section 11 if you need native modules for other projects, but do not rely on the source-built Kilo binary as the final install method.
