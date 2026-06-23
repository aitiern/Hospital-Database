# pages/06_Alerts_and_Quality.py

import streamlit as st

from db.queries import (
    getChronicPatientsWithNoRecentEncounter,
    getActivePlansWithNoRecentEncounter,
    getHighRiskPatients,
)


def main() -> None:
    st.title("Alerts & Quality Gaps")

    st.write(
        "These views highlight potential quality gaps such as chronic "
        "patients without recent encounters, treatment plans without "
        "follow-up, and high-risk patients based on model scores."
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        days_chronic = st.number_input(
            "Days without encounter (chronic conditions)",
            min_value=30,
            max_value=730,
            value=180,
            step=30,
        )
    with col2:
        days_plans = st.number_input(
            "Days without encounter (active treatment plans)",
            min_value=30,
            max_value=365,
            value=90,
            step=15,
        )
    with col3:
        min_score = st.number_input(
            "Min risk score for 'High Risk'",
            min_value=0.0,
            max_value=1.0,
            value=0.7,
            step=0.05,
        )

    tabs = st.tabs(
        [
            "Chronic: no recent encounter",
            "Active plans: no recent encounter",
            "High-risk patients",
        ]
    )

    # ---------- Tab 1 ----------
    with tabs[0]:
        st.subheader("Chronic Condition Patients Without Recent Encounter")
        df = getChronicPatientsWithNoRecentEncounter(days=int(days_chronic))
        if df.empty:
            st.success("No patients currently meet this condition (which is good!).")
        else:
            st.warning(
                f"{len(df)} patient(s) have chronic conditions and "
                f"no encounter in the last {int(days_chronic)} days."
            )
            st.dataframe(df, use_container_width=True)

    # ---------- Tab 2 ----------
    with tabs[1]:
        st.subheader("Active Treatment Plans Without Recent Encounter")
        df = getActivePlansWithNoRecentEncounter(days=int(days_plans))
        if df.empty:
            st.success(
                "No active treatment plans are overdue for follow-up "
                "based on the selected threshold."
            )
        else:
            st.warning(
                f"{len(df)} active treatment plans with no encounter "
                f"in the last {int(days_plans)} days."
            )
            st.dataframe(df, use_container_width=True)

    # ---------- Tab 3 ----------
    with tabs[2]:
        st.subheader("High-Risk Patients")
        bucket_only = st.checkbox(
            "Use risk_bucket='High' instead of numeric threshold",
            value=False,
        )
        df = getHighRiskPatients(minScore=float(min_score), bucketOnly=bucket_only)
        if df.empty:
            st.success("No patients currently meet the selected high-risk threshold.")
        else:
            st.warning(f"{len(df)} patient(s) are currently flagged as high-risk.")
            st.dataframe(df, use_container_width=True)


if __name__ == "__main__":
    main()
