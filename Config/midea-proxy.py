#!/usr/bin/env python3
"""
Local reverse proxy for the Midea AIMP internal OpenAI-compatible API.

Kilo Code (and most other coding agents) cannot inject arbitrary HTTP headers,
but the Midea endpoint requires three headers:
  - Authorization: Bearer msk-xxxx
  - Aimp-Biz-Id: volcengine-glm-5.3
  - AIGC-USER: <your 4A account>

This proxy runs on 127.0.0.1 and adds those headers to every request, so you
can point Kilo at http://127.0.0.1:<port>/v1 with a dummy API key.
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import Response, StreamingResponse
import uvicorn

# ----- configuration from environment -----
MSK_API_KEY = os.environ.get("MIDEA_MSK_API_KEY", "")
AIMP_BIZ_ID = os.environ.get("MIDEA_AIMP_BIZ_ID", "volcengine-glm-5.3")
AIGC_USER = os.environ.get("MIDEA_AIGC_USER", "")
UPSTREAM_BASE = os.environ.get(
    "MIDEA_UPSTREAM_BASE",
    "https://aimpapi.midea.com/t-aigc/mip-chat-app/openai",
)
BIND_HOST = os.environ.get("MIDEA_PROXY_HOST", "127.0.0.1")
BIND_PORT = int(os.environ.get("MIDEA_PROXY_PORT", "8000"))
FORCE_MODEL = os.environ.get("MIDEA_FORCE_MODEL", "volcengine-glm-5.3")

REQUIRED_VARS = [("MIDEA_MSK_API_KEY", MSK_API_KEY), ("MIDEA_AIGC_USER", AIGC_USER)]


def _check_config() -> None:
    missing = [name for name, value in REQUIRED_VARS if not value]
    if missing:
        print("Missing required environment variables:", file=sys.stderr)
        for name in missing:
            print(f"  - {name}", file=sys.stderr)
        print("\nExample:", file=sys.stderr)
        print(
            "  export MIDEA_MSK_API_KEY='msk-...'\n"
            "  export MIDEA_AIGC_USER='your_4a_account'\n"
            "  python midea-proxy.py",
            file=sys.stderr,
        )
        sys.exit(1)


app = FastAPI(title="Midea AIMP Local Proxy")
client = httpx.AsyncClient(timeout=300, follow_redirects=False)


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"])
async def relay(path: str, request: Request) -> Response | StreamingResponse:
    """Relay every request to the upstream Midea API, injecting the required headers."""
    body = await request.body()

    # If the body is JSON and contains a model field, rewrite it to the Midea model.
    modified_body = body
    if body and FORCE_MODEL:
        try:
            payload: dict[str, Any] = json.loads(body)
            if "model" in payload:
                original_model = payload["model"]
                payload["model"] = FORCE_MODEL
                modified_body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                print(f"[midea-proxy] model override: {original_model} -> {FORCE_MODEL}")
        except (json.JSONDecodeError, UnicodeDecodeError):
            pass

    headers = {
        "Authorization": f"Bearer {MSK_API_KEY}",
        "Aimp-Biz-Id": AIMP_BIZ_ID,
        "AIGC-USER": AIGC_USER,
        "Content-Type": request.headers.get("Content-Type", "application/json"),
    }

    # Forward a few other safe headers if present.
    for h in ("Accept", "Accept-Encoding", "User-Agent"):
        if h in request.headers:
            headers[h] = request.headers[h]

    upstream_url = f"{UPSTREAM_BASE}/{path}"
    print(f"[midea-proxy] {request.method} {upstream_url}")

    upstream_resp = await client.request(
        method=request.method,
        url=upstream_url,
        headers=headers,
        content=modified_body,
        params=request.query_params,
    )

    response_headers = {
        k: v
        for k, v in upstream_resp.headers.items()
        if k.lower() not in {"content-encoding", "transfer-encoding", "connection"}
    }

    if upstream_resp.headers.get("content-type", "").startswith("text/event-stream"):
        return StreamingResponse(
            upstream_resp.aiter_raw(),
            status_code=upstream_resp.status_code,
            headers=response_headers,
        )

    return Response(
        content=upstream_resp.content,
        status_code=upstream_resp.status_code,
        headers=response_headers,
    )


if __name__ == "__main__":
    _check_config()
    print(f"[midea-proxy] starting on http://{BIND_HOST}:{BIND_PORT}/v1")
    print(f"[midea-proxy] upstream: {UPSTREAM_BASE}")
    print(f"[midea-proxy] Aimp-Biz-Id: {AIMP_BIZ_ID}")
    print(f"[midea-proxy] AIGC-USER: {AIGC_USER}")
    uvicorn.run(app, host=BIND_HOST, port=BIND_PORT)
