# Action Plan — make "subagenting" auto-trigger verification scaling in Kilo Code CLI

> **Rename (2026-08-19, same day):** shipped as **"agent-voting"** — files now `plugin/agent-voting.ts`, `skill/agent-voting/SKILL.md`, `command/agent-voting.md`; rollback paths below updated. Body otherwise keeps the original name.

**Date:** 2026-08-19
**Companion:** [`WorkingNote.md`](./WorkingNote.md) (mechanism verification, issues, degree ladder)
**Status:** **Implemented 2026-08-19** (L1+L2+L3+L5; L4 deferred). Outcomes in `WorkingNote.md` §9.

---

## TL;DR of the decision

| Layer | Mechanism | Mandatory? | Why |
|---|---|---|---|
| L1 | **Plugin** (`chat.message` + `experimental.chat.system.transform` + `chat.params`) | **Yes** | Only mechanism that makes the bare keyword *deterministic* |
| L2 | **Skill** `subagenting/SKILL.md` | Yes | Holds the methodology; keeps the injected prompt short |
| L3 | **Subagents** `verifier.md`, `candidate.md` | Yes | Enforces generator ≠ approver; lets the judge use a different model |
| L4 | **MCP** wrapping `llm-verifier` | Optional | Real logprob scoring instead of eyeballed judging |
| L5 | **Command** `/subagenting <N> <rounds>` | Optional | Explicit-degree escape hatch |

MCP alone **cannot** do the trigger — it exposes tools, it cannot see or rewrite prompts. Skill alone is **model-discretion**, not deterministic. Hence L1 + L2 + L3 is the minimum viable set.

---

## Step 0 — Decide the install root (do this first)

Pick **one** global config dir and stay there; Kilo merges all roots, so duplicated definitions get loaded twice.

- Recommended: `~/.config/kilo/` → `skill/subagenting/SKILL.md`, `agent/verifier.md`, `agent/candidate.md`, `plugin/subagenting.ts`.
- Leave `~/.kilo/kilo.json` untouched; add nothing to `~/.kilocode/`.
- Coordinate with `Update/20260819_AgentEvolving/` (that plan proposed `~/.kilocode/skills/evolve-setup`) so the two features do not split across roots.

## Step 1 — Prove the hooks fire (spike, ~30 min)

Write a throwaway logging-only plugin and confirm both hooks run in the installed Kilo build:

- `chat.message` → log the user text; confirm keyword matching works.
- `experimental.chat.system.transform` → push a sentinel string into `output.system`, then ask the model to quote it back.

**Abort/adjust criterion:** if `experimental.chat.system.transform` is missing in the installed build, fall back to appending a synthetic part in `chat.message`, or to the `AGENTS.md` + skill-only route (Working Note §4.6).

References in the local checkout: `VibeCoder_Kilo/kilo-source/packages/plugin/src/index.ts:222` (Hooks), `:234` (`chat.message`), `:291` (`experimental.chat.system.transform`), `:247` (`chat.params`), `:266`/`:274` (`tool.execute.before/after`).

## Step 2 — Write the skill (pure markdown, useful standalone)

`~/.config/kilo/skill/subagenting/SKILL.md` — frontmatter `name: subagenting` plus a description that explicitly says *"Use whenever the user says 'subagenting' …"*, so it is discoverable even without the plugin.

Body = condensed from existing sources (reference them by absolute path, do not deep-copy, to keep one source of truth):
- `0_Skills_MCP/General/Claude_SubAgent.md` **Step 5b** — pattern → reference-repo table, rules of thumb
- the 5 rules from the `0_Skills_MCP/README.md` "READ FIRST WHEN SUBAGENTING" callout
- the degree ladder (Working Note §6)
- output contracts for candidate subagents and for the verifier

## Step 3 — Define the subagents

- `agent/candidate.md` — `mode: subagent`, generator role, receives the same spec N times.
- `agent/verifier.md` — `mode: subagent`, **read-only** (`permission: { edit: deny, bash: deny|ask, read: allow }`), optionally a different `model` than the generator. Output contract: per-criterion scores + winner index + concrete discrepancies with `file:line`, nothing else.

## Step 4 — Implement the plugin

1. **Detect** — match `subagenting` in the user's own message text only; ignore fenced code blocks and quoted file content (Working Note issue #7). Support an off-switch such as "no subagenting".
2. **Parse explicit degree** — accept `subagenting 4`, `subagenting N=4 rounds=2`, `subagenting heavy`, etc. Explicit always wins.
3. **Classify when implicit** — derive tier 0–4 from complexity signals: number of files/paths mentioned, whether a spec file exists, whether tests exist, irreversibility (writes/migrations/deletes), expected output size, and words like "carefully" / "production" / "publication".
4. **Inject** — append a compact protocol block to `output.system`: chosen tier, N, verifier depth, refine rounds, and an instruction to load the `subagenting` skill for detail.
5. **Diversify** — in `chat.params`, raise `temperature`/`topP` when N > 1 so the candidates genuinely differ.
6. **Enforce (optional)** — in `tool.execute.before/after`, count `task` fan-out and refuse to conclude the turn until a verifier pass ran.
7. **Announce** — print the selected tier so the degree is visible and can be overridden next turn.

## Step 5 — Optional: `/subagenting` command

`~/.config/kilo/command/subagenting.md` with `$1` = N, `$2` = refine rounds, frontmatter `subtask: true` if it should run isolated. Gives a precise explicit path alongside the keyword path.

## Step 6 — Optional: the real verifier via MCP

1. Test whether Ark `/api/plan/v3` returns `logprobs`. If not, use `deepseek-v4-flash` (already in the Ark provider list and named as a supported verifier backend) or a local `vllm serve` OpenAI-compatible endpoint.
2. `pip install llm-verifier` in an **isolated venv** (repo policy: no global pip installs), e.g. `~/.local/share/llm-verifier-venv/`.
3. Wrap `llm_verifier.select(problem, candidates, criteria)` as a small local MCP server exposing `verifier_score`.
4. Register under `mcp` in `~/.config/kilo/opencode.json`; set tool permission `llmverifier_*` explicitly.
5. Reference implementation to copy from: `1_References/Program/ai-agent-dev/verification-selfimprove/llm-as-a-verifier` and `.../TurboAgent` (proxy + pivot tournament).

## Step 7 — Validate

- [ ] Keyword in a normal prompt reliably activates the protocol (10/10 runs).
- [ ] Keyword inside a code block / quoted file does **not** activate it.
- [ ] Explicit degree is honoured verbatim.
- [ ] Implicit degree lands on a sensible tier for: (a) a one-line typo fix → Tier 0/1, (b) a multi-file refactor → Tier 2/3, (c) a publication-grade report → Tier 3/4.
- [ ] Verifier subagent cannot edit files (permission denial observed).
- [ ] Token cost per tier measured and recorded; budget cap works.
- [ ] Behaviour re-tested after the next Kilo upgrade (`experimental.` hook stability, Working Note issue #1).

## Step 8 — Document

- Append outcomes + measured costs to `WorkingNote.md`.
- If a Kilo-side patch was needed, log it under `VibeCoder_Kilo/Bugs/`.
- Update `0_Skills_MCP/General/Claude_SubAgent.md` (version history) to note that Step 5b is now partly automated, and how to invoke it.

## Rollback

Everything is additive and file-based:

```
rm -rf ~/.config/kilo/skill/agent-voting
rm -f  ~/.config/kilo/agent/verifier.md ~/.config/kilo/agent/candidate.md
rm -f  ~/.config/kilo/plugin/agent-voting.ts
rm -f  ~/.config/kilo/command/agent-voting.md
rm -rf ~/.local/share/llm-verifier-venv          # if Step 6 was done
# and remove the mcp.llm-verifier block from ~/.config/kilo/opencode.json
```

Back up `~/.config/kilo/opencode.json` before editing it (a `.merged-20260819.bak` precedent already exists in that dir).

## Explicitly out of scope for the first pass

- Auto-applying verifier verdicts without showing the user the winner and the discrepancies.
- Tier 4 by default — must stay opt-in on cost grounds.
- Replacing the existing manual prompt workflow before the plugin is proven (keep both paths until validation passes).
