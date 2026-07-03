import uuid

from httpx import AsyncClient

from app.models.user import Role
from app.security import create_access_token, create_refresh_token
from tests.helpers import auth_headers, register


async def test_register_creates_user_and_returns_tokens(client: AsyncClient) -> None:
    tokens = await register(client, tenant_name="SYNTH Uni A", email="a@example.com")
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    assert tokens["token_type"] == "bearer"


async def test_register_duplicate_email_fails(client: AsyncClient) -> None:
    await register(client, tenant_name="SYNTH Uni A", email="dupe@example.com")

    response = await client.post(
        "/api/v1/auth/register",
        json={
            "tenant_name": "SYNTH Uni A",
            "email": "dupe@example.com",
            "password": "testpassword123",
            "role": "advisor",
        },
    )
    assert response.status_code == 400


async def test_register_password_too_short_fails(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "tenant_name": "SYNTH Uni A",
            "email": "short@example.com",
            "password": "short",
            "role": "advisor",
        },
    )
    assert response.status_code == 422


async def test_register_invalid_role_fails(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "tenant_name": "SYNTH Uni A",
            "email": "badrole@example.com",
            "password": "testpassword123",
            "role": "superuser",
        },
    )
    assert response.status_code == 422


async def test_login_success(client: AsyncClient) -> None:
    await register(client, tenant_name="SYNTH Uni A", email="login@example.com")

    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "login@example.com", "password": "testpassword123"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


async def test_login_wrong_password_fails(client: AsyncClient) -> None:
    await register(client, tenant_name="SYNTH Uni A", email="login2@example.com")

    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "login2@example.com", "password": "wrongpassword"},
    )
    assert response.status_code == 401


async def test_login_nonexistent_user_fails(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "ghost@example.com", "password": "testpassword123"},
    )
    assert response.status_code == 401


async def test_me_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


async def test_me_returns_current_user(client: AsyncClient) -> None:
    tokens = await register(client, tenant_name="SYNTH Uni A", email="me@example.com")

    response = await client.get("/api/v1/auth/me", headers=auth_headers(tokens["access_token"]))
    assert response.status_code == 200
    assert response.json()["email"] == "me@example.com"


async def test_refresh_returns_new_access_token(client: AsyncClient) -> None:
    tokens = await register(client, tenant_name="SYNTH Uni A", email="refresh@example.com")

    response = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert response.status_code == 200
    new_access_token = response.json()["access_token"]

    me_response = await client.get("/api/v1/auth/me", headers=auth_headers(new_access_token))
    assert me_response.status_code == 200


async def test_refresh_rejects_access_token(client: AsyncClient) -> None:
    tokens = await register(client, tenant_name="SYNTH Uni A", email="refresh2@example.com")

    response = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": tokens["access_token"]}
    )
    assert response.status_code == 401


async def test_me_rejects_refresh_token(client: AsyncClient) -> None:
    tokens = await register(client, tenant_name="SYNTH Uni A", email="refresh3@example.com")

    response = await client.get("/api/v1/auth/me", headers=auth_headers(tokens["refresh_token"]))
    assert response.status_code == 401


async def test_me_rejects_token_for_nonexistent_user(client: AsyncClient) -> None:
    """A well-formed, correctly-signed token for a user that doesn't exist
    (e.g. deleted after the token was issued) must not grant access."""
    token = create_access_token(user_id=uuid.uuid4(), tenant_id=uuid.uuid4(), role=Role.advisor)

    response = await client.get("/api/v1/auth/me", headers=auth_headers(token))
    assert response.status_code == 401


async def test_refresh_rejects_token_for_nonexistent_user(client: AsyncClient) -> None:
    token = create_refresh_token(user_id=uuid.uuid4(), tenant_id=uuid.uuid4(), role=Role.advisor)

    response = await client.post("/api/v1/auth/refresh", json={"refresh_token": token})
    assert response.status_code == 401


async def test_me_rejects_garbage_token(client: AsyncClient) -> None:
    response = await client.get("/api/v1/auth/me", headers=auth_headers("not-a-real-token"))
    assert response.status_code == 401
