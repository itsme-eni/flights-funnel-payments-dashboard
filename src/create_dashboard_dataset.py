"""Create a dashboard-ready dataset for Flights Funnel + Payments analysis.

Input files:
- data/processed/search_booking_events.csv
- data/processed/payment_events.csv
- data/processed/ticket_events.csv
- data/processed/refund_events.csv

Output file:
- data/processed/dashboard_flights_core_services.csv
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

SEARCH_PATH = PROCESSED_DIR / "search_booking_events.csv"
PAYMENT_PATH = PROCESSED_DIR / "payment_events.csv"
TICKET_PATH = PROCESSED_DIR / "ticket_events.csv"
REFUND_PATH = PROCESSED_DIR / "refund_events.csv"

OUTPUT_PATH = PROCESSED_DIR / "dashboard_flights_core_services.csv"


def load_csv(path: Path, name: str) -> pd.DataFrame:
    """Load a CSV file if present, otherwise return an empty frame."""
    if not path.exists():
        print(f"[WARN] Missing {name}: {path}. Using empty dataframe.")
        return pd.DataFrame()
    df = pd.read_csv(path)
    print(f"[INFO] Loaded {name}: {df.shape}")
    return df


def ensure_columns(df: pd.DataFrame, columns: list[str], default=np.nan) -> pd.DataFrame:
    """Ensure required columns exist in a dataframe."""
    out = df.copy()
    for col in columns:
        if col not in out.columns:
            out[col] = default
    return out


def first_existing(df: pd.DataFrame, candidates: list[str]) -> str | None:
    """Return first existing column from candidates."""
    for col in candidates:
        if col in df.columns:
            return col
    return None


def merge_sources(
    search_booking: pd.DataFrame,
    payment: pd.DataFrame,
    ticket: pd.DataFrame,
    refund: pd.DataFrame,
) -> pd.DataFrame:
    """Merge source tables into one dashboard-ready dataset."""
    # Payment is the natural booking-level backbone for post-booking funnel analysis.
    if not payment.empty and "booking_id" in payment.columns:
        base = payment.copy()
    else:
        # Fallback path if payment is absent or malformed.
        fallback_booking_col = first_existing(ticket, ["booking_id"])
        if fallback_booking_col is None and not refund.empty:
            fallback_booking_col = first_existing(refund, ["booking_id"])

        if fallback_booking_col is None:
            base = pd.DataFrame(columns=["booking_id"])
        else:
            base = ticket[[fallback_booking_col]].copy() if fallback_booking_col in ticket.columns else refund[[fallback_booking_col]].copy()
            base = base.rename(columns={fallback_booking_col: "booking_id"}).drop_duplicates()

    # Add ticket attributes.
    if not ticket.empty:
        ticket_cols = [
            "booking_id",
            "payment_id",
            "ticket_status",
            "ticketing_error_code",
            "ticketing_delay_minutes",
        ]
        ticket_small = ensure_columns(ticket, ticket_cols)[ticket_cols]

        if "payment_id" in base.columns and base["payment_id"].notna().any():
            base = base.merge(
                ticket_small.drop(columns=["booking_id"]),
                on="payment_id",
                how="left",
            )
        else:
            base = base.merge(
                ticket_small.drop(columns=["payment_id"]),
                on="booking_id",
                how="left",
            )

    # Add refund attributes.
    if not refund.empty:
        refund_cols = [
            "booking_id",
            "payment_id",
            "refund_requested",
            "refund_status",
            "refund_reason",
            "refund_amount",
        ]
        refund_small = ensure_columns(refund, refund_cols)[refund_cols]

        if "payment_id" in base.columns and base["payment_id"].notna().any():
            base = base.merge(
                refund_small.drop(columns=["booking_id"]),
                on="payment_id",
                how="left",
            )
        else:
            base = base.merge(
                refund_small.drop(columns=["payment_id"]),
                on="booking_id",
                how="left",
            )

    # If search table has booking_id, merge is_booking from source.
    if not search_booking.empty and "booking_id" in search_booking.columns:
        search_small = ensure_columns(search_booking, ["booking_id", "is_booking"])[["booking_id", "is_booking"]]
        base = base.merge(search_small, on="booking_id", how="left")

    return base


def create_calculated_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Create dashboard calculation flags and risk metric."""
    out = df.copy()

    # Ensure expected analysis columns exist.
    required_columns = [
        "booking_id",
        "customer_id",
        "device",
        "country",
        "route_or_destination",
        "amount",
        "payment_method",
        "payment_status",
        "payment_error_code",
        "ticket_status",
        "ticketing_error_code",
        "ticketing_delay_minutes",
        "refund_requested",
        "refund_status",
        "refund_reason",
        "refund_amount",
        "is_booking",
    ]
    out = ensure_columns(out, required_columns)

    # Fill is_booking from booking_id if source column is unavailable.
    out["is_booking"] = np.where(out["is_booking"].isna(), out["booking_id"].notna().astype(int), out["is_booking"])  # type: ignore[arg-type]
    out["is_booking"] = pd.to_numeric(out["is_booking"], errors="coerce").fillna(0).astype(int)

    out["payment_status"] = out["payment_status"].astype("string")
    out["ticket_status"] = out["ticket_status"].astype("string")
    out["refund_status"] = out["refund_status"].astype("string")

    out["is_payment_success"] = (out["payment_status"].str.lower() == "success").astype(int)
    out["is_payment_failed"] = (out["payment_status"].str.lower() == "failed").astype(int)
    out["is_ticket_issued"] = (out["ticket_status"].str.lower() == "issued").astype(int)
    out["is_ticket_failed"] = out["ticket_status"].str.lower().isin(["failed", "not_issued_payment_failed"]).astype(int)

    refund_requested_bool = out["refund_requested"].fillna(False).astype(bool)
    refund_status_bool = out["refund_status"].str.lower().isin(["approved", "pending"])
    out["is_refunded"] = (refund_requested_bool | refund_status_bool).astype(int)

    out["amount"] = pd.to_numeric(out["amount"], errors="coerce").fillna(0)
    out["refund_amount"] = pd.to_numeric(out["refund_amount"], errors="coerce").fillna(0)

    # Revenue at risk logic:
    # - full booking amount for failed payments and ticket failures
    # - refund amount when refunded
    out["revenue_at_risk"] = 0.0
    out.loc[out["is_payment_failed"] == 1, "revenue_at_risk"] = out.loc[out["is_payment_failed"] == 1, "amount"]
    out.loc[(out["is_payment_failed"] == 0) & (out["is_ticket_failed"] == 1), "revenue_at_risk"] = out.loc[
        (out["is_payment_failed"] == 0) & (out["is_ticket_failed"] == 1),
        "amount",
    ]
    out.loc[out["is_refunded"] == 1, "revenue_at_risk"] = np.maximum(
        out.loc[out["is_refunded"] == 1, "revenue_at_risk"],
        out.loc[out["is_refunded"] == 1, "refund_amount"],
    )

    return out


def select_dashboard_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Keep requested columns plus calculated fields for Tableau."""
    ordered_columns = [
        "booking_id",
        "customer_id",
        "device",
        "country",
        "route_or_destination",
        "amount",
        "payment_method",
        "payment_status",
        "payment_error_code",
        "ticket_status",
        "ticketing_error_code",
        "ticketing_delay_minutes",
        "refund_requested",
        "refund_status",
        "refund_reason",
        "refund_amount",
        "is_booking",
        "is_payment_success",
        "is_payment_failed",
        "is_ticket_issued",
        "is_ticket_failed",
        "is_refunded",
        "revenue_at_risk",
    ]
    return ensure_columns(df, ordered_columns)[ordered_columns]


def main() -> None:
    search_booking = load_csv(SEARCH_PATH, "search_booking_events")
    payment = load_csv(PAYMENT_PATH, "payment_events")
    ticket = load_csv(TICKET_PATH, "ticket_events")
    refund = load_csv(REFUND_PATH, "refund_events")

    merged = merge_sources(search_booking, payment, ticket, refund)
    merged = create_calculated_columns(merged)
    dashboard_df = select_dashboard_columns(merged)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    dashboard_df.to_csv(OUTPUT_PATH, index=False)

    print(f"[SUCCESS] Saved dashboard dataset to: {OUTPUT_PATH}")
    print(f"[INFO] Output shape: {dashboard_df.shape}")


if __name__ == "__main__":
    main()
