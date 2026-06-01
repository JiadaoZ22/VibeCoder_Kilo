# Kilo Code

## Set Up Kilo Code CLI
> Refer https://kilo.ai/docs/code-with-ai/platforms/cli
```bash
npm install -g @kilocode/cli
```

### Set Up LM Providers

#### OpenRouter
- That is easy, just `kilo` and then `/connect`, and then choose `OpenRouter` and select the default model you'd like to use as favourite.

#### Ark (Volcano Engine — Exclusive API Key Plan)
> Refer https://www.volcengine.com/docs/82379/1928261?lang=zh
- Create *~/.config/kilo/opencode.json* with the Ark (Volcano Engine) setup.
    - Provider ID: ark
    - Base URL: `https://ark.cn-beijing.volces.com/api/plan/v3` (OpenAI-compatible endpoint for the Exclusive API Key plan)
    - API Key: pulled from your existing *~/.local/share/kilo/auth.json*, which is set by Kilo's `connect` commands.
    - Models: all supported models from the doc:
        - **Language**: `ark-code-latest`, `doubao-seed-2.0-code/pro/lite`, `doubao-seed-code`, `minimax-latest`, `glm-5.1`, `glm-4.7`, `deepseek-v3.2`, `kimi-k2.6`, `kimi-k2.5`
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

The `mcp` block has already been added to `opencode.json` in this repo. When you copy the file to `~/.config/kilo/opencode.json`, the block comes along automatically.

Key parameters:

| Parameter | Value | Description |
|-----------|-------|-------------|
| `type` | `local` | Required by Kilo's MCP schema |
| `command` | `["npx", "@modelcontextprotocol/server-vector-search", ...]` | Command and arguments as a single array |
| `--provider` | `openai` | Driver for OpenAI-compatible APIs |
| `--base-url` | `https://ark.cn-beijing.volces.com/api/plan/v3` | Reuses the Ark endpoint for the Exclusive API Key plan |
| `--api-key` | `YOUR_ARK_API_KEY_HERE` | Replace with your actual Ark API key (same key as in `provider.ark.options.apiKey`) |
| `--model` | `doubao-embedding-vision` | Ark-compatible embedding model |
| `--chunk-size` | `1024` | Characters per chunk |
| `--chunk-overlap` | `200` | Overlap between adjacent chunks |
| `enabled` | `true` | Start the MCP server automatically |

### Enable / Disable

- **Enable**: Keep the `mcp` object in `opencode.json`.
- **Disable**: Remove (or comment out) the entire `mcp` block and restart Kilo.

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

### Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `vector-search` not in `/mcp list` | MCP server not installed or crashed on start | Re-run `npm install -g @modelcontextprotocol/server-vector-search`; check Node version (`node -v`) |
| Index command fails with auth error | API key missing or invalid | Ensure `ARK_API_KEY` is exported in your shell, or hard-code the key in the `mcp.vector-search.command` array |
| Retrieved chunks are irrelevant | Chunk size / overlap mismatch for your codebase | Tune `--chunk-size` and `--chunk-overlap` in `opencode.json` |
| Slow indexing | Large repo or network latency to Ark | Exclude large generated directories (`node_modules`, `dist`, `.git`) by passing `--exclude` to the index command |
