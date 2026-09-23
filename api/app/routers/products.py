from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db, require_role
from app.models.user import User
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate
from app.services import product_service

router = APIRouter()


@router.get("", response_model=list[ProductResponse])
async def list_products(
    db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    return await product_service.list_products(db, user)


@router.post("", response_model=ProductResponse, status_code=201)
async def create_product(
    body: ProductCreate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_role("admin")),
):
    return await product_service.create_product(db, body)


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await product_service.get_product(db, product_id, user)


@router.patch("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    body: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_role("admin")),
):
    return await product_service.update_product(db, product_id, body)


@router.delete("/{product_id}", status_code=204)
async def delete_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_role("admin")),
):
    await product_service.delete_product(db, product_id)
