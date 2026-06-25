# Kilo Code

> **Fixed binary installed** — if you see a Qdrant compatibility warning, see [`Bugs/IDX/a_Solution.md`](../Bugs/IDX/a_Solution.md) for the patch details.

## Set Up Kilo Code CLI
> Refer https://kilo.ai/docs/code-with-ai/platforms/cli
```bash
npm install -g @kilocode/cli
```

## Set Up LM Providers

#### OpenRouter
- That is easy, just `kilo` and then `/connect`, and then choose `OpenRouter` and select the default model you'd like to use as favourite.

#### Ark (Volcano Engine — Exclusive API Key Plan)
> Refer https://www.volcengine.com/docs/82379/1928261?lang=zh
- Create *~/.config/kilo/opencode.json* with the Ark (Volcano Engine) setup.
    - Provider ID: ark
    - Base URL: `https://ark.cn-beijing.volces.com/api/plan/v3` (OpenAI-compatible endpoint for the Exclusive API Key plan)
    - API Key: pulled from your existing *~/.local/share/kilo/auth.json*, which is set by Kilo's `connect` commands.
    - Models: all supported models from the doc:
        - **Language**: `ark-code-latest`, `doubao-seed-2.0-code/pro/lite`, `doubao-seed-code`, `doubao-seed-evolving` (Coding & Agent, weekly upgrade), `minimax-latest`, `glm-5.1`, `glm-4.7`, `deepseek-v4-pro`, `deepseek-v4-flash`, `kimi-k2.6`
        - **Vision**: `doubao-seedance-2.0`, `doubao-seedance-2.0-fast`, `doubao-seedance-1.5-pro`, `doubao-seedream-5.0-lite`
    - **Default model is set to `ark/ark-code-latest`.** You can change the `"model"` field at the top level to any other model ID (e.g., `"ark/doubao-seedance-2.0"`).
- Next steps:
    1. Restart Kilo (`kilo` or `kilocode`).
    2. Run `/models` in the TUI to switch models if needed.
    3. If you ever want to rotate the key without editing this file, replace `"apiKey": ""` with `"apiKey": "{env:ARK_API_KEY}"` and set the environment variable instead.

---

## Optional: Vector Search MCP (Memory Embedding)

To mitigate context-window exhaustion, you can enable a **local vector-search MCP server** that indexes your codebase and retrieves only the most relevant snippets before each query.

### Prerequisites

Make sure you have Node.js ≥ 18 and npm installed, then install the MCP server globally:

```bash
npm install -g @modelcontextprotocol/server-vector-search
```

### Configuration

For Kilo's built-in code indexing with Volcano Ark embeddings, add an `indexing` block to `opencode.json`:

```json
{
  "indexing": {
    "enabled": true,
    "provider": "openai-compatible",
    "model": "doubao-embedding-vision",
    "dimension": 2048,
    "vectorStore": "lancedb",
    "openai-compatible": {
      "apiKey": "{env:ARK_API_KEY}",
      "baseUrl": "https://ark.cn-beijing.volces.com/api/plan/v3"
    }
  }
}
```

Use `/api/plan/v3` for embeddings when using a Coding Plan exclusive API key. A standard Ark API key may use `/api/v3`, but the configured exclusive key returns 401 there.

### Avoid Indexing Generated Data

If your workspace contains large experimental outputs (e.g. FreeSurfer `data_roots`, training logs, model checkpoints), exclude them from indexing. Otherwise the indexer will waste time and API quota on thousands of small data JSON files and appear stuck at a low percentage.

> **Important:** Kilo uses **two separate** ignore mechanisms:
>
> | Mechanism | What it controls | Where to put it |
> |---|---|---|
> | `watcher.ignore` in Kilo config | The `@parcel/watcher` file watcher (CPU/filesystem events) | `~/.config/kilo/opencode.json` or `.kilo/kilo.json` |
> | `.kilocodeignore` / `.gitignore` | The IDX scanner (what gets embedded) | Workspace root (`<project>/.kilocodeignore`) |
> | `~/.kilocode/.kiloindexignore` | IDX-only exclusions, machine-wide | `~/.kilocode/.kiloindexignore` |
>
> `watcher.ignore` does **not** prevent files from being embedded. To stop IDX from indexing data/model files, add them to `.kilocodeignore` (project-level) or `~/.kilocode/.kiloindexignore` (global).

#### Project-level `.kilocodeignore` (recommended)

Create or edit `<your-project>/.kilocodeignore`. Example for a neuroimaging / ML project:

```text
# === Dependency / package / tool caches ===
node_modules/
.pnpm/
.yarn/
.venv*/
__pycache__/
.mypy_cache/
.pytest_cache/
.ruff_cache/
.egg-info/
dist/
build/
.next/
.nuxt/
.vite/
.turbo/
.cache/
.parcel-cache/

# === Editor / agent metadata ===
.kilo/
.kilocode/
.kiloindex/
.vscode/
.idea/
.zed/

# === Logs and runtime outputs ===
0_Logs/
logs/
*.log

# === Data / prep / output directories (prune early during traversal) ===
# Directory patterns are much cheaper than file patterns: they stop the
# scanner/file-watcher from descending into generated data trees at all.
Data/
x_Report/
*/2_DataPrep/
*/1_DataSync/
*/runs/
*/models/
2_QuickStart/**/runs/
2_QuickStart/**/data_roots/

# === Generated data / model / binary artifacts ===
data_roots/
datasets/
checkpoints/
weights/

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
*.parquet
*.csv
*.tsv
*.nii
*.nii.gz

*.png
*.jpg
*.jpeg
*.gif
*.bmp
*.webp
*.ico
*.pdf
*.zip
*.tar
*.gz
*.rar
*.7z
```

This keeps **code scripts, text documents, and project config files** in the index while skipping data/model binaries.

> **Note for large data directories:** File-level patterns like `*.nii.gz` still force the indexer to enumerate every file inside a data tree before filtering it out. If a directory contains thousands of generated files, ignore the whole directory (e.g. `Data/`, `*/2_DataPrep/`, `2_QuickStart/**/runs/`). The patched Kilo binary also passes these patterns into `glob()` so directory pruning happens during traversal, not after.

#### Optional: also reduce watcher load

Add a `watcher.ignore` block to your Kilo config so the file watcher does not watch the same directories:

```json
{
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
  }
}
```

After editing the ignore files, **clear the old index and restart Kilo**:

```bash
rm -rf ~/.local/state/kilo/indexing
kilo
```

### Usage

1. **Restart Kilo** so the MCP server is loaded:
   ```bash
   kilo
   ```

2. **Verify the connection**:
   ```
   > /mcp list
   ```
   You should see `vector-search` listed.

3. **Index your project** (run inside the repo you want to query):
   ```
   > /mcp call vector-search index --path .
   ```

4. **Ask questions naturally**. Kilo will automatically retrieve relevant code chunks from the vector index and inject them into the context:
   ```
   > Explain the user authentication flow in this project
   ```

---

## Avoid Over-Indexing (Built-in `/indexing`)

If you use Kilo's built-in `/indexing` feature (separate from the MCP server above), keep large/binary/dependency directories out of the index with a machine-wide ignore file:

- **`~/.kilocode/.kiloindexignore`** — indexing-only exclusions. IDX skips these paths, but the agent can still read or edit them when explicitly asked.
- **`~/.kilocode/.kilocodeignore`** — access-control exclusions. IDX skips these paths **and** the agent's tools are denied access unless you add a negation rule.

Example `~/.kilocode/.kiloindexignore`:

```text
Data/
.venv*
.venv.*/
.dataprep_status/
*.nii.gz
*.nii
__pycache__/
```

See [`README.md`](../README.md) for the full explanation and the source patch that makes the global indexing ignore work.
