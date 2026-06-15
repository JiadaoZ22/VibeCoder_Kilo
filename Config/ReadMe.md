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
        - **Language**: `ark-code-latest`, `doubao-seed-2.0-code/pro/lite`, `doubao-seed-code`, `minimax-latest`, `glm-5.1`, `glm-4.7`, `deepseek-v4-pro`, `deepseek-v4-flash`, `kimi-k2.6`
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
