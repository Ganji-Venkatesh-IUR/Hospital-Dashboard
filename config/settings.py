"""Central project settings and repository-relative paths."""

from pathlib import Path

PROJECT_NAME = "Hospital Emergency Room Analytics Dashboard"
PROJECT_DESCRIPTION = (
    "An interactive dashboard foundation for analyzing real hospital "
    "emergency room data."
)

ROOT_DIR = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = ROOT_DIR / "data" / "raw"
PROCESSED_DATA_DIR = ROOT_DIR / "data" / "processed"
ASSET_DIR = ROOT_DIR / "assets"
SUPPORTED_DATASET_FILENAME = "Hospital ER_Data.csv"