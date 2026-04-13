from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, schemas
from ..db import get_db
from ..deps import CurrentUser, get_current_user, require_patient
from ..enums import UserRole
from ..services.appointments import (
    cancel_appointment_as_user,
    create_appointment,
    list_my_appointments,
)

router = APIRouter(prefix="/appointments", tags=["appointments"])


@router.post("", response_model=schemas.AppointmentResponse)
def create(
    payload: schemas.AppointmentCreateRequest,
    patient: models.PatientProfile = Depends(require_patient),
    db: Session = Depends(get_db),
):
    result = create_appointment(
        db=db,
        patient=patient,
        doctor_id=payload.doctor_id,
        start_at=payload.start_at,
        end_at=payload.end_at,
    )
    return schemas.AppointmentResponse.from_appointment_dto(result.appointment)


@router.post("/{appointment_id}/cancel", response_model=schemas.AppointmentResponse)
def cancel(
    appointment_id: int,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    dto = cancel_appointment_as_user(
        db=db,
        user_id=user["general"].id,
        role=UserRole(user["role"]),
        appointment_id=appointment_id,
    )
    return schemas.AppointmentResponse.from_appointment_dto(dto)


@router.get("/me", response_model=list[schemas.AppointmentResponse])
def my_appointments(user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    dtos = list_my_appointments(db=db, user_id=user["general"].id, role=UserRole(user["role"]))
    return [schemas.AppointmentResponse.from_appointment_dto(d) for d in dtos]
