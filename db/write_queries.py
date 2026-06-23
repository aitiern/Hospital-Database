# db/write_queries.py

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import text

from .connection import getDbEngine

import json


def logAuditEvent(
    entityType: str,
    entityId: int,
    action: str,
    userProviderId: Optional[int] = None,
    oldValues: Optional[dict] = None,
    newValues: Optional[dict] = None,
) -> None:
    """
    Insert a simple audit log entry. Values are serialized as JSON strings.
    """
    engine = getDbEngine()
    sql = text("""
        INSERT INTO audit_log
          (user_provider_id, entity_type, entity_id, action,
           old_values_json, new_values_json)
        VALUES
          (:user_provider_id, :entity_type, :entity_id, :action,
           :old_values_json, :new_values_json)
        """)
    with engine.begin() as conn:
        conn.execute(
            sql,
            {
                "user_provider_id": userProviderId,
                "entity_type": entityType,
                "entity_id": entityId,
                "action": action,
                "old_values_json": json.dumps(oldValues) if oldValues else None,
                "new_values_json": json.dumps(newValues) if newValues else None,
            },
        )


def createEncounter(
    patientId: int,
    providerId: int,
    facilityId: Optional[int],
    encounterDt: datetime,
    reason: str,
    notes: Optional[str] = None,
) -> int:
    """
    Insert a new encounter and return encounter_id.
    """
    engine = getDbEngine()
    sql = text("""
        INSERT INTO encounters
            (patient_id, provider_id, facility_id,
             encounter_dt, reason, notes)
        VALUES
            (:patient_id, :provider_id, :facility_id,
             :encounter_dt, :reason, :notes)
        """)
    with engine.begin() as conn:
        result = conn.execute(
            sql,
            {
                "patient_id": patientId,
                "provider_id": providerId,
                "facility_id": facilityId,
                "encounter_dt": encounterDt,
                "reason": reason,
                "notes": notes,
            },
        )
        encounter_id = result.lastrowid or 0
    return int(encounter_id)


def createAppointment(
    patientId: int,
    providerId: int,
    facilityId: Optional[int],
    startTime,
    endTime,
    reason: str,
    status: str = "Scheduled",
) -> int:
    """
    Insert a new appointment and return appointment_id.
    """
    engine = getDbEngine()
    sql = text("""
        INSERT INTO appointments
            (patient_id, provider_id, facility_id,
             start_time, end_time, reason, status)
        VALUES
            (:patient_id, :provider_id, :facility_id,
             :start_time, :end_time, :reason, :status)
        """)
    with engine.begin() as conn:
        result = conn.execute(
            sql,
            {
                "patient_id": patientId,
                "provider_id": providerId,
                "facility_id": facilityId,
                "start_time": startTime,
                "end_time": endTime,
                "reason": reason,
                "status": status,
            },
        )
        appt_id = result.lastrowid or 0
    return int(appt_id)


def createTreatmentPlanItem(
    treatmentPlanId: int,
    itemType: str,
    medicationId: Optional[int],
    resourceId: Optional[int],
    instructions: Optional[str],
    frequency: Optional[str],
    startDate,
    endDate,
) -> int:
    """
    Insert a new treatment plan item and return tpi_id.
    """
    engine = getDbEngine()
    sql = text("""
        INSERT INTO treatmentplanitems
            (treatment_plan_id, item_type, medication_id, resource_id,
             instructions, frequency, start_date, end_date)
        VALUES
            (:treatment_plan_id, :item_type, :medication_id, :resource_id,
             :instructions, :frequency, :start_date, :end_date)
        """)
    with engine.begin() as conn:
        result = conn.execute(
            sql,
            {
                "treatment_plan_id": treatmentPlanId,
                "item_type": itemType,
                "medication_id": medicationId,
                "resource_id": resourceId,
                "instructions": instructions,
                "frequency": frequency,
                "start_date": startDate,
                "end_date": endDate,
            },
        )
        tpi_id = result.lastrowid or 0
    return int(tpi_id)
