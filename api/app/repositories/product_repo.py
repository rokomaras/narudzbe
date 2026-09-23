# =============================================================
# product_repo.py — upiti za products
# =============================================================
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import OrderItem
from app.models.product import Product


async def get_by_id(
    db: AsyncSession, product_id: int, *, for_update: bool = False
) -> Product | None:
    """for_update=True -> SELECT ... FOR UPDATE (zaključa red do kraja transakcije).

    Bez toga bi dva kupca istovremeno mogla kupiti zadnji komad (race condition):
    oba pročitaju stock=1, oba ga smanje. S lockom drugi čeka prvog.
    populate_existing osigurava da pročitamo SVJEŽU vrijednost zalihe.
    (SQLite u testovima ignorira FOR UPDATE, PostgreSQL ga poštuje.)
    """
    stmt = select(Product).where(Product.id == product_id)
    if for_update:
        stmt = stmt.with_for_update().execution_options(populate_existing=True)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_by_name(db: AsyncSession, name: str) -> Product | None:
    result = await db.execute(select(Product).where(Product.name == name))
    return result.scalar_one_or_none()


async def list_all(db: AsyncSession, *, only_active: bool) -> list[Product]:
    stmt = select(Product).order_by(Product.name)
    if only_active:
        stmt = stmt.where(Product.is_active.is_(True))
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def add(db: AsyncSession, product: Product) -> Product:
    db.add(product)
    await db.flush()
    return product


async def delete(db: AsyncSession, product: Product) -> None:
    await db.delete(product)
    await db.flush()


async def count_order_items(db: AsyncSession, product_id: int) -> int:
    result = await db.execute(
        select(func.count()).select_from(OrderItem).where(OrderItem.product_id == product_id)
    )
    return result.scalar_one()
