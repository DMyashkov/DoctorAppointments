from __future__ import annotations

from datetime import timedelta

from app.time_utils import utc_now_naive, utc_today

from tests.support import (
    login_access_token,
    register_doctor,
    register_patient,
    schedule_weekdays_only,
    slot_weekday_at_least_24h_ahead,
)


def test_temporary_schedule_saved_for_doctor(client):
    register_doctor(client, email="tmpsched@example.com", name="Dr T")
    token = login_access_token(client, "tmpsched@example.com")
    start = utc_now_naive() + timedelta(days=1)
    end = start + timedelta(days=7)
    r = client.post(
        "/doctor/schedule/temporary",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "start_at": start.isoformat(),
            "end_at": end.isoformat(),
            "schedule": {
                "monday": [["10:00", "14:00"]],
                "tuesday": [],
                "wednesday": [],
                "thursday": [],
                "friday": [],
                "saturday": [],
                "sunday": [],
            },
        },
    )
    assert r.status_code == 200, r.text
    assert "saved" in r.json()["message"].lower()


def test_patient_cannot_set_temporary_schedule_returns_403(client):
    doctor_id = register_doctor(client, email="tmpdeny@example.com", name="Dr Deny")
    register_patient(client, email="ptmp@example.com", doctor_id=doctor_id, phone="+359888000500", name="P")
    token = login_access_token(client, "ptmp@example.com")
    start = utc_now_naive() + timedelta(days=1)
    r = client.post(
        "/doctor/schedule/temporary",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "start_at": start.isoformat(),
            "end_at": (start + timedelta(days=2)).isoformat(),
            "schedule": schedule_weekdays_only(),
        },
    )
    assert r.status_code == 403


def test_permanent_schedule_first_succeeds(client):
    register_doctor(client, email="perm1@example.com", name="Dr P1")
    token = login_access_token(client, "perm1@example.com")
    eff = utc_today() + timedelta(days=7)
    r = client.post(
        "/doctor/schedule/permanent",
        headers={"Authorization": f"Bearer {token}"},
        json={"effective_from_date": eff.isoformat(), "schedule": schedule_weekdays_only()},
    )
    assert r.status_code == 200, r.text


def test_permanent_schedule_duplicate_effective_date_returns_409(client):
    register_doctor(client, email="permsched@example.com", name="Dr P")
    token = login_access_token(client, "permsched@example.com")
    eff = utc_today() + timedelta(days=7)
    payload = {"effective_from_date": eff.isoformat(), "schedule": schedule_weekdays_only()}
    assert client.post("/doctor/schedule/permanent", headers={"Authorization": f"Bearer {token}"}, json=payload).status_code == 200
    r = client.post("/doctor/schedule/permanent", headers={"Authorization": f"Bearer {token}"}, json=payload)
    assert r.status_code == 409


def test_permanent_schedule_before_seven_day_rule_returns_400(client):
    register_doctor(client, email="permsoon@example.com", name="Dr PS")
    token = login_access_token(client, "permsoon@example.com")
    too_soon = utc_today() + timedelta(days=1)
    r = client.post(
        "/doctor/schedule/permanent",
        headers={"Authorization": f"Bearer {token}"},
        json={"effective_from_date": too_soon.isoformat(), "schedule": schedule_weekdays_only()},
    )
    assert r.status_code == 400


def test_booking_inside_temporary_window_uses_temporary_hours_empty_returns_400(client):
    doctor_id = register_doctor(client, email="efftmp@example.com", name="Dr Eff")
    register_patient(client, email="peff@example.com", doctor_id=doctor_id, phone="+359888000501", name="P")
    doc_token = login_access_token(client, "efftmp@example.com")
    pat_token = login_access_token(client, "peff@example.com")

    slot_start, slot_end = slot_weekday_at_least_24h_ahead(10, 0)
    win_start = slot_start.replace(hour=0, minute=0, second=0, microsecond=0)
    win_end = win_start + timedelta(days=1)

    r = client.post(
        "/doctor/schedule/temporary",
        headers={"Authorization": f"Bearer {doc_token}"},
        json={
            "start_at": win_start.isoformat(),
            "end_at": win_end.isoformat(),
            "schedule": {
                "monday": [],
                "tuesday": [],
                "wednesday": [],
                "thursday": [],
                "friday": [],
                "saturday": [],
                "sunday": [],
            },
        },
    )
    assert r.status_code == 200, r.text

    r = client.post(
        "/appointments",
        headers={"Authorization": f"Bearer {pat_token}"},
        json={"doctor_id": doctor_id, "start_at": slot_start.isoformat(), "end_at": slot_end.isoformat()},
    )
    assert r.status_code == 400
    assert "working hours" in r.text.lower()
