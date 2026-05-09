# VibeCoder Kilo — Kilo Code CLI Configuration

This repository stores the configuration files and documentation for running [Kilo Code CLI](https://kilo.ai/docs/code-with-ai/platforms/cli) with the **Volcano Ark (火山方舟)** provider and optional **vector-search MCP** for intelligent code retrieval.

---

## What's Inside

| File | Purpose |
|------|---------|
| `Config/opencode.json` | Kilo main configuration (models, provider, MCP servers) |
| `Config/auth.json` | API-key storage template for OpenRouter & Ark |
| `Config/ReadMe.md` | Detailed setup & troubleshooting guide |

---

## Quick Start

### 1. Install Kilo

```bash
npm install -g @kilocode/cli
```

### 2. Copy Config Files

```bash
mkdir -p ~/.config/kilo
mkdir -p ~/.local/share/kilo

# Main configuration
cp Config/opencode.json ~/.config/kilo/opencode.json

# Auth keys (fill in your own keys first!)
cp Config/auth.json    ~/.local/share/kilo/auth.json
```

### 3. Add Your Ark API Key

Edit `~/.local/share/kilo/auth.json` and paste your key:

```json
{
  "ark": {
    "type": "api",
    "key": "your-ark-api-key-here"
  }
}
```

Or export it as an environment variable:

```bash
export ARK_API_KEY="your-ark-api-key-here"
```

### 4. Launch Kilo

```bash
kilo
```

---

## Features

### Multi-Model Support (Ark / Volcano Engine)

All configured models are OpenAI-compatible endpoints served through Ark:

- `doubao-seed-2.0-code` / `pro` / `lite`
- `minimax-latest`
- `glm-5.1`, `glm-4.7`
- `deepseek-v3.2`
- `kimi-k2.6`, `kimi-k2.5`

Switch models anytime inside Kilo with `/models`.

### Optional: Vector Search MCP (Memory Embedding)

To fight **context-window exhaustion**, this config includes an optional **MCP vector-search server** that:

1. Indexes your codebase locally using Ark's embedding model.
2. Retrieves only the most relevant code snippets before each query.
3. Injects those snippets into the LLM context automatically.

#### Prerequisites

```bash
npm install -g @modelcontextprotocol/server-vector-search
```

#### Enable

The `mcpServers` block is already present in `opencode.json`. It will be active as soon as you copy the config and restart Kilo.

#### Usage

```
> /mcp list                           # verify vector-search is connected
> /mcp call vector-search index --path .   # index current project
> Explain the auth flow in this repo  # Kilo auto-retrieves relevant code
```

See [`Config/ReadMe.md`](Config/ReadMe.md) for full parameters, troubleshooting, and tuning tips.

---

## Repository Structure

```
.
├── Config/
│   ├── opencode.json   # Kilo configuration (provider, models, MCP)
│   ├── auth.json       # API-key template
│   └── ReadMe.md       # Detailed setup guide
├── README.md           # This file
└── .gitignore
```

---

## Tips

- **Rotate keys without editing files**: replace `"apiKey": ""` with `"apiKey": "{env:ARK_API_KEY}"` in `opencode.json` and export the variable in your shell.
- **Disable vector search**: simply remove the `mcpServers` block from `opencode.json` and restart Kilo.
- **Chunk tuning**: if retrieval quality feels off, adjust `--chunk-size` and `--chunk-overlap` in the `mcpServers` configuration.

---

## References

- [Kilo Code CLI Docs](https://kilo.ai/docs/code-with-ai/platforms/cli)
- [Volcano Ark API Docs](https://www.volcengine.com/docs/82379/1928261?lang=zh)
- [MCP Vector Search Server](https://github.com/modelcontextprotocol/servers/tree/main/src/vector-search)
