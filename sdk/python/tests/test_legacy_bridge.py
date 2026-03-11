from __future__ import annotations

import pathlib
import sys

import httpx
import pytest
from fastapi import FastAPI, HTTPException

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pinquark_connector_sdk.legacy import augment_legacy_fastapi_app


@pytest.mark.asyncio
async def test_legacy_bridge_adds_sdk_action_proxy(tmp_path: pathlib.Path) -> None:
    manifest = tmp_path / "connector.yaml"
    manifest.write_text(
        """
name: demo-legacy
category: other
version: 1.0.0
display_name: Demo Legacy
description: Demo
interface: other
action_routes:
  ping:
    method: POST
    path: /legacy/ping
""".strip(),
        encoding="utf-8",
    )

    app = FastAPI()

    @app.post("/legacy/ping")
    async def ping(payload: dict) -> dict:
        return {"pong": True, "payload": payload}

    augment_legacy_fastapi_app(app, manifest_path=manifest)

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/actions/ping", json={"hello": "world"})

    assert response.status_code == 200
    assert response.json() == {"pong": True, "payload": {"hello": "world"}}


@pytest.mark.asyncio
async def test_legacy_bridge_preserves_error_status(tmp_path: pathlib.Path) -> None:
    manifest = tmp_path / "connector.yaml"
    manifest.write_text(
        """
name: demo-legacy
category: other
version: 1.0.0
display_name: Demo Legacy
description: Demo
interface: other
action_routes:
  fail:
    method: POST
    path: /legacy/fail
""".strip(),
        encoding="utf-8",
    )

    app = FastAPI()

    @app.post("/legacy/fail")
    async def fail(_payload: dict) -> dict:
        raise HTTPException(status_code=422, detail="invalid")

    augment_legacy_fastapi_app(app, manifest_path=manifest)

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/actions/fail", json={"hello": "world"})

    assert response.status_code == 422
    assert response.json() == {"detail": "invalid"}
