# pages/04_Facilities_Resources.py

import streamlit as st

from db.queries import getFacilities, getFacilityResources


def main() -> None:
    st.title("Facilities & Resources")

    facilities_df = getFacilities(activeOnly=False)
    if facilities_df.empty:
        st.error("No facilities found.")
        return

    st.subheader("Facilities")
    st.dataframe(facilities_df, use_container_width=True)

    facility_labels = (
        facilities_df["name"]
        + " ("
        + facilities_df["city"]
        + ", "
        + facilities_df["state"]
        + ")"
    )
    selected_label = st.selectbox(
        "Select a facility to view resources",
        options=facility_labels,
    )
    idx = facility_labels[facility_labels == selected_label].index[0]
    facility_id = int(facilities_df.loc[idx, "facility_id"])

    st.markdown("---")
    st.subheader("Resources at Selected Facility")

    resources_df = getFacilityResources(facility_id)
    if resources_df.empty:
        st.info("No resources configured for this facility.")
    else:
        st.dataframe(resources_df, use_container_width=True)


if __name__ == "__main__":
    main()
