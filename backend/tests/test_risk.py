from typing import Any

from httpx import AsyncClient

from tests.helpers import auth_headers, register

BASE_STUDENT: dict[str, Any] = {
    "programme": "Computer Science",
    "year_of_study": 2,
    "attendance_rate": 0.8,
    "credits_attempted": 60,
    "credits_completed": 50,
    "age": 20,
}


async def _create_student(
    client: AsyncClient, token: str, code: str, gpa: float, **overrides: Any
) -> dict[str, Any]:
    payload = {**BASE_STUDENT, "synth_student_code": code, "gpa": gpa, **overrides}
    response = await client.post("/api/v1/students", json=payload, headers=auth_headers(token))
    assert response.status_code == 201, response.text
    data: dict[str, Any] = response.json()
    return data


async def test_admin_can_trigger_batch_scoring(client: AsyncClient) -> None:
    tokens = await register(
        client, tenant_name="SYNTH Uni A", email="admin@example.com", role="admin"
    )
    token = tokens["access_token"]

    await _create_student(client, token, "SYNTH-R-0001", gpa=3.5)  # -> low
    await _create_student(client, token, "SYNTH-R-0002", gpa=2.0)  # -> medium
    await _create_student(client, token, "SYNTH-R-0003", gpa=1.0)  # -> high

    response = await client.post("/api/v1/risk/score", json={}, headers=auth_headers(token))
    assert response.status_code == 200
    body = response.json()
    assert body["scored_count"] == 3
    assert body["model_version"] == "v1"


async def test_advisor_cannot_trigger_batch_scoring(client: AsyncClient) -> None:
    tokens = await register(
        client, tenant_name="SYNTH Uni A", email="advisor@example.com", role="advisor"
    )
    response = await client.post(
        "/api/v1/risk/score", json={}, headers=auth_headers(tokens["access_token"])
    )
    assert response.status_code == 403


async def test_batch_scoring_scopes_to_requested_student_ids(client: AsyncClient) -> None:
    tokens = await register(
        client, tenant_name="SYNTH Uni A", email="admin2@example.com", role="admin"
    )
    token = tokens["access_token"]

    student_a = await _create_student(client, token, "SYNTH-R-0004", gpa=3.5)
    await _create_student(client, token, "SYNTH-R-0005", gpa=2.0)

    response = await client.post(
        "/api/v1/risk/score",
        json={"student_ids": [student_a["id"]]},
        headers=auth_headers(token),
    )
    assert response.status_code == 200
    assert response.json()["scored_count"] == 1


async def test_risk_score_reflects_expected_tier(client: AsyncClient) -> None:
    tokens = await register(
        client, tenant_name="SYNTH Uni A", email="admin3@example.com", role="admin"
    )
    token = tokens["access_token"]

    high_risk_student = await _create_student(client, token, "SYNTH-R-0006", gpa=1.0)

    await client.post("/api/v1/risk/score", json={}, headers=auth_headers(token))

    response = await client.get(
        f"/api/v1/students/{high_risk_student['id']}/risk-scores", headers=auth_headers(token)
    )
    assert response.status_code == 200
    scores = response.json()
    assert len(scores) == 1
    assert scores[0]["tier"] == "high"
    assert scores[0]["score"] == 0.75


async def test_risk_score_history_orders_most_recent_first(client: AsyncClient) -> None:
    tokens = await register(
        client, tenant_name="SYNTH Uni A", email="admin4@example.com", role="admin"
    )
    token = tokens["access_token"]

    student = await _create_student(client, token, "SYNTH-R-0007", gpa=3.5)

    await client.post("/api/v1/risk/score", json={}, headers=auth_headers(token))
    await client.post("/api/v1/risk/score", json={}, headers=auth_headers(token))

    response = await client.get(
        f"/api/v1/students/{student['id']}/risk-scores", headers=auth_headers(token)
    )
    scores = response.json()
    assert len(scores) == 2
    assert scores[0]["scored_at"] >= scores[1]["scored_at"]


async def test_cohort_summary_counts_latest_score_only(client: AsyncClient) -> None:
    tokens = await register(
        client, tenant_name="SYNTH Uni A", email="admin5@example.com", role="admin"
    )
    token = tokens["access_token"]

    await _create_student(client, token, "SYNTH-R-0008", gpa=3.5)
    await _create_student(client, token, "SYNTH-R-0009", gpa=2.0)
    await _create_student(client, token, "SYNTH-R-0010", gpa=1.0)

    await client.post("/api/v1/risk/score", json={}, headers=auth_headers(token))
    await client.post("/api/v1/risk/score", json={}, headers=auth_headers(token))  # re-score

    response = await client.get("/api/v1/risk/cohort", headers=auth_headers(token))
    assert response.status_code == 200
    counts = response.json()["tier_counts"]
    assert counts == {"low": 1, "medium": 1, "high": 1, "total": 3}


async def test_cohort_summary_filters_by_programme(client: AsyncClient) -> None:
    tokens = await register(
        client, tenant_name="SYNTH Uni A", email="admin6@example.com", role="admin"
    )
    token = tokens["access_token"]

    await _create_student(client, token, "SYNTH-R-0011", gpa=1.0, programme="Nursing")
    await _create_student(client, token, "SYNTH-R-0012", gpa=1.0, programme="Computer Science")

    await client.post("/api/v1/risk/score", json={}, headers=auth_headers(token))

    response = await client.get(
        "/api/v1/risk/cohort", params={"programme": "Nursing"}, headers=auth_headers(token)
    )
    counts = response.json()["tier_counts"]
    assert counts["total"] == 1


async def test_cross_tenant_risk_score_history_returns_404(client: AsyncClient) -> None:
    tenant_a_tokens = await register(
        client, tenant_name="SYNTH Tenant A", email="a-admin@example.com", role="admin"
    )
    student = await _create_student(
        client, tenant_a_tokens["access_token"], "SYNTH-R-0013", gpa=2.0
    )
    await client.post(
        "/api/v1/risk/score", json={}, headers=auth_headers(tenant_a_tokens["access_token"])
    )

    tenant_b_tokens = await register(
        client, tenant_name="SYNTH Tenant B", email="b-admin@example.com", role="admin"
    )
    response = await client.get(
        f"/api/v1/students/{student['id']}/risk-scores",
        headers=auth_headers(tenant_b_tokens["access_token"]),
    )
    assert response.status_code == 404
