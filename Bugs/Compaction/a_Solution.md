# Compaction Optimization & Configuration

## Timestamp
- Analysis completed: **2026-06-25 18:21 CST**
- Configuration applied: **2026-06-25 18:21 CST**

## Goal
Make Kilo Code CLI compaction faster by:
1. Using a smaller, cheaper, faster model for compaction summaries.
2. Disabling reasoning/thinking on that model to minimize latency.
3. Documenting additional code-level improvements that can be applied later.

## Applied Configuration

### File: `~/.config/kilo/opencode.json`

Added `doubao-seed-2.0-mini` to the Ark provider model list and configured the `compaction` agent to use it with thinking disabled.

```json
{
  "$schema": "https://app.kilo.ai/config.json",
  "model": "ark/ark-code-latest",
  "agent": {
    "compaction": {
      "model": "ark/doubao-seed-2.0-mini",
      "options": {
        "reasoningEffort": "minimal"
      }
    }
  },
  "provider": {
    "ark": {
      "name": "Volcano Ark (Exclusive API Key)",
      "npm": "@ai-sdk/openai-compatible",
      "options": {
        "apiKey": "ark-24ec078c-3483-4f1a-a3b9-0db792d9af47-04380",
        "baseURL": "https://ark.cn-beijing.volces.com/api/plan/v3"
      },
      "models": {
        "ark-code-latest": {
          "name": "Ark(VolcanoEngine) Auto: effect+speed"
        },
        "doubao-seed-2.0-mini": {
          "name": "Doubao Seed 2.0 Mini"
        },
        ...
      }
    }
  },
  ...
}
```

### Why `doubao-seed-2.0-mini`

- Low-latency, cost-efficient model from ByteDance / Volcano Ark.
- 256K context window, 32K max output.
- Suitable for summarization tasks.

### Why `reasoningEffort: "minimal"`

Doubao Seed 2.0 Mini supports four thinking levels:
- `minimal` — no thinking (fastest, cheapest)
- `low`
- `medium`
- `high`

Compaction only needs factual summarization, not deep reasoning, so `minimal` is the correct setting.

### How Kilo picks the compaction model

```ts
// packages/opencode/src/session/compaction.ts
const agent = yield* agents.get("compaction")
const model = agent.model
  ? yield* provider.getModel(agent.model.providerID, agent.model.modelID)
  : yield* provider.getModel(userMessage.model.providerID, userMessage.model.modelID)
```

Because `agent.compaction.model` is now set, compaction will use `ark/doubao-seed-2.0-mini` instead of falling back to the session model.

The agent options are merged into the final provider request in `packages/opencode/src/session/llm.ts`:

```ts
const options = mergeOptions(
  mergeOptions(mergeOptions(base, input.model.options), input.agent.options),
  variant
)
```

So `reasoningEffort: "minimal"` is passed to the Ark API alongside the compaction request.

## Additional Code-Level Improvements (Optional)

If the configuration alone is not enough, the following changes can be made in `packages/opencode/src/kilocode/session/compaction-chunks.ts`:

1. **Raise concurrency**
   ```ts
   const CONCURRENCY = 3  // → 5 or 8
   ```

2. **Short-circuit recursive reduce**
   When `chunks.length <= 3`, merge partial summaries in one final call instead of pairwise reduction.

3. **Use a compact transcript format**
   Replace XML serialization with JSON or terse bullets.

4. **Dedicated default compaction model in source**
   Modify `packages/opencode/src/agent/agent.ts` so the `compaction` agent defaults to a lightweight model instead of inheriting the session model.

## Validation

### Configuration syntax
```bash
python3 -m json.tool ~/.config/kilo/opencode.json > /dev/null && echo "valid JSON"
```

### After restarting Kilo
- Open a long session.
- Trigger `/compact` or wait for auto-compaction.
- Verify the status bar / progress message no longer references the session model and compaction completes faster.

## Notes

- `doubao-embedding-vision` must **not** be used for compaction — it is an embedding model that outputs vectors, not text summaries.
- The currently running Kilo process (`PID 2264008`) was started before this config change; restart Kilo to apply the new compaction agent.

## Date
2026-06-25
