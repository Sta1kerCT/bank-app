"""Tests for monitoring metrics."""
import pytest
from unittest.mock import Mock, AsyncMock, MagicMock

from app.monitoring.metrics import (
    init_metrics,
    metrics_endpoint,
    PrometheusMiddleware,
)
from fastapi import Request


def test_init_metrics():
    init_metrics()


def test_metrics_endpoint():
    request = Mock(spec=Request)
    response = metrics_endpoint(request)
    assert response.status_code == 200
    assert "text/plain" in response.media_type
    body = getattr(response, "body", getattr(response, "content", b""))
    assert len(body) > 0
    assert b"#" in body or b"http" in body


@pytest.mark.asyncio
async def test_prometheus_middleware_passes_non_http():
    app = AsyncMock()
    middleware = PrometheusMiddleware(app)
    scope = {"type": "lifespan"}
    receive = AsyncMock()
    send = AsyncMock()

    await middleware(scope, receive, send)
    app.assert_called_once_with(scope, receive, send)


@pytest.mark.asyncio
async def test_prometheus_middleware_records_http():
    app = AsyncMock()

    async def app_call(scope, receive, send):
        await send({"type": "http.response.start", "status": 200})
        await send({"type": "http.response.body", "body": b"ok"})

    app.side_effect = app_call
    middleware = PrometheusMiddleware(app)
    scope = {"type": "http", "method": "GET", "path": "/test"}
    receive = AsyncMock()
    send = AsyncMock()

    await middleware(scope, receive, send)
    assert send.call_count >= 2
    call_args = send.call_args_list[0][0][0]
    assert call_args.get("type") == "http.response.start"
    assert call_args.get("status") == 200
