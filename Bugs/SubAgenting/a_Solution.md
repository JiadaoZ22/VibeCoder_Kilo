# Restoring Subagent Delegation Outside Orchestrator Mode

## Timestamp
- Analysis completed: **2026-08-07 18:10 CST**
- Status: **diagnosis complete; fixes documented, not yet applied**

## Goal

Make `code` (and `plan` / `debug`) actually delegate to subagents, as the deprecation notice in
`orchestrator-mode.md` promises, without depending on the `orchestrator` agent that is already
marked `deprecated: true`.

The blocker is *instruction*, not *permission* (see `1_Bugs.md`). So every fix below is about
getting delegation guidance into the system prompt for the models actually in use.

## Understanding the prompt assembly order

`packages/opencode/src/session/llm/request.ts:72-83`:

```ts
const system = [
  [
    ...(isOpenaiOauth || !includePersona ? [] : [SystemPrompt.soul()]),
    ...(input.agent.prompt ? [input.agent.prompt] : SystemPrompt.provider(input.model)),
    ...input.system,          // ← env, memory, AGENTS.md, MCP, skills
    ...(input.user.system ? [input.user.system] : []),
  ].filter((x) => x).join("\n"),
]
```

Two important consequences:

1. **An agent-level `prompt` fully replaces the provider prompt.** If you set `agent.code.prompt`,
   you lose all of `default.txt` (tool policy, conventions, verbosity rules). Only override
   wholesale if that is intended.
2. **`input.system` is appended after the base prompt.** `AGENTS.md` is loaded into that slot via
   `instruction.system()` (`packages/opencode/src/session/prompt.ts:1735,1760-1766`), so
   `AGENTS.md` guidance is *additive* — the safest injection point.

## Option A (recommended): global `AGENTS.md` delegation policy

Lowest risk, no source patch, no prompt replacement, applies to every project and every model.

Kilo loads global instructions from `~/.config/kilo/AGENTS.md`
(`packages/opencode/src/session/instruction.ts:62-68`). That file **does not exist yet** on this
machine — confirmed absent — so it can simply be created.

### File: `~/.config/kilo/AGENTS.md`

```markdown
# Delegation policy

- If the `task` tool is available, use it proactively to delegate focused subtasks to subagent
  instances. You can spawn multiple subagents in parallel in a single message.
- Delegate to `explore` for codebase research, locating files, and understanding patterns.
- Delegate to `general` for independent multi-step research, analysis, or implementation.
- Before starting a phase with two or more independent research questions, launch them as
  parallel `task` calls rather than investigating them serially in the main context.
- Give each subagent complete standalone context: it does not inherit the current conversation.
- Do not delegate work that must edit the same files concurrently; sequence those instead.
```

This restores exactly the directive upstream deleted in `1f99fb2332`, plus explicit agent-type
routing lifted from `orchestrator.txt`.

### Trade-off

`AGENTS.md` sits *after* the base prompt, which is normally good for precedence, but it is also
subject to Kilo's own framing that project files are context rather than hard policy. On weak
instruction-followers it may still be ignored. It is also global, so it applies to `ask` too —
harmless, since `ask` has no `task` permission.

## Option B: per-model prompt profile

`SystemPrompt.provider()` (`packages/opencode/src/session/system.ts:48-90`) picks the prompt via
`model.prompt`, falling back through id substring checks to `PROMPT_DEFAULT`. Ark models match
nothing, so both `ark-code-latest` and `doubao-seed-evolving` currently get `default.txt`.

Pointing them at a profile that *does* carry strong delegation language:

```json
"provider": {
  "ark": {
    "models": {
      "ark-code-latest": {
        "name": "Ark(VolcanoEngine) Auto: effect+speed",
        "prompt": "anthropic"
      }
    }
  }
}
```

Valid values per `system.ts:51-68`: `anthropic`, `anthropic_without_todo`, `beast`, `codex`,
`gemini`, `gpt55`, `ling`, `trinity`.

`anthropic.txt:79-93` is by far the most forceful:

```
- You should proactively use the Task tool with specialized agents when the task at hand matches the agent's description.
- VERY IMPORTANT: When exploring the codebase to gather context ... it is CRITICAL that you use the Task tool instead of running search commands directly.
```

`gpt55` (`kilocode-gpt-5.5.txt:29`) is a lighter alternative.

### Trade-off

This swaps the **entire** system prompt, not just delegation. `anthropic.txt` assumes Claude-style
tool semantics and tone. Verify normal editing behaviour does not regress before keeping it.

## Option C: dedicated delegating primary agent

Keep `code` untouched and add a project or global agent that behaves like orchestrator but retains
tool access. Agents defined as markdown use the body as `prompt`
(`packages/opencode/src/config/agent.ts:139-149`), and `agent.<name>.prompt` from config is
applied at `packages/opencode/src/agent/agent.ts:367`.

### File: `.kilo/agent/lead.md`

```markdown
---
description: Implementation agent that delegates research to parallel subagents.
mode: primary
---
You coordinate and implement. Before any phase containing two or more independent research
questions, launch them as parallel `task` calls in a single message — `explore` for codebase
research, `general` for autonomous multi-step work. Give each subagent full standalone context.
Only investigate directly when a question is a single narrow lookup. Unlike orchestrator, you may
edit files yourself once research returns.
```

Note the repo convention: new agents go in `.kilo/`, not `.kilocode/` or `.opencode/`.

### Trade-off

Another agent to remember to select — which is the very friction the deprecation was meant to
remove. But it is explicit and cannot regress `code`.

## Option D: patch the fork (durable, survives upstream)

The local fork already carries a `kilocode_change` layer, so restoring the deleted line there
would persist across submodule bumps. Re-add to
`packages/opencode/src/session/prompt/default.txt` under `# Tool usage policy`:

```
- If the Task tool is available, use it proactively to delegate focused subtasks to a subagent instance. You can spawn multiple subagents in parallel.
```

`default.txt` is the correct target here — unlike `codex.txt`/`gpt.txt` (which upstream stripped),
it is the file Ark models actually resolve to.

### Trade-off

Requires a rebuild and creates a merge-conflict surface with upstream. This is the right fix only
if Options A–B prove insufficient. Note that history shows this exact fight already happened once:
local `75805a2` added delegation guidance, upstream `1f99fb2332` removed it again.

## Recommended sequence

1. Apply **Option A** — costs nothing, patches no source, is globally scoped.
2. Re-run a task with two independent research questions under `code` and check for `task` calls.
3. If delegation still does not fire, apply **Option B** with `"prompt": "anthropic"` on
   `ark-code-latest` only, and re-verify editing behaviour.
4. Only if both fail, apply **Option D** and rebuild.

## Validation

After any change, restart Kilo (prompt assembly is per-request but config is cached), run a
session under `code` with clearly parallelizable research, then query the DB:

```ts
// bun — count task calls grouped by the agent that made them
import { Database } from "bun:sqlite"
const db = new Database(process.env.USERPROFILE + "\\.local\\share\\kilo\\kilo.db", { readonly: true })
const SID = "<session id>"
const agentOf: Record<string, string> = {}
for (const m of db.query("SELECT id,data FROM message WHERE session_id=?").all(SID) as any[]) {
  const d = JSON.parse(m.data)
  if (d.role === "assistant") agentOf[m.id] = d.agent
}
for (const p of db.query("SELECT message_id,data FROM part WHERE session_id=?").all(SID) as any[]) {
  const d = JSON.parse(p.data)
  if (d.type === "tool" && d.tool === "task")
    console.log(agentOf[p.message_id], "→", d.state?.input?.subagent_type)
}
```

Success criterion: at least one row printing `code → explore` or `code → general`.

Cross-check in the UI: subagent tabs should appear while the agent indicator still reads **Code**,
not Orchestrator.

## Notes

- `orchestrator` also has `bash: "deny"` re-applied *after* user config
  (`packages/opencode/src/kilocode/agent/index.ts:524-526`), so it cannot be "fixed" by granting
  it shell access — delegation is structural to it by design.
- Do **not** rely on `plan` for delegation-heavy work: it allows `task` but denies the `general`
  subagent type (`packages/opencode/src/agent/agent.ts:212-214`), leaving only `explore`.
- The upstream removal was deliberate (changeset `remove-gpt-task-prompt.md`), presumably to curb
  over-delegation on GPT profiles. Any fix here is a local policy choice, not a bug fix upstream
  would necessarily accept.
- Until a fix is verified, `orchestrator` remains the only reliable way to get parallel
  delegation — despite being deprecated.

## Date
2026-08-07
