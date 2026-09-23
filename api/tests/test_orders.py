# =============================================================
# Testovi narudžbi: ownership, zaliha, state machine, rok plaćanja, stavke
# =============================================================
from datetime import datetime, timedelta, timezone

from app.models.order import Order
from tests.conftest import auth_header

ADDRESS = "Ulica kralja Zvonimira 1, Zadar"


def order_body(*lines):
    """lines = (product, quantity) parovi"""
    return {
        "shipping_address": ADDRESS,
        "items": [{"product_id": p.id, "quantity": q} for p, q in lines],
    }


async def login(client, who):
    creds = {
        "customer": ("kupac", "kupac123"),
        "other": ("kupac2", "kupac2123"),
        "admin": ("testadmin", "admin123"),
    }[who]
    return await auth_header(client, *creds)


async def stock_of(client, headers, product):
    resp = await client.get(f"/products/{product.id}", headers=headers)
    return resp.json()["stock"]


async def make_order(client, headers, *lines):
    resp = await client.post("/orders", json=order_body(*lines), headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()


# ------------------------- kreiranje -------------------------

async def test_create_order_calculates_total_and_reduces_stock(client, customer, product, product_b):
    h = await login(client, "customer")
    order = await make_order(client, h, (product, 2), (product_b, 1))
    assert order["status"] == "pending"
    assert order["total_cents"] == 2 * 2500 + 1500
    assert order["customer_username"] == "kupac"
    assert len(order["items"]) == 2
    assert await stock_of(client, h, product) == 8
    assert await stock_of(client, h, product_b) == 4


async def test_order_keeps_price_copy_when_product_price_changes(client, customer, admin_user, product):
    h = await login(client, "customer")
    order = await make_order(client, h, (product, 1))
    admin = await login(client, "admin")
    await client.patch(f"/products/{product.id}", json={"price_cents": 9999}, headers=admin)
    resp = await client.get(f"/orders/{order['id']}", headers=h)
    assert resp.json()["items"][0]["unit_price_cents"] == 2500
    assert resp.json()["total_cents"] == 2500


async def test_order_more_than_stock_is_400_and_stock_unchanged(client, customer, product):
    h = await login(client, "customer")
    resp = await client.post("/orders", json=order_body((product, 11)), headers=h)
    assert resp.status_code == 400
    assert resp.json()["code"] == "insufficient_stock"
    assert await stock_of(client, h, product) == 10
    assert (await client.get("/orders", headers=h)).json() == []


async def test_failed_order_rolls_back_everything(client, customer, product, product_b):
    """Prva stavka prolazi, druga puca -> zaliha prve mora ostati netaknuta (transakcija)."""
    h = await login(client, "customer")
    resp = await client.post("/orders", json=order_body((product, 3), (product_b, 99)), headers=h)
    assert resp.status_code == 400
    assert await stock_of(client, h, product) == 10


async def test_admin_cannot_create_order(client, admin_user, product):
    h = await login(client, "admin")
    resp = await client.post("/orders", json=order_body((product, 1)), headers=h)
    assert resp.status_code == 403


async def test_order_requires_login(client, product):
    resp = await client.post("/orders", json=order_body((product, 1)))
    assert resp.status_code == 401


async def test_order_unknown_or_inactive_product_is_404(client, customer, inactive_product):
    h = await login(client, "customer")
    body = {"shipping_address": ADDRESS, "items": [{"product_id": 9999, "quantity": 1}]}
    assert (await client.post("/orders", json=body, headers=h)).status_code == 404
    resp = await client.post("/orders", json=order_body((inactive_product, 1)), headers=h)
    assert resp.status_code == 404


async def test_order_validation(client, customer, product):
    h = await login(client, "customer")
    # prazna lista stavki
    r1 = await client.post("/orders", json={"shipping_address": ADDRESS, "items": []}, headers=h)
    assert r1.status_code == 422
    # količina 0 i prekratka adresa
    r2 = await client.post(
        "/orders",
        json={"shipping_address": "abc", "items": [{"product_id": product.id, "quantity": 0}]},
        headers=h,
    )
    assert r2.status_code == 422
    # isti proizvod dvaput
    r3 = await client.post("/orders", json=order_body((product, 1), (product, 2)), headers=h)
    assert r3.status_code == 422


# ------------------------- ownership -------------------------

async def test_customer_sees_only_own_orders_admin_sees_all(client, customer, other_customer, admin_user, product):
    h1, h2, ha = await login(client, "customer"), await login(client, "other"), await login(client, "admin")
    await make_order(client, h1, (product, 1))
    await make_order(client, h2, (product, 1))

    mine = (await client.get("/orders", headers=h1)).json()
    assert len(mine) == 1 and mine[0]["customer_username"] == "kupac"
    assert len((await client.get("/orders", headers=ha)).json()) == 2


async def test_customer_cannot_view_someone_elses_order(client, customer, other_customer, product):
    h1, h2 = await login(client, "customer"), await login(client, "other")
    order = await make_order(client, h1, (product, 1))
    resp = await client.get(f"/orders/{order['id']}", headers=h2)
    assert resp.status_code == 403


async def test_admin_can_view_any_order(client, customer, admin_user, product):
    h, ha = await login(client, "customer"), await login(client, "admin")
    order = await make_order(client, h, (product, 1))
    assert (await client.get(f"/orders/{order['id']}", headers=ha)).status_code == 200


async def test_missing_order_is_404(client, customer):
    h = await login(client, "customer")
    assert (await client.get("/orders/9999", headers=h)).status_code == 404


async def test_customer_cannot_pay_or_cancel_someone_elses_order(client, customer, other_customer, product):
    h1, h2 = await login(client, "customer"), await login(client, "other")
    order = await make_order(client, h1, (product, 1))
    assert (await client.post(f"/orders/{order['id']}/pay", headers=h2)).status_code == 403
    assert (await client.post(f"/orders/{order['id']}/cancel", headers=h2)).status_code == 403


async def test_status_filter(client, customer, product, product_b):
    h = await login(client, "customer")
    o1 = await make_order(client, h, (product, 1))
    await make_order(client, h, (product_b, 1))
    await client.post(f"/orders/{o1['id']}/pay", headers=h)
    paid = (await client.get("/orders?status=paid", headers=h)).json()
    assert [o["id"] for o in paid] == [o1["id"]]
    assert (await client.get("/orders?status=nepostojeci", headers=h)).status_code == 422


# ------------------------- workflow -------------------------

async def test_full_happy_path(client, customer, admin_user, product):
    h, ha = await login(client, "customer"), await login(client, "admin")
    order = await make_order(client, h, (product, 1))
    oid = order["id"]

    paid = await client.post(f"/orders/{oid}/pay", headers=h)
    assert paid.status_code == 200
    assert paid.json()["status"] == "paid" and paid.json()["paid_at"] is not None

    shipped = await client.post(f"/orders/{oid}/ship", headers=ha)
    assert shipped.json()["status"] == "shipped"

    delivered = await client.post(f"/orders/{oid}/deliver", headers=ha)
    assert delivered.json()["status"] == "delivered"


async def test_cannot_pay_twice(client, customer, product):
    h = await login(client, "customer")
    order = await make_order(client, h, (product, 1))
    assert (await client.post(f"/orders/{order['id']}/pay", headers=h)).status_code == 200
    resp = await client.post(f"/orders/{order['id']}/pay", headers=h)
    assert resp.status_code == 409
    assert resp.json()["code"] == "invalid_transition"


async def test_customer_cannot_ship_or_deliver(client, customer, product):
    h = await login(client, "customer")
    order = await make_order(client, h, (product, 1))
    await client.post(f"/orders/{order['id']}/pay", headers=h)
    assert (await client.post(f"/orders/{order['id']}/ship", headers=h)).status_code == 403
    assert (await client.post(f"/orders/{order['id']}/deliver", headers=h)).status_code == 403


async def test_admin_cannot_pay_for_customer(client, customer, admin_user, product):
    h, ha = await login(client, "customer"), await login(client, "admin")
    order = await make_order(client, h, (product, 1))
    assert (await client.post(f"/orders/{order['id']}/pay", headers=ha)).status_code == 403


async def test_cannot_ship_unpaid_order(client, customer, admin_user, product):
    h, ha = await login(client, "customer"), await login(client, "admin")
    order = await make_order(client, h, (product, 1))
    resp = await client.post(f"/orders/{order['id']}/ship", headers=ha)
    assert resp.status_code == 409


async def test_cannot_deliver_unshipped_order(client, customer, admin_user, product):
    h, ha = await login(client, "customer"), await login(client, "admin")
    order = await make_order(client, h, (product, 1))
    await client.post(f"/orders/{order['id']}/pay", headers=h)
    assert (await client.post(f"/orders/{order['id']}/deliver", headers=ha)).status_code == 409


async def test_cancel_pending_restores_stock(client, customer, product):
    h = await login(client, "customer")
    order = await make_order(client, h, (product, 4))
    assert await stock_of(client, h, product) == 6
    resp = await client.post(f"/orders/{order['id']}/cancel", headers=h)
    assert resp.status_code == 200 and resp.json()["status"] == "cancelled"
    assert await stock_of(client, h, product) == 10


async def test_cancel_paid_is_allowed(client, customer, product):
    h = await login(client, "customer")
    order = await make_order(client, h, (product, 1))
    await client.post(f"/orders/{order['id']}/pay", headers=h)
    resp = await client.post(f"/orders/{order['id']}/cancel", headers=h)
    assert resp.status_code == 200


async def test_admin_can_cancel_customers_order(client, customer, admin_user, product):
    h, ha = await login(client, "customer"), await login(client, "admin")
    order = await make_order(client, h, (product, 1))
    assert (await client.post(f"/orders/{order['id']}/cancel", headers=ha)).status_code == 200


async def test_cannot_cancel_shipped_order(client, customer, admin_user, product):
    h, ha = await login(client, "customer"), await login(client, "admin")
    order = await make_order(client, h, (product, 1))
    await client.post(f"/orders/{order['id']}/pay", headers=h)
    await client.post(f"/orders/{order['id']}/ship", headers=ha)
    resp = await client.post(f"/orders/{order['id']}/cancel", headers=h)
    assert resp.status_code == 409


async def test_cannot_cancel_twice_and_stock_not_restored_twice(client, customer, product):
    h = await login(client, "customer")
    order = await make_order(client, h, (product, 3))
    await client.post(f"/orders/{order['id']}/cancel", headers=h)
    resp = await client.post(f"/orders/{order['id']}/cancel", headers=h)
    assert resp.status_code == 409
    assert await stock_of(client, h, product) == 10


# ------------------------- rok plaćanja -------------------------

async def _age_order(db, order_id, hours):
    """Pomakni created_at u prošlost (simulacija da je prošlo `hours` sati)."""
    order = await db.get(Order, order_id)
    order.created_at = datetime.now(timezone.utc) - timedelta(hours=hours)
    await db.commit()


async def test_pending_order_older_than_24h_is_auto_cancelled(client, db, customer, product):
    h = await login(client, "customer")
    order = await make_order(client, h, (product, 3))
    await _age_order(db, order["id"], hours=25)

    resp = await client.get(f"/orders/{order['id']}", headers=h)
    assert resp.json()["status"] == "cancelled"
    assert await stock_of(client, h, product) == 10  # zaliha vraćena


async def test_pending_order_younger_than_24h_stays_pending(client, db, customer, product):
    h = await login(client, "customer")
    order = await make_order(client, h, (product, 1))
    await _age_order(db, order["id"], hours=23)
    resp = await client.get(f"/orders/{order['id']}", headers=h)
    assert resp.json()["status"] == "pending"


async def test_cannot_pay_expired_order(client, db, customer, product):
    h = await login(client, "customer")
    order = await make_order(client, h, (product, 1))
    await _age_order(db, order["id"], hours=25)
    resp = await client.post(f"/orders/{order['id']}/pay", headers=h)
    assert resp.status_code == 409
    assert resp.json()["code"] == "payment_expired"


async def test_paid_order_never_expires(client, db, customer, product):
    h = await login(client, "customer")
    order = await make_order(client, h, (product, 1))
    await client.post(f"/orders/{order['id']}/pay", headers=h)
    await _age_order(db, order["id"], hours=100)
    assert (await client.get(f"/orders/{order['id']}", headers=h)).json()["status"] == "paid"


# ------------------------- stavke -------------------------

async def test_add_item_reduces_stock_and_updates_total(client, customer, product, product_b):
    h = await login(client, "customer")
    order = await make_order(client, h, (product, 1))
    resp = await client.post(
        f"/orders/{order['id']}/items",
        json={"product_id": product_b.id, "quantity": 2},
        headers=h,
    )
    assert resp.status_code == 201
    assert resp.json()["total_cents"] == 2500 + 2 * 1500
    assert await stock_of(client, h, product_b) == 3


async def test_add_same_product_again_is_409(client, customer, product):
    h = await login(client, "customer")
    order = await make_order(client, h, (product, 1))
    resp = await client.post(
        f"/orders/{order['id']}/items", json={"product_id": product.id, "quantity": 1}, headers=h
    )
    assert resp.status_code == 409


async def test_update_item_quantity_adjusts_stock_both_ways(client, customer, product):
    h = await login(client, "customer")
    order = await make_order(client, h, (product, 2))
    item_id = order["items"][0]["id"]

    up = await client.patch(f"/orders/{order['id']}/items/{item_id}", json={"quantity": 5}, headers=h)
    assert up.status_code == 200
    assert up.json()["total_cents"] == 5 * 2500
    assert await stock_of(client, h, product) == 5

    down = await client.patch(f"/orders/{order['id']}/items/{item_id}", json={"quantity": 1}, headers=h)
    assert down.json()["total_cents"] == 2500
    assert await stock_of(client, h, product) == 9


async def test_update_item_over_stock_is_400(client, customer, product):
    h = await login(client, "customer")
    order = await make_order(client, h, (product, 2))
    item_id = order["items"][0]["id"]
    resp = await client.patch(f"/orders/{order['id']}/items/{item_id}", json={"quantity": 50}, headers=h)
    assert resp.status_code == 400
    assert await stock_of(client, h, product) == 8


async def test_remove_item_restores_stock(client, customer, product, product_b):
    h = await login(client, "customer")
    order = await make_order(client, h, (product, 2), (product_b, 1))
    item_id = order["items"][0]["id"]
    resp = await client.delete(f"/orders/{order['id']}/items/{item_id}", headers=h)
    assert resp.status_code == 204
    assert await stock_of(client, h, product) == 10
    detail = (await client.get(f"/orders/{order['id']}", headers=h)).json()
    assert len(detail["items"]) == 1
    assert detail["total_cents"] == 1500


async def test_cannot_remove_last_item(client, customer, product):
    h = await login(client, "customer")
    order = await make_order(client, h, (product, 1))
    item_id = order["items"][0]["id"]
    resp = await client.delete(f"/orders/{order['id']}/items/{item_id}", headers=h)
    assert resp.status_code == 400
    assert resp.json()["code"] == "last_item"


async def test_cannot_edit_items_of_paid_order(client, customer, product, product_b):
    h = await login(client, "customer")
    order = await make_order(client, h, (product, 1))
    await client.post(f"/orders/{order['id']}/pay", headers=h)
    resp = await client.post(
        f"/orders/{order['id']}/items", json={"product_id": product_b.id, "quantity": 1}, headers=h
    )
    assert resp.status_code == 409
    assert resp.json()["code"] == "order_not_editable"


async def test_cannot_edit_items_of_someone_elses_order(client, customer, other_customer, product, product_b):
    h1, h2 = await login(client, "customer"), await login(client, "other")
    order = await make_order(client, h1, (product, 1))
    resp = await client.post(
        f"/orders/{order['id']}/items", json={"product_id": product_b.id, "quantity": 1}, headers=h2
    )
    assert resp.status_code == 403


async def test_admin_cannot_edit_items(client, customer, admin_user, product, product_b):
    h, ha = await login(client, "customer"), await login(client, "admin")
    order = await make_order(client, h, (product, 1))
    resp = await client.post(
        f"/orders/{order['id']}/items", json={"product_id": product_b.id, "quantity": 1}, headers=ha
    )
    assert resp.status_code == 403


async def test_item_of_another_order_is_404(client, customer, product, product_b):
    h = await login(client, "customer")
    o1 = await make_order(client, h, (product, 1))
    o2 = await make_order(client, h, (product_b, 1))
    foreign_item = o2["items"][0]["id"]
    resp = await client.patch(f"/orders/{o1['id']}/items/{foreign_item}", json={"quantity": 2}, headers=h)
    assert resp.status_code == 404
