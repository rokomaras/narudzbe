# =============================================================
# orders.py — /orders i ugniježđene stavke /orders/{id}/items
# =============================================================
# Tko smije što (autorizacija po ROLI je ovdje, ownership je u servicu):
#   kupac : kreira narudžbu, mijenja stavke, plaća
#   admin : šalje (ship) i dostavlja (deliver)
#   oboje : lista, detalj i otkazivanje (ownership: kupac samo svoje)
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db, require_role
from app.core.order_status import OrderStatus
from app.models.user import User
from app.schemas.order import (
    OrderCreate,
    OrderItemCreate,
    OrderItemUpdate,
    OrderResponse,
)
from app.services import order_service

router = APIRouter()


@router.get("", response_model=list[OrderResponse])
async def list_orders(
    status: OrderStatus | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Admin: sve narudžbe. Kupac: samo svoje. Opcionalno ?status=paid"""
    return await order_service.list_orders(db, user, status.value if status else None)


@router.post("", response_model=OrderResponse, status_code=201)
async def create_order(
    body: OrderCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("customer")),
):
    return await order_service.create_order(db, body, user)


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await order_service.get_order(db, order_id, user)


# ---- stavke ----

@router.post("/{order_id}/items", response_model=OrderResponse, status_code=201)
async def add_item(
    order_id: int,
    body: OrderItemCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("customer")),
):
    return await order_service.add_item(db, order_id, body, user)


@router.patch("/{order_id}/items/{item_id}", response_model=OrderResponse)
async def update_item(
    order_id: int,
    item_id: int,
    body: OrderItemUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("customer")),
):
    return await order_service.update_item(db, order_id, item_id, body, user)


@router.delete("/{order_id}/items/{item_id}", status_code=204)
async def remove_item(
    order_id: int,
    item_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("customer")),
):
    await order_service.remove_item(db, order_id, item_id, user)


# ---- workflow akcije (prijelazi statusa) ----

@router.post("/{order_id}/pay", response_model=OrderResponse)
async def pay_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("customer")),
):
    return await order_service.pay_order(db, order_id, user)


@router.post("/{order_id}/cancel", response_model=OrderResponse)
async def cancel_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await order_service.cancel_order(db, order_id, user)


@router.post("/{order_id}/ship", response_model=OrderResponse)
async def ship_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_role("admin")),
):
    return await order_service.ship_order(db, order_id)


@router.post("/{order_id}/deliver", response_model=OrderResponse)
async def deliver_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_role("admin")),
):
    return await order_service.deliver_order(db, order_id)
