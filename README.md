# VibeCoder Kilo — Kilo Code CLI Configuration

This repository stores the configuration files and documentation for running [Kilo Code CLI](https://kilo.ai/docs/code-with-ai/platforms/cli) with the **Volcano Ark (火山方舟 — 专属 API Key)** provider and optional **vector-search MCP** for intelligent code retrieval.

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

**Option A — Edit `~/.local/share/kilo/auth.json` and paste your key:**

```json
{
  "ark": {
    "type": "api",
    "key": "your-ark-api-key-here"
  }
}
```

**Option B — Hard-code it directly in `~/.config/kilo/opencode.json`:**

Find the `"apiKey"` field under `provider.ark.options` and replace `""` with your key:

```json
"apiKey": "your-ark-api-key-here"
```

**Option C — Export it as an environment variable:**

```bash
export ARK_API_KEY="your-ark-api-key-here"
```

> **Note:** If you use Option C, also change `"apiKey": ""` to `"apiKey": "{env:ARK_API_KEY}"` in `opencode.json` so Kilo picks it up.

### 4. Launch Kilo

```bash
kilo
```

---

## Usage

Once Kilo is running, you interact with it through **slash commands** and **keyboard shortcuts**.

### Essential Slash Commands

| Command | Action |
|---------|--------|
| `/models` | Switch between configured Ark models (e.g., Doubao, DeepSeek, Kimi). |
| `/sessions` (or `/resume`) | List all past sessions; select one to jump back to its end. |
| `/undo` | Roll back to a previous turn in the current session (creates a fork). |
| `/fork` | Branch off from the current session’s latest state into a new session. |
| `/new` | Start a fresh session without restarting Kilo. |
| `/clear` (or `/reset`) | Wipe the current session’s context and start a new conversation. |
| `/help` (or `/h`) | Show all available slash commands and shortcuts in a pager. |
| `/exit` | Quit Kilo. |

### Session Navigation — Rewind & Resume

Kilo preserves every session automatically. To “rewind” to a previous chat:

1. Type `/sessions` to open the session browser.
2. Use **↑/↓** to pick the session you want.
3. Press **Enter** — you’ll land at the **end** of that session instantly.

If you only want to rewind a few turns in the *current* chat, use `/undo` instead.

### MCP (Vector Search) Commands

If you enabled the vector-search MCP server:

| Command | Action |
|---------|--------|
| `/mcp list` | Verify that `vector-search` is connected. |
| `/mcp call vector-search index --path .` | Index the current project. |
| `/mcp call vector-search query --text "auth flow"` | Manually retrieve relevant snippets. |

After indexing, simply ask questions in natural language and Kilo will auto-retrieve relevant code context.

### Keyboard Shortcuts

| Shortcut | Function |
|----------|----------|
| `Ctrl-X` | Toggle between **Agent mode** (AI chat) and **Shell mode** (local shell). |
| `Ctrl-O` | Open the current input in your external editor (`$EDITOR`). |
| `Ctrl-S` | **Steer**: inject a message immediately into a running turn. |
| `Ctrl-C` | Interrupt the current operation. |
| `Ctrl-D` | Exit Kilo (when input box is empty). |

---

## Features

### Multi-Model Support (Ark / Volcano Engine)

All configured models are OpenAI-compatible endpoints served through Ark:

**Language models**
- `ark-code-latest` (Auto-routing)
- `doubao-seed-2.0-code` / `pro` / `lite`
- `doubao-seed-code`
- `minimax-latest`
- `glm-5.1`, `glm-4.7`
- `deepseek-v3.2`
- `kimi-k2.6`, `kimi-k2.5`

**Vision models**
- `doubao-seedance-2.0`
- `doubao-seedance-2.0-fast`
- `doubao-seedance-1.5-pro`
- `doubao-seedream-5.0-lite`

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

The `mcp` block is already present in `opencode.json`. It will be active as soon as you copy the config and restart Kilo.

#### Usage

```
> /mcp list                           # verify vector-search is connected
> /mcp call vector-search index --path .   # index current project
> Explain the auth flow in this repo  # Kilo auto-retrieves relevant code
```

See [`Config/ReadMe.md`](Config/ReadMe.md) for full parameters, troubleshooting, and tuning tips.

---

## Managing Oversized Context

As sessions grow, context-window exhaustion causes slower responses, truncated outputs, or lost reasoning. Use this **layered strategy** to keep Kilo fast and effective.

### 1. Proactive Compaction (Primary Defense)

Use **`/compact`** (or **`/summarize`**) regularly to condense conversation history into a summary, preserving key decisions while dropping intermediate tool outputs.

**When to use it:**
- After completing a major sub-task.
- When responses get slower or truncated.
- Before switching to a new area of the codebase.

**Tip:** You can add instructions to preserve specific context:
```text
/compact preserve the database schema decisions and auth flow
```

### 2. Enable Vector-Search MCP (Codebase RAG)

The `mcp` block in this repo's `Config/opencode.json` sets up **Retrieval-Augmented Generation (RAG)**. Instead of dumping entire files into the prompt, Kilo retrieves only the most relevant code snippets.

**To enable it now:**
```bash
# Copy the config with MCP (if you haven't already)
cp Config/opencode.json ~/.config/kilo/opencode.json

# Ensure the MCP server is installed
npm install -g @modelcontextprotocol/server-vector-search

# In Kilo, index your project once
> /mcp call vector-search index --path .
```

After indexing, ask questions in natural language and Kilo auto-retrieves relevant context.

### 3. Session Hygiene — Don't Let Sessions Grow Forever

| Pattern | Command | When to use |
|---------|---------|-------------|
| Start fresh | `/new` | Switching to a new, unrelated task |
| Branch off | `/fork` | Exploring a tangent without losing the main thread |
| Jump back in time | `/timeline` | Need to revisit an earlier message |
| Save & restart | `/export` → `/new` | Session is too bloated to compact effectively |

**Rule of thumb:** If you're switching from "fix auth bug" to "refactor CSS," start a new session.

### 4. Pick Models With Larger Context Windows

Switch to a high-capacity model before long-haul tasks:

| Model | Typical Context | Best For |
|-------|----------------|----------|
| `kimi-k2.6` | Very long (200K+) | Massive codebases, long sessions |
| `deepseek-v3.2` | Long (128K+) | Deep reasoning, large files |
| `doubao-seed-2.0-pro` | Medium-long | Balanced speed / capacity |

Switch anytime with `> /models`.

### 5. Prevent Context Pollution

- **Don't paste entire stack traces** — summarize the key error.
- **Don't ask Kilo to "read all files in src/"** — ask specific questions so RAG finds the right files.
- **Use `/add-dir` carefully** — adding huge monorepos increases indexing noise.

### Recommended Workflow

```text
# Start Kilo for a new task
kilo

# Index the project (do this once per major change)
> /mcp call vector-search index --path .

# Work normally...

# When context feels heavy (~10+ turns or slow responses)
> /compact

# When starting a completely new task
> /new

# When a session becomes too bloated to compact effectively
> /export                    # save transcript
> /new                       # start fresh
```

**The combination of RAG + proactive `/compact` + session discipline** is the most effective way to prevent context bloat.

---

## Known Issues & Workarounds

### Session History Missing in TUI `/sessions`

**Symptom:** You launch `kilo` in a project directory, type `/sessions`, and see no historical records — even though you have previously worked there.

**Root cause:** This is a known Kilo CLI TUI bug tracked in GitHub issues ([#6616](https://github.com/Kilo-Org/kilocode/issues/6616), [#7846](https://github.com/Kilo-Org/kilocode/issues/7846), [#7965](https://github.com/Kilo-Org/kilocode/issues/7965)). The session data is safely stored in `~/.local/share/kilo/`, but the TUI's `/sessions` dialog sometimes fails to render them.

**Verification:** Your sessions are not lost. From the shell you can still list them:
```bash
kilo session list
```

**Workarounds:**
- Resume the most recent session for the current workspace: **`kilo -c`** (or `kilo --continue`)
- Resume a specific session by ID: **`kilo --session <session_id>`**
- Start Kilo normally, then use `/timeline` to jump to a specific message in the current session.

### Mouse Selection Does Not Copy to Clipboard

**Symptom:** You select text inside Kilo's TUI with your mouse, but nothing ends up in the system clipboard.

**Root cause:** Kilo's TUI captures mouse events for its own UI interactions (scrolling, buttons, etc.), which intercepts your terminal emulator's native text selection. Additionally, on Linux there is a known bug ([#8326](https://github.com/Kilo-Org/kilocode/issues/8326)) where Kilo shows "Copied to clipboard" feedback without actually writing to the system clipboard (especially on Wayland).

> **Fix:** If Kilo says "Copied to clipboard" but nothing is actually copied, you are likely missing the underlying clipboard utility. Install the one matching your display server, then restart Kilo:
> ```bash
> # X11
> sudo apt install xclip    # or xsel
> # Wayland
> sudo apt install wl-clipboard
> ```

**Workarounds:**

| Method | How |
|--------|-----|
| **Shift + Select** | Hold **Shift** while clicking and dragging to select text. This bypasses Kilo's mouse capture and uses your terminal's native selection. |
| **`/copy`** | Type `/copy` inside Kilo to copy the entire session transcript to the clipboard. |
| **`kilo export`** | Export the session to a Markdown file, then open it in your editor. |
| **Install clipboard helpers** | Ensure `xclip` / `xsel` (X11) or `wl-copy` (Wayland) is installed so Kilo can access the system clipboard. |

---

## Customization & Tips

### Repository Structure

```
.
├── Config/
│   ├── opencode.json   # Kilo configuration (provider, models, MCP)
│   ├── auth.json       # API-key template
│   └── ReadMe.md       # Detailed setup guide
├── README.md           # This file
└── .gitignore
```

### Configuration Tips

- **Rotate keys without editing files**: replace `"apiKey": ""` with `"apiKey": "{env:ARK_API_KEY}"` in `opencode.json` and export the variable in your shell.
- **API key location**: You have three choices for supplying the key — `~/.local/share/kilo/auth.json` (recommended), the `apiKey` field inside `~/.config/kilo/opencode.json`, or the `ARK_API_KEY` environment variable.
- **Disable vector search**: simply remove the `mcp` block from `opencode.json` and restart Kilo.
- **Chunk tuning**: if retrieval quality feels off, adjust `--chunk-size` and `--chunk-overlap` in the `mcp` configuration.

---

## References

- [Kilo Code CLI Docs](https://kilo.ai/docs/code-with-ai/platforms/cli)
- [Ark API Docs](https://www.volcengine.com/docs/82379/1928261?lang=zh)
- [MCP Vector Search Server](https://github.com/modelcontextprotocol/servers/tree/main/src/vector-search)
