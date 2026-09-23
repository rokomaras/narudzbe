# Testovi kataloga: autorizacija po roli, validacija, duplikati, brisanje.
from tests.conftest import auth_header

NEW = {"name": "Šalica", "description": "keramika", "price_cents": 899, "stock": 20}


async def test_products_require_login(client):
    assert (await client.get("/products")).status_code == 401


async def test_customer_sees_only_active_products(client, customer, product, inactive_product):
    headers = await auth_header(client, "kupac", "kupac123")
    resp = await client.get("/products", headers=headers)
    assert resp.status_code == 200
    names = [p["name"] for p in resp.json()]
    assert names == ["Majica"]


async def test_admin_sees_all_products(client, admin_user, product, inactive_product):
    headers = await auth_header(client, "testadmin", "admin123")
    resp = await client.get("/products", headers=headers)
    assert {p["name"] for p in resp.json()} == {"Majica", "Povučeno"}


async def test_customer_gets_404_for_inactive_product(client, customer, inactive_product):
    headers = await auth_header(client, "kupac", "kupac123")
    resp = await client.get(f"/products/{inactive_product.id}", headers=headers)
    assert resp.status_code == 404


async def test_get_missing_product_is_404(client, customer):
    headers = await auth_header(client, "kupac", "kupac123")
    assert (await client.get("/products/9999", headers=headers)).status_code == 404


async def test_customer_cannot_create_product(client, customer):
    headers = await auth_header(client, "kupac", "kupac123")
    resp = await client.post("/products", json=NEW, headers=headers)
    assert resp.status_code == 403
    assert resp.json()["code"] == "forbidden"


async def test_admin_creates_product(client, admin_user):
    headers = await auth_header(client, "testadmin", "admin123")
    resp = await client.post("/products", json=NEW, headers=headers)
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Šalica"
    assert body["is_active"] is True


async def test_duplicate_product_name_is_409(client, admin_user, product):
    headers = await auth_header(client, "testadmin", "admin123")
    resp = await client.post("/products", json={**NEW, "name": "Majica"}, headers=headers)
    assert resp.status_code == 409


async def test_invalid_product_is_422(client, admin_user):
    headers = await auth_header(client, "testadmin", "admin123")
    bad = {"name": "", "price_cents": -5, "stock": -1}
    resp = await client.post("/products", json=bad, headers=headers)
    assert resp.status_code == 422
    fields = {e["field"] for e in resp.json()["errors"]}
    assert {"name", "price_cents", "stock"} <= fields


async def test_admin_updates_product_partially(client, admin_user, product):
    headers = await auth_header(client, "testadmin", "admin123")
    resp = await client.patch(f"/products/{product.id}", json={"price_cents": 3000}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["price_cents"] == 3000
    assert resp.json()["name"] == "Majica"  # nepromijenjeno


async def test_rename_to_existing_name_is_409(client, admin_user, product, product_b):
    headers = await auth_header(client, "testadmin", "admin123")
    resp = await client.patch(f"/products/{product_b.id}", json={"name": "Majica"}, headers=headers)
    assert resp.status_code == 409


async def test_customer_cannot_update_or_delete(client, customer, product):
    headers = await auth_header(client, "kupac", "kupac123")
    assert (await client.patch(f"/products/{product.id}", json={"stock": 1}, headers=headers)).status_code == 403
    assert (await client.delete(f"/products/{product.id}", headers=headers)).status_code == 403


async def test_admin_deletes_unused_product(client, admin_user, product):
    headers = await auth_header(client, "testadmin", "admin123")
    assert (await client.delete(f"/products/{product.id}", headers=headers)).status_code == 204
    assert (await client.get(f"/products/{product.id}", headers=headers)).status_code == 404


async def test_cannot_delete_product_that_is_in_an_order(client, admin_user, customer, product):
    cust = await auth_header(client, "kupac", "kupac123")
    order = {"shipping_address": "Ulica 1, Zadar", "items": [{"product_id": product.id, "quantity": 1}]}
    assert (await client.post("/orders", json=order, headers=cust)).status_code == 201

    admin = await auth_header(client, "testadmin", "admin123")
    resp = await client.delete(f"/products/{product.id}", headers=admin)
    assert resp.status_code == 409
    assert resp.json()["code"] == "product_in_use"
