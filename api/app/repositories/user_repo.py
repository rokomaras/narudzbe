# =============================================================
# user_repo.py — SVI upiti za tablicu users (samo SQL, nikakva logika)
# =============================================================
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


async def get_by_username(db: AsyncSession, username: str) -> User | None:
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def get_by_id(db: AsyncSession, user_id: int) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def add(db: AsyncSession, user: User) -> User:
    db.add(user)
    await db.flush()  # flush = pošalji INSERT (dobij id), ali još bez commita
    return user
