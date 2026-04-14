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

from tests.support import (
    doctor_and_patient_tokens,
    login_access_token,
    register_doctor,
    register_patient,
    schedule_all_week,
    slot_weekday_at_least_24h_ahead,
)


def _schedule_all_week_tuples():
    day = [("08:00", "20:00")]
    return {
        "monday": day,
        "tuesday": day,
        "wednesday": day,
        "thursday": day,
        "friday": day,
        "saturday": day,
        "sunday": day,
    }


def test_doctor_cancels_distant_appointment_returns_cancelled(client):
    doctor_id, token_patient, token_doctor = doctor_and_patient_tokens(
        client, doc_email="dr2c@example.com", pat_email="p2c@example.com", pat_phone="+359888000011"
    )
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
    r = client.post(
        f"/appointments/{appt_id}/cancel",
        headers={"Authorization": f"Bearer {token_doctor}"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "cancelled"


def test_cancel_unknown_appointment_returns_404(client):
    register_doctor(client, email="cancel404@example.com", name="Dr 404")
    token = login_access_token(client, "cancel404@example.com")
    r = client.post(
        "/appointments/999999/cancel",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 404


def test_patient_cannot_cancel_other_patient_appointment_returns_403(client):
    doctor_id = register_doctor(client, email="doc403@example.com", name="Dr 403")
    register_patient(client, email="pa403@example.com", doctor_id=doctor_id, phone="+359888000106", name="P A")
    register_patient(client, email="pb403@example.com", doctor_id=doctor_id, phone="+359888000107", name="P B")
    token_a = login_access_token(client, "pa403@example.com")
    token_b = login_access_token(client, "pb403@example.com")
    start, end = slot_weekday_at_least_24h_ahead(10, 0)
    r = client.post(
        "/appointments",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"doctor_id": doctor_id, "start_at": start.isoformat(), "end_at": end.isoformat()},
    )
    assert r.status_code == 200, r.text
    appt_id = r.json()["id"]
    r = client.post(
        f"/appointments/{appt_id}/cancel",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert r.status_code == 403


def test_doctor_cannot_cancel_other_doctors_appointment_returns_403(client):
    doctor_a = register_doctor(client, email="docAca@example.com", name="Dr Aca")
    doctor_b = register_doctor(client, email="docBca@example.com", name="Dr Bca")
    register_patient(client, email="paca@example.com", doctor_id=doctor_a, phone="+359888000201", name="P")
    token_p = login_access_token(client, "paca@example.com")
    token_b = login_access_token(client, "docBca@example.com")
    start, end = slot_weekday_at_least_24h_ahead(15, 0)
    r = client.post(
        "/appointments",
        headers={"Authorization": f"Bearer {token_p}"},
        json={"doctor_id": doctor_a, "start_at": start.isoformat(), "end_at": end.isoformat()},
    )
    assert r.status_code == 200, r.text
    appt_id = r.json()["id"]
    r = client.post(
        f"/appointments/{appt_id}/cancel",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert r.status_code == 403


def test_patient_cancels_own_appointment_ok(client):
    doctor_id, _, _ = doctor_and_patient_tokens(
        client, doc_email="pcandoc@example.com", pat_email="pcpat@example.com", pat_phone="+359888200001"
    )
    token_p = login_access_token(client, "pcpat@example.com")
    start, end = slot_weekday_at_least_24h_ahead(11, 0)
    r = client.post(
        "/appointments",
        headers={"Authorization": f"Bearer {token_p}"},
        json={"doctor_id": doctor_id, "start_at": start.isoformat(), "end_at": end.isoformat()},
    )
    assert r.status_code == 200, r.text
    appt_id = r.json()["id"]
    r = client.post(
        f"/appointments/{appt_id}/cancel",
        headers={"Authorization": f"Bearer {token_p}"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "cancelled"


def test_cancel_twice_by_doctor_is_idempotent(client):
    doctor_id, _, token_d = doctor_and_patient_tokens(
        client, doc_email="idmdoc@example.com", pat_email="idmpat@example.com", pat_phone="+359888200002"
    )
    token_p = login_access_token(client, "idmpat@example.com")
    start, end = slot_weekday_at_least_24h_ahead(12, 0)
    r = client.post(
        "/appointments",
        headers={"Authorization": f"Bearer {token_p}"},
        json={"doctor_id": doctor_id, "start_at": start.isoformat(), "end_at": end.isoformat()},
    )
    assert r.status_code == 200, r.text
    appt_id = r.json()["id"]
    r = client.post(
        f"/appointments/{appt_id}/cancel",
        headers={"Authorization": f"Bearer {token_d}"},
    )
    assert r.status_code == 200, r.text
    r = client.post(
        f"/appointments/{appt_id}/cancel",
        headers={"Authorization": f"Bearer {token_d}"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "cancelled"


def test_cancel_within_12h_before_start_raises_at_service():
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
            schedule_json=schedule_to_json(_schedule_all_week_tuples()),
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
