"""Build a cleaned search/booking events dataset from raw travel data.

This script is designed for portfolio-style reproducibility:
1. Load raw data.
2. Print dataset diagnostics.
3. Assess missingness and duplicates.
4. Map columns to analytical roles.
5. Create an initial cleaned dataframe.
6. Save cleaned output for downstream SQL/EDA/dashboard work.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_PRIMARY = PROJECT_ROOT / "data" / "raw" / "travel_agency_data.csv"
RAW_FALLBACK = PROJECT_ROOT / "data" / "raw" / "travel.csv"
OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "search_booking_events.csv"


def resolve_input_path() -> Path:
    """Use the requested raw file, with fallback to current workspace raw file."""
    if RAW_PRIMARY.exists():
        return RAW_PRIMARY
    if RAW_FALLBACK.exists():
        print(
            "[INFO] Requested file not found at "
            f"{RAW_PRIMARY}. Using fallback file {RAW_FALLBACK}."
        )
        return RAW_FALLBACK
    raise FileNotFoundError(
        "No raw dataset found. Expected one of: "
        f"{RAW_PRIMARY} or {RAW_FALLBACK}"
    )


def print_dataset_overview(df: pd.DataFrame) -> None:
    """Print shape, columns, dtypes, and preview rows."""
    print("\n=== Dataset Overview ===")
    print(f"Shape: {df.shape}")
    print("\nColumns:")
    for col in df.columns:
        print(f"- {col}")
    print("\nData types:")
    print(df.dtypes)
    print("\nFirst 5 rows:")
    print(df.head())


def print_data_quality_checks(df: pd.DataFrame) -> None:
    """Print missing values and duplicate-row counts."""
    print("\n=== Missing Values By Column ===")
    missing_counts = df.isna().sum().sort_values(ascending=False)
    missing_pct = (missing_counts / len(df) * 100).round(2)
    missing_report = pd.DataFrame(
        {
            "missing_count": missing_counts,
            "missing_pct": missing_pct,
        }
    )
    print(missing_report)

    duplicate_count = df.duplicated().sum()
    print("\n=== Duplicate Rows ===")
    print(f"Duplicate rows: {duplicate_count}")


def infer_column_roles(columns: List[str]) -> Dict[str, List[str]]:
    """Assign columns to analytical role groups for funnel analysis."""
    roles = {
        "search_behavior": [
            "site_name",
            "channel",
            "is_mobile",
            "is_package",
            "srch_adults_cnt",
            "srch_children_cnt",
            "srch_rm_cnt",
            "srch_destination_type_id",
        ],
        "booking_outcome_conversion": [
            "is_booking",
            "cnt",
            "hotel_cluster",
        ],
        "customer_trip_characteristics": [
            "user_id",
            "user_location_country",
            "user_location_region",
            "user_location_city",
            "orig_destination_distance",
        ],
        "dates": [
            "date_time",
            "srch_ci",
            "srch_co",
        ],
        "destination_hotel": [
            "posa_continent",
            "srch_destination_id",
            "hotel_continent",
            "hotel_country",
            "hotel_market",
        ],
        "price": [],
    }

    filtered_roles: Dict[str, List[str]] = {}
    for role, role_columns in roles.items():
        filtered_roles[role] = [col for col in role_columns if col in columns]
    return filtered_roles


def print_column_roles(df: pd.DataFrame) -> None:
    """Display analytical role mapping and unclassified columns."""
    role_map = infer_column_roles(df.columns.tolist())
    classified = {col for cols in role_map.values() for col in cols}
    unclassified = [col for col in df.columns if col not in classified]

    print("\n=== Column Role Mapping ===")
    for role, cols in role_map.items():
        print(f"\n{role}:")
        if cols:
            for col in cols:
                print(f"- {col}")
        else:
            print("- None identified")

    print("\nUnclassified / technical columns:")
    if unclassified:
        for col in unclassified:
            print(f"- {col}")
    else:
        print("- None")


def create_initial_clean_df(df: pd.DataFrame) -> pd.DataFrame:
    """Apply initial, conservative cleaning suitable for further analysis."""
    clean_df = df.copy()

    # Remove technical index-export columns if present.
    drop_candidates = [col for col in clean_df.columns if col.lower().startswith("unnamed")]
    if drop_candidates:
        clean_df = clean_df.drop(columns=drop_candidates)

    # Normalize column names for analysis and SQL portability.
    clean_df.columns = [col.strip().lower() for col in clean_df.columns]

    # Parse date fields into pandas datetime.
    for col in ["date_time", "srch_ci", "srch_co"]:
        if col in clean_df.columns:
            clean_df[col] = pd.to_datetime(clean_df[col], errors="coerce")

    # Convert likely numeric fields where available.
    numeric_columns = [
        "site_name",
        "posa_continent",
        "user_location_country",
        "user_location_region",
        "user_location_city",
        "orig_destination_distance",
        "user_id",
        "is_mobile",
        "is_package",
        "channel",
        "srch_adults_cnt",
        "srch_children_cnt",
        "srch_rm_cnt",
        "srch_destination_id",
        "srch_destination_type_id",
        "is_booking",
        "cnt",
        "hotel_continent",
        "hotel_country",
        "hotel_market",
        "hotel_cluster",
    ]
    for col in numeric_columns:
        if col in clean_df.columns:
            clean_df[col] = pd.to_numeric(clean_df[col], errors="coerce")

    # Add useful derived fields for funnel analysis.
    if {"srch_ci", "srch_co"}.issubset(clean_df.columns):
        clean_df["stay_length_nights"] = (clean_df["srch_co"] - clean_df["srch_ci"]).dt.days
    if {"date_time", "srch_ci"}.issubset(clean_df.columns):
        clean_df["booking_lead_days"] = (clean_df["srch_ci"] - clean_df["date_time"]).dt.days

    return clean_df


def main() -> None:
    input_path = resolve_input_path()
    print(f"[INFO] Loading data from: {input_path}")

    # Step 1: Load the dataset.
    df = pd.read_csv(input_path)

    # Step 2: Display shape, columns, data types, and head.
    print_dataset_overview(df)

    # Step 3 and 4: Missing values and duplicate checks.
    print_data_quality_checks(df)

    # Step 5: Identify analytical column groups.
    print_column_roles(df)

    # Step 6: Create an initial cleaned dataframe.
    clean_df = create_initial_clean_df(df)
    print("\n=== Cleaned Dataset Overview ===")
    print(f"Cleaned shape: {clean_df.shape}")
    print(clean_df.dtypes)
    print(clean_df.head())

    # Step 7: Save the cleaned dataset for next project steps.
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    clean_df.to_csv(OUTPUT_PATH, index=False)
    print(f"\n[SUCCESS] Saved cleaned dataset to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
