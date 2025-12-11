# Home.py
"""
HealthDB Clinical Platform - Landing Page

This is the main landing page for your HealthDB EHR + Analytics app.
It gives an overview of the system, key metrics, and a guide to the
rest of the pages.
"""

import streamlit as st

from db.queries import (
    getCountsSummary,
    getTopConditions,
    getFacilities,
    getProviders,
)


# ---------- Sidebar: "login" as provider ----------

def renderLoginSidebar() -> None:
    """
    Simple provider 'login': pick an active provider from a dropdown.
    Stores provider_id and display name in session_state.
    """
    with st.sidebar:
        st.header("Provider Login")

        providers_df = getProviders(activeOnly=True)
        if providers_df.empty:
            st.warning("No active providers found.")
            return

        labels = (
            providers_df["last_name"]
            + ", "
            + providers_df["first_name"]
            + " ("
            + providers_df["specialty_name"].fillna("")
            + ")"
        )

        current_id = st.session_state.get("current_provider_id")
        index_default = 0
        if current_id is not None:
            matches = providers_df.index[
                providers_df["provider_id"] == current_id
            ]
            if len(matches) > 0:
                index_default = int(matches[0])

        selected_label = st.selectbox(
            "Logged-in provider",
            options=labels,
            index=index_default,
        )
        idx = labels[labels == selected_label].index[0]
        provider_id = int(providers_df.loc[idx, "provider_id"])
        provider_name = (
            f"{providers_df.loc[idx, 'first_name']} "
            f"{providers_df.loc[idx, 'last_name']}"
        )

        st.session_state["current_provider_id"] = provider_id
        st.session_state["current_provider_name"] = provider_name

        st.caption(f"Current provider: **{provider_name}**")


# ---------- Main page ----------

def main() -> None:
    st.set_page_config(
        page_title="HealthDB Clinical Platform",
        layout="wide",
    )

    renderLoginSidebar()

    st.title("HealthDB Clinical Platform")
    st.subheader("Integrated EHR, Quality Monitoring, and Analytics")

    st.write(
        """
        Welcome to the **HealthDB** application – a teaching-focused,
        clinic-style system that combines:
        - A **normalized transactional EHR** (patients, encounters, meds, plans),
        - A **data warehouse / star schema** for analytics, and
        - A **Streamlit frontend** for providers, staff, and analysts.
        """
    )

    # ---------- KPI metrics from core tables ----------
    counts = getCountsSummary()
    kpi_col1, kpi_col2, kpi_col3, kpi_col4, kpi_col5 = st.columns(5)
    kpi_col1.metric("Patients", f"{counts['patients']}")
    kpi_col2.metric("Active Providers", f"{counts['providers']}")
    kpi_col3.metric("Active Facilities", f"{counts['facilities']}")
    kpi_col4.metric("Active Treatment Plans", f"{counts['active_plans']}")
    kpi_col5.metric("Appointments Today", f"{counts['today_appointments']}")

    st.markdown("---")

    # ---------- Quick navigation overview ----------
    st.subheader("Application Modules")

    nav_col1, nav_col2, nav_col3 = st.columns(3)

    with nav_col1:
        st.markdown("### 🧍 Patient-Centered Views")
        st.markdown(
            """
            **Patient Explorer**  
            - Search patients by MRN / name / location  
            - Set an active patient for the rest of the app  

            **Patient Chart**  
            - Demographics & contact  
            - Conditions & medications  
            - Treatment plans & items  
            - Encounters & appointments  
            - Referrals, insurance, care team  
            - Vitals timeline & model risk score
            """
        )

    with nav_col2:
        st.markdown("### 👨‍⚕️ Provider & Workflow")
        st.markdown(
            """
            **Provider Dashboard**  
            - See a provider's panel size  
            - Upcoming schedule (next 24h)  
            - Recent encounters  

            **New Clinical Entries**  
            - Record new encounters  
            - Schedule new appointments  
            - Add treatment plan items  
            """
        )

    with nav_col3:
        st.markdown("### 📊 Quality & Analytics")
        st.markdown(
            """
            **Alerts & Quality**  
            - Chronic patients with no recent encounters  
            - Active plans without follow-up  
            - High-risk patients based on ML scores  

            **Analytics Dashboard (OLAP)**  
            - Encounters by month (time trend)  
            - Encounters by facility / provider  
            - Weekend vs weekday volumes  
            """
        )

    st.info(
        "Use the **Streamlit sidebar page selector** to navigate to these "
        "modules. The current provider you chose in the sidebar will be used "
        "by the Provider Dashboard and New Clinical Entries pages."
    )

    st.markdown("---")

    # ---------- Top conditions + facilities snapshot ----------
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("### Top Clinical Conditions")
        top_conditions = getTopConditions(limit=10)
        if top_conditions.empty:
            st.info("No condition data available yet.")
        else:
            st.dataframe(top_conditions, use_container_width=True)

    with col_right:
        st.markdown("### Active Facilities")
        facilities_df = getFacilities(activeOnly=True)
        if facilities_df.empty:
            st.info("No facilities configured.")
        else:
            cols_to_show = [
                "name",
                "type",
                "city",
                "state",
                "phone",
            ]
            st.dataframe(
                facilities_df[cols_to_show],
                use_container_width=True,
            )

    st.markdown("---")

    # ---------- Architecture overview ----------
    st.subheader("System Architecture Overview")

    arch_col1, arch_col2 = st.columns(2)

    with arch_col1:
        st.markdown("#### Transactional EHR Layer")
        st.markdown(
            """
            - **Core tables**: patients, providers, facilities, encounters,
              appointments, conditions, medications, treatmentplans, treatmentplanitems  
            - **Care coordination**: care teams, referrals, insurance policies  
            - **Clinical extensions**: patient_vitals, risk_scores  
            - **Auditability**: audit_log (for key write operations)
            """
        )

    with arch_col2:
        st.markdown("#### Analytics & Warehouse Layer")
        st.markdown(
            """
            - **Dimensions**: dim_date, dim_provider, dim_facility, dim_condition  
            - **Facts**: fact_encounter, fact_appointment, fact_treatmentplan  
            - Designed for **OLAP-style queries** about volume, utilization,
              provider productivity, and chronic disease burden.
            """
        )

    st.markdown(
        """
        Together, these layers support both **day-to-day clinical workflows**
        and **longitudinal analytics** from the same logical health database.
        """
    )

    st.markdown("---")

    st.caption(
        "Built with MariaDB/MySQL, SQLAlchemy, and Streamlit as part of an "
        "advanced database concepts project."
    )


if __name__ == "__main__":
    main()
