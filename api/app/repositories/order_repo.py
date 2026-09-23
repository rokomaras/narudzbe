# =============================================================
# order_repo.py — upiti za orders (+ učitavanje stavki i korisnika)
# =============================================================
# populate_existing=True: uvijek pročitaj svježe stanje iz baze i
# osvježi objekte koje sesija već drži (bitno nakon izmjena stavki).
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order


async def get_by_id(db: AsyncSession, order_id: int) -> Order | None:
    stmt = (
        select(Order)
        .where(Order.id == order_id)
        .execution_options(populate_existing=True)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def list_orders(db: AsyncSession, *, user_id: int | None) -> list[Order]:
    """user_id=None -> sve narudžbe (admin); inače samo narudžbe tog korisnika."""
    stmt = (
        select(Order)
        .order_by(Order.created_at.desc(), Order.id.desc())
        .execution_options(populate_existing=True)
    )
    if user_id is not None:
        stmt = stmt.where(Order.user_id == user_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def add(db: AsyncSession, order: Order) -> Order:
    db.add(order)
    await db.flush()
    return order
