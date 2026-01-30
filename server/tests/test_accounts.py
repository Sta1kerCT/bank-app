import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.models.database import Base, get_db
import asyncio

TEST_DATABASE_URL = "postgresql+asyncpg://test_user:test_password@localhost:5432/test_db"

engine = create_async_engine(TEST_DATABASE_URL, echo=True)
TestingSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
async def setup_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.mark.asyncio
async def test_create_account():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/accounts/",
            json={"owner_name": "John Doe", "initial_balance": 1000.0}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["owner_name"] == "John Doe"
        assert data["balance"] == 1000.0
        assert "account_number" in data


@pytest.mark.asyncio
async def test_get_account():
    async with AsyncClient(app=app, base_url="http://test") as client:
        create_response = await client.post(
            "/accounts/",
            json={"owner_name": "Jane Doe", "initial_balance": 500.0}
        )
        account_number = create_response.json()["account_number"]

        response = await client.get(f"/accounts/{account_number}")
        assert response.status_code == 200
        data = response.json()
        assert data["account_number"] == account_number
        assert data["owner_name"] == "Jane Doe"


@pytest.mark.asyncio
async def test_list_accounts():
    async with AsyncClient(app=app, base_url="http://test") as client:
        for i in range(3):
            await client.post(
                "/accounts/",
                json={"owner_name": f"User {i}", "initial_balance": 100.0 * i}
            )

        response = await client.get("/accounts/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3