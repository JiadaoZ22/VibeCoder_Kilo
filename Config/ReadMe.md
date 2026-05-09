# Kilo Code

## Set Up Kilo Code CLI
> Refer https://kilo.ai/docs/code-with-ai/platforms/cli
```bash
npm install -g @kilocode/cli
```

### Set Up LM Providers

#### OpenRouter
- That is easy, just `kilo` and then `/connect`, and then choose `OpenRouter` and select the default model you'd like to use as favourite.

#### Ark (Voclano Engine)
> Refer https://www.volcengine.com/docs/82379/1928261?lang=zh
- created *~/.config/kilo/opencode.json* with the Ark (Volcano Engine Coding Plan) setup.
    - Provider ID: ark
    - Base URL: https://ark.cn-beijing.volces.com/api/coding/v3 (OpenAI-compatible ndpoint for Coding Plan), or https://ark.cn-beijing.volces.com/api/coding.
    - API Key: pulled from your existing *~/.local/share/kilo/auth.json*, which is set by Kilo's `connect` commands.
    - Models: all supported Coding Plan models from the doc:
        - doubao-seed-2.0-code/pro/lite
        - doubao-seed-code
        - minimax-latest (MiniMax M2.7)
        - glm-5.1, glm-4.7
        - deepseek-v3.2
        - kimi-k2.6, kimi-k2.5
        - **Default model is set to ark/glm-5.1 You can change the "model" field at the top level to any other model ID (e.g., "ark/deepseek-v3.2").**
- Next steps:
    1. Restart Kilo (kilo or kilocode).
    2. Run /models in the TUI to switch models if needed.
    3. If you ever want to rotate the key without editing this file, replace "apiKey" with "apiKey": "{env:ARK_API_KEY}" and set the environment variable instead.

---

## Optional: Vector Search MCP (Memory Embedding)

To mitigate context-window exhaustion, you can enable a **local vector-search MCP server** that indexes your codebase and retrieves only the most relevant snippets before each query.

### Prerequisites

Make sure you have Node.js ≥ 18 and npm installed, then install the MCP server globally:

```bash
npm install -g @modelcontextprotocol/server-vector-search
```

### Configuration

The `mcpServers` block has already been added to `opencode.json` in this repo. When you copy the file to `~/.config/kilo/opencode.json`, the block comes along automatically.

Key parameters:

| Parameter | Value | Description |
|-----------|-------|-------------|
| `--provider` | `openai` | Driver for OpenAI-compatible APIs |
| `--base-url` | `https://ark.cn-beijing.volces.com/api/coding/v3` | Reuses the existing Ark endpoint |
| `--api-key` | `{env:ARK_API_KEY}` | Reads the Ark key from an environment variable (recommended). **If Kilo does not expand `{env:…}` inside `args`, replace this with your actual key or set the key in `auth.json` and reference it accordingly.** |
| `--model` | `doubao-embedding-vision-251215` | Ark-compatible embedding model |
| `--chunk-size` | `1024` | Characters per chunk |
| `--chunk-overlap` | `200` | Overlap between adjacent chunks |

### Enable / Disable

- **Enable**: Keep the `mcpServers` object in `opencode.json`.
- **Disable**: Remove (or comment out) the entire `mcpServers` block and restart Kilo.

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
| Index command fails with auth error | API key missing or invalid | Ensure `ARK_API_KEY` is exported in your shell, or hard-code the key temporarily for testing |
| Retrieved chunks are irrelevant | Chunk size / overlap mismatch for your codebase | Tune `--chunk-size` and `--chunk-overlap` in `opencode.json` |
| Slow indexing | Large repo or network latency to Ark | Exclude large generated directories (`node_modules`, `dist`, `.git`) by passing `--exclude` to the index command |