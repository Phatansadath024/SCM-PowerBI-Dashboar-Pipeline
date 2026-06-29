"""Functions for reading WayRTS JobTask export files."""

from pathlib import Path
import pandas as pd


REQUIRED_COLUMNS = [
    "Task ID",
    "Customer",
    "Production Area",
    "Planned Quantity",
    "Actual Quantity",
    "Start Date",
    "Due Date",
    "Work Center",
    "Status",
]


def find_latest_export(input_dir: Path) -> Path:
    """Return the newest Excel export from the WayRTS input folder."""
    candidates = list(input_dir.glob("*.xlsx")) + list(input_dir.glob("*.xlsm"))
    if not candidates:
        raise FileNotFoundError(f"No WayRTS Excel export found in {input_dir}")
    return max(candidates, key=lambda path: path.stat().st_mtime)


def load_wayrts_export(file_path: Path, sheet_name: str | int = 0) -> pd.DataFrame:
    """Load a WayRTS JobTask export and validate the expected columns."""
    df = pd.read_excel(file_path, sheet_name=sheet_name, engine="openpyxl")
    df.columns = [str(col).strip() for col in df.columns]

    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"Missing columns in WayRTS export: {missing}")

    return df[REQUIRED_COLUMNS].copy()
