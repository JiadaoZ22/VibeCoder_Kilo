# Kilo Code

> **Fixed binary installed** — if you see a Qdrant compatibility warning, see [`Bugs/Indexing/a_Solution.md`](../Bugs/Indexing/a_Solution.md) for the patch details.

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

## Web Search MCP (Doubao Search)

Doubao Search (豆包搜索, ex 联网搜索) has two versions — [version comparison](https://docs.volcengine.com/docs/87772/2272949?lang=en): **Global** (global sites, per-result `ContentTokenCount`, pay-as-you-go only) and **Custom** (lower latency, fuller body text, subscription plans). 500 free searches/month shared across both.

Two MCP entries exist in `~/.config/kilo/opencode.json`:

| MCP name | Server | Version | Key |
|---|---|---|---|
| `doubao-search` | `huashu-doubao-search` (local clone at `~/.local/share/kilo/mcp/huashu-doubao-search`) | **Global** by default (`DOUBAO_SEARCH_VERSION=global`); pass `version: "custom"` per call to switch | `DOUBAO_SEARCH_API_KEY` — dedicated key from the 豆包搜索 console |
| `doubao-search-custom` | Volcengine `mcp_server_askecho_search_infinity` via `uvx` | Custom版 (`web_search` endpoint) | Ark exclusive-plan key — verified working 2026-08-20 |

**Key facts verified by direct API calls (2026-08-20):**

- The Ark exclusive-plan key **works** on the Custom版 endpoint `https://open.feedcoopapi.com/search_api/web_search` (returned real results).
- The same Ark key is **rejected** on the Global版 endpoint `.../global_search` with `700901 invalid_api_key`. Global版 requires a dedicated key created in the 豆包搜索 (联网搜索) console → API Key管理 → 按量后付费 ([Global版 API doc](https://www.volcengine.com/docs/87772/2548026)).
- If the console shows 0 token consumption, no successful search ever ran — the uvx server was failing to start (PyPI blocked; fixed via `~/.config/uv/uv.toml` TUNA mirror) and the Global key was never created.

**One manual step:** paste the console API key into `mcp.doubao-search.environment.DOUBAO_SEARCH_API_KEY` in `opencode.json`, then restart Kilo. Until then the `doubao_search` tool answers `invalid api key`; `doubao-search-custom` keeps working meanwhile.

The `doubao-search` entry also sets `ARK_API_KEY`/`ARK_BASE_URL`/`ARK_MODEL`, enabling the server's optional AI layer (`max_tokens` context compression, `doubao_cross_check` multi-source verification) on the Ark plan endpoint — failures there degrade gracefully to raw search results.

> **MCP editing note:** Kilo's TUI MCP dialog (`/mcp`) is view + enable/disable **toggle only** — there is no edit UI (`packages/tui/src/component/dialog-mcp.tsx` has a single `toggle` action). Edit `opencode.json` directly and restart.

> **Network note:** this machine's proxy TLS-blocks pypi.org and registry.npmjs.org. Mirrors are configured globally: `~/.config/uv/uv.toml` (TUNA PyPI) and `~/.npmrc` (npmmirror). `github.com` is intermittently unreachable — if a clone/push times out, retry or use `https://gitclone.com/github.com/<owner>/<repo>.git`.

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

> **Dimension note:** Kilo IDX uses `dimension: 2048` because direct testing against `/api/plan/v3/embeddings` confirmed `doubao-embedding-vision` returns 2048-dimensional vectors. The official Volcano Ark Agent Plan documentation shows `dimension: 1024` in the OpenViking example, but Kilo's verified setup uses 2048.

### Avoid Indexing Generated Data

If your workspace contains large experimental outputs (e.g. FreeSurfer `data_roots`, training logs, model checkpoints), exclude them from indexing. Otherwise the indexer will waste time and API quota on thousands of small data JSON files and appear stuck at a low percentage.

> **Important:** Kilo uses **three separate** ignore mechanisms:
>
> | Mechanism | What it controls | Affects agent tools | Where to put it |
> |---|---|---|---|
> | `watcher.ignore` in Kilo config | The `@parcel/watcher` file watcher (CPU/filesystem events) | No | `~/.config/kilo/opencode.json` or `.kilo/kilo.json` |
> | `.kilocodeignore` / `.gitignore` | IDX scanner + agent access control | Yes | Workspace root (`<project>/.kilocodeignore`) |
> | `~/.kilocode/.kiloindexignore` | IDX scanner only | No | `~/.kilocode/.kiloindexignore` |
>
> `watcher.ignore` does **not** prevent files from being embedded. To stop IDX from indexing data/model files, add them to `.kilocodeignore` (project-level, also blocks agent tools) or `~/.kilocode/.kiloindexignore` (global, indexing-only).

#### Recommended: machine-wide type-based ignore (`~/.kilocode/.kiloindexignore`)

The best place for data-type filtering is the global indexing-only ignore file. It applies to every workspace, does **not** restrict agent tool access, and follows file types rather than fragile folder paths.

A ready-to-use template is included in this repo:

```bash
mkdir -p ~/.kilocode
cp /media/zoujd4/DATA1/Users/zoujd4/JDgentLAB/VibeCoder_Kilo/Config/kiloindexignore ~/.kilocode/.kiloindexignore
```

Create or edit `~/.kilocode/.kiloindexignore`:

```text
# === Common data / output directories (type-based) ===
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
*.img
*.hdr
*.dcm
*.dicom
*.nrrd
*.nhdr
*.mha
*.mhd
*.vtk
*.vti
*.fib
*.trk
*.tck
*.gii
*.gii.gz
*.annot
*.label
*.surface
*.stl
*.obj
*.ply
*.srf
*.inflated
*.sphere
*.white
*.pial
*.curv
*.sulc
*.thickness
*.area
*.bvals
*.bvecs

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
*.dta
*.sas7bdat
*.xpt
*.db
*.sqlite
*.sqlite3
*.msgpack
*.bcolz
*.zarr
*.tfrecord
*.lmdb
*.mdb
*.leveldb

# === R data formats ===
*.rds
*.rda
*.RData
*.rdata
*.qs
*.fst
*.sav
*.por
*.rdb
*.rdx

# === Tabular / serialized data ===
*.parquet
*.csv
*.tsv
*.jsonl

# === Binary media / archives / documents ===
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

# === Tool caches / environments ===
node_modules/
__pycache__/
.venv*/
.venv.*/
.cache/
.parcel-cache/
*.egg-info/
```

This keeps **code scripts, text documents, and project config files** in the index while skipping data/model binaries, regardless of where they live.

> **Directory pruning vs file filtering:** Directory patterns (e.g. `Data/`, `runs/`) are much cheaper than file patterns because they stop the scanner from descending into entire trees. File patterns (e.g. `*.nii.gz`) are still needed for files scattered under mixed directories. The patched Kilo binary passes these patterns into `glob()` so pruning happens during traversal, not after.

#### Optional: workspace `.kilocodeignore`

Use the workspace file only for project-specific exclusions or when you also want to deny agent-tool access to a path. Keep it short and avoid hard-coding paths that may change:

```text
# Project-specific generated outputs
0_Logs/
x_Report/
```

#### Optional: reduce the file watcher load

Add a `watcher.ignore` block to your Kilo config so the file watcher does not watch data directories:

```json
{
  "watcher": {
    "ignore": [
      "Data/**",
      "data/**",
      "data_roots/**",
      "datasets/**",
      "checkpoints/**",
      "weights/**",
      "runs/**",
      "logs/**",
      ".venv*",
      ".dataprep_status/**",
      "**/*.nii.gz",
      "**/*.nii",
      "__pycache__",
      ".kilo/**",
      "node_modules/**",
      "0_Logs/**",
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
