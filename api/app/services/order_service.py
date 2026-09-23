from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.core.order_status import OrderStatus, can_transition, is_payment_expired
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.models.user import User
from app.repositories import order_repo, product_repo
from app.schemas.order import OrderCreate, OrderItemCreate, OrderItemUpdate


async def list_orders(
    db: AsyncSession, current_user: User, status: str | None = None
) -> list[Order]:
    user_id = None if current_user.role == "admin" else current_user.id
    orders = await order_repo.list_orders(db, user_id=user_id)
    for order in orders:
        _expire_if_needed(order)
    await db.flush()
    if status:
        orders = [o for o in orders if o.status == status]
    return orders


async def get_order(db: AsyncSession, order_id: int, current_user: User) -> Order:
    order = await _get_order_or_404(db, order_id)
    _check_access(order, current_user)
    _expire_if_needed(order)
    await db.flush()
    return order


async def create_order(
    db: AsyncSession, body: OrderCreate, current_user: User
) -> Order:
    order = Order(
        user_id=current_user.id,
        status=OrderStatus.PENDING.value,
        shipping_address=body.shipping_address,
        total_cents=0,
        created_at=_now(),
    )
    for line in body.items:
        product = await _get_available_product(db, line.product_id)
        _take_from_stock(product, line.quantity)
        order.items.append(
            OrderItem(
                product=product,
                quantity=line.quantity,
                unit_price_cents=product.price_cents,
            )
        )
    _recalculate_total(order)
    await order_repo.add(db, order)
    return await _reload(db, order.id)


async def pay_order(db: AsyncSession, order_id: int, current_user: User) -> Order:
    order = await _get_order_or_404(db, order_id)
    _check_access(order, current_user, owner_only=True)
    if is_payment_expired(order.status, order.created_at):
        raise AppError(
            "payment_expired", "Rok za plaćanje je istekao, narudžba je otkazana", 409
        )
    _transition(order, OrderStatus.PAID)
    order.paid_at = _now()
    await db.flush()
    return await _reload(db, order.id)


async def cancel_order(db: AsyncSession, order_id: int, current_user: User) -> Order:
    order = await _get_order_or_404(db, order_id)
    _check_access(order, current_user)
    _expire_if_needed(order)
    _transition(order, OrderStatus.CANCELLED)
    _restore_stock(order)
    await db.flush()
    return await _reload(db, order.id)


async def ship_order(db: AsyncSession, order_id: int) -> Order:
    order = await _get_order_or_404(db, order_id)
    _transition(order, OrderStatus.SHIPPED)
    await db.flush()
    return await _reload(db, order.id)


async def deliver_order(db: AsyncSession, order_id: int) -> Order:
    order = await _get_order_or_404(db, order_id)
    _transition(order, OrderStatus.DELIVERED)
    await db.flush()
    return await _reload(db, order.id)


async def add_item(
    db: AsyncSession, order_id: int, body: OrderItemCreate, current_user: User
) -> Order:
    order = await _get_editable_order(db, order_id, current_user)
    if any(i.product_id == body.product_id for i in order.items):
        raise AppError(
            "duplicate", "Proizvod je već u narudžbi, promijeni količinu", 409
        )
    product = await _get_available_product(db, body.product_id)
    _take_from_stock(product, body.quantity)
    order.items.append(
        OrderItem(
            product=product,
            quantity=body.quantity,
            unit_price_cents=product.price_cents,
        )
    )
    _recalculate_total(order)
    await db.flush()
    return await _reload(db, order.id)


async def update_item(
    db: AsyncSession,
    order_id: int,
    item_id: int,
    body: OrderItemUpdate,
    current_user: User,
) -> Order:
    order = await _get_editable_order(db, order_id, current_user)
    item = _find_item(order, item_id)
    product = await product_repo.get_by_id(db, item.product_id, for_update=True)
    assert product is not None

    delta = body.quantity - item.quantity
    if delta > 0:
        _take_from_stock(product, delta)
    else:
        product.stock -= delta
    item.quantity = body.quantity
    _recalculate_total(order)
    await db.flush()
    return await _reload(db, order.id)


async def remove_item(
    db: AsyncSession, order_id: int, item_id: int, current_user: User
) -> None:
    order = await _get_editable_order(db, order_id, current_user)
    item = _find_item(order, item_id)
    if len(order.items) == 1:
        raise AppError(
            "last_item",
            "Narudžba mora imati barem jednu stavku. Umjesto toga je otkaži.",
            400,
        )
    item.product.stock += item.quantity
    order.items.remove(item)
    _recalculate_total(order)
    await db.flush()


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def _reload(db: AsyncSession, order_id: int) -> Order:
    order = await order_repo.get_by_id(db, order_id)
    assert order is not None
    return order


async def _get_order_or_404(db: AsyncSession, order_id: int) -> Order:
    order = await order_repo.get_by_id(db, order_id)
    if not order:
        raise AppError("not_found", "Narudžba nije pronađena", 404)
    return order


def _check_access(order: Order, user: User, *, owner_only: bool = False) -> None:
    is_owner = order.user_id == user.id
    if owner_only:
        if not is_owner:
            raise AppError("forbidden", "Samo vlasnik narudžbe može ovo napraviti", 403)
    elif not (is_owner or user.role == "admin"):
        raise AppError("forbidden", "Ne možete pristupiti tuđoj narudžbi", 403)


async def _get_editable_order(
    db: AsyncSession, order_id: int, user: User
) -> Order:
    order = await _get_order_or_404(db, order_id)
    _check_access(order, user, owner_only=True)
    _expire_if_needed(order)
    if order.status != OrderStatus.PENDING.value:
        raise AppError(
            "order_not_editable",
            "Stavke se mogu mijenjati samo dok narudžba čeka plaćanje",
            409,
        )
    return order


def _find_item(order: Order, item_id: int) -> OrderItem:
    for item in order.items:
        if item.id == item_id:
            return item
    raise AppError("not_found", "Stavka nije pronađena u ovoj narudžbi", 404)


async def _get_available_product(db: AsyncSession, product_id: int) -> Product:
    product = await product_repo.get_by_id(db, product_id, for_update=True)
    if not product or not product.is_active:
        raise AppError("not_found", f"Proizvod {product_id} nije pronađen", 404)
    return product


def _take_from_stock(product: Product, quantity: int) -> None:
    if product.stock < quantity:
        raise AppError(
            "insufficient_stock",
            f"Nedovoljno zalihe za '{product.name}' (dostupno: {product.stock})",
            400,
        )
    product.stock -= quantity


def _restore_stock(order: Order) -> None:
    for item in order.items:
        item.product.stock += item.quantity


def _recalculate_total(order: Order) -> None:
    order.total_cents = sum(i.quantity * i.unit_price_cents for i in order.items)


def _transition(order: Order, target: OrderStatus) -> None:
    if not can_transition(order.status, target):
        raise AppError(
            "invalid_transition",
            f"Narudžba sa statusom '{order.status}' ne može prijeći u '{target.value}'",
            409,
        )
    order.status = target.value


def _expire_if_needed(order: Order) -> None:
    if is_payment_expired(order.status, order.created_at):
        order.status = OrderStatus.CANCELLED.value
        _restore_stock(order)
