# =============================================================
# product_service.py — poslovna logika kataloga
# =============================================================
# Admin vidi sve proizvode, kupac samo aktivne.
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.models.product import Product
from app.models.user import User
from app.repositories import product_repo
from app.schemas.product import ProductCreate, ProductUpdate


async def list_products(db: AsyncSession, current_user: User) -> list[Product]:
    return await product_repo.list_all(db, only_active=current_user.role != "admin")


async def get_product(db: AsyncSession, product_id: int, current_user: User) -> Product:
    product = await product_repo.get_by_id(db, product_id)
    # Neaktivan proizvod kupcu "ne postoji" (404), admin ga vidi.
    if not product or (not product.is_active and current_user.role != "admin"):
        raise AppError("not_found", "Proizvod nije pronađen", 404)
    return product


async def create_product(db: AsyncSession, body: ProductCreate) -> Product:
    if await product_repo.get_by_name(db, body.name):
        raise AppError("duplicate", "Proizvod s tim imenom već postoji", 409)
    product = Product(**body.model_dump())
    return await product_repo.add(db, product)


async def update_product(
    db: AsyncSession, product_id: int, body: ProductUpdate
) -> Product:
    product = await product_repo.get_by_id(db, product_id)
    if not product:
        raise AppError("not_found", "Proizvod nije pronađen", 404)

    changes = body.model_dump(exclude_none=True)
    new_name = changes.get("name")
    if new_name and new_name != product.name:
        other = await product_repo.get_by_name(db, new_name)
        if other:
            raise AppError("duplicate", "Proizvod s tim imenom već postoji", 409)

    for field, value in changes.items():
        setattr(product, field, value)
    await db.flush()
    return product


async def delete_product(db: AsyncSession, product_id: int) -> None:
    """Proizvod koji se već pojavljuje u narudžbama ne smije se obrisati
    (pokvarilo bi povijest). Umjesto toga admin ga deaktivira (is_active=false)."""
    product = await product_repo.get_by_id(db, product_id)
    if not product:
        raise AppError("not_found", "Proizvod nije pronađen", 404)
    if await product_repo.count_order_items(db, product_id) > 0:
        raise AppError(
            "product_in_use",
            "Proizvod je u narudžbama i ne može se obrisati. Deaktiviraj ga.",
            409,
        )
    await product_repo.delete(db, product)
