from typing import Any

from httpx import AsyncClient

from tests.helpers import auth_headers, register

STUDENT_PAYLOAD: dict[str, Any] = {
    "synth_student_code": "SYNTH-STU-0001",
    "programme": "Computer Science",
    "year_of_study": 2,
    "gpa": 3.2,
    "attendance_rate": 0.85,
    "credits_attempted": 60,
    "credits_completed": 55,
    "age": 20,
}


async def _create_student(
    client: AsyncClient, token: str, payload: dict[str, Any] | None = None
) -> dict[str, Any]:
    response = await client.post(
        "/api/v1/students",
        json=payload or STUDENT_PAYLOAD,
        headers=auth_headers(token),
    )
    assert response.status_code == 201, response.text
    data: dict[str, Any] = response.json()
    return data


async def test_admin_can_create_student(client: AsyncClient) -> None:
    tokens = await register(
        client, tenant_name="SYNTH Uni A", email="admin@example.com", role="admin"
    )

    student = await _create_student(client, tokens["access_token"])
    assert student["synth_student_code"] == "SYNTH-STU-0001"
    assert student["extra_features"] == {}


async def test_advisor_cannot_create_student(client: AsyncClient) -> None:
    tokens = await register(
        client, tenant_name="SYNTH Uni A", email="advisor@example.com", role="advisor"
    )

    response = await client.post(
        "/api/v1/students", json=STUDENT_PAYLOAD, headers=auth_headers(tokens["access_token"])
    )
    assert response.status_code == 403


async def test_create_student_rejects_non_synth_code(client: AsyncClient) -> None:
    tokens = await register(
        client, tenant_name="SYNTH Uni A", email="admin2@example.com", role="admin"
    )

    payload = {**STUDENT_PAYLOAD, "synth_student_code": "REAL-STUDENT-001"}
    response = await client.post(
        "/api/v1/students", json=payload, headers=auth_headers(tokens["access_token"])
    )
    assert response.status_code == 422


async def test_create_duplicate_synth_code_fails(client: AsyncClient) -> None:
    tokens = await register(
        client, tenant_name="SYNTH Uni A", email="admin3@example.com", role="admin"
    )

    await _create_student(client, tokens["access_token"])
    response = await client.post(
        "/api/v1/students", json=STUDENT_PAYLOAD, headers=auth_headers(tokens["access_token"])
    )
    assert response.status_code == 400


async def test_advisor_can_list_and_read_students(client: AsyncClient) -> None:
    admin_tokens = await register(
        client, tenant_name="SYNTH Uni A", email="admin4@example.com", role="admin"
    )
    student = await _create_student(client, admin_tokens["access_token"])

    advisor_tokens = await register(
        client, tenant_name="SYNTH Uni A", email="advisor2@example.com", role="advisor"
    )

    list_response = await client.get(
        "/api/v1/students", headers=auth_headers(advisor_tokens["access_token"])
    )
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    get_response = await client.get(
        f"/api/v1/students/{student['id']}", headers=auth_headers(advisor_tokens["access_token"])
    )
    assert get_response.status_code == 200


async def test_list_students_filters_by_programme_and_year(client: AsyncClient) -> None:
    tokens = await register(
        client, tenant_name="SYNTH Uni A", email="admin5@example.com", role="admin"
    )

    await _create_student(client, tokens["access_token"], STUDENT_PAYLOAD)
    await _create_student(
        client,
        tokens["access_token"],
        {
            **STUDENT_PAYLOAD,
            "synth_student_code": "SYNTH-STU-0002",
            "programme": "Nursing",
            "year_of_study": 1,
        },
    )

    response = await client.get(
        "/api/v1/students",
        params={"programme": "Nursing"},
        headers=auth_headers(tokens["access_token"]),
    )
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 1
    assert results[0]["programme"] == "Nursing"

    year_response = await client.get(
        "/api/v1/students",
        params={"year_of_study": 1},
        headers=auth_headers(tokens["access_token"]),
    )
    assert year_response.status_code == 200
    year_results = year_response.json()
    assert len(year_results) == 1
    assert year_results[0]["synth_student_code"] == "SYNTH-STU-0002"


async def test_admin_can_update_student(client: AsyncClient) -> None:
    tokens = await register(
        client, tenant_name="SYNTH Uni A", email="admin6@example.com", role="admin"
    )
    student = await _create_student(client, tokens["access_token"])

    response = await client.patch(
        f"/api/v1/students/{student['id']}",
        json={"gpa": 3.9},
        headers=auth_headers(tokens["access_token"]),
    )
    assert response.status_code == 200
    assert response.json()["gpa"] == 3.9


async def test_advisor_cannot_update_student(client: AsyncClient) -> None:
    admin_tokens = await register(
        client, tenant_name="SYNTH Uni A", email="admin7@example.com", role="admin"
    )
    student = await _create_student(client, admin_tokens["access_token"])

    advisor_tokens = await register(
        client, tenant_name="SYNTH Uni A", email="advisor3@example.com", role="advisor"
    )
    response = await client.patch(
        f"/api/v1/students/{student['id']}",
        json={"gpa": 3.9},
        headers=auth_headers(advisor_tokens["access_token"]),
    )
    assert response.status_code == 403


async def test_admin_can_delete_student(client: AsyncClient) -> None:
    tokens = await register(
        client, tenant_name="SYNTH Uni A", email="admin8@example.com", role="admin"
    )
    student = await _create_student(client, tokens["access_token"])

    delete_response = await client.delete(
        f"/api/v1/students/{student['id']}", headers=auth_headers(tokens["access_token"])
    )
    assert delete_response.status_code == 204

    get_response = await client.get(
        f"/api/v1/students/{student['id']}", headers=auth_headers(tokens["access_token"])
    )
    assert get_response.status_code == 404


async def test_get_nonexistent_student_returns_404(client: AsyncClient) -> None:
    tokens = await register(
        client, tenant_name="SYNTH Uni A", email="admin9@example.com", role="admin"
    )

    response = await client.get(
        "/api/v1/students/00000000-0000-0000-0000-000000000000",
        headers=auth_headers(tokens["access_token"]),
    )
    assert response.status_code == 404


async def test_cross_tenant_access_is_impossible(client: AsyncClient) -> None:
    """Proves tenant isolation: a user in Tenant B can never read, list, or
    modify a student that belongs to Tenant A, even when they know its ID."""
    tenant_a_tokens = await register(
        client, tenant_name="SYNTH Tenant A", email="a-admin@example.com", role="admin"
    )
    student = await _create_student(client, tenant_a_tokens["access_token"])

    tenant_b_tokens = await register(
        client, tenant_name="SYNTH Tenant B", email="b-admin@example.com", role="admin"
    )
    tenant_b_headers = auth_headers(tenant_b_tokens["access_token"])

    get_response = await client.get(f"/api/v1/students/{student['id']}", headers=tenant_b_headers)
    assert get_response.status_code == 404

    list_response = await client.get("/api/v1/students", headers=tenant_b_headers)
    assert list_response.status_code == 200
    assert list_response.json() == []

    update_response = await client.patch(
        f"/api/v1/students/{student['id']}", json={"gpa": 0.0}, headers=tenant_b_headers
    )
    assert update_response.status_code == 404

    delete_response = await client.delete(
        f"/api/v1/students/{student['id']}", headers=tenant_b_headers
    )
    assert delete_response.status_code == 404
