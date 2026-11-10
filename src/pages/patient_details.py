"""Privacy-conscious patient details section."""

import pandas as pd
import streamlit as st

from src.components.tables import prepare_patient_details, render_bounded_table


def render_patient_details(dataframe: pd.DataFrame) -> None:
    st.subheader("Filtered visit records")
    if dataframe.empty:
        st.info("No visits match the selected filters.")
        return

    details = prepare_patient_details(dataframe)
    row_limit = st.selectbox("Rows to display", [50, 100, 200], index=0)
    shown = min(len(details), row_limit)
    st.caption(f"Showing {shown:,} of {len(details):,} filtered visits")
    render_bounded_table(details, row_limit)