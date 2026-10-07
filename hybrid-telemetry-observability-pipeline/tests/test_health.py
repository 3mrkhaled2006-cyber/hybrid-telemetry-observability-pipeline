"""
Unit and integration tests for Health and Readiness probes.
Tests HTTP status codes for Kubernetes probe scenarios.
"""

import pytest
from aiohttp.test_utils import TestClient, TestServer
from src.health import HealthServer


@pytest.mark.asyncio
async def test_healthz_liveness_endpoint():
    server = HealthServer(is_ready_callback=lambda: True)
    test_server = TestServer(server.app)
    client = TestClient(test_server)
    await client.start_server()

    try:
        resp = await client.get("/healthz")
        assert resp.status == 200
        data = await resp.json()
        assert data["status"] == "UP"
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_readyz_readiness_endpoint():
    ready_state = False
    server = HealthServer(is_ready_callback=lambda: ready_state)
    test_server = TestServer(server.app)
    client = TestClient(test_server)
    await client.start_server()

    try:
        # Initially not ready
        resp = await client.get("/readyz")
        assert resp.status == 503
        data = await resp.json()
        assert data["status"] == "NOT_READY"

        # Now ready
        ready_state = True
        resp_ready = await client.get("/readyz")
        assert resp_ready.status == 200
        data_ready = await resp_ready.json()
        assert data_ready["status"] == "READY"
    finally:
        await client.close()
