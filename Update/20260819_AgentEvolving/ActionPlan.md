# Action Plan — Enable Ark Agent Evolve in Kilo Code CLI

**Date:** 2026-08-19
**Companion:** [`WorkingNote.md`](./WorkingNote.md) (research + risks)
**Status:** Planned — not yet executed

---

## Goal

Wire Volcano Ark's Agent Evolve into the local Kilo Code CLI so it can learn from sessions and propose confirmed improvements to `AGENTS.md` / skills, using the existing Ark Agent Plan key and the already-enabled harness switch.

## Prerequisites (already satisfied)

- [x] Ark Agent Plan exclusive API key — present in `~/.config/kilo/opencode.json` (never copy it into repo files; reference it via env at runtime)
- [x] Agent 进化 deduction switch enabled in Agent Plan console (harness)
- [x] Python 3.10.12 + pip 26.1.1
- [x] Outbound HTTPS access to `prompt-pilot.cn-beijing.volces.com`

## Step 1 — Download and inspect the bundle (no install yet)

```bash
mkdir -p /tmp/evolve-skill && cd /tmp/evolve-skill
curl -fsSL "https://ark-self-evolve.tos-cn-beijing.volces.com/evolve_skill/latest/evolve_skill.tar.gz" -o bundle.tgz
tar -xzf bundle.tgz
```

Inspect before installing anything:

- `cli/src/evolve_cli/` — connector code: confirm where the `trae` (and `openclaw`) connectors read session logs from, and which files each marks evolvable.
- `trae/SKILL.md`, `openclaw/SKILL.md`, `shared/` — the agent-facing lifecycle instructions we will adapt for Kilo.

**Decision point:** pick connector (`trae` expected — Kilo's evolvable surface is `AGENTS.md`, same as TRAE). Record the choice + evidence in `WorkingNote.md`.

## Step 2 — Install the Evolve CLI in an isolated env

Per repo policy, no global pip installs — use a dedicated venv:

```bash
python3 -m venv ~/.local/share/evolve-venv
~/.local/share/evolve-venv/bin/pip install --upgrade pip setuptools
~/.local/share/evolve-venv/bin/pip install /tmp/evolve-skill/evolve_skill/cli
~/.local/share/evolve-venv/bin/python -m evolve_cli --help   # sanity check
```

Symlink for convenience (optional): `ln -s ~/.local/share/evolve-venv/bin/evolve ~/.npm-global/bin/evolve` if that bin dir is on PATH — otherwise call `~/.local/share/evolve-venv/bin/python -m evolve_cli`.

## Step 3 — Credentials via env file (reuse existing key, no new secrets on disk)

```bash
install -m 600 /dev/null ~/.evolve-skill.env
cat >> ~/.evolve-skill.env <<'EOF'
export EVOLVE_BASE_URL="https://prompt-pilot.cn-beijing.volces.com/case-platform"
# Reuse the Agent Plan key already configured for Kilo:
export EVOLVE_API_KEY="$(python3 -c "import json;print(json.load(open('$HOME/.config/kilo/opencode.json'))['provider']['ark']['options']['apiKey'])")"
EOF
```

(The subshell reads the key straight out of the existing Kilo config at source time — nothing new is hard-coded.) Add `source ~/.evolve-skill.env` to `~/.bashrc`.

## Step 4 — Install the skill into Kilo's skill paths

Global (all projects), Kilo convention:

```bash
mkdir -p ~/.kilocode/skills/evolve-setup
cp /tmp/evolve-skill/evolve_skill/trae/SKILL.md ~/.kilocode/skills/evolve-setup/SKILL.md
cp -R /tmp/evolve-skill/evolve_skill/shared ~/.kilocode/skills/evolve-setup/shared
```

Adapt `SKILL.md` minimally for Kilo (record edits in this folder):

- Point CLI invocations at the venv (`~/.local/share/evolve-venv/bin/python -m evolve_cli`).
- State the connector (`trae`) and that the runtime root = current project root.
- Keep the confirmation-before-apply semantics.

## Step 5 — Initialize per project

For each project that should evolve (start with this repo):

```bash
source ~/.evolve-skill.env
cd /media/zoujd4/DATA1/Users/zoujd4/JDgentLAB/VibeCoder_Kilo
~/.local/share/evolve-venv/bin/python -m evolve_cli init --connector trae --runtime-root "$PWD"
~/.local/share/evolve-venv/bin/python -m evolve_cli status   # expect capability_synced: true
```

## Step 6 — First learning cycle (from inside Kilo)

```bash
kilo   # in the initialized project
```

Then in the TUI:

- `set me up for evolve` — should report already initialized
- `learn from my recent sessions` — **watch for the session-log gap (Risk 1)**: if import finds nothing, bridge by exporting Kilo sessions to the JSONL location the connector scans
- `what suggestions are there?` → `show me the diff` → `apply this proposal` only after reviewing

## Step 7 — Verify and document

- [ ] `evolve status` shows `capability_synced: true`
- [ ] At least one session import attempted; record whether Kilo sessions were visible to the connector
- [ ] First proposal reviewed via `--dry-run` diff before applying
- [ ] Applied changes confirmed to carry `evolvor:chg_*` marker blocks
- [ ] Append results + any SKILL.md adaptations to `WorkingNote.md`; if a Kilo-side patch was needed (e.g. session JSONL export bridge), record it under `Bugs/` or a new `Update/` entry

## Rollback / Uninstall

- Skill: `rm -rf ~/.kilocode/skills/evolve-setup`
- CLI: `rm -rf ~/.local/share/evolve-venv ~/.evolve ~/.evolve-skill.env` (remove the `source` line from `~/.bashrc`)
- Applied proposals: delete `evolvor:chg_<id>` marker blocks, or `git checkout` the affected `AGENTS.md` (all target projects are git repos)

## Notes

- Billing is token-based (AFP deduction) — session imports on large logs cost tokens; start with `evolve import --limit 5`.
- Do **not** enable Auto Apply until several proposals have been manually reviewed.
- Kilo is not an officially supported Evolve runtime; if Ark ships a native Kilo connector later, migrate to it and retire this shim.
