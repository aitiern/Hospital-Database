# pages/02_Patient_Chart.py

import streamlit as st
import pandas as pd

from db.queries import (
    getPatientById,
    getPatientConditions,
    getPatientMedications,
    getPatientTreatmentPlans,
    getTreatmentPlanItems,
    getPatientEncounters,
    getPatientAppointments,
    getPatientReferrals,
    getPatientInsurancePolicies,
    getPatientCareTeam,
    getPatientVitals,
    getLatestRiskScore,
)


def main() -> None:
    st.title("Patient Chart")

    patient_id = st.session_state.get("selected_patient_id")
    patient_id = st.number_input(
        "Patient ID",
        min_value=1,
        value=int(patient_id) if patient_id else 1,
        step=1,
        help=(
            "If you came from Patient Explorer, this will be pre-filled. "
            "You can change it to open another chart."
        ),
    )

    patient_row = getPatientById(int(patient_id))
    if patient_row is None:
        st.error("No patient found with that ID.")
        return

    # ---------- header ----------
    st.subheader(
        f"{patient_row['first_name']} {patient_row['last_name']} "
        f"(MRN {patient_row['mrn']})"
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.write(f"**DOB:** {patient_row['dob']}")
        st.write(f"**Sex at birth:** {patient_row['sex_at_birth']}")
        st.write(f"**Gender identity:** {patient_row['gender_identity']}")

    with col2:
        st.write(
            f"**Address:** {patient_row['addr_line1']}, "
            f"{patient_row['city']}, {patient_row['state']} "
            f"{patient_row['postal_code']}"
        )
        st.write(f"**Phone:** {patient_row['phone']}")
        st.write(f"**Email:** {patient_row['email']}")

    with col3:
        consent = "Yes" if patient_row["consent_share"] else "No"
        st.write(f"**Consent to data sharing:** {consent}")
        st.write(f"**Created:** {patient_row['created_at']}")
        st.write(f"**Updated:** {patient_row['updated_at']}")

    st.markdown("---")

    (
        tab_summary,
        tab_conditions,
        tab_meds,
        tab_plans,
        tab_encounters,
        tab_appts,
        tab_referrals,
        tab_ins,
        tab_team,
        tab_vitals,
        tab_risk,
    ) = st.tabs(
        [
            "Summary",
            "Conditions",
            "Medications",
            "Treatment Plans",
            "Encounters",
            "Appointments",
            "Referrals",
            "Insurance",
            "Care Team",
            "Vitals",
            "Risk & Scores",
        ]
    )

    # ---------- Summary ----------
    with tab_summary:
        st.subheader("Clinical Summary")

        conditions_df = getPatientConditions(int(patient_id))
        meds_df = getPatientMedications(int(patient_id))
        plans_df = getPatientTreatmentPlans(int(patient_id))

        col1, col2, col3 = st.columns(3)
        col1.metric("Conditions", f"{len(conditions_df)}")
        col2.metric(
            "Active Medications",
            f"{(meds_df['status'] == 'Active').sum() if not meds_df.empty else 0}",
        )
        col3.metric("Treatment Plans", f"{len(plans_df)}")

        if not conditions_df.empty:
            st.markdown("**Recent Conditions**")
            st.dataframe(conditions_df.head(5), use_container_width=True)

        if not meds_df.empty:
            st.markdown("**Recent Medications**")
            st.dataframe(meds_df.head(5), use_container_width=True)

        if not plans_df.empty:
            st.markdown("**Recent Treatment Plans**")
            st.dataframe(plans_df.head(5), use_container_width=True)

    # ---------- Conditions ----------
    with tab_conditions:
        st.subheader("Conditions")
        df = getPatientConditions(int(patient_id))
        if df.empty:
            st.info("No conditions recorded.")
        else:
            st.dataframe(df, use_container_width=True)

    # ---------- Medications ----------
    with tab_meds:
        st.subheader("Medications")
        df = getPatientMedications(int(patient_id))
        if df.empty:
            st.info("No medications recorded.")
        else:
            st.dataframe(df, use_container_width=True)

    # ---------- Treatment Plans ----------
    with tab_plans:
        st.subheader("Treatment Plans")
        plans_df = getPatientTreatmentPlans(int(patient_id))
        if plans_df.empty:
            st.info("No treatment plans recorded.")
        else:
            st.dataframe(plans_df, use_container_width=True)

            plan_ids = plans_df["treatment_plan_id"].tolist()
            selected_plan_id = st.selectbox(
                "Select a treatment plan to view items",
                options=plan_ids,
            )
            items_df = getTreatmentPlanItems(int(selected_plan_id))
            st.markdown("**Plan Items**")
            if items_df.empty:
                st.info("This plan currently has no items.")
            else:
                st.dataframe(items_df, use_container_width=True)

    # ---------- Encounters ----------
    with tab_encounters:
        st.subheader("Encounters")
        df = getPatientEncounters(int(patient_id))
        if df.empty:
            st.info("No encounters recorded.")
        else:
            st.dataframe(df, use_container_width=True)

    # ---------- Appointments ----------
    with tab_appts:
        st.subheader("Appointments")
        include_past = st.checkbox(
            "Include past appointments", value=True, key="include_past_appts"
        )
        df = getPatientAppointments(
            int(patient_id), includePast=include_past
        )
        if df.empty:
            st.info("No appointments recorded.")
        else:
            st.dataframe(df, use_container_width=True)

    # ---------- Referrals ----------
    with tab_referrals:
        st.subheader("Referrals")
        df = getPatientReferrals(int(patient_id))
        if df.empty:
            st.info("No referrals recorded.")
        else:
            st.dataframe(df, use_container_width=True)

    # ---------- Insurance ----------
    with tab_ins:
        st.subheader("Insurance Policies")
        df = getPatientInsurancePolicies(int(patient_id))
        if df.empty:
            st.info("No insurance policies on file.")
        else:
            st.dataframe(df, use_container_width=True)

    # ---------- Care Team ----------
    with tab_team:
        st.subheader("Care Team")
        df = getPatientCareTeam(int(patient_id))
        if df.empty:
            st.info("No care team members recorded.")
        else:
            st.dataframe(df, use_container_width=True)

    # ---------- Vitals ----------
    with tab_vitals:
        st.subheader("Patient Vitals Over Time")
        vitals_df = getPatientVitals(int(patient_id))
        if vitals_df.empty:
            st.info("No vitals recorded for this patient.")
        else:
            st.dataframe(vitals_df, use_container_width=True)

            # Simple charts for common vitals if available
            for vt_label, vt in [
                ("Systolic BP", "BP_SYS"),
                ("Diastolic BP", "BP_DIA"),
                ("Heart Rate", "HR"),
                ("Weight", "WEIGHT"),
            ]:
                vt_df = vitals_df[vitals_df["vital_type"] == vt]
                if not vt_df.empty:
                    st.markdown(f"**{vt_label}**")
                    chart_df = vt_df.set_index("measured_at")[["value"]]
                    st.line_chart(chart_df)

    # ---------- Risk & Scores ----------
    with tab_risk:
        st.subheader("Risk Scores")

        risk_row = getLatestRiskScore(int(patient_id))
        if risk_row is None:
            st.info("No risk scores on file for this patient.")
        else:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(
                    "Risk Score",
                    f"{risk_row['score']:.3f}",
                )
            with col2:
                st.metric("Risk Bucket", risk_row["risk_bucket"])
            with col3:
                st.write(f"**Model:** {risk_row['model_name']}")
                st.write(f"**Generated:** {risk_row['generated_at']}")

            st.caption(
                "Score and bucket are model outputs stored in the risk_scores table."
            )


if __name__ == "__main__":
    main()

