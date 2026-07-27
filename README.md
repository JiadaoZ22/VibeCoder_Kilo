# VibeCoder Kilo — Kilo Code CLI Configuration

> **Current binary:** Kilo Code `0.0.0-fix-qdrant-check-compatibility-202607270050` (built from upstream Kilo `v7.4.16` merged into the local `fix/qdrant-check-compatibility` fork).  
> **Last updated:** 2026-07-27.  
> **Context management:** auto-compaction, pruning, and provider overflow detection are enabled by default for models with known context limits.

This repository stores the configuration files and documentation for running [Kilo Code CLI](https://kilo.ai/docs/code-with-ai/platforms/cli) with the **Volcano Ark (火山方舟 — 专属 API Key)** provider and optional **vector-search MCP** for intelligent code retrieval.

---

## What's Inside

| File | Purpose |
|------|---------|
| `Config/opencode.json` | Kilo main configuration (models, provider, MCP servers) |
| `Config/auth.json` | API-key storage template for OpenRouter & Ark |
| `Config/kiloindexignore` | Template for `~/.kilocode/.kiloindexignore` (global IDX data-type ignores) |
| `Config/ReadMe.md` | Detailed setup & troubleshooting guide |

---

## Build from Source (Recommended)

> **The stock `npm install -g @kilocode/cli` package contains known upstream bugs** — most notably the Qdrant "Failed to obtain server version" warning on every startup, plus several indexing (IDX) reliability issues. To get a clean, bug-free experience, **build and install your own binary from the patched source** included in this repository.

The patched source is pinned to upstream **Kilo `v7.4.5`** plus local fixes for Ark/Doubao embeddings and Qdrant/IDX stability.

### Why Build Yourself?

| Problem | Stock npm package | Our forked source |
|---------|------------------|-------------------|
| Qdrant compatibility warning | ❌ Appears on every launch | ✅ Patched (`checkCompatibility: false`) |
| Code indexing (IDX) stability | ❌ Unreliable, frequent ENOSPC / watcher errors | ✅ Qdrant fix + LanceDB defaults remain stable |
| Ark/Doubao embedding batch size | ❌ `max 10, got 60` error | ✅ Batched to provider limit (10) |
| Semantic search with Doubao embeddings | ❌ Returns empty results | ✅ Query-instruction prefix applied only to queries |
| `/compact` on large sessions | ❌ Appears frozen with no progress | ✅ Live chunking progress shown |
| `/settings` slash command | ❌ Crashes with context errors | ✅ Uses correct TUI contexts |
| Over-indexing data/model files | ❌ Stuck at 1% on generated JSONs | ✅ `.kilocodeignore` + source patch prune ignored dirs during glob traversal |
| Indexing throughput | ❌ Embedder split 60-input batches into 6 serial 10-input calls | ✅ Embedder-aware batch sizing (`maxBatchInputs`) |
| File-system overhead during scan | ❌ `stat()` on every path including ignored files | ✅ Extension/ignore filtering before `stat()` |
| Compaction chunk reduce | ❌ Recursive reduce ran sequentially | ✅ Concurrent reduce (up to 3) |
| Ability to apply your own fixes | ❌ Black-box binary | ✅ Full TypeScript source in `kilo-source/` |

### Quick Build

This repo already includes the forked source as a submodule (`kilo-source/`).

```bash
# 1. Initialize the submodule (if you haven't already)
git submodule update --init --recursive

# 2. Enter the source directory
cd kilo-source

# 3. Install dependencies (only needed once)
bun install

# 4. Build for your current platform only
#    Use --skip-install after the first build to save time.
bun run --cwd packages/opencode script/build.ts --single --skip-install

# 5. Replace the system-installed binary
#    (adjust path if your npm global prefix differs)
cp packages/opencode/dist/@kilocode/cli-linux-x64/bin/kilo \
   ~/.npm-global/lib/node_modules/@kilocode/cli/bin/.kilo

# 6. Verify
kilo --version
```

> **Tip:** Keep the original binary as a backup: `cp ~/.npm-global/lib/node_modules/@kilocode/cli/bin/.kilo ~/.npm-global/lib/node_modules/@kilocode/cli/bin/.kilo.backup`
>
> **Note:** The version string shown by `kilo --version` is generated from the **last git commit timestamp** on the current branch, not the build time. Don't be surprised if it shows an earlier date than when you built it.

For the full technical breakdown of the indexing patches, see [`Bugs/Indexing/a_Solution.md`](Bugs/Indexing/a_Solution.md). For compaction tuning, see [`Bugs/Compaction/a_Solution.md`](Bugs/Compaction/a_Solution.md).

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
- `ark-code-latest` (Auto-routing, 128K context)
- `doubao-seed-2.0-code` / `pro` / `lite` (128K context)
- `doubao-seed-2.0-mini` (256K context — default compaction model)
- `doubao-seed-code` (128K context)
- `doubao-seed-evolving` (Coding & Agent, weekly upgrade, **1M context** — [Volcano Ark docs](https://www.volcengine.com/docs/82379))
- `minimax-latest`
- `glm-5.1`, `glm-4.7`
- `deepseek-v4-pro`, `deepseek-v4-flash`
- `kimi-k2.6`

**Vision models**
- `doubao-seedance-2.0`
- `doubao-seedance-2.0-fast`
- `doubao-seedance-1.5-pro`
- `doubao-seedream-5.0-lite`

Switch models anytime inside Kilo with `/models`.

See [`Config/ReadMe.md`](Config/ReadMe.md) for full parameters, troubleshooting, and tuning tips.

---

## Managing Oversized Context

As sessions grow, context-window exhaustion causes slower responses, truncated outputs, or lost reasoning. Use this **layered strategy** to keep Kilo fast and effective.

### 1. Proactive Compaction (Primary Defense)

Use **`/compact`** (or **`/summarize`**) regularly to condense conversation history into a summary, preserving key decisions while dropping intermediate tool outputs.

**Auto-compaction is also active by default.** Kilo monitors token usage after each response and automatically compacts when the conversation reaches `compaction.threshold_percent` or hits the reserved safety buffer. You can still run `/compact` manually if you want control over when it happens.

**When to use it:**
- After completing a major sub-task.
- When responses get slower or truncated.
- Before switching to a new area of the codebase.

**Tip:** You can add instructions to preserve specific context:
```text
/compact preserve the database schema decisions and auth flow
```

**Use a dedicated lightweight compaction model:** By default Kilo falls back to your chat model (e.g., `ark-code-latest`) for compaction summaries. The bundled `Config/opencode.json` now pins compaction to `ark/doubao-seed-2.0-mini` with thinking disabled (`reasoningEffort: minimal`), which is smaller, faster, and cheaper than the chat model. If you copy the config template, this is already set; otherwise add it manually:

```json
"agent": {
  "compaction": {
    "model": "ark/doubao-seed-2.0-mini",
    "options": {
      "reasoningEffort": "minimal"
    }
  }
}
```

> **Do not use `doubao-embedding-vision` for compaction** — it is an embedding model that outputs vectors, not text summaries.

### 2. Optional: Enable Vector-Search MCP (Codebase RAG)

> **Note:** The base `Config/opencode.json` in this repo no longer includes a pre-configured MCP block. If you want vector search, you must add it manually.

You can set up **Retrieval-Augmented Generation (RAG)** by installing the MCP server and adding an `mcp` block to your `~/.config/kilo/opencode.json`.

**To enable it:**
```bash
# Ensure the MCP server is installed
npm install -g @modelcontextprotocol/server-vector-search

# Add the mcp block to your opencode.json (see Config/ReadMe.md for the snippet)
# Then, in Kilo, index your project once
> /mcp call vector-search index --path .
```

After indexing, ask questions in natural language and Kilo auto-retrieves relevant context. See [`Config/ReadMe.md`](Config/ReadMe.md) for the full configuration snippet.

### 3. Optional: Enable Project Memory (Kilo v7.4.5+)

**Memory is not the same as IDX.** IDX searches your codebase; Memory remembers facts, preferences, and session summaries across conversations.

|  | IDX / vector search | Project Memory (`/memory`) |
|---|---|---|
| **Stores** | Code files and chunks from the repo. | Facts, corrections, conventions, and session digests. |
| **Populated by** | Scanning/indexing the codebase (`/indexing`, MCP vector-search). | Explicit saves or automatic turn/session consolidation. |
| **Used for** | Finding relevant code when you ask a question. | Giving the agent persistent project/user context. |
| **Example** | “How does auth work?” → returns `auth.ts` snippets. | “We use 2-space indentation” → applied in future sessions. |

**Enable project memory:**
```text
> /memory on
```

**Common commands:**
```text
> /memory remember we deploy to Vercel and use pnpm
> /memory correct always use single quotes in TypeScript
> /memory forget Vercel
> /memory status
> /memory auto on     # auto-save extracted facts after each turn
```

Memory files live inside the project (or workspace) and are editable. They are injected into the system prompt, so the agent starts new sessions already knowing the important details. Use memory for **decisions, conventions, and cross-session context**; use IDX for **finding code**.

### 4. Session Hygiene — Don't Let Sessions Grow Forever

| Pattern | Command | When to use |
|---------|---------|-------------|
| Start fresh | `/new` | Switching to a new, unrelated task |
| Branch off | `/fork` | Exploring a tangent without losing the main thread |
| Jump back in time | `/timeline` | Need to revisit an earlier message |
| Save & restart | `/export` → `/new` | Session is too bloated to compact effectively |

**Rule of thumb:** If you're switching from "fix auth bug" to "refactor CSS," start a new session.

### 5. Pick Models With Larger Context Windows

Switch to a high-capacity model before long-haul tasks:

| Model | Typical Context | Best For |
|-------|----------------|----------|
| `kimi-k2.6` | Very long (200K+) | Massive codebases, long sessions |
| `deepseek-v4-pro` | Long (128K+) | Deep reasoning, large files |
| `doubao-seed-2.0-pro` | Medium-long | Balanced speed / capacity |

Switch anytime with `> /models`.

### 6. Prevent Context Pollution

- **Don't paste entire stack traces** — summarize the key error.
- **Don't ask Kilo to "read all files in src/"** — ask specific questions so RAG finds the right files.
- **Use `/add-dir` carefully** — adding huge monorepos increases indexing noise.

### Recommended Workflow

```text
# Start Kilo for a new task
kilo

# Work normally...

# When context feels heavy (~10+ turns or slow responses)
> /compact

# When starting a completely new task
> /new

# When a session becomes too bloated to compact effectively
> /export                    # save transcript
> /new                       # start fresh
```

**Proactive `/compact` + session discipline** is the most effective way to prevent context bloat. Add the optional vector-search MCP only if you frequently work in very large codebases where manual context management isn't enough.

---

## Avoid Over-Indexing

Kilo's codebase indexer scans every file under the workspace root that is not excluded by `.gitignore`, `.kilocodeignore`, or the global `~/.kilocode/.kiloindexignore` (plus a small hardcoded list such as `node_modules`, `.git`, `__pycache__`). If the workspace contains large/binary/dependency directories, indexing can hang, consume excessive CPU/memory, or take a very long time.

### Two different ignore mechanisms

| File | Affects IDX | Affects agent tools | Best for |
|---|---|---|---|
| `~/.kilocode/.kiloindexignore` | ✅ Yes | ❌ No | **Machine-wide indexing-only exclusions** (e.g. `Data/`, `.venv*`, `*.nii.gz`). The agent can still read or edit these paths when you explicitly ask it to. |
| `~/.kilocode/.kilocodeignore` | ✅ Yes | ✅ Yes | **Machine-wide access-control exclusions**. Patterns here are converted to permission denies, so the agent cannot touch those paths unless you add a negation rule. |
| Workspace `.gitignore` | ✅ Yes | ❌ No | Project-specific indexing exclusions that also apply to Git. |
| Workspace `.kilocodeignore` | ✅ Yes | ✅ Yes | Project-specific access-control exclusions. |

### Recommended global indexing-only ignore

Create `~/.kilocode/.kiloindexignore` (one per machine) with patterns like:

```text
# Large / binary data
Data/
*.nii.gz
*.nii

# Python virtual environments
.venv*
.venv.*/

# Runtime/status directories
.dataprep_status/
__pycache__/
```

Because `.kiloindexignore` is **indexing-only**, commands like these still work:

```text
> read Data/subject_001.nii.gz
> edit the script under .venv.zoujd4-Legion/bin/
```

If you also want to deny tool access globally, add the same patterns to `~/.kilocode/.kilocodeignore` instead (or in addition). A negated line such as `!Data/README.md` inside `.kilocodeignore` can re-allow a specific file after a broader deny rule.

This patched binary also loads a global file-watcher ignore list from `~/.config/kilo/kilo.json` (`watcher.ignore`), which prevents Kilo from watching those directories for live changes.

Without these exclusions, IDX may open thousands of large files (e.g., `.nii.gz` neuroimaging data, full `.venv` site-packages) and appear stuck while CPU and memory usage stay high.

---

## Known Issues & Workarounds

> **Upstream vs. This Fork:** Many of the issues below are present in the **stock npm package** (`npm install -g @kilocode/cli`). If you build from the patched source in this repo's `kilo-source/` submodule, several indexing-related bugs (Qdrant warnings, ENOSPC watcher exhaustion) are already fixed. TUI-level bugs (session rendering, clipboard) may still apply until upstream resolves them.

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
