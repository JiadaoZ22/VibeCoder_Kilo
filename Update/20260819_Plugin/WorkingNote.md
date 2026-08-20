# Working Note — "subagenting" as an automatic verification-scaling trigger in Kilo Code CLI

> **Rename (2026-08-19, same day):** the feature is now called **"agent-voting"** — "subagenting" read as generic parallel subagents, while the feature is specifically best-of-N candidates + a verifier vote. All live files moved: `plugin/agent-voting.ts`, `skill/agent-voting/SKILL.md`, `command/agent-voting.md`, log at `~/.local/state/kilo/agent-voting-plugin.log`. Wake keyword: `agent-voting` (also matches "agent voting"); off-switch: "no agent-voting". Body below keeps the original name for historical accuracy.

**Date:** 2026-08-19
**Status:** **Implemented and validated** (same day). See §9 for outcomes. L4 (MCP logprob verifier) deliberately not built yet — optional layer, pending an Ark `logprobs` probe.
**Companion:** [`ActionPlan.md`](./ActionPlan.md)

---

## 1. Goal (what was asked)

Today the workflow is manual: the user writes a prompt that *tells* the coding agent to use subagents. Desired end state:

1. Saying the word **"subagenting"** in any prompt, in any project, automatically activates a **verification-scaling workflow** — best-of-N generation plus a separate verifier subagent that scores and selects/refines — instead of a single-shot answer.
2. The **degree** of subagenting (fan-out N, verifier depth, refinement rounds) is:
   - honoured when stated explicitly (e.g. "subagenting, 4 candidates, 2 refine rounds"), **and**
   - **auto-decided by the agent from task complexity** when not stated.
3. Packaged as a reusable **skill / plugin / MCP** for the Kilo Code CLI, not a copy-pasted prompt.

## 2. Background — why this works (already collected, 2026-08-19)

Vendored at `1_References/Program/ai-agent-dev/verification-selfimprove/` (8 submodules, all starred). Core empirical claim: **a weak generator + a fine-grained verifier beats a strong generator sampled once.**

| Repo | Role in this design |
|---|---|
| `llm-as-a-verifier` (★2.0k, 152f, MIT, [paper](https://arxiv.org/abs/2607.05391)) | The scoring method: fine-grained granularity, expectation over the logprob distribution of score tokens, repeated evaluation + criteria decomposition. SOTA on Terminal-Bench, SWE-Bench Verified, MedAgentBench, RoboRewardBench |
| `TurboAgent` (★83, Apache-2.0) | Reference for the **proxy** approach: N concurrent candidates → Probabilistic Pivot Tournament → best response. Closest existing analogue to the goal |
| `agent-as-a-judge` (★811, 107f) | Verifier should be an **agent with tool access** (reads files/tests), not a prose judge |
| `verdict` (★343, 28f) | Composing/ensembling judges when one verifier pass is too noisy |
| `reflexion` (★3.2k, 315f) / `self-refine` (★817, 71f) | Critique-then-retry instead of blind resampling |
| `all-agentic-architectures` (★4.1k, 729f) | Catalogue for choosing a decomposition |
| `fable-mode` (★829, 89f) | Prior art: a *skill* that forces plan → subagent fan-out → verification gate |

Guidance already written and reusable verbatim as skill body text:
- `0_Skills_MCP/README.md` — top-of-file "⚠️ READ FIRST WHEN SUBAGENTING" callout + 5 practical rules.
- `0_Skills_MCP/General/Claude_SubAgent.md` — **Step 5b "Scale verification deliberately"** (pattern → submodule table, rules of thumb). Doc bumped to v2.1 on 2026-08-19.

## 3. Local environment (verified 2026-08-19)

| Fact | Value |
|---|---|
| Loaded global config | `~/.config/kilo/opencode.json` (legacy filename, still loaded). **`~/.config/kilo/kilo.json` does not exist** |
| Second global config | `~/.kilo/kilo.json` — exists, currently only `{"indexing":{"enabled":true}}` |
| Legacy dir | `~/.kilocode/` exists (no `skills/`, no `agent/`, no `command/`) |
| Global skills dir | **None yet** — no `~/.config/kilo/skill{,s}/`, no `~/.kilocode/skills/` |
| Global agents dir | **None yet** — no `~/.config/kilo/agent{,s}/` |
| Default model | `ark/ark-code-latest`; small model `ark/doubao-seed-2.0-mini` |
| Permissions | `bash: allow`, `read: *: allow`, `*: *: allow` (wide open — a plugin/skill will not be blocked by permission prompts) |
| MCP already configured | `doubao-search` (local, uvx). Note: its API key is a placeholder `<AGENT_PLAN_API_KEY>`, so live web search via that MCP currently fails — worked around with `webfetch` |
| Kilo source checkout | `VibeCoder_Kilo/kilo-source/` — available for reading the plugin/skill APIs |

## 4. Mechanism check — does each packaging option actually work?

Verified against `kilo-source` and the `kilo-config` skill reference.

### 4.1 Skill — **works, but does not auto-trigger on a keyword**

- Discovery: `{skill,skills}/<name>/SKILL.md` inside any config directory (`.kilo/`, legacy `.kilocode/`, `~/.config/kilo/`, `~/.kilo/`), plus `skills.paths` / `skills.urls` in config.
- All discovered skills are injected into the system prompt as an `<available_skills>` list containing only **name + description**; the body is loaded only when the model calls the `skill` tool (`kilo-source/packages/opencode/src/tool/skill.txt`: "Load a specialized skill when the task at hand matches one of the skills listed in the system prompt").
- **Consequence:** a skill named `subagenting` with a description like *"Use when the user says 'subagenting' …"* is a **model-discretion trigger**, not a hard one. Reliable in practice, but not guaranteed — the model may skip loading it.
- **Verdict: necessary but not sufficient on its own.** It is the right place to hold the *methodology text* (fan-out, verifier, rubric, degree ladder).

### 4.2 Plugin hook — **works, and gives the deterministic trigger**

`kilo-source/packages/plugin/src/index.ts:222` `Hooks` interface. Relevant hooks:

| Hook | Line | Use for this feature |
|---|---|---|
| `"chat.message"` | 234 | Fires on every new user message with `{sessionID, agent, model}` and `output.{message, parts}`. **Read-side keyword detection** — see if "subagenting" is present |
| `"experimental.chat.system.transform"` | 291 | `output.system: string[]` — **append the full subagenting protocol into the system prompt** for that session/model. This is the deterministic injection point |
| `"chat.params"` | 247 | Can raise `temperature`/`topP` so N parallel candidates are actually diverse, and bump `maxOutputTokens` |
| `"tool.execute.before"` / `".after"` | 266 / 274 | Observe/gate `task` (subagent) calls — e.g. count fan-out, enforce that a verifier pass happened before the turn is allowed to finish |
| `"command.execute.before"` | 262 | Alternative entry if triggering via `/subagenting` instead of a bare keyword |
| `event` / `config` / `tool` | 224–228 | Plugin can also register its own tools |

- Plugins are loaded from `{plugin,plugins}/*.{ts,js}` inside any config directory, or via the top-level `plugin: string[]` field (npm specifier or `file://` path).
- **Verdict: this is the only mechanism that makes the keyword deterministic.** `chat.message` (detect) + `experimental.chat.system.transform` (inject) is the core of the design.
- Caveat: the injection hook is prefixed `experimental.` — it can change across Kilo releases. Pin/lock behaviour and re-test after upgrades (this repo already tracks upgrades under `Update/`).

### 4.3 Subagent definition — **works, needed for the verifier role**

- `{agent,agents}/**/*.md` with frontmatter `mode: subagent`, own `model`, `steps`, `permission`, `hidden`.
- A dedicated `verifier` subagent (read-only permissions: `edit: deny`, `bash: ask/deny`) is the clean way to guarantee the judge cannot "fix" what it is judging — implements the `agent-as-a-judge` separation and the "generator ≠ approver" rule.
- Can be forced to a **different model** than the generator (cheap generator + stronger verifier, or vice versa) — directly exploits the weak-generator/strong-verifier finding.

### 4.4 MCP server — **works, but wrong tool for the trigger**

- `mcp.<name>` local/remote; MCP tool permissions keyed `{server}_{tool}`.
- MCP cannot observe or rewrite prompts — it only exposes tools. So it **cannot** provide the keyword trigger.
- Where it *is* right: wrapping the actual `llm-verifier` Python package (`pip install llm-verifier`) as an MCP tool, e.g. `verifier_score(problem, candidates[], criteria{})` → returns per-candidate scores. That gives **real logprob-based scoring** instead of the agent eyeballing candidates.
- Requires a backend that returns logprobs (per `llm-as-a-verifier` README: DeepSeek/Vertex keys, or an OpenAI-compatible server such as `vllm serve`). **Open question:** whether the Ark `/api/plan/v3` endpoint returns `logprobs`. If not, either (a) use `deepseek-v4-flash` (listed in our Ark provider config and named as a supported verifier backend in the repo's 0.2.0 notes) or (b) fall back to agent-judged rubric scoring without logprobs.

### 4.5 `/command` — **works as the explicit-degree escape hatch**

- `{command,commands}/**/*.md`, invoked `/name`, supports `$1..$N`, `$ARGUMENTS`, and frontmatter `agent`, `model`, `subtask: true`.
- Good for `/subagenting 4 2` (explicit N and refine rounds) — complements, not replaces, the keyword path.

### 4.6 `AGENTS.md` instructions — **works as a zero-code fallback**

- Auto-loaded instruction file. Putting the protocol + trigger sentence there gives ~most of the behaviour with no plugin at all, but it is per-project (or needs `instructions` globs) and burns context on every turn even when not subagenting.

## 5. Recommended architecture (layered, each layer independently useful)

```
user prompt containing "subagenting"
        │
 [L1 plugin] chat.message → detect keyword + parse explicit degree
        │            └─ no degree given? → classify complexity → pick degree
 [L1 plugin] experimental.chat.system.transform → inject protocol + chosen degree
        │
 [L1 plugin] chat.params → raise temperature/topP for candidate diversity
        │
 [L2 skill]  skills/subagenting/SKILL.md ← full methodology, loaded on demand
        │
 [L3 agents] agent/verifier.md (read-only, own model)  ← the judge
             agent/candidate.md (generator, mode: subagent)
        │
 [L4 MCP]    llm-verifier MCP → verifier_score(...) real logprob scoring (optional)
        │
 [L1 plugin] tool.execute.before/after on `task` → enforce verifier ran; count fan-out
```

- **L1 is the only mandatory piece for the keyword requirement.**
- L2/L3 work today with zero code (pure markdown) and already give most of the benefit if the user says "subagenting" *and* the model honours the skill.
- L4 is the only piece that needs an external dependency and network/logprob support.

## 6. Degree ladder (draft — to be refined during implementation)

Explicit user syntax wins; otherwise the plugin/skill classifies. Proposed tiers:

| Tier | Trigger heuristic | Fan-out N | Verifier | Refine rounds |
|---|---|---|---|---|
| **0 — off** | trivial/one-file/read-only question | 1 | inline spot-check | 0 |
| **1 — light** | single-file edit, well-specified | 2 | 1 verifier subagent, rubric only | 0–1 |
| **2 — standard** (default when "subagenting" is said with no degree) | multi-file change, spec exists, or report/deliverable | 3 | 1 verifier subagent with tool access (reads files/tests) | 1 |
| **3 — heavy** | cross-module refactor, dataset conversion, publication-grade report | 4–5 | ensembled/2-stage judge (`verdict` pattern) | 1–2 |
| **4 — max** | high-stakes, irreversible, or explicitly requested | 5+ | ensemble + independent re-verification of the winner | 2+ |

Complexity signals the classifier can use: number of files/paths mentioned, presence of a spec file, whether tests exist, whether the request is irreversible (writes/deletes/migrations), estimated output length, and whether the user used words like "carefully", "production", "publication".

Guardrails to encode: a token/时间 budget per tier; stop early when the verifier's pick stops changing; never let the generator be the sole approver; verification is skipped for Tier 0 by design.

## 7. Issues / open questions to resolve during implementation

1. **`experimental.` hook stability** — `experimental.chat.system.transform` may be renamed/removed in a Kilo upgrade. Need a version check + a graceful no-op, and a note in `Update/` on each upgrade.
2. **Skill auto-load is probabilistic** — the `<available_skills>` list only advertises name+description; the model chooses whether to call the `skill` tool. Do not rely on it alone for the trigger (this is exactly why L1 exists).
3. **Does Kilo's `task` tool support true parallel fan-out with independent samples?** The tool description says multiple agents can be launched concurrently in one message, but need to confirm N *independent* candidates on the *same* prompt is allowed and not deduplicated.
4. **Cost/latency blow-up.** Tier 3–4 multiplies token spend by N + verifier. Need an explicit budget cap and a visible warning; consider defaulting the verifier to a cheaper model (`doubao-seed-2.0-mini` is already the small model) and reserving the strong model for generation, or the reverse — to be measured.
5. **Logprob availability on Ark `/api/plan/v3`** — determines whether the real `llm-verifier` scoring (L4) is possible or whether we fall back to rubric-only judging. Test with a minimal request before building the MCP.
6. **Which config root to install into.** Global candidates: `~/.config/kilo/` (canonical XDG, but currently holds only the legacy `opencode.json`), `~/.kilo/` (has `kilo.json`), `~/.kilocode/` (legacy). Pick **one** to avoid duplicate skill/agent definitions being merged twice. Recommendation: `~/.config/kilo/` for skills/agents/plugin, and keep `~/.kilo/kilo.json` as-is.
7. **Keyword false positives** — "subagenting" appearing inside a quoted file, a code block, or a discussion *about* the technique (like this note) should not trigger it. Needs a narrow match (e.g. only in the user's own text, ignore fenced blocks) and probably an explicit off-switch phrase.
8. **Interaction with existing `0_Skills_MCP` docs** — the skill body should *reference* `General/Claude_SubAgent.md` Step 5b rather than duplicating it, so there is one source of truth. But note that file lives in a different repo (`JDgentLAB/0_Skills_MCP`), so a global skill needs either an absolute path reference or a copied condensed version.
9. **`doubao-search` MCP key is a placeholder** (`<AGENT_PLAN_API_KEY>`) — unrelated to this feature but worth fixing while touching config, since research-heavy subagenting would benefit from working web search.
10. **No revert needed for this session** — only config/source *reads* were performed; nothing was installed or modified for this feature.

## 8. Related prior notes

- `Update/20260819_AgentEvolving/` — Ark Agent Evolve integration (same day). Overlaps on: skill install paths, which global config dir to use, and the fact that Kilo is not an officially supported runtime for third-party agent tooling. Both features want to write into a global skills dir — coordinate so they do not fight over `~/.kilocode/skills/` vs `~/.config/kilo/skill/`.
- `0_Skills_MCP/General/Claude_SubAgent.md` v2.1 — the human-facing methodology this feature automates.

---

## 9. Implementation outcomes (2026-08-19, same day)

Implemented L1 + L2 + L3 + L5. L4 (MCP logprob verifier) skipped for now — optional layer, blocked on an Ark `logprobs` probe.

### Files installed (all under the chosen single root `~/.config/kilo/`)

| File | Layer |
|---|---|
| `plugin/subagenting.ts` | L1 — keyword detect + explicit-degree parse + complexity classify + system-prompt injection + temperature/topP raise |
| `skill/subagenting/SKILL.md` | L2 — methodology (5 rules, degree ladder, output contracts), references `0_Skills_MCP` by absolute path |
| `agent/candidate.md` | L3 — generator subagent (`mode: subagent`) with 3-section output contract |
| `agent/verifier.md` | L3 — read-only judge (`edit/write/bash: deny`), 4-section verdict contract |
| `command/subagenting.md` | L5 — `/subagenting [N] [rounds] <task>` explicit-degree path |

### Validation results

Plugin logic (8 cases, run under `bun` against the file directly — no model calls):

- keyword arms and injects the protocol block ✅
- `chat.params` raises temperature to 0.9 when N>1 ✅
- keyword inside a fenced code block does NOT trigger ✅
- explicit degree honoured verbatim (`N=4 rounds=2 tier 3` → N=4, rounds=2, Tier 3) ✅
- next plain message disarms ✅ · "no subagenting" off-switch ✅
- messages from `candidate`/`verifier` subagent sessions never arm (no recursion) ✅
- trivial prompt classifies to Tier 0–1 ✅

In the real built CLI (`0.0.0-fix-qdrant-check-compatibility-202608190324`):

- Plugin loads from `~/.config/kilo/plugin/` at instance init — confirmed via `kilo serve` + `GET /config` (plugin logs `loaded` to `~/.local/state/kilo/subagenting-plugin.log`). Note: plugins load per-instance, not at server start.
- End-to-end: `kilo run "subagenting tier 0: reply with exactly: OK"` → plugin log shows `armed … tier=0 explicit=true`, and the model announced "Tier 0 — N=1, verifier: inline spot-check, refine rounds: 0." — proof that `experimental.chat.system.transform` injected the block and the model followed it.

### Also fixed while in config

- `mcp.doubao-search` had placeholder key `<AGENT_PLAN_API_KEY>` (issue #9) — filled from the existing `provider.ark` key in `~/.config/kilo/opencode.json`.

### Deferred / watch items

- L4 MCP `llm-verifier`: probe whether Ark `/api/plan/v3` returns `logprobs` before building; fallback is rubric-only judging (current state) or `deepseek-v4-flash`/local vLLM.
- `experimental.chat.system.transform` stability across Kilo upgrades (issue #1): re-run the end-to-end check after each rebuild; the plugin log file makes this a 1-command check.
- Plugin enforcement hook (`tool.execute.before/after` counting fan-out / gating turn end) intentionally not implemented — the injected protocol relies on model compliance; add only if validation shows the model skips the verifier.
- Cost per tier not yet measured — first real Tier 2+ run should record token spend into this note.
- AgentEvolving plan updated to the same config root (`~/.config/kilo/skills/evolve-setup`, was `~/.kilocode/skills/`).
