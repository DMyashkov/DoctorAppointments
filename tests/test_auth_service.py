from __future__ import annotations

import os

os.environ.setdefault("JWT_SECRET", "test-secret")

import pytest
from app.db import Base
from app.exceptions import UnauthorizedError
from app.schemas import DoctorRegisterRequest, LoginRequest
from app.services.auth_service import login, register_doctor
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


def _db() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)
    return SessionLocal()


def test_auth_service_register_and_login_doctor():
    db = _db()
    try:
        doc = register_doctor(
            db=db,
            payload=DoctorRegisterRequest(
                name="Dr",
                email="dr@example.com",
                address="Sofia",
                password="secret12",
                schedule={},
            ),
        )
        assert doc.user_id is not None
        assert doc.email == "dr@example.com"

        token = login(db=db, payload=LoginRequest(email="dr@example.com", password="secret12"))
        assert token.access_token
        assert token.token_type == "bearer"
    finally:
        db.close()


def test_auth_service_login_rejects_wrong_password():
    db = _db()
    try:
        register_doctor(
            db=db,
            payload=DoctorRegisterRequest(
                name="Dr",
                email="dr@example.com",
                address="Sofia",
                password="secret12",
                schedule={},
            ),
        )

        with pytest.raises(UnauthorizedError):
            login(db=db, payload=LoginRequest(email="dr@example.com", password="wrongpass"))
    finally:
        db.close()
