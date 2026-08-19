# Intermittent "Error fetching balance: Unknown certificate verification error … ({"error":"Unauthorized"})"

**Product:** Kilo Code CLI (local build)
**Source tree:** `/media/zoujd4/DATA1/Users/zoujd4/JDgentLAB/VibeCoder_Kilo/kilo-source`
**Observed in build:** `0.0.0-fix-qdrant-check-compatibility-202608190324`
**Date:** 2026-08-19
**Status:** 🟡 Diagnosed — environmental (proxy TLS interception) + benign token-refresh 401; no code fix required, cosmetic only.

---

## Symptom

From time to time, a running session shows:

```
Error fetching balance: warn: Unknown certificate verification error … https://api.kilo.ai/api/profile/balance ({"error":"Unauthorized","success":false})
```

Self-heals; balance display returns on a later refresh.

## Where it comes from

`packages/kilo-gateway/src/api/profile.ts:67` — `fetchBalance()` is deliberately best-effort:

- non-2xx response → `console.warn("Failed to fetch balance: <status>")`, returns `null`
- thrown fetch error → `console.warn("Error fetching balance:", error)`, returns `null`

Either way the only effect is a blank balance indicator. Sessions, models, and billing are unaffected.

## Diagnosis (two distinct failures bundled in one line)

### 1. TLS: "Unknown certificate verification error"

This string is **not in the repo** — it is the JS runtime's TLS layer rejecting the certificate presented for `api.kilo.ai`.

Direct probe on 2026-08-19 (no proxy env):

```
* Connected to api.kilo.ai (64.239.109.129) port 443
*  CAfile: /etc/ssl/certs/ca-certificates.crt
* SSL connection using TLSv1.3 / TLS_AES_128_GCM_SHA256
*  subject: CN=api.kilo.ai
*  issuer: C=US; O=Let's Encrypt; CN=YR2
*  SSL certificate verify ok.
< HTTP/2 401            ← expected without a token
```

The direct route is healthy. The intermittent TLS failures correlate with this machine's fake-ip proxy (198.18.x range), which earlier the same day TLS-blocked/unreachable: `registry.npmjs.org`, `cdn.sheetjs.com`, `plugins.gradle.org`, `packages.jetbrains.team` (while npmmirror/Aliyun/TUNA mirrors worked). When the route to `api.kilo.ai` flaps through an intercepting proxy node, the runtime cannot verify the presented cert → this error. When it goes direct, it works.

### 2. API: `({"error":"Unauthorized","success":false})`

A plain 401 from the Kilo API when the request **did** get through: the OAuth access token was stale at that moment — refresh boundary, or rotated by another client (mobile app, another instance, an earlier login). `getProfile()` (`packages/kilo-gateway/src/server/handlers.ts:67`) re-reads the auth store per call, so the next cycle uses the fresh token and the warning disappears.

Note: at the time of writing only one `kilo` process is running (the pre-fix zombie processes from deleted FUSE inodes are gone), so cross-process token races on this machine are no longer a contributor.

## Why "from times to times"

Proxy route instability (TLS half) + token refresh boundaries (401 half). Not a regression in the local build — the same best-effort warning exists upstream.

## Mitigations (no code change)

1. Proxy client (Clash etc.): add `api.kilo.ai` / `*.kilo.ai` to **DIRECT / bypass** rules.
2. If MITM proxying is intentional: `NODE_EXTRA_CA_CERTS=/path/to/proxy-ca.pem kilo`.
3. Persistent (not occasional) 401 → re-login once: `kilo auth login`.

## Optional code hardening (deferred)

Patch `fetchBalance` to retry once before warning, or demote the warning to debug-level, so transient flaps never surface in the UI. Not applied — kept verbatim with upstream to minimise merge surface.
