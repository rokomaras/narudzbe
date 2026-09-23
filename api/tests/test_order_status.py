# Jedinični testovi state machinea (bez baze i HTTP-a).
from datetime import datetime, timedelta, timezone

import pytest

from app.core.order_status import OrderStatus, can_transition, is_payment_expired


@pytest.mark.parametrize(
    "current,target",
    [
        ("pending", OrderStatus.PAID),
        ("pending", OrderStatus.CANCELLED),
        ("paid", OrderStatus.SHIPPED),
        ("paid", OrderStatus.CANCELLED),
        ("shipped", OrderStatus.DELIVERED),
    ],
)
def test_allowed_transitions(current, target):
    assert can_transition(current, target)


@pytest.mark.parametrize(
    "current,target",
    [
        ("pending", OrderStatus.SHIPPED),      # ne možeš poslati neplaćeno
        ("pending", OrderStatus.DELIVERED),
        ("paid", OrderStatus.PENDING),
        ("shipped", OrderStatus.CANCELLED),    # poslano se ne otkazuje
        ("delivered", OrderStatus.CANCELLED),
        ("cancelled", OrderStatus.PAID),       # otkazano je završno stanje
    ],
)
def test_forbidden_transitions(current, target):
    assert not can_transition(current, target)


def test_payment_expiry():
    now = datetime(2026, 1, 2, 12, 0, tzinfo=timezone.utc)
    fresh = now - timedelta(hours=23)
    old = now - timedelta(hours=25)
    assert not is_payment_expired("pending", fresh, now)
    assert is_payment_expired("pending", old, now)
    # samo 'pending' može isteći
    assert not is_payment_expired("paid", old, now)


def test_payment_expiry_handles_naive_datetime():
    now = datetime(2026, 1, 2, 12, 0, tzinfo=timezone.utc)
    naive_old = datetime(2026, 1, 1, 10, 0)  # bez tzinfo (SQLite)
    assert is_payment_expired("pending", naive_old, now)
