"""Generate synthetic payment, ticket, and refund event tables.

This script extends the cleaned search/booking dataset to complete the funnel:
Search -> Booking -> Payment Attempt -> Payment Success -> Ticket Issued -> Refund
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = PROJECT_ROOT / "data" / "processed" / "search_booking_events.csv"
PAYMENT_OUTPUT = PROJECT_ROOT / "data" / "processed" / "payment_events.csv"
TICKET_OUTPUT = PROJECT_ROOT / "data" / "processed" / "ticket_events.csv"
REFUND_OUTPUT = PROJECT_ROOT / "data" / "processed" / "refund_events.csv"


def load_cleaned_events() -> pd.DataFrame:
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Missing cleaned dataset at {INPUT_PATH}. "
            "Run src/build_search_booking_events.py first."
        )

    df = pd.read_csv(INPUT_PATH)
    for col in ["date_time", "srch_ci", "srch_co"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def build_booking_units(df: pd.DataFrame) -> pd.DataFrame:
    """Expand booking rows by cnt so each row is one booked unit."""
    bookings = df.loc[df["is_booking"] == 1].copy()
    bookings["cnt"] = pd.to_numeric(bookings["cnt"], errors="coerce").fillna(1)
    bookings["booking_units"] = bookings["cnt"].clip(lower=1).astype(int)
    bookings = bookings.reset_index(names="source_row_id")

    expanded = bookings.loc[bookings.index.repeat(bookings["booking_units"])].reset_index(drop=True)
    expanded["booking_id"] = [f"BKG{idx:08d}" for idx in range(1, len(expanded) + 1)]
    return expanded


def synthesize_payment_events(bookings: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    """Create payment attempt events with synthetic outcomes and reasons."""
    payment = bookings.copy()

    booking_offset_min = rng.integers(5, 181, size=len(payment))
    payment["booking_ts"] = payment["date_time"] + pd.to_timedelta(booking_offset_min, unit="m")

    attempt_offset_min = rng.integers(0, 31, size=len(payment))
    payment["payment_attempt_ts"] = payment["booking_ts"] + pd.to_timedelta(attempt_offset_min, unit="m")

    # Synthetic gross booking amount based on party size and stay duration.
    nights = pd.to_numeric(payment.get("stay_length_nights"), errors="coerce").fillna(2).clip(lower=1, upper=21)
    rooms = pd.to_numeric(payment.get("srch_rm_cnt"), errors="coerce").fillna(1).clip(lower=1, upper=6)
    adults = pd.to_numeric(payment.get("srch_adults_cnt"), errors="coerce").fillna(2).clip(lower=1, upper=8)
    children = pd.to_numeric(payment.get("srch_children_cnt"), errors="coerce").fillna(0).clip(lower=0, upper=6)
    market = pd.to_numeric(payment.get("hotel_market"), errors="coerce").fillna(0)

    nightly_base = 85 + (market % 200) * 0.85 + rng.normal(0, 20, size=len(payment))
    nightly_base = np.clip(nightly_base, 45, 450)
    gross_amount = (nightly_base * nights * rooms) + (adults * 12) + (children * 7)
    payment["amount_usd"] = np.round(np.clip(gross_amount, 60, None), 2)

    payment_methods = ["credit_card", "debit_card", "paypal", "apple_pay", "bank_transfer"]
    method_probs = [0.42, 0.22, 0.16, 0.10, 0.10]
    payment["payment_method"] = rng.choice(payment_methods, size=len(payment), p=method_probs)

    continent_to_currency = {
        0: "USD",
        1: "USD",
        2: "EUR",
        3: "USD",
        4: "GBP",
    }
    posa = pd.to_numeric(payment.get("posa_continent"), errors="coerce").fillna(0).astype(int)
    payment["currency"] = posa.map(continent_to_currency).fillna("USD")

    # Failure probability tuned by channel context and amount.
    fail_prob = (
        0.10
        + 0.03 * pd.to_numeric(payment.get("is_mobile"), errors="coerce").fillna(0)
        + 0.02 * pd.to_numeric(payment.get("is_package"), errors="coerce").fillna(0)
        + 0.02 * (payment["amount_usd"] > 1200).astype(int)
    )
    fail_prob = np.clip(fail_prob, 0.05, 0.35)

    rand = rng.random(len(payment))
    payment["payment_status"] = np.where(rand < fail_prob, "failed", "success")

    failure_reasons = [
        "insufficient_funds",
        "3ds_auth_failed",
        "issuer_declined",
        "gateway_timeout",
        "fraud_rule_block",
    ]
    failure_probs = [0.27, 0.18, 0.29, 0.16, 0.10]
    sampled_reasons = rng.choice(failure_reasons, size=len(payment), p=failure_probs)
    payment["failure_reason"] = np.where(payment["payment_status"] == "failed", sampled_reasons, pd.NA)

    payment["payment_attempt_id"] = [f"PAY{idx:09d}" for idx in range(1, len(payment) + 1)]

    payment = payment[
        [
            "payment_attempt_id",
            "booking_id",
            "source_row_id",
            "user_id",
            "booking_ts",
            "payment_attempt_ts",
            "amount_usd",
            "currency",
            "payment_method",
            "payment_status",
            "failure_reason",
            "channel",
            "is_mobile",
            "is_package",
            "hotel_market",
        ]
    ].copy()

    return payment


def synthesize_ticket_events(payment: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    """Create ticket issuance events for successful payments."""
    successful = payment.loc[payment["payment_status"] == "success"].copy()

    issue_delay_min = rng.integers(2, 46, size=len(successful))
    successful["ticket_issued_ts"] = successful["payment_attempt_ts"] + pd.to_timedelta(issue_delay_min, unit="m")

    issuance_status = np.where(rng.random(len(successful)) < 0.985, "issued", "issuance_error")
    successful["ticket_status"] = issuance_status
    successful["ticket_id"] = [f"TKT{idx:09d}" for idx in range(1, len(successful) + 1)]

    ticket = successful[
        [
            "ticket_id",
            "payment_attempt_id",
            "booking_id",
            "user_id",
            "ticket_issued_ts",
            "ticket_status",
        ]
    ].copy()
    return ticket


def synthesize_refund_events(payment: pd.DataFrame, ticket: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    """Create refund events for a subset of issued tickets."""
    issued = ticket.loc[ticket["ticket_status"] == "issued"].copy()
    payment_subset = payment[["payment_attempt_id", "amount_usd", "is_package"]]
    issued = issued.merge(payment_subset, on="payment_attempt_id", how="left")

    refund_prob = 0.06 + 0.03 * pd.to_numeric(issued["is_package"], errors="coerce").fillna(0)
    refund_prob = np.clip(refund_prob, 0.03, 0.25)
    flagged_refund = rng.random(len(issued)) < refund_prob
    refunds = issued.loc[flagged_refund].copy()

    if refunds.empty:
        return pd.DataFrame(
            columns=[
                "refund_id",
                "ticket_id",
                "payment_attempt_id",
                "booking_id",
                "user_id",
                "refund_requested_ts",
                "refund_processed_ts",
                "refund_status",
                "refund_reason",
                "refund_amount_usd",
                "original_amount_usd",
            ]
        )

    request_delay_days = rng.integers(1, 91, size=len(refunds))
    refunds["refund_requested_ts"] = refunds["ticket_issued_ts"] + pd.to_timedelta(request_delay_days, unit="D")
    process_delay_hours = rng.integers(2, 97, size=len(refunds))
    refunds["refund_processed_ts"] = refunds["refund_requested_ts"] + pd.to_timedelta(process_delay_hours, unit="h")

    status_choices = ["approved_full", "approved_partial", "rejected"]
    status_probs = [0.72, 0.18, 0.10]
    refunds["refund_status"] = rng.choice(status_choices, size=len(refunds), p=status_probs)

    reason_choices = [
        "customer_changed_plans",
        "schedule_change",
        "duplicate_booking",
        "service_quality_issue",
        "fare_rule_exception",
    ]
    reason_probs = [0.36, 0.21, 0.12, 0.19, 0.12]
    refunds["refund_reason"] = rng.choice(reason_choices, size=len(refunds), p=reason_probs)

    partial_factor = rng.uniform(0.20, 0.85, size=len(refunds))
    refund_amount = np.where(
        refunds["refund_status"] == "approved_full",
        refunds["amount_usd"],
        np.where(
            refunds["refund_status"] == "approved_partial",
            refunds["amount_usd"] * partial_factor,
            0,
        ),
    )
    refunds["refund_amount_usd"] = np.round(refund_amount, 2)
    refunds["original_amount_usd"] = np.round(refunds["amount_usd"], 2)

    refunds["refund_id"] = [f"REF{idx:09d}" for idx in range(1, len(refunds) + 1)]

    refunds = refunds[
        [
            "refund_id",
            "ticket_id",
            "payment_attempt_id",
            "booking_id",
            "user_id",
            "refund_requested_ts",
            "refund_processed_ts",
            "refund_status",
            "refund_reason",
            "refund_amount_usd",
            "original_amount_usd",
        ]
    ].copy()
    return refunds


def save_outputs(payment: pd.DataFrame, ticket: pd.DataFrame, refund: pd.DataFrame) -> None:
    PAYMENT_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    payment.to_csv(PAYMENT_OUTPUT, index=False)
    ticket.to_csv(TICKET_OUTPUT, index=False)
    refund.to_csv(REFUND_OUTPUT, index=False)


def print_summary(payment: pd.DataFrame, ticket: pd.DataFrame, refund: pd.DataFrame) -> None:
    payment_success_rate = (payment["payment_status"] == "success").mean() if len(payment) else 0.0
    ticket_issue_rate = (ticket["ticket_status"] == "issued").mean() if len(ticket) else 0.0
    refund_rate = len(refund) / len(ticket.loc[ticket["ticket_status"] == "issued"]) if len(ticket) else 0.0

    print("\n=== Synthetic Event Summary ===")
    print(f"Payment events: {len(payment):,}")
    print(f"Ticket events: {len(ticket):,}")
    print(f"Refund events: {len(refund):,}")
    print(f"Payment success rate: {payment_success_rate:.2%}")
    print(f"Ticket issued share (among successful payments): {ticket_issue_rate:.2%}")
    print(f"Refund incidence (among issued tickets): {refund_rate:.2%}")
    print(f"Saved: {PAYMENT_OUTPUT}")
    print(f"Saved: {TICKET_OUTPUT}")
    print(f"Saved: {REFUND_OUTPUT}")


def main() -> None:
    rng = np.random.default_rng(20260803)
    df = load_cleaned_events()
    bookings = build_booking_units(df)
    payment = synthesize_payment_events(bookings, rng)
    ticket = synthesize_ticket_events(payment, rng)
    refund = synthesize_refund_events(payment, ticket, rng)
    save_outputs(payment, ticket, refund)
    print_summary(payment, ticket, refund)


if __name__ == "__main__":
    main()
