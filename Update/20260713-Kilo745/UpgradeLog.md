# Kilo Code CLI Upgrade: 7.3.54 → 7.4.5

**Date:** 2026-07-13  
**Upstream version:** [`Kilo-Org/kilocode v7.4.5`](https://github.com/Kilo-Org/kilocode/releases/tag/v7.4.5)  
**Local fork branch:** `JiadaoZ22/kilocode:fix/qdrant-check-compatibility`  
**Installed binary version:** `public-7.4.5_private-0.0.0`

---

## Summary

Bumped the `kilo-source` submodule from upstream Kilo `7.3.54` to the latest public release `7.4.5`, merged it into the local `fix/qdrant-check-compatibility` branch, rebuilt the Linux x64 CLI binary, and replaced the installed `~/.npm-global/lib/node_modules/@kilocode/cli/bin/.kilo` binary.

Local Ark/Doubao indexing patches are preserved:

- Qdrant compatibility warning suppressed (`checkCompatibility: false`).
- Ark/Doubao embedding batches capped to provider limit (10 inputs/request).
- Query-instruction prefix applied only to queries (semantic search works with Doubao embeddings).
- `.kiloindexignore` global indexing-only ignore file supported.
- Embedder-aware batch sizing, concurrent compaction reduce, and glob directory pruning retained.

---

## Steps Performed

1. **Fetched upstream tags** in `kilo-source`.
2. **Merged** `v7.4.5` into the local `fix/qdrant-check-compatibility` branch.
3. **Resolved merge conflicts** in:
   - `packages/kilo-indexing/src/indexing/processors/scanner.ts`
   - `packages/kilo-indexing/src/indexing/service-factory.ts`
   - `packages/kilo-indexing/src/indexing/shared/load-ignore.ts`
   - `packages/opencode/src/kilocode/kilo-commands.tsx`
4. **Restored `.kiloindexignore` support** after upstream refactored `load-ignore.ts` to use a new `IgnoreMatcher` interface.
5. **Committed and pushed** the submodule branch.
6. **Updated the parent repo submodule pointer** and pushed `VibeCoder_Kilo/main`.
7. **Built** the binary:
   ```bash
   cd kilo-source
   bun run --cwd packages/opencode script/build.ts --single --skip-install
   ```
   Smoke tests passed:
   - `kilo --version` → `public-7.4.5_private-0.0.0`
   - `kilo --pure models anthropic` → models snapshot passed
8. **Installed** the new binary:
   ```bash
   cp kilo-source/packages/opencode/dist/@kilocode/cli-linux-x64/bin/kilo \
      ~/.npm-global/lib/node_modules/@kilocode/cli/bin/.kilo
   ```

---

## Verification

```bash
$ kilo --version
public-7.4.5_private-0.0.0
```

Both the wrapper `~/.npm-global/bin/kilo` and the underlying binary report the new version.

---

## Notes

- The old `kilo-source/packages/opencode/dist/` directory was locked by running `kilo` processes, so it was renamed to `dist.old.<timestamp>` to allow the build to proceed. Once those processes exit, that backup directory can be removed.
- Husky pre-push typechecks passed for all TypeScript packages. The JetBrains package check was skipped because the local JVM is 11 while Gradle 9 requires 17; no JetBrains code was modified.
- Documents updated in this repo:
  - `README.md` — current version banner and build-from-source note.
  - `Config/ReadMe.md` — fixed broken `Bugs/IDX/a_Solution.md` link.
  - `Bugs/Submodule-Worktree/README.md` and `Problem.md` — version range updated to ≤ 7.4.5.

---

## Rollback

If something breaks, the previous binary backups are in `~/.npm-global/lib/node_modules/@kilocode/cli/bin/`:

- `.kilo.backup`
- `.kilo.before-upstream-merge`
- `.kilo.before-efficiency-updates`
- `.kilo.before-compaction-fix`
- `.kilo.prev`

Restore with:

```bash
cp ~/.npm-global/lib/node_modules/@kilocode/cli/bin/.kilo.before-upstream-merge \
   ~/.npm-global/lib/node_modules/@kilocode/cli/bin/.kilo
```
