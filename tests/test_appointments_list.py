from __future__ import annotations

from tests.support import (
    doctor_and_patient_tokens,
    login_access_token,
    register_doctor,
    register_patient,
    slot_weekday_at_least_24h_ahead,
)


def test_appointments_me_empty_for_new_patient(client):
    doctor_id = register_doctor(client, email="emptydoc@example.com", name="Dr E")
    register_patient(client, email="emptyp@example.com", doctor_id=doctor_id, phone="+359888000400", name="P")
    token = login_access_token(client, "emptyp@example.com")
    r = client.get("/appointments/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json() == []


def test_appointments_me_doctor_empty_when_no_bookings(client):
    register_doctor(client, email="nodoc@example.com", name="Dr No")
    token = login_access_token(client, "nodoc@example.com")
    r = client.get("/appointments/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json() == []


def test_same_booking_visible_to_patient_and_doctor(client):
    doctor_id, _, _ = doctor_and_patient_tokens(
        client, doc_email="listdoc@example.com", pat_email="listpat@example.com", pat_phone="+359888200003"
    )
    token_p = login_access_token(client, "listpat@example.com")
    token_d = login_access_token(client, "listdoc@example.com")
    start, end = slot_weekday_at_least_24h_ahead(14, 0)
    r = client.post(
        "/appointments",
        headers={"Authorization": f"Bearer {token_p}"},
        json={"doctor_id": doctor_id, "start_at": start.isoformat(), "end_at": end.isoformat()},
    )
    assert r.status_code == 200, r.text
    appt_id = r.json()["id"]
    r = client.get("/appointments/me", headers={"Authorization": f"Bearer {token_p}"})
    assert r.status_code == 200
    assert any(a["id"] == appt_id for a in r.json())
    r = client.get("/appointments/me", headers={"Authorization": f"Bearer {token_d}"})
    assert r.status_code == 200
    assert any(a["id"] == appt_id for a in r.json())
