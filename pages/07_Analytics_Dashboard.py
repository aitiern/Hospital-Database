# pages/07_Analytics_Dashboard.py

import streamlit as st
import pandas as pd

from db.queries import (
    getEncounterCountsByMonth,
    getEncountersByFacility,
    getEncountersByProvider,
    getWeekendVsWeekdayEncounters,
)


def main() -> None:
    st.title("Analytics Dashboard (OLAP View)")

    st.write(
        "This dashboard uses the dimensional model (dim_date, dim_provider, "
        "dim_facility, fact_encounter) to show high-level trends."
    )

    # ---------- Encounters over time ----------
    st.subheader("Encounters by Month")
    monthly_df = getEncounterCountsByMonth()
    if monthly_df.empty:
        st.info("No encounter data available in the warehouse.")
    else:
        st.dataframe(monthly_df, use_container_width=True)

        chart_df = monthly_df.copy()
        chart_df["year_month"] = (
            chart_df["year"].astype(str)
            + "-"
            + chart_df["month"].astype(str).str.zfill(2)
        )
        chart_df = chart_df.set_index("year_month")[["encounter_count"]]
        st.line_chart(chart_df)

    st.markdown("---")

    # ---------- Facility breakdown ----------
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Encounters by Facility")
        fac_df = getEncountersByFacility()
        if fac_df.empty:
            st.info("No facility-level encounter data.")
        else:
            st.dataframe(fac_df, use_container_width=True)
            chart_df = fac_df.set_index("facility_name")[["encounter_count"]]
            st.bar_chart(chart_df)

    # ---------- Provider breakdown ----------
    with col2:
        st.subheader("Encounters by Provider")
        prov_df = getEncountersByProvider()
        if prov_df.empty:
            st.info("No provider-level encounter data.")
        else:
            prov_df["provider_name"] = (
                prov_df["last_name"] + ", " + prov_df["first_name"]
            )
            st.dataframe(prov_df, use_container_width=True)
            chart_df = prov_df.set_index("provider_name")[["encounter_count"]]
            st.bar_chart(chart_df)

    st.markdown("---")

    # ---------- Weekend vs weekday ----------
    st.subheader("Weekend vs Weekday Encounters")
    ww_df = getWeekendVsWeekdayEncounters()
    if ww_df.empty:
        st.info("No encounter data for weekend/weekday split.")
    else:
        ww_df["label"] = ww_df["is_weekend"].map({0: "Weekday", 1: "Weekend"})
        st.dataframe(ww_df, use_container_width=True)

        chart_df = ww_df.set_index("label")[["encounter_count"]]
        st.bar_chart(chart_df)


if __name__ == "__main__":
    main()
