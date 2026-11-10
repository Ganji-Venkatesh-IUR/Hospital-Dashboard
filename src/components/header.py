"""Shared dashboard section heading."""

import streamlit as st


def render_page_header(title: str, filter_labels: list[str]) -> None:
    st.caption("HOSPITAL OPERATIONS  /  EMERGENCY DEPARTMENT")
    st.title(title)
    if filter_labels:
        st.caption("Selected filters: " + "  |  ".join(filter_labels))