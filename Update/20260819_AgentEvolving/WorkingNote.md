# Working Note — Volcano Ark "Agent Evolve" for Kilo Code CLI

**Date:** 2026-08-19
**Reference:** [Agent Evolve docs (Volcano Engine Ark)](https://docs.volcengine.com/docs/82379/2545597?lang=en)
**Goal:** Add Ark's Agent Evolve (持续进化) capability to the local Kilo Code CLI, reusing the existing Ark Agent Plan API key.

---

## What Evolve Is

Evolve is a closed loop: **learn from recent agent sessions → generate optimization proposals in the cloud → apply to instruction files after confirmation**.

- **Capability discovery** — scans the runtime root for evolvable instruction files (CLAUDE.md / AGENTS.md / skills).
- **Session learning** — imports recent session logs (JSONL) as optimization *evidence*.
- **Proposals** — each proposal carries reason, source-session evidence, risk, confidence; filterable by status (`not_applied`, `applied`, …).
- **Cloud gene library** — cross-model/cross-agent big-data knowledge base that steers proposals.
- **Controlled apply** — unified diff preview; writes only after explicit confirmation; optional per-capability Auto Apply. Appended changes are wrapped in `<!-- evolvor:chg_<id> -->` marker blocks (delete block to undo; replacement-style changes have no marker — restore from the dry-run diff).
- **Billing** — token consumption converted to AFP deduction; no extra service fee.

## Officially Supported Runtimes (Kilo is NOT one)

| Runtime | Connector | Evolvable files |
|---|---|---|
| Claude Code | `claude_code` | project `CLAUDE.md`, `CLAUDE.local.md`, user `~/.claude/CLAUDE.md` |
| OpenClaw | `openclaw` | `AGENTS.md`, `SOUL.md`, `IDENTITY.md`, `USER.md`, `TOOLS.md`, `BOOTSTRAP.md`, `HEARTBEAT.md`, `MEMORY.md`, `skills/` |
| TRAE | `trae` | project-level `AGENTS.md` |

## Installer Facts (from `install.sh`, fetched 2026-08-19)

Source: `https://ark-self-evolve.tos-cn-beijing.volces.com/evolve_skill/latest/install.sh` (downloads `evolve_skill.tar.gz` bundle with `cli/`, `shared/`, per-runtime manifests).

- Backend: `https://prompt-pilot.cn-beijing.volces.com/case-platform` (baked-in default; env var `EVOLVE_BASE_URL`).
- Auth: **Ark Agent Plan exclusive API key only**, sent as `Authorization: Bearer`; identity is derived from the key (no account ID / username needed). Env var `EVOLVE_API_KEY` (falls back to `ARK_API_KEY`).
- CLI install: `pip install ./cli` → callable as `python3 -m evolve_cli` or `evolve` on PATH.
- CLI state is sharded **per connector**: `~/.evolve/<connector>/`.
- Env file written by installer: `~/.evolve-skill.env` (chmod 600).
- Skill install targets per runtime:
  - `claude_code` → `~/.claude/skills/evolve-setup/` (`SKILL.md` + `shared/`)
  - `openclaw` → `~/.openclaw/workspace/skills/evolve-setup/` (`SKILL.toml` + `SKILL.md` + `shared/`)
  - `trae` → `<project>/.trae/skills/evolve-setup/` **and** `<project>/.agents/skills/evolve-setup/`
- `evolve init --connector <c> --runtime-root <dir> --base-url <url> [--agent-id] [--api-key]` registers the agent; `evolve status` shows `capability_synced: true` when initialized.
- Useful env overrides: `EVOLVE_NONINTERACTIVE=1`, `EVOLVE_SKIP_INIT=1`, `EVOLVE_RUNTIME_ROOT`, `EVOLVE_AGENT_ID`.

## Kilo CLI Mapping (this repo)

- **Skills**: Kilo scans `.kilo/skills/*/SKILL.md` and `.kilocode/skills/*/SKILL.md` (project), plus global `~/.kilocode/skills/` (`packages/opencode/src/kilocode/paths.ts`, `src/kilocode/docs/migration.md`). SKILL.md format is the same frontmatter style as opencode/Claude skills.
- **Instruction files**: Kilo's canonical runtime instruction file is `AGENTS.md` (project + repo docs), same target as the **TRAE connector**.
- **Sessions**: stored in SQLite (`~/.local/share/kilo/kilo.db`, `opencode-<branch>.db`), **not** JSONL files — see Risks.

## Local Environment (verified 2026-08-19)

- Python 3.10.12, pip 26.1.1 ✅ (requirement: ≥3.9, pip ≥23 for PEP 621).
- Ark Agent Plan exclusive key already configured in `~/.config/kilo/opencode.json` (provider + indexing, base URL `/api/plan/v3`) — reuse it for `EVOLVE_API_KEY`. **Do not copy the key into this note or any repo file.**
- Harness (Agent 进化抵扣开关) already enabled in the Agent Plan console (user-confirmed).
- No `~/.kilocode/skills/` or `~/.claude/skills/` exists yet.

## Risks / Open Questions

1. **Session-log format gap** — Evolve's session import reads connector-specific JSONL logs; Kilo stores sessions in SQLite. Expect `evolve import` to find nothing unless we bridge: export Kilo sessions to JSONL (Kilo has session export machinery — `session-export.db`, export command) into a directory the chosen connector scans. *Investigate where the `trae` connector looks for logs before relying on session learning; until bridged, proposals will lean on the cloud gene library only.*
2. **Connector choice** — `trae` (project `AGENTS.md`) is the closest semantic match for Kilo; `openclaw` covers more file types but targets a different directory layout. Decide per project after inspecting the bundle's connector code (`cli/src/evolve_cli/`).
3. **Capability binding is per runtime-root** — each project must be initialized separately (`evolve init --runtime-root <project>`), or use a global root for user-level `AGENTS.md`.
4. **No official rollback command** — rely on `evolvor:chg_*` marker blocks and `apply --dry-run` previews; git-tracked AGENTS.md files give us real rollback.
5. **Key scope** — docs require the Agent Plan *exclusive* key (ours is), not the unified Ark key.
