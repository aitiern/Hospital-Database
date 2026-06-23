# db/queries.py

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Optional

import pandas as pd
from sqlalchemy import text

from .connection import getDbEngine

# ---------- General summary queries ----------


def getCountsSummary() -> dict:
    """
    High-level counts for dashboard: patients, providers, active facilities,
    active treatment plans, upcoming appointments.
    """
    engine = getDbEngine()
    with engine.connect() as conn:
        patients = conn.execute(text("SELECT COUNT(*) FROM patients")).scalar()
        providers = conn.execute(
            text("SELECT COUNT(*) FROM providers WHERE active = 1")
        ).scalar()
        facilities = conn.execute(
            text("SELECT COUNT(*) FROM facilities WHERE active = 1")
        ).scalar()
        active_plans = conn.execute(
            text("SELECT COUNT(*) FROM treatmentplans WHERE status = 'Active'")
        ).scalar()
        today = date.today()
        upcoming_appts = conn.execute(
            text("""
                SELECT COUNT(*) FROM appointments
                WHERE start_time >= :start_of_day AND start_time < :end_of_day
                """),
            {
                "start_of_day": datetime.combine(today, datetime.min.time()),
                "end_of_day": datetime.combine(today, datetime.max.time()),
            },
        ).scalar()

    return {
        "patients": patients or 0,
        "providers": providers or 0,
        "facilities": facilities or 0,
        "active_plans": active_plans or 0,
        "today_appointments": upcoming_appts or 0,
    }


def getTopConditions(limit: int = 10) -> pd.DataFrame:
    """
    Top conditions by patient count.
    """
    engine = getDbEngine()
    sql = text("""
        SELECT
            c.condition_id,
            c.icd10_code,
            c.name,
            c.chronic,
            COUNT(pc.patient_id) AS patient_count
        FROM conditions c
        LEFT JOIN patientconditions pc
            ON c.condition_id = pc.condition_id
        GROUP BY c.condition_id, c.icd10_code, c.name, c.chronic
        ORDER BY patient_count DESC, c.name
        LIMIT :limit
        """)
    with engine.connect() as conn:
        df = pd.read_sql(sql, conn, params={"limit": limit})
    return df


# ---------- Patient list / search ----------


def getPatients(
    searchText: Optional[str] = None,
    city: Optional[str] = None,
    state: Optional[str] = None,
    limit: int = 200,
) -> pd.DataFrame:
    """
    Search patients by MRN / first / last, and optional city/state filters.
    """
    engine = getDbEngine()

    base_sql = """
        SELECT
            p.patient_id,
            p.mrn,
            p.first_name,
            p.last_name,
            p.dob,
            p.sex_at_birth,
            p.gender_identity,
            p.city,
            p.state,
            p.postal_code,
            p.consent_share
        FROM patients p
    """

    filters = []
    params: dict = {"limit": limit}

    if searchText and searchText.strip():
        params["q"] = f"%{searchText.strip()}%"
        filters.append("(p.mrn LIKE :q OR p.first_name LIKE :q OR p.last_name LIKE :q)")

    if city and city.strip():
        params["city"] = city.strip()
        filters.append("p.city = :city")

    if state and state.strip():
        params["state"] = state.strip()
        filters.append("p.state = :state")

    if filters:
        where_clause = " WHERE " + " AND ".join(filters)
    else:
        where_clause = ""

    sql = text(base_sql + where_clause + """
        ORDER BY p.last_name, p.first_name
        LIMIT :limit
        """)

    with engine.connect() as conn:
        df = pd.read_sql(sql, conn, params=params)

    return df


def getPatientById(patientId: int) -> Optional[pd.Series]:
    """
    Returns a single patient's demographic row as a Series, or None.
    """
    engine = getDbEngine()
    sql = text("""
        SELECT
            patient_id,
            mrn,
            first_name,
            last_name,
            dob,
            sex_at_birth,
            gender_identity,
            phone,
            email,
            addr_line1,
            addr_line2,
            city,
            state,
            postal_code,
            consent_share,
            created_at,
            updated_at
        FROM patients
        WHERE patient_id = :patient_id
        """)
    with engine.connect() as conn:
        df = pd.read_sql(sql, conn, params={"patient_id": patientId})
    if df.empty:
        return None
    return df.iloc[0]


# ---------- Patient clinical data ----------


def getPatientConditions(patientId: int) -> pd.DataFrame:
    engine = getDbEngine()
    sql = text("""
        SELECT
            pc.patient_id,
            pc.condition_id,
            c.icd10_code,
            c.name AS condition_name,
            c.chronic,
            pc.onset_date,
            pc.status,
            pc.notes
        FROM patientconditions pc
        JOIN conditions c ON pc.condition_id = c.condition_id
        WHERE pc.patient_id = :patient_id
        ORDER BY pc.onset_date DESC, c.name
        """)
    with engine.connect() as conn:
        return pd.read_sql(sql, conn, params={"patient_id": patientId})


def getPatientMedications(patientId: int) -> pd.DataFrame:
    engine = getDbEngine()
    sql = text("""
        SELECT
            pm.patient_id,
            pm.medication_id,
            m.name AS medication_name,
            m.form,
            m.strength,
            pm.prescribing_provider_id,
            pp.first_name AS provider_first_name,
            pp.last_name AS provider_last_name,
            pm.start_date,
            pm.end_date,
            pm.dosage,
            pm.route,
            pm.frequency,
            pm.status,
            pm.notes
        FROM patientmedications pm
        JOIN medications m
            ON pm.medication_id = m.medication_id
        LEFT JOIN providers pp
            ON pm.prescribing_provider_id = pp.provider_id
        WHERE pm.patient_id = :patient_id
        ORDER BY pm.status DESC, pm.start_date DESC, m.name
        """)
    with engine.connect() as conn:
        return pd.read_sql(sql, conn, params={"patient_id": patientId})


def getPatientTreatmentPlans(patientId: int) -> pd.DataFrame:
    engine = getDbEngine()
    sql = text("""
        SELECT
            tp.treatment_plan_id,
            tp.patient_id,
            tp.condition_id,
            c.icd10_code,
            c.name AS condition_name,
            tp.start_date,
            tp.target_outcome,
            tp.status,
            tp.created_by_provider_id,
            p.first_name AS provider_first_name,
            p.last_name AS provider_last_name,
            tp.created_at
        FROM treatmentplans tp
        LEFT JOIN conditions c ON tp.condition_id = c.condition_id
        LEFT JOIN providers p ON tp.created_by_provider_id = p.provider_id
        WHERE tp.patient_id = :patient_id
        ORDER BY tp.status DESC, tp.start_date DESC
        """)
    with engine.connect() as conn:
        return pd.read_sql(sql, conn, params={"patient_id": patientId})


def getTreatmentPlanItems(treatmentPlanId: int) -> pd.DataFrame:
    engine = getDbEngine()
    sql = text("""
        SELECT
            tpi.tpi_id,
            tpi.treatment_plan_id,
            tpi.item_type,
            tpi.medication_id,
            m.name AS medication_name,
            tpi.resource_id,
            r.name AS resource_name,
            r.category AS resource_category,
            tpi.instructions,
            tpi.frequency,
            tpi.start_date,
            tpi.end_date
        FROM treatmentplanitems tpi
        LEFT JOIN medications m ON tpi.medication_id = m.medication_id
        LEFT JOIN resources r ON tpi.resource_id = r.resource_id
        WHERE tpi.treatment_plan_id = :treatment_plan_id
        ORDER BY tpi.item_type, tpi.start_date
        """)
    with engine.connect() as conn:
        return pd.read_sql(sql, conn, params={"treatment_plan_id": treatmentPlanId})


def getPatientEncounters(patientId: int) -> pd.DataFrame:
    engine = getDbEngine()
    sql = text("""
        SELECT
            e.encounter_id,
            e.patient_id,
            e.provider_id,
            p.first_name AS provider_first_name,
            p.last_name AS provider_last_name,
            e.facility_id,
            f.name AS facility_name,
            e.encounter_dt,
            e.reason,
            e.notes
        FROM encounters e
        LEFT JOIN providers p ON e.provider_id = p.provider_id
        LEFT JOIN facilities f ON e.facility_id = f.facility_id
        WHERE e.patient_id = :patient_id
        ORDER BY e.encounter_dt DESC
        """)
    with engine.connect() as conn:
        return pd.read_sql(sql, conn, params={"patient_id": patientId})


def getPatientAppointments(patientId: int, includePast: bool = True) -> pd.DataFrame:
    engine = getDbEngine()
    base = """
        SELECT
            a.appointment_id,
            a.patient_id,
            a.provider_id,
            p.first_name AS provider_first_name,
            p.last_name AS provider_last_name,
            a.facility_id,
            f.name AS facility_name,
            a.start_time,
            a.end_time,
            a.reason,
            a.status
        FROM appointments a
        LEFT JOIN providers p ON a.provider_id = p.provider_id
        LEFT JOIN facilities f ON a.facility_id = f.facility_id
        WHERE a.patient_id = :patient_id
    """
    params = {"patient_id": patientId}
    if not includePast:
        base += " AND a.start_time >= :now "
        params["now"] = datetime.now()

    base += " ORDER BY a.start_time DESC"

    sql = text(base)
    with engine.connect() as conn:
        return pd.read_sql(sql, conn, params=params)


def getPatientReferrals(patientId: int) -> pd.DataFrame:
    engine = getDbEngine()
    sql = text("""
        SELECT
            r.referral_id,
            r.patient_id,
            r.from_provider_id,
            fp.first_name AS from_first_name,
            fp.last_name AS from_last_name,
            r.to_provider_id,
            tp.first_name AS to_first_name,
            tp.last_name AS to_last_name,
            r.reason,
            r.referral_date,
            r.status,
            r.notes
        FROM referrals r
        LEFT JOIN providers fp ON r.from_provider_id = fp.provider_id
        LEFT JOIN providers tp ON r.to_provider_id = tp.provider_id
        WHERE r.patient_id = :patient_id
        ORDER BY r.referral_date DESC
        """)
    with engine.connect() as conn:
        return pd.read_sql(sql, conn, params={"patient_id": patientId})


def getPatientInsurancePolicies(patientId: int) -> pd.DataFrame:
    engine = getDbEngine()
    sql = text("""
        SELECT
            policy_id,
            patient_id,
            payer_name,
            plan_name,
            member_id,
            group_id,
            coverage_start,
            coverage_end
        FROM insurancepolicies
        WHERE patient_id = :patient_id
        ORDER BY coverage_start DESC
        """)
    with engine.connect() as conn:
        return pd.read_sql(sql, conn, params={"patient_id": patientId})


def getPatientCareTeam(patientId: int) -> pd.DataFrame:
    """
    Returns providers on the patient's care team (via careteams + careteammembers).
    """
    engine = getDbEngine()
    sql = text("""
        SELECT
            ct.care_team_id,
            ct.name AS care_team_name,
            ctm.provider_id,
            p.first_name,
            p.last_name,
            p.specialty_name,
            ctm.role
        FROM careteams ct
        JOIN careteammembers ctm
            ON ct.care_team_id = ctm.care_team_id
        JOIN providers p
            ON ctm.provider_id = p.provider_id
        WHERE ct.patient_id = :patient_id
        ORDER BY ct.name, p.last_name, p.first_name
        """)
    with engine.connect() as conn:
        return pd.read_sql(sql, conn, params={"patient_id": patientId})


# ---------- Providers / schedules ----------


def getProviders(activeOnly: bool = True) -> pd.DataFrame:
    engine = getDbEngine()
    sql = """
        SELECT
            provider_id,
            npi,
            first_name,
            last_name,
            specialty_code,
            specialty_name,
            phone,
            email,
            facility_id,
            active
        FROM providers
    """
    if activeOnly:
        sql += " WHERE active = 1"
    sql += " ORDER BY last_name, first_name"

    with engine.connect() as conn:
        return pd.read_sql(text(sql), conn)


def getProviderById(providerId: int) -> Optional[pd.Series]:
    engine = getDbEngine()
    sql = text("""
        SELECT
            provider_id,
            npi,
            first_name,
            last_name,
            specialty_code,
            specialty_name,
            phone,
            email,
            facility_id,
            active,
            created_at,
            updated_at
        FROM providers
        WHERE provider_id = :provider_id
        """)
    with engine.connect() as conn:
        df = pd.read_sql(sql, conn, params={"provider_id": providerId})
    if df.empty:
        return None
    return df.iloc[0]


def getProviderPanel(providerId: int) -> pd.DataFrame:
    """
    Very simple panel size approximation:
    all patients with this provider in encounters, appointments, or referrals.
    """
    engine = getDbEngine()
    sql = text("""
        SELECT DISTINCT
            p.patient_id,
            p.mrn,
            p.first_name,
            p.last_name,
            p.dob,
            p.sex_at_birth,
            p.city,
            p.state
        FROM patients p
        WHERE p.patient_id IN (
            SELECT patient_id FROM encounters WHERE provider_id = :provider_id
            UNION
            SELECT patient_id FROM appointments WHERE provider_id = :provider_id
            UNION
            SELECT patient_id FROM referrals WHERE from_provider_id = :provider_id
            UNION
            SELECT patient_id FROM referrals WHERE to_provider_id = :provider_id
        )
        ORDER BY p.last_name, p.first_name
        """)
    with engine.connect() as conn:
        return pd.read_sql(sql, conn, params={"provider_id": providerId})


def getProviderSchedule(
    providerId: int,
    days: int = 1,
) -> pd.DataFrame:
    """
    Returns upcoming appointments for a provider over the next `days` days.
    """
    engine = getDbEngine()
    now = datetime.now()
    end = now + timedelta(days=days)

    sql = text("""
        SELECT
            a.appointment_id,
            a.patient_id,
            p.mrn,
            p.first_name,
            p.last_name,
            a.facility_id,
            f.name AS facility_name,
            a.start_time,
            a.end_time,
            a.reason,
            a.status
        FROM appointments a
        JOIN patients p ON a.patient_id = p.patient_id
        LEFT JOIN facilities f ON a.facility_id = f.facility_id
        WHERE a.provider_id = :provider_id
          AND a.start_time >= :start_time
          AND a.start_time < :end_time
        ORDER BY a.start_time
        """)
    with engine.connect() as conn:
        return pd.read_sql(
            sql,
            conn,
            params={
                "provider_id": providerId,
                "start_time": now,
                "end_time": end,
            },
        )


def getProviderRecentEncounters(providerId: int, limit: int = 20) -> pd.DataFrame:
    engine = getDbEngine()
    sql = text("""
        SELECT
            e.encounter_id,
            e.patient_id,
            p.mrn,
            p.first_name,
            p.last_name,
            e.encounter_dt,
            e.reason,
            e.notes
        FROM encounters e
        JOIN patients p ON e.patient_id = p.patient_id
        WHERE e.provider_id = :provider_id
        ORDER BY e.encounter_dt DESC
        LIMIT :limit
        """)
    with engine.connect() as conn:
        return pd.read_sql(
            sql, conn, params={"provider_id": providerId, "limit": limit}
        )


# ---------- Facilities / resources ----------


def getFacilities(activeOnly: bool = True) -> pd.DataFrame:
    engine = getDbEngine()
    sql = """
        SELECT
            facility_id,
            name,
            type,
            phone,
            email,
            addr_line1,
            addr_line2,
            city,
            state,
            postal_code,
            hours_json,
            active
        FROM facilities
    """
    if activeOnly:
        sql += " WHERE active = 1"
    sql += " ORDER BY name"

    with engine.connect() as conn:
        return pd.read_sql(text(sql), conn)


def getFacilityResources(facilityId: int) -> pd.DataFrame:
    engine = getDbEngine()
    sql = text("""
        SELECT
            fr.facility_id,
            f.name AS facility_name,
            fr.resource_id,
            r.name AS resource_name,
            r.category,
            fr.quantity,
            fr.availability,
            fr.notes
        FROM facilityresources fr
        JOIN facilities f ON fr.facility_id = f.facility_id
        JOIN resources r ON fr.resource_id = r.resource_id
        WHERE fr.facility_id = :facility_id
        ORDER BY r.category, r.name
        """)
    with engine.connect() as conn:
        return pd.read_sql(sql, conn, params={"facility_id": facilityId})


def getMedications() -> pd.DataFrame:
    engine = getDbEngine()
    sql = text("""
        SELECT
            medication_id,
            rxnorm_code,
            name,
            form,
            strength
        FROM medications
        ORDER BY name
        """)
    with engine.connect() as conn:
        return pd.read_sql(sql, conn)


def getResources() -> pd.DataFrame:
    engine = getDbEngine()
    sql = text("""
        SELECT
            resource_id,
            name,
            category,
            active
        FROM resources
        ORDER BY category, name
        """)
    with engine.connect() as conn:
        return pd.read_sql(sql, conn)


def getChronicPatientsWithNoRecentEncounter(days: int = 180) -> pd.DataFrame:
    """
    Patients with chronic conditions but no encounter in the last `days` days.
    Uses a subquery so we can safely ORDER BY last_encounter_dt.
    """
    engine = getDbEngine()
    cutoff = datetime.now() - timedelta(days=days)

    sql = text("""
        SELECT *
        FROM (
            SELECT
                p.patient_id,
                p.mrn,
                p.first_name,
                p.last_name,
                p.city,
                p.state,
                c.name AS condition_name,
                MAX(e.encounter_dt) AS last_encounter_dt
            FROM patientconditions pc
            JOIN conditions c ON pc.condition_id = c.condition_id
            JOIN patients p ON pc.patient_id = p.patient_id
            LEFT JOIN encounters e ON pc.patient_id = e.patient_id
            WHERE c.chronic = 1
              AND pc.status = 'Active'
            GROUP BY
                p.patient_id, p.mrn, p.first_name, p.last_name,
                p.city, p.state, c.name
            HAVING (MAX(e.encounter_dt) IS NULL OR MAX(e.encounter_dt) < :cutoff)
        ) AS t
        ORDER BY
            t.last_encounter_dt IS NULL DESC,
            t.last_encounter_dt,
            t.last_name
        """)

    with engine.connect() as conn:
        return pd.read_sql(sql, conn, params={"cutoff": cutoff})


def getActivePlansWithNoRecentEncounter(days: int = 90) -> pd.DataFrame:
    """
    Active treatment plans whose patient has no encounter in last `days` days.
    Uses a subquery so we can safely ORDER BY last_encounter_dt.
    """
    engine = getDbEngine()
    cutoff = datetime.now() - timedelta(days=days)

    sql = text("""
        SELECT *
        FROM (
            SELECT
                tp.treatment_plan_id,
                tp.patient_id,
                p.mrn,
                p.first_name,
                p.last_name,
                c.name AS condition_name,
                tp.start_date,
                tp.status,
                MAX(e.encounter_dt) AS last_encounter_dt
            FROM treatmentplans tp
            JOIN patients p ON tp.patient_id = p.patient_id
            LEFT JOIN conditions c ON tp.condition_id = c.condition_id
            LEFT JOIN encounters e ON tp.patient_id = e.patient_id
            WHERE tp.status = 'Active'
            GROUP BY
                tp.treatment_plan_id,
                tp.patient_id,
                p.mrn,
                p.first_name,
                p.last_name,
                c.name,
                tp.start_date,
                tp.status
            HAVING (MAX(e.encounter_dt) IS NULL OR MAX(e.encounter_dt) < :cutoff)
        ) AS t
        ORDER BY
            t.last_encounter_dt IS NULL DESC,
            t.last_encounter_dt,
            t.start_date
        """)

    with engine.connect() as conn:
        return pd.read_sql(sql, conn, params={"cutoff": cutoff})


def getPatientVitals(patientId: int) -> pd.DataFrame:
    """
    Returns all vitals for a patient, ordered by time, across all types.
    """
    engine = getDbEngine()
    sql = text("""
        SELECT
            vital_id,
            patient_id,
            encounter_id,
            vital_type,
            value,
            unit,
            measured_at
        FROM patient_vitals
        WHERE patient_id = :patient_id
        ORDER BY measured_at ASC, vital_type
        """)
    with engine.connect() as conn:
        return pd.read_sql(sql, conn, params={"patient_id": patientId})


def getPatientVitalsByType(patientId: int, vitalType: str) -> pd.DataFrame:
    """
    Convenience helper: vitals of a single type (e.g., 'BP_SYS').
    """
    engine = getDbEngine()
    sql = text("""
        SELECT
            vital_id,
            patient_id,
            encounter_id,
            vital_type,
            value,
            unit,
            measured_at
        FROM patient_vitals
        WHERE patient_id = :patient_id
          AND vital_type = :vital_type
        ORDER BY measured_at ASC
        """)
    with engine.connect() as conn:
        return pd.read_sql(
            sql,
            conn,
            params={"patient_id": patientId, "vital_type": vitalType},
        )


def getLatestRiskScore(patientId: int) -> pd.Series | None:
    """
    Latest risk score row for a single patient, or None if no scores.
    """
    engine = getDbEngine()
    sql = text("""
        SELECT *
        FROM risk_scores
        WHERE patient_id = :patient_id
        ORDER BY generated_at DESC
        LIMIT 1
        """)
    with engine.connect() as conn:
        df = pd.read_sql(sql, conn, params={"patient_id": patientId})
    if df.empty:
        return None
    return df.iloc[0]


def getHighRiskPatients(
    minScore: float = 0.7, bucketOnly: bool = False
) -> pd.DataFrame:
    """
    Returns patients whose latest risk score is high.

    - minScore: numeric threshold (e.g., 0.7)
    - bucketOnly: if True, only use risk_bucket='High' ignoring the numeric score.
    """
    engine = getDbEngine()
    # Subquery to get latest score per patient
    sql = text("""
        SELECT
            p.patient_id,
            p.mrn,
            p.first_name,
            p.last_name,
            p.city,
            p.state,
            rs.model_name,
            rs.score,
            rs.risk_bucket,
            rs.generated_at
        FROM risk_scores rs
        JOIN (
            SELECT patient_id, MAX(generated_at) AS max_gen
            FROM risk_scores
            GROUP BY patient_id
        ) latest
          ON rs.patient_id = latest.patient_id
         AND rs.generated_at = latest.max_gen
        JOIN patients p ON p.patient_id = rs.patient_id
        WHERE
            (:bucket_only = 1 AND rs.risk_bucket = 'High')
          OR (:bucket_only = 0 AND rs.score >= :min_score)
        ORDER BY rs.score DESC, rs.generated_at DESC
        """)
    with engine.connect() as conn:
        return pd.read_sql(
            sql,
            conn,
            params={
                "min_score": float(minScore),
                "bucket_only": 1 if bucketOnly else 0,
            },
        )


def getEncounterCountsByMonth() -> pd.DataFrame:
    engine = getDbEngine()
    sql = text("""
        SELECT
            dd.year,
            dd.month,
            dd.month_name,
            COUNT(*) AS encounter_count
        FROM fact_encounter fe
        JOIN dim_date dd ON fe.date_key = dd.date_key
        GROUP BY dd.year, dd.month, dd.month_name
        ORDER BY dd.year, dd.month
        """)
    with engine.connect() as conn:
        return pd.read_sql(sql, conn)


def getEncountersByFacility() -> pd.DataFrame:
    engine = getDbEngine()
    sql = text("""
        SELECT
            df.name AS facility_name,
            df.city,
            df.state,
            COUNT(*) AS encounter_count
        FROM fact_encounter fe
        JOIN dim_facility df ON fe.facility_key = df.facility_key
        GROUP BY df.facility_key, df.name, df.city, df.state
        ORDER BY encounter_count DESC
        """)
    with engine.connect() as conn:
        return pd.read_sql(sql, conn)


def getEncountersByProvider() -> pd.DataFrame:
    engine = getDbEngine()
    sql = text("""
        SELECT
            dp.first_name,
            dp.last_name,
            dp.specialty_name,
            COUNT(*) AS encounter_count
        FROM fact_encounter fe
        JOIN dim_provider dp ON fe.provider_key = dp.provider_key
        GROUP BY dp.provider_key, dp.first_name, dp.last_name, dp.specialty_name
        ORDER BY encounter_count DESC
        """)
    with engine.connect() as conn:
        return pd.read_sql(sql, conn)


def getWeekendVsWeekdayEncounters() -> pd.DataFrame:
    engine = getDbEngine()
    sql = text("""
        SELECT
            dd.is_weekend,
            COUNT(*) AS encounter_count
        FROM fact_encounter fe
        JOIN dim_date dd ON fe.date_key = dd.date_key
        GROUP BY dd.is_weekend
        ORDER BY dd.is_weekend
        """)
    with engine.connect() as conn:
        return pd.read_sql(sql, conn)


def getCountsSummary() -> dict:
    engine = getDbEngine()
    sql = text("""
        SELECT
            (SELECT COUNT(*) FROM patients) AS patients,
            (SELECT COUNT(*) FROM providers WHERE active = 1) AS providers,
            (SELECT COUNT(*) FROM facilities WHERE active = 1) AS facilities,
            (SELECT COUNT(*) FROM treatmentplans WHERE status = 'Active') AS active_plans,
            (SELECT COUNT(*) FROM appointments
             WHERE DATE(start_time) = CURDATE()) AS today_appointments
    """)

    with engine.connect() as conn:
        row = conn.execute(sql).mappings().first()
        return dict(row)


def getTopConditions(limit: int = 10) -> pd.DataFrame:
    engine = getDbEngine()
    sql = text("""
        SELECT c.name, c.icd10_code, c.chronic,
               COUNT(*) AS patient_count
        FROM patientconditions pc
        JOIN conditions c ON c.condition_id = pc.condition_id
        WHERE pc.status = 'Active'
        GROUP BY c.name, c.icd10_code, c.chronic
        ORDER BY patient_count DESC
        LIMIT :limit
    """)
    with engine.connect() as conn:
        return pd.read_sql(sql, conn, params={"limit": limit})


def getFacilities(activeOnly: bool = False) -> pd.DataFrame:
    engine = getDbEngine()
    where_clause = "WHERE active = 1" if activeOnly else ""
    sql = text(f"SELECT * FROM facilities {where_clause} ORDER BY name")
    with engine.connect() as conn:
        return pd.read_sql(sql, conn)


def getProviders(activeOnly: bool = False) -> pd.DataFrame:
    engine = getDbEngine()
    clause = "WHERE active = 1" if activeOnly else ""
    sql = text(f"""
        SELECT provider_id, first_name, last_name,
               specialty_name, facility_id, active
        FROM providers
        {clause}
        ORDER BY last_name, first_name
    """)
    with engine.connect() as conn:
        return pd.read_sql(sql, conn)
