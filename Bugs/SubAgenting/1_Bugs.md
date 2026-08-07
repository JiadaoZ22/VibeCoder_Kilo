# Subagent Delegation Never Happens Outside Orchestrator Mode

## Timestamp
- Initial observation: **2026-08-07 17:45 CST**
- Investigation completed: **2026-08-07 18:10 CST**
- Root cause corrected and fix applied: **2026-08-07 20:45 CST**

## Status
**Resolved.** The fix is applied in `kilo-source` commit `f0e4ba4d48` and published on
`JiadaoZ22/kilocode` branch `fix/qdrant-check-compatibility`. See `a_Solution.md`.

A rebuild is still required before the running binary picks it up.

## Context

Kilo's own documentation declares orchestrator mode deprecated and claims that ordinary
full-tool-access agents now delegate on their own:

> `packages/kilo-docs/pages/code-with-ai/agents/orchestrator-mode.md:9`
>
> Orchestrator mode is deprecated and will be removed in a future release. In the VSCode
> extension and CLI, **agents with full tool access (Code, Plan, Debug) can now delegate to
> subagents automatically**. You no longer need a dedicated orchestrator — just pick the agent
> for your task and it will coordinate subagents when helpful.

Observed behaviour contradicts this: in practice only `orchestrator` ever spawns subagents.
`code` never does, even across long sessions containing obviously parallelizable research.

## Observed Behavior

Evidence comes from a real session in the `E2E_DK_Parcellation` project, read directly out of
`~/.local/share/kilo/kilo.db`.

Session `ses_024a72bc3ffer5Pg480zV71R3D`
("Task summary and work plan for Nanjing Gulou Hospital project"), 61 messages, CLI `v7.4.5`:

| Messages | `agent` | Model | `task` calls |
|---|---|---|---|
| 2–12 | **orchestrator** | `ark-code-latest` | **8** |
| 14–60 | **code** | `doubao-seed-evolving`, then `ark-code-latest` | **0** |

All 8 subagents were spawned while `agent=orchestrator`:

```
1. parentAgent=orchestrator  subagent_type=general  "Extract 申报书 docx text"
2. parentAgent=orchestrator  subagent_type=general  "Extract 分工 and 附件 docx"
3. parentAgent=orchestrator  subagent_type=general  "Describe the two PNG images"
4. parentAgent=orchestrator  subagent_type=explore  "Survey existing capabilities"
5. parentAgent=orchestrator  subagent_type=explore  "Survey existing capabilities"
6. parentAgent=orchestrator  subagent_type=general  "Write MineTask.md summary"
7. parentAgent=orchestrator  subagent_type=explore  "Map Try2_FederatedLearning pipeline"
8. parentAgent=orchestrator  subagent_type=general  "Survey BrainSeg knowledge base"
```

After the switch to `agent=code` at 09:37, the session ran **47 more assistant messages** using
only `read` / `edit` / `bash` / `write` / `webfetch` / `todowrite` — and **zero** `task` calls.
That phase included work that is textbook delegation material: surveying open-source OCR
projects, verifying four GitHub repos' licenses and sizes, and probing local tooling. All of it
was done serially in the main context.

### Reproduction

Query the local session database (read-only):

```ts
// bun
import { Database } from "bun:sqlite"
const db = new Database(process.env.USERPROFILE + "\\.local\\share\\kilo\\kilo.db", { readonly: true })
const SID = "ses_..."
const msgs = db.query("SELECT id,data FROM message WHERE session_id=? ORDER BY time_created").all(SID)
// message.data.agent  → which primary agent authored each assistant message
// part.data.tool === "task"  → delegation calls, with state.input.subagent_type
```

Child subagent sessions are also directly visible:

```sql
SELECT id, agent, title FROM session WHERE parent_id = '<parent session id>';
```

## Root Cause Analysis

The docs statement is true about **permissions** but false about **behaviour**. Nothing instructs
non-orchestrator agents to delegate.

### 1. `task` really is permitted for code/plan/debug

- `code` is derived from `build`, which inherits `defaults` (where `*` is allow), so `task` is
  allowed — `packages/opencode/src/agent/agent.ts:184` and
  `packages/opencode/src/kilocode/agent/index.ts:410-422`.
- `plan` explicitly allows `task`, denying only the `general` subagent type —
  `packages/opencode/src/agent/agent.ts:212-214`.
- `debug` also merges `defaults`, so `task` is allowed —
  `packages/opencode/src/kilocode/agent/index.ts:476-493`.

So permission is not the blocker.

### 2. Only orchestrator has a prompt that actually demands delegation

`orchestrator` gets a dedicated system prompt whose entire purpose is delegation
(`packages/opencode/src/agent/prompt/orchestrator.txt`):

```
4. Execute wave by wave. Launch all subtasks in a wave as parallel tool calls in a single message.
5. For each subtask, use the task tool with the appropriate agent type:
   - "explore" for codebase research, finding files, understanding patterns
   - "general" for implementation, analysis, and multi-step tasks
7. Do not edit files directly. Delegate all implementation to agents.
```

It is additionally locked into delegating: its ruleset is `"*": "deny"` with `task: "allow"` and a
hard `bash: "deny"` re-applied *after* user config, so it cannot do the work itself
(`packages/opencode/src/kilocode/agent/index.ts:501-527`). Note it is already flagged
`deprecated: true` at line 530 — while remaining the only agent that reliably delegates.

`code` / `plan` / `debug` receive no such instruction. They get the provider prompt selected by
`SystemPrompt.provider()` (`packages/opencode/src/session/system.ts:48-90`), and delegation
guidance there ranges from weak to absent.

### 3. Upstream deleted the one explicit delegation instruction

Commit `1f99fb2332` — *"fix(cli): remove explicit subagent delegation prompt"* (2026-07-10,
upstream) — deleted this line from both `codex.txt` and `gpt.txt`:

```diff
 ## Tool usage
-- If the Task tool is available, use it proactively to delegate focused subtasks to a subagent instance. You can spawn multiple subagents in parallel.
```

This is confirmed present in the currently built `kilo-source` HEAD (`git merge-base
--is-ancestor 1f99fb2332 HEAD` → true), so the line is gone from the running binary.

This directly regresses local commit `75805a2` — *"feat(code): bump submodule for code-mode
subagent delegation prompt"* — which had been made specifically to pick up that guidance.
Upstream removed it again on the next submodule bump.

### 3a. The earlier local fix existed but targeted the wrong file

Follow-up investigation found that the local fix behind `75805a2` **was never lost**. It lives on
the tracked submodule branch as `249f4a71c1` — *"feat(code): encourage subagent delegation in code
mode prompt"* — and adds exactly the needed directive:

```
- For complex, multi-step work, delegate to subagents with the task tool. Use `explore` for
  codebase research, `general` for autonomous implementation or verification, and launch multiple
  subagents in parallel when subtasks are independent. Do not duplicate work the subagent is doing.
```

But it was added to **`codex.txt` only**. Ark models resolve to **`default.txt`** (see §5), so the
guidance never reached the models actually in use. Verified:

| Branch file | Delegation guidance |
|---|---|
| `codex.txt` @ `fix/qdrant-check-compatibility` | present (`249f4a7`) |
| `default.txt` @ same branch | **absent** — only the file-search line |

This is the true root cause of the observed behaviour: not a missing fix, but a fix applied to a
prompt profile that the configured provider never selects.

### 3b. The build in use had also drifted off the tracked branch

`.gitmodules` pins `branch = fix/qdrant-check-compatibility`, but the `kilo-source` worktree was
checked out on `main`, which is a different lineage (diverged, ~1444 commits, not an
ancestor-descendant pair). Consequences:

- The **Qdrant fix was absent** from the working tree — `checkCompatibility: false` was missing
  from `packages/kilo-indexing/src/indexing/vector-store/qdrant-client.ts`, i.e. the very bug this
  fork exists to patch (see `README.md`) had silently regressed locally.
- `main` was at package version `7.4.20` while the tracked branch was `7.4.16`, so local state no
  longer matched what `README.md` documents.
- The recorded gitlink `249f4a7` was not reachable from the checked-out branch, and the worktree
  commit `0ac10df` was **not pushed to any remote**, so publishing that pointer would have broken
  `git clone --recursive`.

### 4. What remains in each prompt is far too weak

| Prompt | Delegation guidance | Strength |
|---|---|---|
| `codex.txt` | *(upstream removed it in `1f99fb2332`; local `249f4a7` restored it)* | **strong (local only)** |
| `gpt.txt` | *(none — removed by `1f99fb2332`)* | **none** |
| `default.txt:81` | "When doing file search, prefer to use the Task tool in order to reduce context usage." | file search only |
| `trinity.txt:83` | same as default | file search only |
| `kimi.txt:11` | "If the `task` tool is available, you can **use it** to delegate…" | permissive, not directive |
| `kilocode-gpt-5.5.txt:29` | "use it **proactively** to delegate… spawn multiple subagents in parallel" | strong |
| `anthropic.txt:79-93` | "**proactively** use the Task tool…"; "**VERY IMPORTANT** … it is **CRITICAL** that you use the Task tool" | strongest |
| `orchestrator.txt` | entire prompt is delegation protocol | strongest |

So automatic delegation from `code` is effectively **model-dependent**: it can work on Claude and
GPT-5.5 prompt profiles, and essentially never fires on the profiles with no guidance at all —
which includes `default.txt`, the profile every generic OpenAI-compatible provider falls back to.

### 5. Why this session in particular never delegated

`ark/ark-code-latest` and `ark/doubao-seed-evolving` are registered under a generic
`@ai-sdk/openai-compatible` Ark provider in `Config/opencode.json` with no `prompt` field. In
`SystemPrompt.provider()` none of the id checks match (`gpt`, `claude`, `gemini`, `codex`,
`trinity`, `kimi`, `ling`), so both fall through to:

```ts
return [PROMPT_DEFAULT]   // packages/opencode/src/session/system.ts:89
```

`default.txt` mentions the Task tool only for *file search*. Result: the `code` agent had the
permission to delegate and no instruction to do so — and did not.

A contributing signal: delegation stopped at the exact message where the model switched to
`doubao-seed-evolving` (msg 14). Weaker instruction-following amplifies an already-absent
directive.

## Impact

- The deprecation notice is misleading. Following it — "stop switching to orchestrator mode" —
  silently loses parallel delegation for any model on the `default`/`codex`/`gpt` prompt paths.
- The only agent that reliably delegates is the one marked `deprecated: true` and slated for
  removal, with no replacement behaviour in place.
- Long research phases run serially in the main context, inflating context usage and forcing
  earlier compaction — which is itself already a known pain point (see `Bugs/Compaction`).

## Related Code

- `packages/kilo-docs/pages/code-with-ai/agents/orchestrator-mode.md` — the deprecation claim.
- `packages/opencode/src/agent/agent.ts:184-228` — `build`/`plan` defaults; `task` permission.
- `packages/opencode/src/kilocode/agent/index.ts:410-531` — `build`→`code` rename, `debug` and
  `orchestrator` definitions, `deprecated: true`.
- `packages/opencode/src/agent/prompt/orchestrator.txt` — the only true delegation prompt.
- `packages/opencode/src/session/system.ts:48-90` — provider→prompt selection, `PROMPT_DEFAULT`
  fallback.
- `packages/opencode/src/session/prompt/{codex,gpt,default,anthropic,kimi,kilocode-gpt-5.5}.txt`
  — per-profile delegation guidance.
- Upstream `1f99fb2332` — removal of the explicit delegation line.

## Date
2026-08-07
