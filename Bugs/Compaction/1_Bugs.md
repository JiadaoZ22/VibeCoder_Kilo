# Kilo Code CLI Compaction Slowness

## Timestamp
- Initial observation: **2026-06-25 16:54 CST**
- Investigation completed: **2026-06-25 18:21 CST**

## Context
While using Kilo Code CLI on the `E2E_DK_Parcellation` project, compaction (`/compact` or auto-compaction when context is full) is noticeably slower than comparable tools such as Claude Code or Kimi Code.

## Observed Behavior
- Auto/manual compaction can take **tens of seconds to minutes** on long sessions.
- The fallback chunk-based compaction emits progress updates like:
  ```
  Compacting session summary... (3/7 chunks summarized)
  ```
- Each progress step corresponds to a separate LLM round-trip.

## Root Cause Analysis

### 1. Fallback chunking issues many LLM calls
Kilo has two compaction paths:

| Path | Trigger | Calls |
|---|---|---|
| Primary anchored summary | Context still fits | 1 |
| **Chunks fallback** (`compaction-chunks.ts`) | Context too large | **~10 calls for 7 chunks** |

The chunks fallback:
1. Splits the transcript into chunks (`split()`).
2. Summarizes each chunk in batches of `CONCURRENCY = 3`.
3. Recursively reduces partial summaries (`reduce()`, `DEPTH = 3`).

For a 7-chunk session this produces roughly:
- 7 chunk-summary calls
- 3–4 recursive reduce calls
- **~10 total LLM round-trips**

### 2. Low hard-coded concurrency
```ts
// packages/opencode/src/kilocode/session/compaction-chunks.ts
const CONCURRENCY = 3
```

Only 3 summaries run concurrently. With provider latency of 100–300 ms per call, a 7-chunk compaction spends significant time waiting.

### 3. Same heavy model used for compaction
The compaction agent has no dedicated model:

```ts
// packages/opencode/src/agent/agent.ts
compaction: {
  name: "compaction",
  mode: "primary",
  options: {},
  ...
}
```

It falls back to the session model (e.g., `ark-code-latest`), which is overkill for summarization.

### 4. Verbose transcript serialization
`transcript()` converts every message, tool call, file attachment, and reasoning block into XML:

```xml
<message index="1" role="user">...</message>
```

This inflates prompt size and prefill cost.

### 5. Progress-update overhead
Live progress updates are good UX but add Effect/DB/bus round-trips after every batch.

## Comparison with Other Tools

| Factor | Kilo Code CLI | Claude Code | Kimi Code |
|---|---|---|---|
| Typical compaction calls | 1 → ~10 | 1 + state reinjection | Likely 1, server-side |
| Max concurrency | 3 (hard-coded) | Higher / direct API | Up to 30 concurrent |
| Compaction model | Same as chat | Can use smaller model | Likely native/optimized |
| Transcript format | XML | Stripped/reinjected attachments | Internal/native |
| State preservation | High | High | High |
| Provider latency sensitivity | High (generic adapter) | Lower (direct Anthropic) | Lower (Moonshot) |

Claude Code uses `compactConversation()` which strips images/docs, summarizes in one call, and reinjects file/plan/attachment state. Kimi Code likely uses a server-side or native compaction path. Both avoid the client-side chunk → summarize → reduce loop.

## Why Kilo Is Built This Way

Kilo is provider-agnostic: it works with OpenAI, Anthropic, Ark, Ollama, local models, etc. It cannot rely on a provider’s private compaction endpoint, so it does the work client-side with generic chat completions. The tradeoff is more calls and higher latency.

## Related Code

- `packages/opencode/src/session/compaction.ts` — main compaction entry, anchored summary.
- `packages/opencode/src/kilocode/session/compaction-chunks.ts` — chunk fallback, recursive reduce.
- `packages/opencode/src/kilocode/session/compaction-payload-recovery.ts` — single-call recovery attempt.
- `packages/opencode/src/agent/agent.ts` — default agents including `compaction`.

## Date
2026-06-25
