from __future__ import annotations

from datetime import timedelta

from app.time_utils import utc_now_naive

from tests.support import login_access_token, register_doctor, register_patient, schedule_all_week, slot_weekday_at_least_24h_ahead


def test_register_doctor_unknown_schedule_key_returns_422(client):
    r = client.post(
        "/auth/register-doctor",
        json={
            "name": "Dr",
            "email": "badsched@example.com",
            "address": "Sofia",
            "password": "secret12",
            "schedule": {"not_a_day": []},
        },
    )
    assert r.status_code == 422


def test_register_doctor_overlapping_day_intervals_returns_422(client):
    r = client.post(
        "/auth/register-doctor",
        json={
            "name": "Dr",
            "email": "overlap@example.com",
            "address": "Sofia",
            "password": "secret12",
            "schedule": {"monday": [["08:00", "10:00"], ["09:00", "11:00"]]},
        },
    )
    assert r.status_code == 422


def test_appointments_me_without_bearer_returns_401(client):
    r = client.get("/appointments/me")
    assert r.status_code == 401


def test_appointments_me_with_invalid_jwt_returns_401(client):
    r = client.get("/appointments/me", headers={"Authorization": "Bearer not-a-jwt"})
    assert r.status_code == 401


def test_register_patient_invalid_phone_returns_422(client):
    doctor_id = register_doctor(client, email="phonedoc@example.com", name="Dr Ph")
    r = client.post(
        "/auth/register-patient",
        json={
            "name": "Bad Ph",
            "email": "badph@example.com",
            "phone": "not-a-number!!!",
            "password": "secret12",
            "doctor_id": doctor_id,
        },
    )
    assert r.status_code == 422


def test_create_appointment_end_before_start_returns_422(client):
    doctor_id = register_doctor(client, email="intdoc@example.com", name="Dr Int")
    register_patient(client, email="intpat@example.com", doctor_id=doctor_id, phone="+359888000108", name="P Int")
    token = login_access_token(client, "intpat@example.com")
    start, _ = slot_weekday_at_least_24h_ahead(10, 0)
    end = start - timedelta(minutes=30)
    r = client.post(
        "/appointments",
        headers={"Authorization": f"Bearer {token}"},
        json={"doctor_id": doctor_id, "start_at": start.isoformat(), "end_at": end.isoformat()},
    )
    assert r.status_code == 422


def test_temporary_schedule_end_before_start_returns_422(client):
    register_doctor(client, email="tmpint@example.com", name="Dr TI")
    token = login_access_token(client, "tmpint@example.com")
    t0 = utc_now_naive()
    start = t0 + timedelta(days=2)
    end = t0 + timedelta(days=1)
    r = client.post(
        "/doctor/schedule/temporary",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "start_at": start.isoformat(),
            "end_at": end.isoformat(),
            "schedule": schedule_all_week(),
        },
    )
    assert r.status_code == 422
