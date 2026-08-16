# src/analysis.py
"""Deterministic data analysis utilities used by the GenAR prototype.
All heavy lifting (counts, aggregations, deduplication) is performed with pandas – no LLM involvement.
"""

from pathlib import Path
import pandas as pd
from typing import Dict, Any, List
import datetime as dt


def load_data(file_path: Path) -> pd.DataFrame:
    """Load CSV or Excel into a DataFrame, normalising column names.

    Args:
        file_path: Path to the dataset (CSV or Excel).
    Returns:
        DataFrame with lower‑cased, stripped column names.
    """
    if file_path.suffix.lower() in {".xlsx", ".xls"}:
        df = pd.read_excel(file_path, engine="openpyxl")
    else:
        df = pd.read_csv(file_path, low_memory=False)
    df.columns = [c.strip().lower() for c in df.columns]
    return df


def deduplicate_cases(df: pd.DataFrame) -> pd.DataFrame:
    """Return one row per unique safetyreportid.
    The raw file may contain multiple rows per case (one per reaction).
    """
    return df.drop_duplicates(subset=["safetyreportid"]).reset_index(drop=True)


def _parse_dates(df: pd.DataFrame) -> pd.DataFrame:
    """Parse common date columns into datetime objects (errors become NaT)."""
    for col in ["receivedate", "receiptdate", "eventdate"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def compute_basic_stats(df: pd.DataFrame) -> Dict[str, Any]:
    """Compute the core statistics required for the report.

    Returns a dictionary with:
        - start_date / end_date (ISO strings)
        - total_cases
        - serious_cases / non_serious_cases
        - top_reactions (list of (term, count))
        - top_serious_reactions (list of (term, count))
        - age_groups (list of (group, count))
        - sex_counts (dict)
        - country_counts (list of (country, count))
    """
    df = _parse_dates(df.copy())
    cases = deduplicate_cases(df)

    # Reporting period
    start_date = df["receivedate"].min().date().isoformat() if "receivedate" in df.columns else ""
    end_date   = df["receivedate"].max().date().isoformat() if "receivedate" in df.columns else ""
    
    # Total case counts (cast to native int)
    total_cases = int(len(cases))
    
    # Serious flag – any of the seriousness columns set to "yes" (case‑insensitive)
    seriousness_cols = [c for c in df.columns if c.startswith("seriousness")]
    if seriousness_cols:
        serious_mask = df[seriousness_cols].apply(lambda col: col.astype(str).str.strip().str.lower() == "yes").any(axis=1)
        serious_cases = int(serious_mask.sum())
        non_serious_cases = total_cases - serious_cases
    else:
        serious_cases = 0
        non_serious_cases = total_cases

    # Top reaction terms (Preferred Term column)
    reaction_col = None
    for cand in ["patient_reaction_reactionmeddrapt", "reactionmeddrapt", "reactionterm"]:
        if cand in df.columns:
            reaction_col = cand
            break
    if reaction_col:
        top_reactions_df = (
            df[reaction_col]
            .value_counts()
            .head(10)
            .reset_index()
            .rename(columns={"index": "term", reaction_col: "count"})
        )
        top_reactions = list(top_reactions_df.itertuples(index=False, name=None))
    else:
        top_reactions = []

    # Serious reactions – filter to serious rows first
    if seriousness_cols:
        serious_df = df[serious_mask]
        if reaction_col:
            top_serious = (
                serious_df[reaction_col]
                .value_counts()
                .head(10)
                .reset_index()
                .rename(columns={"index": "term", reaction_col: "count"})
            )
            top_serious = list(top_serious.itertuples(index=False, name=None))
        else:
            top_serious = []
    else:
        top_serious = []

    # Age groups – use numeric age if present, otherwise the bucket column
    age_counts: List[tuple] = []
    if "patient_patientonsetage" in df.columns:
        # bucket ages into decades
        bins = [0, 18, 30, 40, 50, 60, 70, 80, 120]
        labels = ["0‑17", "18‑29", "30‑39", "40‑49", "50‑59", "60‑69", "70‑79", "80+"]
        age_series = pd.to_numeric(df["patient_patientonsetage"], errors="coerce")
        age_group = pd.cut(age_series, bins=bins, labels=labels, right=False)
        age_counts = list(age_group.value_counts().sort_index().items())
    elif "patient_patientagegroup" in df.columns:
        age_counts = list(df["patient_patientagegroup"].value_counts().items())

    # Sex distribution
    sex_counts = {}
    if "patient_patientsex" in df.columns:
        sex_counts = df["patient_patientsex"].value_counts().to_dict()

    # Country distribution – prefer primarysource_reportercountry if present
    country_col = "primarysource_reportercountry" if "primarysource_reportercountry" in df.columns else "occurcountry"
    country_counts = []
    if country_col in df.columns:
        # Convert counts to native int
        country_counts = [(c, int(cnt)) for c, cnt in df[country_col].value_counts().head(15).items()]

    return {
        "start_date": start_date,
        "end_date": end_date,
        "total_cases": total_cases,
        "serious_cases": serious_cases,
        "non_serious_cases": non_serious_cases,
        "top_reactions": top_reactions,
        "top_serious_reactions": top_serious,
        "age_groups": age_counts,
        "sex_counts": sex_counts,
        "country_counts": country_counts,
    }
