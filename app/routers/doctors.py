from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, schemas
from ..db import get_db
from ..deps import require_doctor
from ..services.doctors_service import (
    add_permanent_schedule_change as add_permanent_schedule_change_service,
)
from ..services.doctors_service import (
    set_temporary_schedule_change as set_temporary_schedule_change_service,
)

router = APIRouter(prefix="/doctor", tags=["doctor"])

@router.post("/schedule/temporary", response_model=schemas.MessageResponse)
def set_temporary_schedule_change(
    payload: schemas.TemporaryScheduleChangeRequest,
    doctor: models.DoctorProfile = Depends(require_doctor),
    db: Session = Depends(get_db),
):
    set_temporary_schedule_change_service(db=db, doctor=doctor, payload=payload)
    return schemas.MessageResponse.with_message("Temporary schedule change saved")


@router.post("/schedule/permanent", response_model=schemas.MessageResponse)
def add_permanent_schedule_change(
    payload: schemas.PermanentScheduleChangeRequest,
    doctor: models.DoctorProfile = Depends(require_doctor),
    db: Session = Depends(get_db),
):
    add_permanent_schedule_change_service(db=db, doctor=doctor, payload=payload)
    return schemas.MessageResponse.with_message("Permanent schedule change added")
