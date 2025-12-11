# pages/05_New_Clinical_Entries.py

from datetime import datetime, date, time, timedelta

import streamlit as st

from db.queries import (
    getFacilities,
    getPatientTreatmentPlans,
    getMedications,   # we'll add this helper in a second
    getResources,     # same here
)
from db.write_queries import (
    createEncounter,
    createAppointment,
    createTreatmentPlanItem,
)


def getCurrentProviderId() -> int | None:
    return st.session_state.get("current_provider_id")


def badgeCurrentProvider() -> None:
    provider_name = st.session_state.get("current_provider_name")
    if provider_name:
        st.caption(f"Logged in as **{provider_name}**")
    else:
        st.warning("No provider logged in from the main dashboard.")


def main() -> None:
    st.title("New Clinical Entries")
    badgeCurrentProvider()

    tabs = st.tabs(
        [
            "New Encounter",
            "New Appointment",
            "New Treatment Plan Item",
        ]
    )

    # ---------- New Encounter ----------
    with tabs[0]:
        st.subheader("Record New Encounter")

        provider_id = getCurrentProviderId()
        if provider_id is None:
            st.error(
                "No provider is currently logged in. "
                "Select a provider in the main dashboard sidebar."
            )
        else:
            with st.form("new_encounter_form"):
                patient_id = st.number_input(
                    "Patient ID", min_value=1, step=1
                )

                facilities_df = getFacilities(activeOnly=True)
                facility_id = None
                if facilities_df.empty:
                    st.warning("No facilities configured.")
                else:
                    facility_labels = (
                        facilities_df["name"]
                        + " ("
                        + facilities_df["city"]
                        + ", "
                        + facilities_df["state"]
                        + ")"
                    )
                    selected_label = st.selectbox(
                        "Facility", options=facility_labels
                    )
                    idx = facility_labels[
                        facility_labels == selected_label
                    ].index[0]
                    facility_id = int(
                        facilities_df.loc[idx, "facility_id"]
                    )

                enc_date = st.date_input("Encounter date", value=date.today())
                enc_time = st.time_input(
                    "Encounter time", value=datetime.now().time()
                )
                reason = st.text_input("Reason for visit")
                notes = st.text_area("Notes (optional)")

                submitted = st.form_submit_button("Create Encounter")

                if submitted:
                    encounter_dt = datetime.combine(enc_date, enc_time)
                    enc_id = createEncounter(
                        patientId=int(patient_id),
                        providerId=int(provider_id),
                        facilityId=facility_id,
                        encounterDt=encounter_dt,
                        reason=reason,
                        notes=notes or None,
                    )
                    st.success(f"Encounter created (ID = {enc_id}).")

    # ---------- New Appointment ----------
    with tabs[1]:
        st.subheader("Schedule New Appointment")

        provider_id = getCurrentProviderId()
        if provider_id is None:
            st.error(
                "No provider is currently logged in. "
                "Select a provider in the main dashboard sidebar."
            )
        else:
            with st.form("new_appt_form"):
                patient_id = st.number_input(
                    "Patient ID ", min_value=1, step=1, key="appt_patient_id"
                )

                facilities_df = getFacilities(activeOnly=True)
                facility_id = None
                if facilities_df.empty:
                    st.warning("No facilities configured.")
                else:
                    facility_labels = (
                        facilities_df["name"]
                        + " ("
                        + facilities_df["city"]
                        + ", "
                        + facilities_df["state"]
                        + ")"
                    )
                    selected_label = st.selectbox(
                        "Facility",
                        options=facility_labels,
                        key="appt_facility",
                    )
                    idx = facility_labels[
                        facility_labels == selected_label
                    ].index[0]
                    facility_id = int(
                        facilities_df.loc[idx, "facility_id"]
                    )

                start_date = st.date_input(
                    "Start date", value=date.today(), key="appt_date"
                )
                start_time = st.time_input(
                    "Start time", value=time(9, 0), key="appt_start_time"
                )
                duration_minutes = st.number_input(
                    "Duration (minutes)", min_value=15, max_value=240, value=30
                )

                reason = st.text_input(
                    "Reason for appointment", key="appt_reason"
                )
                status = st.selectbox(
                    "Status",
                    options=[
                        "Scheduled",
                        "CheckedIn",
                        "Completed",
                        "Canceled",
                    ],
                    index=0,
                )

                submitted = st.form_submit_button("Create Appointment")
                if submitted:
                    start_dt = datetime.combine(start_date, start_time)
                    end_dt = start_dt + timedelta(minutes=int(duration_minutes))

                    appt_id = createAppointment(
                        patientId=int(patient_id),
                        providerId=int(provider_id),
                        facilityId=facility_id,
                        startTime=start_dt,
                        endTime=end_dt,
                        reason=reason,
                        status=status,
                    )
                    st.success(f"Appointment created (ID = {appt_id}).")

    # ---------- New Treatment Plan Item ----------
    with tabs[2]:
        st.subheader("Add Treatment Plan Item")

        with st.form("new_tpi_form"):
            patient_id = st.number_input(
                "Patient ID",
                min_value=1,
                step=1,
                key="tpi_patient_id",
            )

            # load patient's plans to choose from
            plans_df = getPatientTreatmentPlans(int(patient_id))
            if plans_df.empty:
                st.warning(
                    "No treatment plans found for this patient. "
                    "You must create a plan in SQL for now."
                )
                st.stop()

            plan_labels = (
                plans_df["treatment_plan_id"].astype(str)
                + " - "
                + plans_df["condition_name"].fillna("No condition")
                + " ("
                + plans_df["status"]
                + ")"
            )
            selected_label = st.selectbox(
                "Treatment plan", options=plan_labels
            )
            idx = plan_labels[plan_labels == selected_label].index[0]
            treatment_plan_id = int(
                plans_df.loc[idx, "treatment_plan_id"]
            )

            item_type = st.selectbox(
                "Item type",
                options=["Medication", "Therapy", "Procedure", "Resource"],
            )

            # lookups
            meds_df = getMedications()
            resources_df = getResources()

            medication_id = None
            resource_id = None

            if item_type == "Medication":
                if meds_df.empty:
                    st.warning("No medications defined.")
                else:
                    med_labels = (
                        meds_df["name"]
                        + " "
                        + meds_df["strength"].fillna("")
                    )
                    selected_med = st.selectbox(
                        "Medication", options=med_labels
                    )
                    midx = med_labels[med_labels == selected_med].index[0]
                    medication_id = int(
                        meds_df.loc[midx, "medication_id"]
                    )
            elif item_type in ["Therapy", "Procedure", "Resource"]:
                if resources_df.empty:
                    st.warning("No resources defined.")
                else:
                    res_labels = (
                        resources_df["name"]
                        + " ("
                        + resources_df["category"]
                        + ")"
                    )
                    selected_res = st.selectbox(
                        "Resource", options=res_labels
                    )
                    ridx = res_labels[res_labels == selected_res].index[0]
                    resource_id = int(
                        resources_df.loc[ridx, "resource_id"]
                    )

            instructions = st.text_area("Instructions", height=80)
            frequency = st.text_input("Frequency (e.g., BID, weekly)")
            start_date = st.date_input(
                "Start date", value=date.today(), key="tpi_start"
            )
            end_date = st.date_input(
                "End date (optional)", value=start_date, key="tpi_end"
            )

            submitted = st.form_submit_button("Create Treatment Plan Item")
            if submitted:
                tpi_id = createTreatmentPlanItem(
                    treatmentPlanId=int(treatment_plan_id),
                    itemType=item_type,
                    medicationId=medication_id,
                    resourceId=resource_id,
                    instructions=instructions or None,
                    frequency=frequency or None,
                    startDate=start_date,
                    endDate=end_date,
                )
                st.success(f"Treatment plan item created (ID = {tpi_id}).")


if __name__ == "__main__":
    main()

