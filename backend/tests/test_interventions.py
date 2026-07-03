from typing import Any

from httpx import AsyncClient

from tests.helpers import auth_headers, register

STUDENT_PAYLOAD: dict[str, Any] = {
    "synth_student_code": "SYNTH-INT-0001",
    "programme": "Computer Science",
    "year_of_study": 2,
    "gpa": 3.2,
    "attendance_rate": 0.85,
    "credits_attempted": 60,
    "credits_completed": 55,
    "age": 20,
}


async def _create_student(client: AsyncClient, token: str) -> dict[str, Any]:
    response = await client.post(
        "/api/v1/students", json=STUDENT_PAYLOAD, headers=auth_headers(token)
    )
    assert response.status_code == 201, response.text
    data: dict[str, Any] = response.json()
    return data


async def test_advisor_can_create_and_list_intervention(client: AsyncClient) -> None:
    admin_tokens = await register(
        client, tenant_name="SYNTH Uni A", email="admin@example.com", role="admin"
    )
    student = await _create_student(client, admin_tokens["access_token"])

    advisor_tokens = await register(
        client, tenant_name="SYNTH Uni A", email="advisor@example.com", role="advisor"
    )
    token = advisor_tokens["access_token"]

    create_response = await client.post(
        f"/api/v1/students/{student['id']}/interventions",
        json={"type": "advising_meeting", "notes": "Discussed attendance", "status": "open"},
        headers=auth_headers(token),
    )
    assert create_response.status_code == 201
    intervention = create_response.json()
    assert intervention["status"] == "open"
    assert intervention["student_id"] == student["id"]

    list_response = await client.get(
        f"/api/v1/students/{student['id']}/interventions", headers=auth_headers(token)
    )
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1


async def test_update_intervention_status(client: AsyncClient) -> None:
    tokens = await register(
        client, tenant_name="SYNTH Uni A", email="admin2@example.com", role="admin"
    )
    token = tokens["access_token"]
    student = await _create_student(client, token)

    create_response = await client.post(
        f"/api/v1/students/{student['id']}/interventions",
        json={"type": "follow_up", "status": "open"},
        headers=auth_headers(token),
    )
    intervention_id = create_response.json()["id"]

    update_response = await client.patch(
        f"/api/v1/interventions/{intervention_id}",
        json={"status": "resolved"},
        headers=auth_headers(token),
    )
    assert update_response.status_code == 200
    assert update_response.json()["status"] == "resolved"


async def test_advisor_cannot_delete_intervention(client: AsyncClient) -> None:
    admin_tokens = await register(
        client, tenant_name="SYNTH Uni A", email="admin3@example.com", role="admin"
    )
    student = await _create_student(client, admin_tokens["access_token"])

    create_response = await client.post(
        f"/api/v1/students/{student['id']}/interventions",
        json={"type": "follow_up", "status": "open"},
        headers=auth_headers(admin_tokens["access_token"]),
    )
    intervention_id = create_response.json()["id"]

    advisor_tokens = await register(
        client, tenant_name="SYNTH Uni A", email="advisor2@example.com", role="advisor"
    )
    response = await client.delete(
        f"/api/v1/interventions/{intervention_id}",
        headers=auth_headers(advisor_tokens["access_token"]),
    )
    assert response.status_code == 403


async def test_admin_can_delete_intervention(client: AsyncClient) -> None:
    tokens = await register(
        client, tenant_name="SYNTH Uni A", email="admin4@example.com", role="admin"
    )
    token = tokens["access_token"]
    student = await _create_student(client, token)

    create_response = await client.post(
        f"/api/v1/students/{student['id']}/interventions",
        json={"type": "follow_up", "status": "open"},
        headers=auth_headers(token),
    )
    intervention_id = create_response.json()["id"]

    delete_response = await client.delete(
        f"/api/v1/interventions/{intervention_id}", headers=auth_headers(token)
    )
    assert delete_response.status_code == 204


async def test_cross_tenant_intervention_access_is_impossible(client: AsyncClient) -> None:
    tenant_a_tokens = await register(
        client, tenant_name="SYNTH Tenant A", email="a-admin@example.com", role="admin"
    )
    student = await _create_student(client, tenant_a_tokens["access_token"])
    create_response = await client.post(
        f"/api/v1/students/{student['id']}/interventions",
        json={"type": "follow_up", "status": "open"},
        headers=auth_headers(tenant_a_tokens["access_token"]),
    )
    intervention_id = create_response.json()["id"]

    tenant_b_tokens = await register(
        client, tenant_name="SYNTH Tenant B", email="b-admin@example.com", role="admin"
    )
    tenant_b_headers = auth_headers(tenant_b_tokens["access_token"])

    list_response = await client.get(
        f"/api/v1/students/{student['id']}/interventions", headers=tenant_b_headers
    )
    assert list_response.status_code == 404

    update_response = await client.patch(
        f"/api/v1/interventions/{intervention_id}",
        json={"status": "resolved"},
        headers=tenant_b_headers,
    )
    assert update_response.status_code == 404

    delete_response = await client.delete(
        f"/api/v1/interventions/{intervention_id}", headers=tenant_b_headers
    )
    assert delete_response.status_code == 404
