# Kilo Code CLI + Volcano Ark Agent Plan: Local Coding & Building Power-Up Guide

---

## Goal
Upgrade your **local** Kilo Code CLI setup for daily coding and building workflows by wiring in two new agent powers:

1. **Doubao Search MCP** — real-time web search for API docs, error explanations, and latest framework usage.
2. **OpenViking MCP** — semantic retrieval over your local codebase, replacing or augmenting Kilo's built-in IDX.

All secrets (API keys, MCP endpoint tokens) are kept out of this guide. You will insert them into the **local config file manually later**.

---

## Key Clarifications

1. **Auto intelligent routing**: When enabled, Kilo automatically picks the best coding model (Doubao Seed Code, Seed 2.0 Pro, etc.) for each request. Coding tasks are prioritized for code-optimized models; stronger general models are used only for complex reasoning.
2. **Coding models do NOT browse the web**: All internet access comes through the **Doubao Search MCP**, which is built for agent workflows.
3. **OpenViking vs. native IDX**: OpenViking uses L0/L1/L2 layered context that loads on demand, avoiding context-window crashes and improving retrieval accuracy on large projects. You can run it alongside native IDX or disable native IDX entirely.

---

## Local Config File

All configuration changes apply to the project-level file:

```text
/media/zoujd4/DATA1/Users/zoujd4/JDgentLAB/VibeCoder_Kilo/Config/opencode.json
```

> **Do not commit secrets.** This file is local to your workspace. Insert API keys and MCP tokens manually before running Kilo.

---

## What Is Already Configured

Your local config already contains:

- **Ark provider** with model `ark/ark-code-latest`.
- **Built-in indexing** using `doubao-embedding-vision` + LanceDB.
- **Watcher ignore rules** for data/checkpoints/logs.
- **Permissions** allowing Bash and other tools.

This upgrade focuses on **adding the two MCP servers** and deciding how indexing should work.

---

## Required Secrets (Set Manually Later)

Before running Kilo, fill in these values in `Config/opencode.json`:

1. **Volcano Ark Agent Plan API Key** — from Volcano Ark Console → Agent Plan → API Access.
2. **Doubao Search MCP endpoint URL + key** — from Agent Plan Console → Skill Marketplace → Doubao Search → MCP Integration.
3. **OpenViking API Key** — from the Volcano Engine OpenViking console.

---

## Configuration Changes

### 1. Keep or Tune the Ark Provider

Your existing provider block is already functional. If you want auto-routing, use `ark/ark-code-latest` as the top-level model or add an `auto` routing entry if your Kilo build supports it.

No change is required unless you want to experiment with a different default model (e.g., `ark/doubao-seed-2.0-code`).

### 2. Add the MCP Servers Block

Append the following to `Config/opencode.json` (merge into the top-level object). Replace the bracketed placeholders with your secrets later.

```json
{
  "mcp": {
    "doubao-search": {
      "type": "local",
      "enabled": true,
      "command": ["uvx", "--from", "git+https://github.com/volcengine/mcp-server#subdirectory=server/mcp_server_askecho_search_infinity", "mcp-server-askecho-search-infinity"],
      "environment": {
        "ASK_ECHO_SEARCH_INFINITY_API_KEY": "<AGENT_PLAN_API_KEY>"
      }
    },
    "openviking": {
      "type": "http",
      "url": "https://api.vikingdb.cn-beijing.volces.com/openviking/mcp",
      "headers": {
        "Authorization": "Bearer <YOUR_OPENVIKING_API_KEY>"
      }
    }
  }
}
```

### 3. Choose Your Indexing Strategy


#### Option A — Keep Built-in IDX + OpenViking (Recommended for Transition)

Leave the existing `indexing` block as-is:

```json
{
  "indexing": {
    "enabled": true,
    "provider": "openai-compatible",
    "model": "doubao-embedding-vision",
    "dimension": 2048,
    "vectorStore": "lancedb",
    "openai-compatible": {
      "apiKey": "<YOUR_ARK_API_KEY>",
      "baseUrl": "https://ark.cn-beijing.volces.com/api/v3"
    }
  }
}
```

- Built-in IDX stays fast for small, local lookups.
- OpenViking handles cross-file and large-project retrieval.

#### Option B: Migrate Fully to OpenViking

If you want OpenViking to handle **all** semantic retrieval:

```json
{
  "indexing": {
    "enabled": false
  }
}
```

This avoids duplicate indexing and redundant compute. Use OpenViking for every codebase query.

### 4. Keep Watcher Ignore Tuned

Your existing `watcher.ignore` list is already solid. Make sure it still covers:

- Data/output directories (`Data/**`, `runs/**`, `logs/**`)
- Model weights (`*.pth`, `*.ckpt`, `*.safetensors`, `*.bin`, etc.)
- Virtual environments and `node_modules/`

Also verify `.kilocodeignore` and `~/.kilocode/.kiloindexignore` exclude large binaries so the indexer does not waste quota.

---

## 4-Step Validation

After filling in secrets, restart Kilo and run:

1. **Verify MCP connections**
   ```text
   /mcp list
   ```
   Confirm `doubao-search` and `openviking` are both online.

2. **Verify web search (Doubao Search)**
   Ask something that requires current information:
   ```text
   Search for the latest use hook syntax in React 19 and give a runnable code example.
   ```
   The agent should call Doubao Search and return up-to-date code.

3. **Verify codebase retrieval (OpenViking)**
   Index the current project:
   ```text
   /mcp call openviking index --path .
   ```
   Then ask a cross-file question:
   ```text
   Walk me through the full user authentication flow in this project.
   ```

4. **Verify a local build/test command**
   Try a concrete local task, for example:
   ```text
   Run the project's test suite and summarize any failures.
   ```
   The agent should use Bash to invoke the correct test runner.

---

## Daily Local Building & Coding Workflows

1. **Kick off a feature or fix**
   Describe what you want to build in plain language. Auto-routing picks a code-optimized model.

2. **Unknown errors / new frameworks**
   Paste the error or ask about a new API. The agent will trigger Doubao Search automatically and resolve docs or troubleshooting inside the session.

3. **Large refactoring sessions**
   First index the project with OpenViking:
   ```text
   /mcp call openviking index --path .
   ```
   Then ask cross-file questions. Layered on-demand loading prevents context-window crashes.

4. **Multimodal coding**
   For UI mockups or error screenshots, use:
   ```text
   /add image.png
   ```
   Auto-routing will use a vision model and combine it with search + code retrieval.

5. **Build / test / lint loops**
   Ask Kilo to run local commands:
   ```text
   Build the project and report any errors.
   ```
   or
   ```text
   Run lint and fix the safe issues automatically.
   ```

---

## Best Practices

- **Secrets stay local.** Never commit `Config/opencode.json` with real keys. Consider using `{env:VAR_NAME}` syntax if you prefer environment variables.
- **Re-index after big changes.** Run `/mcp call openviking index --path .` after major refactors or dependency updates.
- **Keep ignore lists current.** Exclude data, weights, and generated outputs from both the watcher and the indexer.
- **Start with Option A.** Run built-in IDX and OpenViking together at first; switch to full OpenViking once you are confident retrieval quality is better for your projects.
- **Use `ark/ark-code-latest` for daily coding.** It balances speed and capability. Switch to `ark/doubao-seed-2.0-pro` only for deep reasoning or architecture decisions.

---

## FAQ

- **Can I input video directly?**
  Kilo CLI does not support full video input. Extract frames, import them into OpenViking, and process them as images with a multimodal model.

- **Will Auto route to non-coding models?**
  No. Coding-style requests are prioritized for code-optimized models. General models are used only for complex reasoning.

- **Will search results bloat my context?**
  No. The model filters only relevant search results into the context.

- **What if I want to rotate an API key?**
  Replace the literal key with `{env:NAME}` (e.g., `{env:ARK_API_KEY}`) in `Config/opencode.json` and set the environment variable before launching Kilo.

- **Do I need to disable native IDX to use OpenViking?**
  No. You can run both. Disable native IDX only if you want to avoid duplicate indexing or if OpenViking fully covers your retrieval needs.
