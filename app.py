"""Streamlit entry point for the Hospital ER Analytics Dashboard."""

from pathlib import Path

import streamlit as st

from config.settings import PROJECT_NAME, RAW_DATA_DIR, SUPPORTED_DATASET_FILENAME
from src.analytics.filters import filter_patients
from src.components.header import render_page_header
from src.components.sidebar import render_sidebar
from src.data.loader import load_csv
from src.pages.consolidated_view import render_consolidated_view
from src.pages.key_takeaways import render_key_takeaways
from src.pages.monthly_view import render_monthly_view
from src.pages.patient_details import render_patient_details


@st.cache_data(show_spinner=False)
def load_dashboard_data(file_path: str, modified_at_ns: int):
    """Cache the loaded dataset, invalidating the cache when the file changes."""
    del modified_at_ns
    return load_csv(Path(file_path))


def _apply_dashboard_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
            --hospital-navy: #174A7E;
            --hospital-blue: #6E9FC5;
            --hospital-border: #DCE4EB;
            --hospital-muted: #607181;
        }
        html, body, .stApp {
            width: 100%;
            max-width: 100%;
            overflow-x: hidden;
        }
        [data-testid="stAppViewContainer"] { background: #FFFFFF; }
        [data-testid="stSidebar"] {
            background: #F5F8FB;
            border-right: 1px solid var(--hospital-border);
        }
        [data-testid="stSidebar"] h2 { color: var(--hospital-navy); }
        .block-container {
            max-width: 1480px;
            width: 100%;
            box-sizing: border-box;
            padding-top: 1.8rem;
            padding-bottom: 3rem;
        }
        h1, h2, h3 { color: #20364A; }
        [data-testid="stMetric"] {
            min-height: 92px;
            padding: 0.7rem 0.9rem;
        }
        [data-testid="stMetricLabel"] { color: var(--hospital-muted); }
        [data-testid="stMetricValue"] { color: var(--hospital-navy); }
        hr { border-color: var(--hospital-border); }
        [data-testid="stPlotlyChart"], [data-testid="stDataFrame"] {
            max-width: 100%;
        }
        @media (max-width: 900px) {
            .block-container {
                max-width: 100%;
                padding: 1.2rem 0.8rem 2rem;
            }
            [data-testid="stHorizontalBlock"] {
                flex-direction: column !important;
                flex-wrap: nowrap !important;
                align-items: stretch !important;
                gap: 0.75rem !important;
            }
            [data-testid="stHorizontalBlock"] > [data-testid="column"] {
                width: 100% !important;
                min-width: 0 !important;
                flex: 1 1 100% !important;
            }
            .st-key-dashboard-kpi-grid [data-testid="stHorizontalBlock"] {
                display: grid !important;
                grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
                gap: 0.55rem !important;
            }
            .st-key-dashboard-kpi-grid [data-testid="stHorizontalBlock"] > [data-testid="column"] {
                width: auto !important;
                min-width: 0 !important;
                flex: unset !important;
            }
            .st-key-dashboard-kpi-grid [data-testid="stMetric"] {
                min-height: 82px;
                padding: 0.5rem 0.6rem;
            }
            .st-key-dashboard-kpi-grid [data-testid="stMetricLabel"] p {
                font-size: 0.78rem;
                line-height: 1.25;
                white-space: normal;
            }
            .st-key-dashboard-kpi-grid [data-testid="stMetricValue"] {
                font-size: 1.15rem;
            }
            [data-testid="stPlotlyChart"], [data-testid="stDataFrame"] {
                width: 100% !important;
                max-width: 100% !important;
                min-width: 0 !important;
                overflow-x: auto;
            }
            h1 { font-size: 1.8rem; }
            h2 { font-size: 1.35rem; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    st.set_page_config(
        page_title=PROJECT_NAME,
        page_icon="🏥",
        layout="wide",
        initial_sidebar_state="auto",
    )
    _apply_dashboard_styles()

    dataset_path = RAW_DATA_DIR / SUPPORTED_DATASET_FILENAME
    if not dataset_path.is_file():
        st.title(PROJECT_NAME)
        st.info("Dataset not found. Add the approved CSV under `data/raw/` to open the dashboard.")
        return

    try:
        dataframe = load_dashboard_data(
            str(dataset_path), dataset_path.stat().st_mtime_ns
        )
    except (FileNotFoundError, OSError, ValueError) as exc:
        st.title(PROJECT_NAME)
        st.error(f"The dataset could not be loaded: {exc}")
        return

    st.success("The configured dataset is available and readable.")
    section, filter_kwargs, filter_labels = render_sidebar(dataframe)
    filtered_data = filter_patients(dataframe, **filter_kwargs)
    render_page_header(section, filter_labels)

    renderers = {
        "Monthly View": render_monthly_view,
        "Consolidated View": render_consolidated_view,
        "Patient Details": render_patient_details,
        "Key Takeaways": render_key_takeaways,
    }
    renderers[section](filtered_data)


main()