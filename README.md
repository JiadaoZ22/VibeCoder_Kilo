# VibeCoder Kilo — Kilo Code CLI Configuration

> **Current binary:** Kilo Code `0.0.0-dev-zoujd-mainline-202608200243` (built from upstream Kilo `v7.4.22` merged into the local `dev/zoujd-mainline` fork).  
> **Last updated:** 2026-08-25.  
> **New (2026-08-19):** **"Agent-Voting" verification-scaling** — say the word `agent-voting` in any prompt (or `/agent-voting N rounds <task>`) to auto fan out N candidate subagents plus a read-only verifier that scores and selects. See [Agent-Voting](#agent-voting--one-word-verification-scaling) and [`Update/20260819_Plugin/`](Update/20260819_Plugin).  
> **New (2026-08-20):** **Doubao Search MCP** — web search is back when using Ark/Volcano Engine as the provider. Add a single MCP block to `~/.config/kilo/opencode.json`; search queries hit the official Volcengine endpoint `open.feedcoopapi.com` and the optional AI filter runs through the official Ark endpoint. See [Doubao Search MCP](#doubao-search-mcp) and [`Config/ReadMe.md`](Config/ReadMe.md).  
> **New (2026-08-25):** **Midea AIMP provider** — use an internal Midea `msk-` API key through a local reverse proxy that injects the required `Aimp-Biz-Id` / `AIGC-USER` headers. See [Midea AIMP Provider](#midea-aimp-provider) and [`Config/ReadMe.md`](Config/ReadMe.md).  
> **Fixed (2026-08-19):** mobile "not found" on `/remote` sessions — resumed sessions are now bootstrapped to the session relay on the first advertising heartbeat. See [`Bugs/Remote-Command/b_Mobile-NotFound-ResumedSession-Fix.md`](Bugs/Remote-Command/b_Mobile-NotFound-ResumedSession-Fix.md).  
> **Context management:** auto-compaction, pruning, and provider overflow detection are enabled by default for models with known context limits.  
> **🔒 Build policy:** New builds are stored as separate immutable artifacts; the working binary is never overwritten and old versions are deleted **only by hand** — see [Build Policy](#build-policy--never-overwrite-the-working-binary).

This repository stores the configuration files and documentation for running [Kilo Code CLI](https://kilo.ai/docs/code-with-ai/platforms/cli) with the **Volcano Ark (火山方舟 — 专属 API Key)** provider, optional **Doubao Search MCP**, optional **Midea AIMP provider** (via a local proxy), and optional **vector-search MCP** for intelligent code retrieval.

---

## What's Inside

| File | Purpose |
|------|---------|
| `Config/opencode.json` | Kilo main configuration (models, provider, MCP servers) |
| `Config/auth.json` | API-key storage template for OpenRouter & Ark |
| `Config/midea-proxy.py` | Local reverse proxy for Midea AIMP `msk-` keys |
| `Config/kiloindexignore` | Template for `~/.kilocode/.kiloindexignore` (global IDX data-type ignores) |
| `Config/ReadMe.md` | Detailed setup & troubleshooting guide |

---

## Build from Source (Recommended)

> **The stock `npm install -g @kilocode/cli` package contains known upstream bugs** — most notably the Qdrant "Failed to obtain server version" warning on every startup, plus several indexing (IDX) reliability issues. To get a clean, bug-free experience, **build and install your own binary from the patched source** included in this repository.

The patched source is pinned to upstream **Kilo `v7.4.22`** plus local fixes on the `dev/zoujd-mainline` branch for Ark/Doubao embeddings, Qdrant/IDX stability, remote-session resumption, and Doubao Search MCP integration.

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

### Build Policy — Never Overwrite the Working Binary

> **Rule (mandatory):** A build must **never** replace or destroy the binary you are currently using. Each build produces a **new, separately stored, immutable artifact**. Switching versions is a *pointer change*, not a file overwrite. **Old versions are deleted only when I explicitly delete them by hand** — no build step, no script, and no agent may prune them automatically.
> **The latest build version's terminal wake-up command shall be "kilo" while the existing one shall be "kilo-<version>" for clarification.**

#### Why this rule exists

Building in place creates a class of confusion that is hard to debug:

| Hazard | What actually happens |
|---|---|
| **In-place overwrite** | `cp … → bin/.kilo` destroys the known-good binary. If the new build is broken, there is nothing to fall back to. |
| **Live symlink into `dist/`** | On this machine `~/.npm-global/bin/kilo` is a symlink **directly into the build tree** (`kilo-source/packages/opencode/dist/@kilocode/cli-linux-x64/bin/kilo`). Any rebuild silently mutates the "installed" CLI — even a *failed* or half-written build. |
| **Rebuild while Kilo is running** | The running process keeps the old inode while new invocations get the new binary → two different versions live at once, with mismatched DB/session expectations. |
| **Ambiguous version string** | `kilo --version` derives from the **last git commit timestamp**, not build time, so an overwritten binary can *look* unchanged after a successful rebuild. |
| **Unclear provenance** | Without one artifact per build you cannot answer "which commit is this binary?" months later. |

#### Layout

```text
~/.npm-global/lib/node_modules/@kilocode/cli/bin/
├── kilo                     # npm launcher shim (do not touch)
├── .kilo -> versions/…      # ACTIVE binary — a symlink, never a real file
└── versions/
    ├── kilo-7.4.16-a1b2c3d-20260727      # kept
    ├── kilo-7.4.22-ccd56a5-20260817      # kept  (currently active)
    └── kilo-7.4.22-f0e4ba4-20260818      # new build under test
```

Each artifact name encodes **upstream version + short commit + build date**, so provenance is self-documenting and no two builds can collide.

#### Build a new version (existing one stays untouched)

```bash
cd kilo-source

# 0. First time only
git submodule update --init --recursive
bun install

# 1. Build into the source dist/ (scratch area — NOT the installed binary)
bun run --cwd packages/opencode script/build.ts --single --skip-install

# 2. Name the artifact from real metadata
BIN=~/.npm-global/lib/node_modules/@kilocode/cli/bin
VER=$(node -p "require('./packages/opencode/package.json').version")
SHA=$(git rev-parse --short HEAD)
TAG="kilo-${VER}-${SHA}-$(date +%Y%m%d)"

# 3. Store it as a NEW immutable artifact
mkdir -p "$BIN/versions"
cp packages/opencode/dist/@kilocode/cli-linux-x64/bin/kilo "$BIN/versions/$TAG"
chmod 555 "$BIN/versions/$TAG"          # read-only: cannot be clobbered later

# 4. Smoke-test the NEW artifact WITHOUT activating it
"$BIN/versions/$TAG" --version
"$BIN/versions/$TAG" --help >/dev/null && echo "new build OK"
```

At this point the active CLI is **still the old, working version**. Nothing has been replaced.

#### Activate the new version (atomic, reversible)

```bash
# Record what is currently active so you can always go back
readlink -f "$BIN/.kilo" | tee ~/.kilo-active-previous

# Atomic pointer swap (ln -sfn replaces the symlink in one syscall)
ln -sfn "$BIN/versions/$TAG" "$BIN/.kilo"

kilo --version
```

> **Exit every running Kilo TUI before switching.** A live session pinned to the old inode plus new invocations on the new binary is the fastest way to corrupt session/DB expectations.

#### Roll back

```bash
ln -sfn "$(cat ~/.kilo-active-previous)" "$BIN/.kilo"
kilo --version
```

Rollback is instant because **the old artifact was never deleted**.

#### One-time migration off the live-`dist/` symlink

The current `~/.npm-global/bin/kilo` points straight into the build tree, which violates the rule above. Fix it once:

```bash
BIN=~/.npm-global/lib/node_modules/@kilocode/cli/bin
mkdir -p "$BIN/versions"

# Freeze the binary that works TODAY as a named artifact
cp "$(readlink -f ~/.npm-global/bin/kilo)" \
   "$BIN/versions/kilo-7.4.22-ccd56a5-20260817"
chmod 555 "$BIN/versions/kilo-7.4.22-ccd56a5-20260817"

# Point the launcher at the artifact store instead of dist/
ln -sfn "$BIN/versions/kilo-7.4.22-ccd56a5-20260817" "$BIN/.kilo"
ln -sfn "$BIN/kilo" ~/.npm-global/bin/kilo

kilo --version
```

After this, `bun run … build.ts` only writes to `kilo-source/…/dist/`, which is **scratch space** — rebuilding can no longer affect the CLI you are using.

#### Retention — manual deletion only

```bash
# Inspect what you have accumulated (each build is ~190–230 MB)
ls -lh ~/.npm-global/lib/node_modules/@kilocode/cli/bin/versions/
du -sh  ~/.npm-global/lib/node_modules/@kilocode/cli/bin/versions/

# Delete ONLY when I decide to, and never the currently active one
readlink -f ~/.npm-global/lib/node_modules/@kilocode/cli/bin/.kilo   # check first
rm ~/.npm-global/lib/node_modules/@kilocode/cli/bin/versions/kilo-7.4.16-a1b2c3d-20260727
```

**Forbidden:** any automatic pruning — no `rm` inside build scripts, no "keep last N" cron job, no cleanup performed by a coding agent on its own initiative. Disk pressure is reported to me; it is not resolved by deleting builds.

Legacy ad-hoc backups (`.kilo.backup`, `.kilo.prev`, `.kilo.before-compaction-fix`, `.kilo.before-efficiency-updates`, `.kilo.before-upstream-merge`) are the old, unstructured form of this same policy. Keep them until I retire them explicitly; new builds go into `versions/` instead.

#### Testing a build without activating it at all

```bash
BIN=~/.npm-global/lib/node_modules/@kilocode/cli/bin
alias kilo-next="$BIN/versions/kilo-7.4.22-f0e4ba4-20260818"
kilo-next            # run the candidate; `kilo` remains the stable version
```

Prefer this for feature work: exercise the candidate in a scratch directory (e.g. `/tmp/kilo`) for a few sessions, then activate only once it has proven itself.

> **Note:** The version string shown by `kilo --version` is generated from the **last git commit timestamp** on the current branch, not the build time. Don't rely on it to tell two builds apart — rely on the artifact filename, which carries the commit SHA.

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
- `doubao-seed-2.0-mini` (256K context)
- `doubao-seed-2.0-lite` (256K context — default compaction / memory model)
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

## Agent-Voting — One-Word Verification Scaling

> **New 2026-08-19.** Full design, validation results, and rollback: [`Update/20260819_Plugin/`](Update/20260819_Plugin). (Renamed from "subagenting" same day — the old name read as generic parallel subagents; "agent-voting" says what it does: candidates compete, a verifier votes.)

Say the word **`agent-voting`** in any prompt, in any project, and Kilo automatically switches from single-shot answering to **verification-scaled generation**: it fans out N independent candidate subagents on the same spec, then runs a **separate read-only verifier subagent** that scores every candidate per criterion, picks a winner, and reports concrete `file:line` discrepancies for a refine round. The empirical basis: a weak generator + a fine-grained verifier beats a strong generator sampled once.

```text
agent-voting: refactor the auth module to use sessions      # auto degree from task complexity
agent-voting N=4 rounds=2: convert the ADNI dataset         # explicit degree, honoured verbatim
/agent-voting 4 2 write the performance report              # slash-command form
```
- **Degree ladder** (tier 0–4): trivial typo fix → single pass + spot-check; multi-file work → N=3 + verifier + 1 refine round; publication-grade / high-stakes → N=4–5 + ensembled judge + re-verification. Explicit numbers always win.
- **Generator ≠ approver**: the verifier subagent (`agent/verifier.md`) is permission-locked read-only (`edit`/`write`/`bash: deny`) — it judges, it can never "fix" what it is judging.
- **No false triggers**: the keyword is ignored inside fenced code blocks, and "no agent-voting" switches it off mid-session.

Implementation (all under `~/.config/kilo/`, no source patches):

| File | Role |
|---|---|
| `plugin/agent-voting.ts` | Keyword detect → degree classify → system-prompt inject (`experimental.chat.system.transform`) → temperature bump for candidate diversity |
| `skill/agent-voting/SKILL.md` | Full methodology, loaded on demand |
| `agent/candidate.md`, `agent/verifier.md` | Generator / read-only judge subagents |
| `command/agent-voting.md` | `/agent-voting [N] [rounds]` explicit-degree escape hatch |

Plugin activity is logged to `~/.local/state/kilo/agent-voting-plugin.log`.

---

## Doubao Search MCP

When Kilo's provider is set to Ark/Volcano Engine, the built-in web-search tool is unavailable (it is an Anthropic-server-side tool). The **Doubao Search MCP** restores web search using Volcengine's own Doubao Search API.

### What you get

- `doubao_search(query, count, snippet_length, ...)` — web search with long-form snippets, publish time, and source URLs.
- Optional `doubao_cross_check(...)` — multi-source fact-checking (only when the AI enhancement layer is enabled).
- Optional **AI enhancement layer** — filters/compresses raw search results with `doubao-seed-2-0-lite-260215` via the official Ark endpoint before they enter the main context window.

### Quick setup

1. Get a **Doubao Search API Key** from the [Volcengine Doubao Search console](https://console.volcengine.com/byteair/app/doubao-search/) (500 free searches/month).
2. Add the MCP block to `~/.config/kilo/opencode.json`:

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

3. Restart Kilo and run `> /mcp list` to confirm `doubao-search` is loaded.

### Safety

- Search queries are sent to `open.feedcoopapi.com`, the official Doubao Search API host documented by Volcengine for the [Global version](https://www.volcengine.com/docs/87772/2548026) and [Custom version](https://www.volcengine.com/docs/87772/2272953).
- The optional AI filter sends raw results to the official Ark endpoint `ark.cn-beijing.volces.com/api/v3`.
- No data is sent to any other third party.

Full configuration details, timeout notes, and security guidance are in [`Config/ReadMe.md`](Config/ReadMe.md).

---

## Midea AIMP Provider

If you have a Midea internal `msk-` API key, you can route Kilo through a small local reverse proxy that injects the two extra HTTP headers (`Aimp-Biz-Id` and `AIGC-USER`) the Midea AIMP endpoint requires.

### Quick setup

1. Install Python dependencies:
   ```bash
   pip install fastapi uvicorn httpx
   ```

2. Export credentials (never commit these):
   ```bash
   export MIDEA_MSK_API_KEY="msk-..."
   export MIDEA_AIGC_USER="your_4a_account"
   ```

3. Start the proxy:
   ```bash
   python /media/zoujd4/DATA1/Users/zoujd4/JDgentLAB/VibeCoder_Kilo/Config/midea-proxy.py
   ```

4. In Kilo, switch model:
   ```text
   > /models
   # select midea/volcengine-glm-5.3
   ```

The bundled `Config/opencode.json` already contains the matching `midea` provider block pointing at `http://127.0.0.1:8000/v1` with a dummy API key. The real authentication happens inside the proxy.

See [`Config/ReadMe.md`](Config/ReadMe.md) for the full proxy reference, environment variables, and caveats.

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

**Use a dedicated lightweight compaction model:** By default Kilo falls back to your chat model (e.g., `ark-code-latest`) for compaction summaries. The bundled `Config/opencode.json` now pins compaction to `ark/doubao-seed-2.0-lite` with thinking disabled (`reasoningEffort: minimal`), which is faster and more capable than `2.0-mini` for these background tasks. If you copy the config template, this is already set; otherwise add it manually:

```json
"agent": {
  "compaction": {
    "model": "ark/doubao-seed-2.0-lite",
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

### `/remote` Requires a Kilo Account

**Symptom:** `/remote` is visible in the TUI palette but disabled; selecting it shows `Kilo login required`. `kilo remote` fails with `Unable to enable remote: no Kilo credentials found.`

**Root cause:** The remote session relay is a **Kilo-account** service. With only third-party credentials (`ark`, `openrouter`) in `auth.json`, `provider_next.connected` lacks `"kilo"`, so the command cannot be enabled.

**Fix:** `kilo auth login` with the Kilo provider, then restart the TUI. Headless alternative: `export KILO_API_KEY=…; kilo remote`. Full analysis in [`Bugs/Remote-Command/Problem.md`](Bugs/Remote-Command/Problem.md); the TUI patch is documented in [`Bugs/Remote-Command/a_Solution.md`](Bugs/Remote-Command/a_Solution.md).

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
├── Bugs/               # Per-issue reports and fixes
│   ├── Compaction/
│   ├── Indexing/
│   ├── Remote-Command/ # /remote requires a Kilo account credential
│   ├── SubAgenting/
│   └── Submodule-Worktree/
├── kilo-source/        # Patched Kilo source (submodule) — dist/ is SCRATCH space
├── README.md           # This file
└── .gitignore
```

> Built binaries do **not** live in this repo. They are stored as immutable artifacts under
> `~/.npm-global/lib/node_modules/@kilocode/cli/bin/versions/`, with the active one selected by the
> `.kilo` symlink. See [Build Policy](#build-policy--never-overwrite-the-working-binary).

### Configuration Tips

- **Rotate keys without editing files**: replace `"apiKey": ""` with `"apiKey": "{env:ARK_API_KEY}"` in `opencode.json` and export the variable in your shell.
- **API key location**: You have three choices for supplying the key — `~/.local/share/kilo/auth.json` (recommended), the `apiKey` field inside `~/.config/kilo/opencode.json`, or the `ARK_API_KEY` environment variable.
- **Disable vector search**: simply remove the `mcp` block from `opencode.json` and restart Kilo.
- **Chunk tuning**: if retrieval quality feels off, adjust `--chunk-size` and `--chunk-overlap` in the `mcp` configuration.

---

## References

- [Kilo Code CLI Docs](https://kilo.ai/docs/code-with-ai/platforms/cli)
- [Ark API Docs](https://www.volcengine.com/docs/82379/1928261?lang=zh)
- [Doubao Search Global API](https://www.volcengine.com/docs/87772/2548026?lang=en)
- [Doubao Search Custom API](https://www.volcengine.com/docs/87772/2272953?lang=en)
- [MCP Vector Search Server](https://github.com/modelcontextprotocol/servers/tree/main/src/vector-search)
