from __future__ import annotations

from datetime import timedelta

from app.time_utils import utc_now_naive

from tests.support import (
    doctor_and_patient_tokens,
    login_access_token,
    next_saturday_at_least_24h,
    register_doctor,
    register_patient,
    schedule_mon_fri,
    schedule_weekdays_only,
    slot_weekday_at_least_24h_ahead,
)


def test_happy_path_register_book_and_list_for_patient(client):
    doctor_id = register_doctor(client, email="dr@example.com", name="Dr A", schedule=schedule_mon_fri())
    register_patient(client, email="p@example.com", doctor_id=doctor_id, phone="+359888000000", name="P")
    token = login_access_token(client, "p@example.com")

    now = utc_now_naive()
    start = now + timedelta(days=2)
    while start.weekday() >= 5:
        start = start + timedelta(days=1)
    start = start.replace(hour=10, minute=0, second=0, microsecond=0)
    end = start + timedelta(minutes=30)

    r = client.post(
        "/appointments",
        headers={"Authorization": f"Bearer {token}"},
        json={"doctor_id": doctor_id, "start_at": start.isoformat(), "end_at": end.isoformat()},
    )
    assert r.status_code == 200, r.text
    appt_id = r.json()["id"]

    r = client.get("/appointments/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200, r.text
    assert any(a["id"] == appt_id for a in r.json())


def test_book_less_than_24h_ahead_returns_400(client):
    doctor_id, token_patient, _ = doctor_and_patient_tokens(
        client, doc_email="dr2@example.com", pat_email="p2@example.com", pat_phone="+359888000001"
    )
    now = utc_now_naive()
    start = (now + timedelta(hours=10)).replace(minute=0, second=0, microsecond=0)
    end = start + timedelta(minutes=30)
    r = client.post(
        "/appointments",
        headers={"Authorization": f"Bearer {token_patient}"},
        json={"doctor_id": doctor_id, "start_at": start.isoformat(), "end_at": end.isoformat()},
    )
    assert r.status_code == 400
    assert "24h" in r.text


def test_book_overlapping_existing_returns_409(client):
    doctor_id, token_patient, _ = doctor_and_patient_tokens(
        client, doc_email="drovl@example.com", pat_email="povr@example.com", pat_phone="+359888000002"
    )
    now = utc_now_naive()
    start = (now + timedelta(days=2)).replace(hour=10, minute=0, second=0, microsecond=0)
    end = start + timedelta(minutes=30)
    r1 = client.post(
        "/appointments",
        headers={"Authorization": f"Bearer {token_patient}"},
        json={"doctor_id": doctor_id, "start_at": start.isoformat(), "end_at": end.isoformat()},
    )
    assert r1.status_code == 200, r1.text
    s2 = (start + timedelta(minutes=15)).isoformat()
    e2 = (end + timedelta(minutes=15)).isoformat()
    r2 = client.post(
        "/appointments",
        headers={"Authorization": f"Bearer {token_patient}"},
        json={"doctor_id": doctor_id, "start_at": s2, "end_at": e2},
    )
    assert r2.status_code == 409, r2.text


def test_book_before_opening_hour_returns_400(client):
    doctor_id = register_doctor(client, email="hours@example.com", name="Dr H")
    register_patient(client, email="ph@example.com", doctor_id=doctor_id, phone="+359888000103", name="PH")
    token = login_access_token(client, "ph@example.com")
    start, end = slot_weekday_at_least_24h_ahead(7, 0)
    r = client.post(
        "/appointments",
        headers={"Authorization": f"Bearer {token}"},
        json={"doctor_id": doctor_id, "start_at": start.isoformat(), "end_at": end.isoformat()},
    )
    assert r.status_code == 400
    assert "working hours" in r.text.lower()


def test_book_on_closed_weekend_returns_400(client):
    doctor_id = register_doctor(
        client, email="weekend@example.com", name="Dr W", schedule=schedule_weekdays_only()
    )
    register_patient(client, email="pw@example.com", doctor_id=doctor_id, phone="+359888000104", name="PW")
    token = login_access_token(client, "pw@example.com")
    start, end = next_saturday_at_least_24h()
    r = client.post(
        "/appointments",
        headers={"Authorization": f"Bearer {token}"},
        json={"doctor_id": doctor_id, "start_at": start.isoformat(), "end_at": end.isoformat()},
    )
    assert r.status_code == 400


def test_book_not_personal_doctor_returns_400(client):
    doctor_a = register_doctor(client, email="dra2@example.com", name="Dr A2")
    doctor_b = register_doctor(client, email="drb2@example.com", name="Dr B2")
    register_patient(client, email="pwd@example.com", doctor_id=doctor_a, phone="+359888000105", name="P WD")
    token = login_access_token(client, "pwd@example.com")
    start, end = slot_weekday_at_least_24h_ahead(10, 0)
    r = client.post(
        "/appointments",
        headers={"Authorization": f"Bearer {token}"},
        json={"doctor_id": doctor_b, "start_at": start.isoformat(), "end_at": end.isoformat()},
    )
    assert r.status_code == 400
    assert "personal doctor" in r.text.lower()


def test_book_doctor_id_zero_returns_422(client):
    doctor_id = register_doctor(client, email="zero@example.com", name="Dr Z")
    register_patient(client, email="pz@example.com", doctor_id=doctor_id, phone="+359888000333", name="PZ")
    token = login_access_token(client, "pz@example.com")
    start, end = slot_weekday_at_least_24h_ahead(10, 0)
    r = client.post(
        "/appointments",
        headers={"Authorization": f"Bearer {token}"},
        json={"doctor_id": 0, "start_at": start.isoformat(), "end_at": end.isoformat()},
    )
    assert r.status_code == 422
