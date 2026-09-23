# Testovi autentikacije: login, refresh, /auth/me, registracija.
from jose import jwt

from app.core.config import settings
from tests.conftest import auth_header


async def test_login_success(client, customer):
    resp = await client.post("/auth/login", json={"username": "kupac", "password": "kupac123"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"] and body["refresh_token"]


async def test_login_wrong_password(client, customer):
    resp = await client.post("/auth/login", json={"username": "kupac", "password": "kriva"})
    assert resp.status_code == 401
    assert resp.json()["code"] == "invalid_credentials"


async def test_login_unknown_user_same_error_as_wrong_password(client, customer):
    """Ista poruka -> napadač ne može otkriti koji username postoji."""
    wrong_pw = await client.post("/auth/login", json={"username": "kupac", "password": "x"})
    unknown = await client.post("/auth/login", json={"username": "nepoznat", "password": "x"})
    assert unknown.status_code == 401
    assert unknown.json() == wrong_pw.json()


async def test_login_inactive_user(client, inactive_user):
    resp = await client.post("/auth/login", json={"username": "neaktivan", "password": "pass123"})
    assert resp.status_code == 401


async def test_me_returns_current_user_without_password(client, customer):
    headers = await auth_header(client, "kupac", "kupac123")
    resp = await client.get("/auth/me", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["username"] == "kupac"
    assert body["role"] == "customer"
    assert "password_hash" not in body


async def test_me_without_token_is_401(client):
    resp = await client.get("/auth/me")
    assert resp.status_code == 401


async def test_me_with_garbage_token_is_401(client):
    resp = await client.get("/auth/me", headers={"Authorization": "Bearer nije.token"})
    assert resp.status_code == 401


async def test_me_with_expired_token_is_401(client, customer, monkeypatch):
    # access token koji je istekao prije minute
    monkeypatch.setattr("app.core.jwt.ACCESS_TOKEN_EXPIRE_MINUTES", -1)
    headers = await auth_header(client, "kupac", "kupac123")
    resp = await client.get("/auth/me", headers=headers)
    assert resp.status_code == 401
    assert resp.json()["code"] == "token_expired"


async def test_token_signed_with_other_secret_is_rejected(client, customer):
    fake = jwt.encode(
        {"sub": str(customer.id), "type": "access", "iss": settings.JWT_ISSUER},
        "tuda-tajna",
        algorithm="HS256",
    )
    resp = await client.get("/auth/me", headers={"Authorization": f"Bearer {fake}"})
    assert resp.status_code == 401


async def test_refresh_returns_new_tokens(client, customer):
    login = await client.post("/auth/login", json={"username": "kupac", "password": "kupac123"})
    resp = await client.post("/auth/refresh", json={"refresh_token": login.json()["refresh_token"]})
    assert resp.status_code == 200
    headers = {"Authorization": f"Bearer {resp.json()['access_token']}"}
    assert (await client.get("/auth/me", headers=headers)).status_code == 200


async def test_access_token_cannot_be_used_as_refresh(client, customer):
    login = await client.post("/auth/login", json={"username": "kupac", "password": "kupac123"})
    resp = await client.post("/auth/refresh", json={"refresh_token": login.json()["access_token"]})
    assert resp.status_code == 401


async def test_refresh_token_cannot_be_used_as_access(client, customer):
    login = await client.post("/auth/login", json={"username": "kupac", "password": "kupac123"})
    headers = {"Authorization": f"Bearer {login.json()['refresh_token']}"}
    assert (await client.get("/auth/me", headers=headers)).status_code == 401


async def test_register_creates_customer(client):
    payload = {"username": "novi", "password": "tajna123", "full_name": "Novi Kupac",
               "email": "novi@example.com"}
    resp = await client.post("/auth/register", json=payload)
    assert resp.status_code == 201
    assert resp.json()["role"] == "customer"
    # novi korisnik se može prijaviti
    login = await client.post("/auth/login", json={"username": "novi", "password": "tajna123"})
    assert login.status_code == 200


async def test_register_duplicate_username_is_409(client, customer):
    payload = {"username": "kupac", "password": "tajna123", "full_name": "Netko",
               "email": "netko@example.com"}
    resp = await client.post("/auth/register", json=payload)
    assert resp.status_code == 409


async def test_register_validation_errors_are_422_with_field_names(client):
    payload = {"username": "ab", "password": "123", "full_name": "N", "email": "nije-email"}
    resp = await client.post("/auth/register", json=payload)
    assert resp.status_code == 422
    body = resp.json()
    assert body["code"] == "validation_error"
    fields = {e["field"] for e in body["errors"]}
    assert {"username", "password", "full_name", "email"} <= fields


async def test_register_cannot_choose_role(client):
    """Klijent ne može poslati role=admin: polje se ignorira, role je uvijek customer."""
    payload = {"username": "haker", "password": "tajna123", "full_name": "Haker H",
               "email": "h@example.com", "role": "admin"}
    resp = await client.post("/auth/register", json=payload)
    assert resp.status_code == 201
    assert resp.json()["role"] == "customer"
