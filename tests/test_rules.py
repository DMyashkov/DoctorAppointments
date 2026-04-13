from __future__ import annotations

from datetime import timedelta

import pytest
from app.db import Base
from app.enums import AppointmentStatus, CancelledBy, UserRole
from app.exceptions import BadRequestError
from app.models import Appointment, DoctorProfile, PatientProfile, User
from app.schedule_codec import schedule_to_json
from app.services.appointments import cancel_appointment
from app.time_utils import utc_now_naive
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


def _schedule_all_week():
    return {
        "monday": [("08:00", "20:00")],
        "tuesday": [("08:00", "20:00")],
        "wednesday": [("08:00", "20:00")],
        "thursday": [("08:00", "20:00")],
        "friday": [("08:00", "20:00")],
        "saturday": [("08:00", "20:00")],
        "sunday": [("08:00", "20:00")],
    }


def _setup(client):
    r = client.post(
        "/auth/register-doctor",
        json={
            "name": "Dr",
            "email": "dr2@example.com",
            "address": "Sofia",
            "password": "secret12",
            "schedule": _schedule_all_week(),
        },
    )
    assert r.status_code == 200, r.text
    doctor_id = r.json()["id"]

    r = client.post(
        "/auth/register-patient",
        json={
            "name": "P2",
            "email": "p2@example.com",
            "phone": "+359888000001",
            "password": "secret12",
            "doctor_id": doctor_id,
        },
    )
    assert r.status_code == 200, r.text

    r = client.post("/auth/login", json={"email": "p2@example.com", "password": "secret12"})
    token_patient = r.json()["access_token"]

    r = client.post("/auth/login", json={"email": "dr2@example.com", "password": "secret12"})
    token_doctor = r.json()["access_token"]

    return doctor_id, token_patient, token_doctor


def test_24h_rule(client):
    doctor_id, token_patient, _ = _setup(client)

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


def test_overlap_rule(client):
    doctor_id, token_patient, _ = _setup(client)

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


def test_cancel_window_12h(client):
    doctor_id, token_patient, token_doctor = _setup(client)

    now = utc_now_naive()
    start = (now + timedelta(days=2)).replace(hour=10, minute=0, second=0, microsecond=0)
    end = start + timedelta(minutes=30)
    r = client.post(
        "/appointments",
        headers={"Authorization": f"Bearer {token_patient}"},
        json={"doctor_id": doctor_id, "start_at": start.isoformat(), "end_at": end.isoformat()},
    )
    assert r.status_code == 200, r.text
    appt_id = r.json()["id"]

    r = client.post(f"/appointments/{appt_id}/cancel", headers={"Authorization": f"Bearer {token_doctor}"})
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "cancelled"


def test_cancel_rejected_within_12h_service_level():
    engine = create_engine("sqlite+pysqlite:///:memory:", connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()
    try:
        user_doctor = User(name="Dr", email="doc@example.com", password_hash="x", role=UserRole.doctor)
        db.add(user_doctor)
        db.commit()
        db.refresh(user_doctor)

        doctor = DoctorProfile(
            user_id=user_doctor.id,
            address="Sofia",
            schedule_json=schedule_to_json(_schedule_all_week()),
        )
        db.add(doctor)
        db.commit()
        db.refresh(doctor)

        user_patient = User(name="P", email="pat@example.com", password_hash="x", role=UserRole.patient)
        db.add(user_patient)
        db.commit()
        db.refresh(user_patient)

        patient = PatientProfile(user_id=user_patient.id, phone="1", doctor_id=user_doctor.id)
        db.add(patient)
        db.commit()
        db.refresh(patient)

        start = utc_now_naive() + timedelta(hours=11)
        appt = Appointment(
            doctor_id=user_doctor.id,
            patient_id=user_patient.id,
            start_at=start,
            end_at=start + timedelta(minutes=30),
            status=AppointmentStatus.active,
        )
        db.add(appt)
        db.commit()
        db.refresh(appt)

        with pytest.raises(BadRequestError):
            cancel_appointment(db=db, appt=appt, by_role=CancelledBy.patient, now=utc_now_naive())
    finally:
        db.close()


def test_global_email_uniqueness(client):
    r = client.post(
        "/auth/register-doctor",
        json={
            "name": "DrX",
            "email": "same@example.com",
            "address": "Sofia",
            "password": "secret12",
            "schedule": _schedule_all_week(),
        },
    )
    assert r.status_code == 200, r.text
    doctor_id = r.json()["id"]

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
    assert r.status_code == 409, r.text

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
            "schedule": _schedule_all_week(),
        },
    )
    assert r.status_code == 409, r.text
