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

> **Model preference:** `ark/doubao-seed-2.0-lite` is used for agent compaction and memory (instead of `2.0-mini`) because it is faster and cheaper, with no measurable quality loss for these background tasks.

---

## Optional: Doubao Search MCP (Web Search)

Kilo's built-in web search is disabled when the provider is switched to Ark (Volcano Engine) or other domestic endpoints. The [huashu-doubao-search](https://github.com/alchaincyf/huashu-doubao-search) MCP server bridges this gap using Volcengine's [Doubao Search Global API](https://docs.volcengine.com/docs/87772/2272949?lang=en).

### What it adds

- `doubao_search(query, count, snippet_length, ...)` — web search with long-form snippets, publish time, and source URLs.
- `doubao_cross_check(...)` — multi-source fact-checking (only appears when the AI enhancement layer is enabled).
- Optional **AI enhancement layer** — compresses/filters raw search results with a small Ark model before they enter the main context window.

### Requirements

- npm/npx (already needed by Kilo CLI).
- A **Doubao Search API Key** from the [Volcengine Doubao Search console](https://console.volcengine.com/byteair/app/doubao-search/). 500 free searches/month.
- For the AI enhancement layer, an **Ark API Key** (reuse the same one configured above for the `ark` provider).

### Configuration

Add this block to `~/.config/kilo/opencode.json` under `mcp`:

```json
{
  "mcp": {
    "doubao-search": {
      "type": "local",
      "command": ["npx", "-y", "github:alchaincyf/huashu-doubao-search"],
      "environment": {
        "DOUBAO_SEARCH_API_KEY": "<paste-your-doubao-search-api-key>",
        "DOUBAO_SEARCH_VERSION": "global",
        "ARK_API_KEY": "<paste-your-ark-api-key>",
        "ARK_MODEL": "doubao-seed-2-0-lite-260215"
      },
      "enabled": true,
      "timeout": 120000
    }
  }
}
```

- `timeout`: 120 seconds. The first `npx github:...` run may need to download and build the package; the default 5 s MCP timeout is too short and Kilo reports `server unavailable`.
- **Data destinations / safety:** search queries go to Volcengine's official Doubao Search API host `open.feedcoopapi.com`. This endpoint is documented in Volcengine's official Doubao Search API references for the [Global version](https://www.volcengine.com/docs/87772/2548026) (`/search_api/global_search`) and the [Custom version](https://www.volcengine.com/docs/87772/2272953) (`/search_api/web_search`). When the AI enhancement layer is enabled, result compression/filtering is done through the official Ark endpoint (`ark.cn-beijing.volces.com/api/v3`). No data is sent to any other third party. The wrapper is open-source at [alchaincyf/huashu-doubao-search](https://github.com/alchaincyf/huashu-doubao-search); you can audit `dist/index.js` after the first npx install.

- `DOUBAO_SEARCH_VERSION`: `global` (default, better global coverage) or `custom` (faster, authority-level filtering). See the [official comparison](https://docs.volcengine.com/docs/87772/2272949?lang=en).
- `ARK_MODEL`: the AI-enhancement post-processing model. Default and recommended is `doubao-seed-2-0-lite-260215` (Seed 2.0 Lite). This is **not** the same string as Kilo's provider alias `ark/doubao-seed-2.0-lite`; it is the Volcengine endpoint model ID used by the MCP server directly.
- **No source rebuild required** — this is a config-only change; restart Kilo to load the new MCP.

### Is `open.feedcoopapi.com` an official Volcengine domain?

**Short answer**: `open.feedcoopapi.com` **is an official internal API domain of Volcengine (ByteDance)**. It is NOT an unknown / untrusted third‑party link.

#### Background verification

1. This host is the official endpoint for Volcengine’s **Doubao Search (豆包搜索 / Ask‑Echo)** API service, documented in Volcengine public documentation.
   - [Global version API reference](https://www.volcengine.com/docs/87772/2548026) lists `https://open.feedcoopapi.com/search_api/global_search`.
   - [Custom version API reference](https://www.volcengine.com/docs/87772/2272953) lists `https://open.feedcoopapi.com/search_api/web_search`.
2. The other endpoint `ark.cn-beijing.volces.com` is the Volcengine Ark LLM inference endpoint, also fully ByteDance-owned cloud infrastructure.

#### Network flow

```text
Your local MCP client → open.feedcoopapi.com         (Volcengine search service)
Your local MCP client → ark.cn-beijing.volces.com    (Volcengine LLM inference)
```

All traffic stays within ByteDance-Volcengine cloud; **no external third-party service is injected**. There is no risk of redirection to malicious outside servers.

#### What you can do to double-check for safety

1. **Inspect network traffic:** Monitor outbound HTTPS requests from your MCP process and confirm DNS resolves to Volcengine-owned IP ranges.
2. **Review source code:**
   - Community [huashu-doubao-search](https://github.com/alchaincyf/huashu-doubao-search): its compiled `dist/index.js` hardcodes `open.feedcoopapi.com` as the default search base URL; you can audit the GitHub source directly.
   - Official [volcengine/mcp-server](https://github.com/volcengine/mcp-server) also references this same API host in source code.
3. **Certificate check:** When HTTPS requests happen, the SSL certificate issuer belongs to Volcengine/ByteDance.

#### Important caveat

Even though this domain is legitimate, **you still need to protect your `DOUBAO_SEARCH_API_KEY`**. If your local environment gets compromised, your API key may get leaked.

> There is no “bad-link / untrusted external domain” risk here. The search and AI-enhancement calls both hit Volcengine-controlled backend services.

### Network notes

If you are behind a proxy that blocks `pypi.org` or GitHub, configure mirrors first:

- `~/.config/uv/uv.toml` for uv/uvx-based tools (see `Bugs/Channel-Database/Problem.md`).
- npm mirror in `~/.npmrc` if npm registry access is unstable.

### Security

Keep API keys in `opencode.json` only on the local machine (this file is under `~/.config/kilo/`, not the repository). For shared machines, use `"{env:DOUBAO_SEARCH_API_KEY}"` and set the key in your shell environment instead.

---

## Optional: Midea AIMP Provider (internal proxy)

If you have a Midea internal `msk-` API key for the AIMP OpenAI-compatible endpoint, you can use it with Kilo through a **local reverse proxy**. The upstream endpoint requires two extra HTTP headers (`Aimp-Biz-Id` and `AIGC-USER`) that Kilo cannot inject directly, so the proxy adds them for you.

### How it works

```text
Kilo → http://127.0.0.1:8000/v1  →  midea-proxy.py  →  https://aimpapi.midea.com/t-aigc/mip-chat-app/openai/v1
```

The proxy runs only on `127.0.0.1`; nothing is exposed to the network. The real `msk-` key and your 4A account never touch `opencode.json`.

### 1. Install dependencies

```bash
pip install fastapi uvicorn httpx
```

### 2. Set credentials as environment variables

```bash
export MIDEA_MSK_API_KEY="msk-xxxxxxxxxxxxxxxx"
export MIDEA_AIGC_USER="your_4a_account"
# optional:
export MIDEA_PROXY_PORT="8000"
export MIDEA_AIMP_BIZ_ID="volcengine-glm-5.3"
```

- `MIDEA_MSK_API_KEY`: your Midea `msk-...` key.
- `MIDEA_AIGC_USER`: **your real 4A account**; the upstream returns 403 without it.
- `MIDEA_AIMP_BIZ_ID`: defaults to `volcengine-glm-5.3`.

### 3. Start the proxy

```bash
python /media/zoujd4/DATA1/Users/zoujd4/JDgentLAB/VibeCoder_Kilo/Config/midea-proxy.py
```

You should see:

```text
[midea-proxy] starting on http://127.0.0.1:8000/v1
[midea-proxy] upstream: https://aimpapi.midea.com/t-aigc/mip-chat-app/openai
```

### 4. Configure Kilo

The bundled `Config/opencode.json` already includes a `midea` provider block:

```json
{
  "provider": {
    "midea": {
      "name": "Midea AIMP (local proxy)",
      "npm": "@ai-sdk/openai-compatible",
      "options": {
        "apiKey": "dummy",
        "baseURL": "http://127.0.0.1:8000/v1"
      },
      "models": {
        "volcengine-glm-5.3": {
          "name": "Midea AIMP - GLM 5.3",
          "limit": { "context": 1000000, "output": 131072 }
        }
      }
    }
  }
}
```

`apiKey` can be `dummy` because authentication is handled by the proxy.

### 5. Switch model in Kilo

Start or restart Kilo, then run:

```text
> /models
```

and select `midea/volcengine-glm-5.3`.

### Using Midea in a Kilo session

Once the proxy is running and Kilo is using `midea/volcengine-glm-5.3`, chat normally. The model name is shown in the status bar; all completions go through the local proxy to Midea AIMP.

To switch back to Ark at any time:

```text
> /models
# select ark/ark-code-latest   (or any other Ark model)
```

### Verify the proxy works (without Kilo)

Before starting Kilo, test the proxy with curl:

```bash
curl -s http://127.0.0.1:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer dummy" \
  -d '{
    "model": "volcengine-glm-5.3",
    "stream": false,
    "messages": [{"role": "user", "content": "hello"}]
  }'
```

If you see a JSON response with assistant content, the proxy and your credentials are good. If you see a 403, check `MIDEA_AIGC_USER` and `MIDEA_MSK_API_KEY`.

### Run the proxy in the background

The proxy must stay alive while Kilo runs. Quick options:

**Option A — `nohup` / disown:**

```bash
nohup python /media/zoujd4/DATA1/Users/zoujd4/JDgentLAB/VibeCoder_Kilo/Config/midea-proxy.py > /tmp/midea-proxy.log 2>&1 &
disown
```

Stop later with:

```bash
pkill -f midea-proxy.py
```

**Option B — tmux / screen session:**

```bash
tmux new -s midea-proxy
python /media/zoujd4/DATA1/Users/zoujd4/JDgentLAB/VibeCoder_Kilo/Config/midea-proxy.py
# detach with Ctrl-B then D
```

**Option C — systemd user service (auto-start on login):**

Create `~/.config/systemd/user/midea-proxy.service`:

```ini
[Unit]
Description=Midea AIMP local proxy for Kilo
After=network.target

[Service]
Type=simple
Environment="MIDEA_MSK_API_KEY=msk-..."
Environment="MIDEA_AIGC_USER=your_4a_account"
ExecStart=/usr/bin/python3 /media/zoujd4/DATA1/Users/zoujd4/JDgentLAB/VibeCoder_Kilo/Config/midea-proxy.py
Restart=on-failure

[Install]
WantedBy=default.target
```

Then:

```bash
systemctl --user daemon-reload
systemctl --user enable midea-proxy.service
systemctl --user start midea-proxy.service
systemctl --user status midea-proxy.service
```

### Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `Failed to connect to 127.0.0.1:8000` in Kilo | Proxy not running | Start `midea-proxy.py` first. |
| Upstream returns 403 | `MIDEA_AIGC_USER` missing/incorrect or `MIDEA_MSK_API_KEY` invalid | Check both env vars, restart proxy. |
| Kilo shows `model not found` | Not switched to the Midea provider | Run `> /models` and pick `midea/volcengine-glm-5.3`. |
| Slow first response | Cold start / token generation | Normal; GLM 5.3 first-token latency can be a few seconds. |

### Caveats

- The proxy must be running before you start Kilo; if the proxy stops, Kilo will fail to get completions.
- The upstream currently exposes only the `volcengine-glm-5.3` model through this path.
- `midea-proxy.py` rewrites the `model` field in the request body to `volcengine-glm-5.3` by default. If Midea later supports more models through the same endpoint, set `MIDEA_FORCE_MODEL` accordingly.
- Keep your `msk-` key and 4A account off GitHub and out of `opencode.json`.

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
