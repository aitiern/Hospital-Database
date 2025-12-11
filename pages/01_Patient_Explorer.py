# pages/01_Patient_Explorer.py

import streamlit as st
import pandas as pd

from db.queries import getPatients


def formatPatientLabel(row: pd.Series) -> str:
    dob = row.get("dob", "")
    sex = row.get("sex_at_birth", "")
    return (
        f"{row['mrn']} - {row['last_name']}, {row['first_name']} "
        f"({sex}, {dob}, {row['city']}, {row['state']})"
    )


def main() -> None:
    st.title("Patient Explorer")

    with st.sidebar:
        st.header("Search Filters")
        search_text = st.text_input(
            "Search by MRN, first or last name",
            placeholder="e.g. 12345 or Smith",
        )
        city = st.text_input("City (optional)")
        state = st.text_input("State (optional)")
        limit = st.slider("Max patients to load", 25, 500, 150, step=25)

    patients_df = getPatients(
        searchText=search_text, city=city, state=state, limit=limit
    )

    if patients_df.empty:
        st.warning("No patients matched your filters.")
        return

    st.subheader("Matching Patients")
    st.dataframe(patients_df, use_container_width=True)

    labels = patients_df.apply(formatPatientLabel, axis=1).tolist()
    selected_label = st.selectbox(
        "Select a patient to focus on",
        options=labels,
    )
    selected_index = labels.index(selected_label)
    selected_patient = patients_df.iloc[selected_index]

    st.markdown("---")
    st.subheader("Quick Patient Snapshot")

    col1, col2 = st.columns(2)

    with col1:
        st.write(f"**Patient ID:** {selected_patient['patient_id']}")
        st.write(f"**MRN:** {selected_patient['mrn']}")
        st.write(
            f"**Name:** {selected_patient['first_name']} "
            f"{selected_patient['last_name']}"
        )
        st.write(f"**DOB:** {selected_patient['dob']}")
        st.write(f"**Sex at birth:** {selected_patient['sex_at_birth']}")

    with col2:
        st.write(
            f"**Location:** {selected_patient['city']}, "
            f"{selected_patient['state']} {selected_patient['postal_code']}"
        )
        consent = "Yes" if selected_patient["consent_share"] else "No"
        st.write(f"**Consent to data sharing:** {consent}")

    # Save to session for Patient Chart page
    st.session_state["selected_patient_id"] = int(
        selected_patient["patient_id"]
    )

    st.info(
        "This patient is now stored as the active selection. "
        "Go to the **Patient Chart** page to view full clinical details."
    )


if __name__ == "__main__":
    main()
