from __future__ import annotations

from tests.support import register_doctor, schedule_all_week


def test_login_wrong_password_returns_401(client):
    register_doctor(client, email="login401@example.com", name="Dr L")
    r = client.post("/auth/login", json={"email": "login401@example.com", "password": "wrongpassword"})
    assert r.status_code == 401


def test_login_unknown_email_returns_401(client):
    r = client.post("/auth/login", json={"email": "nobody@example.com", "password": "secret12"})
    assert r.status_code == 401


def test_register_doctor_duplicate_email_returns_409(client):
    body = {
        "name": "Dr D",
        "email": "dupdoc@example.com",
        "address": "Sofia",
        "password": "secret12",
        "schedule": schedule_all_week(),
    }
    assert client.post("/auth/register-doctor", json=body).status_code == 200
    r = client.post("/auth/register-doctor", json=body)
    assert r.status_code == 409


def test_register_patient_unknown_doctor_id_returns_404(client):
    r = client.post(
        "/auth/register-patient",
        json={
            "name": "P",
            "email": "orphan@example.com",
            "phone": "+359888000099",
            "password": "secret12",
            "doctor_id": 999_999,
        },
    )
    assert r.status_code == 404


def test_register_patient_non_doctor_user_id_returns_404(client):
    doctor_id = register_doctor(client, email="nddoc@example.com", name="Dr ND")
    r = client.post(
        "/auth/register-patient",
        json={
            "name": "P1",
            "email": "p1nd@example.com",
            "phone": "+359888000101",
            "password": "secret12",
            "doctor_id": doctor_id,
        },
    )
    assert r.status_code == 200, r.text
    patient_user_id = r.json()["id"]
    r = client.post(
        "/auth/register-patient",
        json={
            "name": "P2",
            "email": "p2nd@example.com",
            "phone": "+359888000102",
            "password": "secret12",
            "doctor_id": patient_user_id,
        },
    )
    assert r.status_code == 404


def test_global_email_doctor_then_patient_conflict_returns_409(client):
    doctor_id = register_doctor(client, email="same@example.com", name="DrX")
    r = client.post(
        "/auth/register-patient",
        json={
            "name": "PX",
            "email": "same@example.com",
            "phone": "+359888000009",
            "password": "secret12",
            "doctor_id": doctor_id,
        },
    )
    assert r.status_code == 409


def test_global_email_patient_then_doctor_conflict_returns_409(client):
    doctor_id = register_doctor(client, email="docuniq@example.com", name="Dr Base")
    r = client.post(
        "/auth/register-patient",
        json={
            "name": "PY",
            "email": "unique@example.com",
            "phone": "+359888000010",
            "password": "secret12",
            "doctor_id": doctor_id,
        },
    )
    assert r.status_code == 200, r.text
    r = client.post(
        "/auth/register-doctor",
        json={
            "name": "DrY",
            "email": "unique@example.com",
            "address": "Sofia",
            "password": "secret12",
            "schedule": schedule_all_week(),
        },
    )
    assert r.status_code == 409
