from httpx import AsyncClient

from tests.helpers import auth_headers, register


async def test_admin_can_list_and_create_users(client: AsyncClient) -> None:
    admin_tokens = await register(
        client, tenant_name="SYNTH Uni A", email="admin@example.com", role="admin"
    )
    token = admin_tokens["access_token"]

    create_response = await client.post(
        "/api/v1/admin/users",
        json={"email": "new-advisor@example.com", "password": "testpassword123", "role": "advisor"},
        headers=auth_headers(token),
    )
    assert create_response.status_code == 201
    assert create_response.json()["role"] == "advisor"

    list_response = await client.get("/api/v1/admin/users", headers=auth_headers(token))
    assert list_response.status_code == 200
    emails = {user["email"] for user in list_response.json()}
    assert emails == {"admin@example.com", "new-advisor@example.com"}


async def test_advisor_cannot_list_or_create_users(client: AsyncClient) -> None:
    tokens = await register(
        client, tenant_name="SYNTH Uni A", email="advisor@example.com", role="advisor"
    )
    token = tokens["access_token"]

    list_response = await client.get("/api/v1/admin/users", headers=auth_headers(token))
    assert list_response.status_code == 403

    create_response = await client.post(
        "/api/v1/admin/users",
        json={"email": "x@example.com", "password": "testpassword123", "role": "advisor"},
        headers=auth_headers(token),
    )
    assert create_response.status_code == 403


async def test_create_user_duplicate_email_fails(client: AsyncClient) -> None:
    tokens = await register(
        client, tenant_name="SYNTH Uni A", email="admin2@example.com", role="admin"
    )
    token = tokens["access_token"]

    response = await client.post(
        "/api/v1/admin/users",
        json={"email": "admin2@example.com", "password": "testpassword123", "role": "advisor"},
        headers=auth_headers(token),
    )
    assert response.status_code == 400


async def test_admin_users_scoped_to_own_tenant(client: AsyncClient) -> None:
    tenant_a_tokens = await register(
        client, tenant_name="SYNTH Tenant A", email="a-admin@example.com", role="admin"
    )
    await register(client, tenant_name="SYNTH Tenant B", email="b-admin@example.com", role="admin")

    response = await client.get(
        "/api/v1/admin/users", headers=auth_headers(tenant_a_tokens["access_token"])
    )
    emails = {user["email"] for user in response.json()}
    assert emails == {"a-admin@example.com"}
