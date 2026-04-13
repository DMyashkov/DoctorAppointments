from __future__ import annotations

from dataclasses import dataclass

from ..interfaces.repositories import (
    AppointmentsRepository,
    DoctorProfilesRepository,
    PatientProfilesRepository,
    Repositories,
    ScheduleChangesRepository,
    UsersRepository,
)
from . import appointments, doctor_profiles, patient_profiles, schedule_changes, users


class SqlAlchemyUsersRepository(UsersRepository):
    get_user_by_email = staticmethod(users.get_user_by_email)
    get_user_by_id = staticmethod(users.get_user_by_id)
    create_user = staticmethod(users.create_user)


class SqlAlchemyDoctorProfilesRepository(DoctorProfilesRepository):
    get_doctor_profile_by_user_id = staticmethod(doctor_profiles.get_doctor_profile_by_user_id)
    update_doctor_schedule_json = staticmethod(doctor_profiles.update_doctor_schedule_json)
    create_doctor_profile = staticmethod(doctor_profiles.create_doctor_profile)


class SqlAlchemyPatientProfilesRepository(PatientProfilesRepository):
    get_patient_profile_by_user_id = staticmethod(patient_profiles.get_patient_profile_by_user_id)
    create_patient_profile = staticmethod(patient_profiles.create_patient_profile)


class SqlAlchemyAppointmentsRepository(AppointmentsRepository):
    get_appointment_by_id = staticmethod(appointments.get_appointment_by_id)
    list_appointments_for_user = staticmethod(appointments.list_appointments_for_user)
    find_active_overlapping_appointment = staticmethod(appointments.find_active_overlapping_appointment)
    create_appointment = staticmethod(appointments.create_appointment)
    save_appointment = staticmethod(appointments.save_appointment)


class SqlAlchemyScheduleChangesRepository(ScheduleChangesRepository):
    get_temporary_schedule_change_by_doctor_user_id = staticmethod(
        schedule_changes.get_temporary_schedule_change_by_doctor_user_id
    )
    replace_temporary_schedule_change = staticmethod(schedule_changes.replace_temporary_schedule_change)
    find_permanent_schedule_change_for_doctor_on_date = staticmethod(
        schedule_changes.find_permanent_schedule_change_for_doctor_on_date
    )
    create_permanent_schedule_change = staticmethod(schedule_changes.create_permanent_schedule_change)
    get_latest_permanent_schedule_change_on_or_before = staticmethod(
        schedule_changes.get_latest_permanent_schedule_change_on_or_before
    )


@dataclass(frozen=True)
class SqlAlchemyRepositories(Repositories):
    users: UsersRepository = SqlAlchemyUsersRepository()
    doctor_profiles: DoctorProfilesRepository = SqlAlchemyDoctorProfilesRepository()
    patient_profiles: PatientProfilesRepository = SqlAlchemyPatientProfilesRepository()
    appointments: AppointmentsRepository = SqlAlchemyAppointmentsRepository()
    schedule_changes: ScheduleChangesRepository = SqlAlchemyScheduleChangesRepository()


_DEFAULT_REPOS = SqlAlchemyRepositories()


def get_repositories() -> Repositories:
    return _DEFAULT_REPOS

