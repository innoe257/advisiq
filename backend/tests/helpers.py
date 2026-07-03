from typing import Any

from httpx import AsyncClient


async def register(
    client: AsyncClient,
    *,
    tenant_name: str,
    email: str,
    password: str = "testpassword123",
    role: str = "advisor",
) -> dict[str, Any]:
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "tenant_name": tenant_name,
            "email": email,
            "password": password,
            "role": role,
        },
    )
    assert response.status_code == 201, response.text
    data: dict[str, Any] = response.json()
    return data


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
