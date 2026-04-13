from __future__ import annotations

from datetime import timedelta

from app.time_utils import utc_now_naive


def _schedule_mon_fri():
    return {
        "monday": [("08:30", "12:00"), ("13:00", "18:30")],
        "tuesday": [("08:30", "12:00"), ("13:00", "18:30")],
        "wednesday": [("08:30", "12:00"), ("13:00", "18:30")],
        "thursday": [("08:30", "12:00"), ("13:00", "18:30")],
        "friday": [("08:30", "12:00"), ("13:00", "18:30")],
        "saturday": [],
        "sunday": [],
    }


def test_register_login_create_and_list(client):
    r = client.post(
        "/auth/register-doctor",
        json={
            "name": "Dr A",
            "email": "dr@example.com",
            "address": "Sofia",
            "password": "secret12",
            "schedule": _schedule_mon_fri(),
        },
    )
    assert r.status_code == 200, r.text
    doctor_id = r.json()["id"]

    r = client.post(
        "/auth/register-patient",
        json={
            "name": "P",
            "email": "p@example.com",
            "phone": "+359888000000",
            "password": "secret12",
            "doctor_id": doctor_id,
        },
    )
    assert r.status_code == 200, r.text

    r = client.post("/auth/login", json={"email": "p@example.com", "password": "secret12"})
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]

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
