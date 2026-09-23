# =============================================================
# order_status.py — konačni automat (state machine) narudžbe
# =============================================================
#   pending ──pay──▶ paid ──ship──▶ shipped ──deliver──▶ delivered
#      │               │
#      └───cancel──────┴──▶ cancelled
#
# Ovo je JEDINO mjesto koje zna koji su prijelazi dozvoljeni.
# Service samo pita: can_transition(stari, novi)?

from datetime import datetime, timedelta, timezone
from enum import Enum


class OrderStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


# Iz statusa (ključ) smije se prijeći u bilo koji status iz skupa (vrijednost).
ALLOWED_TRANSITIONS: dict[OrderStatus, set[OrderStatus]] = {
    OrderStatus.PENDING: {OrderStatus.PAID, OrderStatus.CANCELLED},
    OrderStatus.PAID: {OrderStatus.SHIPPED, OrderStatus.CANCELLED},
    OrderStatus.SHIPPED: {OrderStatus.DELIVERED},
    OrderStatus.DELIVERED: set(),
    OrderStatus.CANCELLED: set(),
}

# Narudžba koja čeka plaćanje dulje od ovoga automatski se otkazuje.
PAYMENT_WINDOW = timedelta(hours=24)


def can_transition(current: str, target: OrderStatus) -> bool:
    return target in ALLOWED_TRANSITIONS[OrderStatus(current)]


def is_payment_expired(
    status: str, created_at: datetime, now: datetime | None = None
) -> bool:
    """True ako je narudžba još 'pending', a rok za plaćanje je prošao."""
    if status != OrderStatus.PENDING.value:
        return False
    now = now or datetime.now(timezone.utc)
    # SQLite (testovi) ne čuva vremensku zonu, pa naive vrijeme tretiramo kao UTC
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    return now > created_at + PAYMENT_WINDOW
