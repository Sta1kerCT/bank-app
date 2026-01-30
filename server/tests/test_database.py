"""Tests for database module: init_db, get_db."""
import pytest
from unittest.mock import patch

from app.models.database import init_db, get_db
from tests.conftest import engine as test_engine, TestingSessionLocal


@pytest.mark.asyncio
async def test_init_db():
    with patch("app.models.database.engine", test_engine):
        await init_db()


@pytest.mark.asyncio
async def test_get_db():
    with patch("app.models.database.engine", test_engine), patch(
        "app.models.database.AsyncSessionLocal", TestingSessionLocal
    ):
        sessions = []
        async for session in get_db():
            sessions.append(session)
            assert session is not None
        assert len(sessions) == 1
