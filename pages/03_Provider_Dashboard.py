# pages/03_Provider_Dashboard.py

import streamlit as st

from db.queries import (
    getProviders,
    getProviderById,
    getProviderSchedule,
    getProviderPanel,
    getProviderRecentEncounters,
)


def badgeCurrentProvider() -> None:
    """
    Show who is 'logged in' based on app.py sidebar selection.
    """
    provider_name = st.session_state.get("current_provider_name")
    if provider_name:
        st.caption(f"Logged in as **{provider_name}**")
    else:
        st.warning(
            "No provider selected in the main dashboard sidebar. "
            "You can still view any provider below."
        )


def main() -> None:
    st.title("Provider Dashboard")
    badgeCurrentProvider()

    # ---------- Load providers ----------
    providers_df = getProviders(activeOnly=True)
    if providers_df.empty:
        st.error("No providers found.")
        return

    provider_labels = (
        providers_df["last_name"]
        + ", "
        + providers_df["first_name"]
        + " ("
        + providers_df["specialty_name"].fillna("")
        + ")"
    )

    # Default to the provider selected in app.py sidebar if available
    current_id = st.session_state.get("current_provider_id")
    default_index = 0
    if current_id is not None:
        matches = providers_df.index[providers_df["provider_id"] == current_id]
        if len(matches) > 0:
            default_index = int(matches[0])

    selected_label = st.selectbox(
        "Select a provider",
        options=provider_labels,
        index=default_index,
    )
    idx = provider_labels[provider_labels == selected_label].index[0]
    provider_id = int(providers_df.loc[idx, "provider_id"])

    # Keep in session so other pages can use it if needed
    st.session_state["selected_provider_id"] = provider_id

    # ---------- Provider header info ----------
    provider = getProviderById(provider_id)
    if provider is None:
        st.error("Provider not found.")
        return

    st.subheader(
        f"Dr. {provider['first_name']} {provider['last_name']} "
        f"({provider['specialty_name']})"
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.write(f"**NPI:** {provider['npi']}")
        st.write(f"**Phone:** {provider['phone']}")
        st.write(f"**Email:** {provider['email']}")

    with col2:
        st.write(f"**Specialty code:** {provider['specialty_code']}")
        st.write(f"**Facility ID:** {provider['facility_id']}")

    with col3:
        active = "Yes" if provider["active"] else "No"
        st.write(f"**Active:** {active}")
        st.write(f"**Created:** {provider['created_at']}")
        st.write(f"**Updated:** {provider['updated_at']}")

    st.markdown("---")

    # ---------- Load panel, schedule, encounters ----------
    panel_df = getProviderPanel(provider_id)
    schedule_df = getProviderSchedule(provider_id, days=1)
    encounters_df = getProviderRecentEncounters(provider_id)

    col1, col2, col3 = st.columns(3)
    col1.metric("Panel Size (approx)", f"{len(panel_df)}")
    col2.metric("Appts Next 24h", f"{len(schedule_df)}")
    col3.metric("Recent Encounters", f"{len(encounters_df)}")

    st.markdown("---")

    tab_sched, tab_panel, tab_enc = st.tabs(
        ["Schedule (Next 24h)", "Panel", "Recent Encounters"]
    )

    # ---------- Schedule tab ----------
    with tab_sched:
        st.subheader("Upcoming Appointments (Next 24 Hours)")
        if schedule_df.empty:
            st.info("No upcoming appointments for this provider.")
        else:
            st.dataframe(schedule_df, use_container_width=True)

    # ---------- Panel tab ----------
    with tab_panel:
        st.subheader("Panel Patients (Approximate)")
        if panel_df.empty:
            st.info("No panel patients found for this provider.")
        else:
            st.dataframe(panel_df, use_container_width=True)
            st.info(
                "To view a patient's chart, note their **patient_id** and "
                "open the **Patient Chart** page."
            )

    # ---------- Encounters tab ----------
    with tab_enc:
        st.subheader("Recent Encounters")
        if encounters_df.empty:
            st.info("No encounters found for this provider.")
        else:
            st.dataframe(encounters_df, use_container_width=True)


if __name__ == "__main__":
    main()
