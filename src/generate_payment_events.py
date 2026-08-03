"""Generate a synthetic payment_events table from cleaned booking records.

Input:
- data/processed/search_booking_events.csv

Output:
- data/processed/payment_events.csv
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = PROJECT_ROOT / "data" / "processed" / "search_booking_events.csv"
OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "payment_events.csv"


def _choose_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for col in candidates:
        if col in df.columns:
            return col
    return None


def _safe_numeric(series: pd.Series, fallback: float = 0.0) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").fillna(fallback)


def _build_booked_units(df: pd.DataFrame) -> pd.DataFrame:
    booked_col = _choose_column(df, ["is_booking", "booking_flag", "converted"])
    if booked_col is None:
        # Fallback: assume all rows are booked when no explicit conversion field exists.
        booked = df.copy()
    else:
        booked = df.loc[_safe_numeric(df[booked_col], 0) == 1].copy()

    if booked.empty:
        return booked

    count_col = _choose_column(df, ["cnt", "count", "event_count"])
    if count_col is None:
        booked["_unit_count"] = 1
    else:
        booked["_unit_count"] = _safe_numeric(booked[count_col], 1).clip(lower=1).astype(int)

    booked = booked.reset_index(names="source_row_id")
    expanded = booked.loc[booked.index.repeat(booked["_unit_count"])].reset_index(drop=True)
    expanded["booking_id"] = [f"BKG{idx:09d}" for idx in range(1, len(expanded) + 1)]
    return expanded


def main() -> None:
    rng = np.random.default_rng(20260803)

    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Missing input file: {INPUT_PATH}")

    df = pd.read_csv(INPUT_PATH)
    for dt_col in ["date_time", "srch_ci", "srch_co"]:
        if dt_col in df.columns:
            df[dt_col] = pd.to_datetime(df[dt_col], errors="coerce")

    booked = _build_booked_units(df)
    if booked.empty:
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(
            columns=[
                "payment_id",
                "booking_id",
                "customer_id",
                "payment_attempt_time",
                "payment_method",
                "payment_status",
                "payment_error_code",
                "amount",
                "currency",
                "device",
                "country",
                "route_or_destination",
            ]
        ).to_csv(OUTPUT_PATH, index=False)
        print(f"No booked records found. Wrote empty payment table to {OUTPUT_PATH}")
        return

    # Robust fallback mappings.
    customer_col = _choose_column(booked, ["user_id", "customer_id", "traveler_id"])
    country_col = _choose_column(booked, ["user_location_country", "country", "hotel_country"])
    destination_col = _choose_column(
        booked,
        ["srch_destination_id", "hotel_market", "route", "destination", "hotel_cluster"],
    )

    # Payment attempt time based on search timestamp + realistic delay.
    base_time = (
        pd.to_datetime(booked.get("date_time"), errors="coerce")
        if "date_time" in booked.columns
        else pd.Timestamp("2014-01-01")
    )
    missing_base = pd.isna(base_time)
    base_time = pd.Series(base_time).where(~missing_base, pd.Timestamp("2014-01-01"))
    attempt_delay_min = rng.integers(2, 241, size=len(booked))
    payment_attempt_time = base_time + pd.to_timedelta(attempt_delay_min, unit="m")

    # Amount synthesis from available trip signals.
    nights = _safe_numeric(booked.get("stay_length_nights", pd.Series([2] * len(booked))), 2).clip(1, 21)
    rooms = _safe_numeric(booked.get("srch_rm_cnt", pd.Series([1] * len(booked))), 1).clip(1, 6)
    adults = _safe_numeric(booked.get("srch_adults_cnt", pd.Series([2] * len(booked))), 2).clip(1, 8)
    children = _safe_numeric(booked.get("srch_children_cnt", pd.Series([0] * len(booked))), 0).clip(0, 6)
    market_signal = _safe_numeric(booked.get("hotel_market", pd.Series([0] * len(booked))), 0)

    nightly_base = 80 + (market_signal % 180) * 0.9 + rng.normal(0, 22, size=len(booked))
    nightly_base = np.clip(nightly_base, 50, 520)
    amount = (nightly_base * nights * rooms) + adults * 16 + children * 8
    amount = np.round(np.clip(amount, 70, None), 2)

    payment_methods = [
        "credit_card",
        "debit_card",
        "paypal",
        "apple_pay",
        "google_pay",
        "bank_transfer",
    ]
    method_probs = [0.39, 0.22, 0.14, 0.09, 0.08, 0.08]
    payment_method = rng.choice(payment_methods, size=len(booked), p=method_probs)

    is_mobile = _safe_numeric(booked.get("is_mobile", pd.Series([0] * len(booked))), 0)
    device = np.where(is_mobile == 1, "mobile", "desktop")

    if country_col is not None:
        country_vals = _safe_numeric(booked[country_col], 0).astype(int)
    else:
        country_vals = pd.Series([0] * len(booked))

    if destination_col is not None:
        destination_vals = _safe_numeric(booked[destination_col], 0).astype(int)
    else:
        destination_vals = pd.Series([0] * len(booked))

    # Base failure logic: mostly success, with higher risk on mobile and selected country/destination patterns.
    country_risk = ((country_vals % 13) == 0).astype(int) * 0.04
    destination_risk = ((destination_vals % 17) == 0).astype(int) * 0.03
    method_risk = np.where(payment_method == "bank_transfer", 0.02, 0.0) + np.where(
        payment_method == "debit_card", 0.01, 0.0
    )
    mobile_risk = np.where(device == "mobile", 0.03, 0.0)
    high_amount_risk = np.where(amount > 1500, 0.02, 0.0)

    fail_prob = np.clip(0.08 + country_risk + destination_risk + method_risk + mobile_risk + high_amount_risk, 0.04, 0.38)
    failed = rng.random(len(booked)) < fail_prob
    payment_status = np.where(failed, "failed", "success")

    error_codes = [
        "CARD_DECLINED",
        "AUTH_TIMEOUT",
        "INSUFFICIENT_FUNDS",
        "3DS_FAILED",
        "PAYMENT_PROVIDER_ERROR",
    ]
    error_probs = [0.32, 0.16, 0.23, 0.14, 0.15]
    sampled_errors = rng.choice(error_codes, size=len(booked), p=error_probs)
    payment_error_code = np.where(failed, sampled_errors, "NONE")

    posa = _safe_numeric(booked.get("posa_continent", pd.Series([0] * len(booked))), 0).astype(int)
    currency_map = {0: "USD", 1: "USD", 2: "EUR", 3: "USD", 4: "GBP"}
    currency = posa.map(currency_map).fillna("USD")

    if customer_col is not None:
        customer_id = booked[customer_col].astype(str)
    else:
        customer_id = pd.Series([f"CUST{idx:09d}" for idx in range(1, len(booked) + 1)])

    if destination_col is not None:
        route_or_destination = booked[destination_col].astype(str)
    else:
        route_or_destination = pd.Series(["UNKNOWN_DESTINATION"] * len(booked))

    if country_col is not None:
        country = booked[country_col].astype(str)
    else:
        country = pd.Series(["UNKNOWN_COUNTRY"] * len(booked))

    payment_events = pd.DataFrame(
        {
            "payment_id": [f"PAY{idx:09d}" for idx in range(1, len(booked) + 1)],
            "booking_id": booked["booking_id"],
            "customer_id": customer_id,
            "payment_attempt_time": payment_attempt_time,
            "payment_method": payment_method,
            "payment_status": payment_status,
            "payment_error_code": payment_error_code,
            "amount": amount,
            "currency": currency,
            "device": device,
            "country": country,
            "route_or_destination": route_or_destination,
        }
    )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    payment_events.to_csv(OUTPUT_PATH, index=False)

    success_rate = (payment_events["payment_status"] == "success").mean()
    mobile_fail = (
        payment_events.loc[payment_events["device"] == "mobile", "payment_status"].eq("failed").mean()
        if (payment_events["device"] == "mobile").any()
        else 0.0
    )
    desktop_fail = (
        payment_events.loc[payment_events["device"] == "desktop", "payment_status"].eq("failed").mean()
        if (payment_events["device"] == "desktop").any()
        else 0.0
    )

    print(f"Saved payment events: {OUTPUT_PATH}")
    print(f"Rows: {len(payment_events):,}")
    print(f"Success rate: {success_rate:.2%}")
    print(f"Mobile failure rate: {mobile_fail:.2%}")
    print(f"Desktop failure rate: {desktop_fail:.2%}")


if __name__ == "__main__":
    main()
