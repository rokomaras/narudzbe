# =============================================================
# conftest.py — zajednički fixtureovi za pytest
# =============================================================
# Testovi koriste SQLite u memoriji (bez Dockera). get_db se zamijeni
# testnom sesijom, a tablice se prije svakog testa kreiraju i poslije brišu.
from typing import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.core.deps import get_db
from app.core.security import hash_password
from app.main import app as fastapi_app
from app.models.product import Product
from app.models.user import User

engine_test = create_async_engine(
    "sqlite+aiosqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = async_sessionmaker(
    bind=engine_test, class_=AsyncSession, expire_on_commit=False
)


async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


fastapi_app.dependency_overrides[get_db] = _override_get_db


@pytest.fixture(autouse=True)
async def setup_database():
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        yield session


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def _make_user(db: AsyncSession, username: str, password: str, role: str,
                     active: bool = True) -> User:
    user = User(
        username=username,
        password_hash=hash_password(password),
        role=role,
        full_name=f"Test {username}",
        email=f"{username}@example.com",
        is_active=active,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest.fixture
async def admin_user(db) -> User:
    """username=testadmin, password=admin123"""
    return await _make_user(db, "testadmin", "admin123", "admin")


@pytest.fixture
async def customer(db) -> User:
    """username=kupac, password=kupac123"""
    return await _make_user(db, "kupac", "kupac123", "customer")


@pytest.fixture
async def other_customer(db) -> User:
    """Drugi kupac za ownership testove."""
    return await _make_user(db, "kupac2", "kupac2123", "customer")


@pytest.fixture
async def inactive_user(db) -> User:
    return await _make_user(db, "neaktivan", "pass123", "customer", active=False)


async def _make_product(db: AsyncSession, name: str, price: int, stock: int,
                        active: bool = True) -> Product:
    product = Product(name=name, description="opis", price_cents=price,
                      stock=stock, is_active=active)
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product


@pytest.fixture
async def product(db) -> Product:
    """Majica: 25,00 €, zaliha 10."""
    return await _make_product(db, "Majica", 2500, 10)


@pytest.fixture
async def product_b(db) -> Product:
    """Kapa: 15,00 €, zaliha 5."""
    return await _make_product(db, "Kapa", 1500, 5)


@pytest.fixture
async def inactive_product(db) -> Product:
    return await _make_product(db, "Povučeno", 999, 3, active=False)


async def auth_header(client: AsyncClient, username: str, password: str) -> dict:
    """Helper: login i vrati {"Authorization": "Bearer ..."}"""
    resp = await client.post("/auth/login", json={"username": username, "password": password})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}
