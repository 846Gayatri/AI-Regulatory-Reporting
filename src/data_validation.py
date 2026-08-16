# src/data_validation.py
"""Data validation and preprocessing utilities for the GenAR PADER prototype.

The module provides:
- `load_csv(path)`: read CSV into a pandas DataFrame with normalized column names.
- `deduplicate_cases(df)`: keep one row per unique `safetyreportid`.
- `bucket_age(df)`: create an `age_bucket` column for numeric onset ages.
- `explode_reactions(df)`: split comma‑separated reaction fields into separate rows.

These functions are deliberately simple and deterministic; they are used before any
analysis is performed.
"""

from pathlib import Path
import pandas as pd


def load_csv(file_path: Path) -> pd.DataFrame:
    """Load the ICSR CSV, lower‑case and strip column names.

    Args:
        file_path: Path to the CSV file.
    Returns:
        DataFrame with normalized column names.
    """
    df = pd.read_csv(file_path, low_memory=False)
    df.columns = [c.strip().lower() for c in df.columns]
    return df


def deduplicate_cases(df: pd.DataFrame) -> pd.DataFrame:
    """Return a DataFrame with one row per unique `safetyreportid`.
    The raw file may contain multiple rows per case (one per reaction).
    """
    if "safetyreportid" not in df.columns:
        return df
    return df.drop_duplicates(subset=["safetyreportid"]).reset_index(drop=True)


def bucket_age(df: pd.DataFrame) -> pd.DataFrame:
    """Create an `age_bucket` column for numeric onset ages.
    Ages are expected in the `patient_patientonsetage` column (numeric years).
    """
    if "patient_patientonsetage" not in df.columns:
        return df
    age_series = pd.to_numeric(df["patient_patientonsetage"], errors="coerce")
    bins = [0, 18, 30, 40, 50, 60, 70, 80, 120]
    labels = ["0-17", "18-29", "30-39", "40-49", "50-59", "60-69", "70-79", "80+"]
    df = df.copy()
    df["age_bucket"] = pd.cut(age_series, bins=bins, labels=labels, right=False)
    return df


def explode_reactions(df: pd.DataFrame) -> pd.DataFrame:
    """Explode comma‑separated reaction fields into separate rows.
    Handles `patient_reaction_reactionmeddrapt` if present.
    """
    reaction_col = None
    for col in ["patient_reaction_reactionmeddrapt", "reactionmeddrapt", "reactionterm"]:
        if col in df.columns:
            reaction_col = col
            break
    if not reaction_col:
        return df
    # Split on commas, explode, and strip whitespace
    df = df.copy()
    df[reaction_col] = df[reaction_col].astype(str).str.split(",")
    df = df.explode(reaction_col)
    df[reaction_col] = df[reaction_col].str.strip()
    return df

def load_and_validate(file_path: Path) -> pd.DataFrame:
    """Load CSV, deduplicate cases, bucket ages, and explode reactions.

    Returns a cleaned DataFrame ready for analysis.
    """
    df = load_csv(file_path)
    df = deduplicate_cases(df)
    df = bucket_age(df)
    df = explode_reactions(df)
    return df

