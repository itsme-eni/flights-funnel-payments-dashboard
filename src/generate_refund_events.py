"""Generate a synthetic refund_events table from payment and ticket events.

Inputs:
- data/processed/payment_events.csv
- data/processed/ticket_events.csv

Output:
- data/processed/refund_events.csv
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PAYMENT_PATH = PROJECT_ROOT / "data" / "processed" / "payment_events.csv"
TICKET_PATH = PROJECT_ROOT / "data" / "processed" / "ticket_events.csv"
OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "refund_events.csv"


def main() -> None:
    rng = np.random.default_rng(20260803)

    if not PAYMENT_PATH.exists():
        raise FileNotFoundError(f"Missing input file: {PAYMENT_PATH}")
    if not TICKET_PATH.exists():
        raise FileNotFoundError(f"Missing input file: {TICKET_PATH}")

    payment = pd.read_csv(PAYMENT_PATH)
    ticket = pd.read_csv(TICKET_PATH)

    if "payment_attempt_time" in payment.columns:
        payment["payment_attempt_time"] = pd.to_datetime(payment["payment_attempt_time"], errors="coerce")
    if "ticket_issued_time" in ticket.columns:
        ticket["ticket_issued_time"] = pd.to_datetime(ticket["ticket_issued_time"], errors="coerce")

    required_payment = {"payment_id", "booking_id", "payment_status", "amount"}
    required_ticket = {"payment_id", "ticket_status", "ticketing_error_code", "ticketing_delay_minutes"}
    missing_payment = required_payment - set(payment.columns)
    missing_ticket = required_ticket - set(ticket.columns)
    if missing_payment:
        raise ValueError(f"payment_events missing required columns: {sorted(missing_payment)}")
    if missing_ticket:
        raise ValueError(f"ticket_events missing required columns: {sorted(missing_ticket)}")

    # Only successful payments are eligible for refunds.
    eligible = payment.loc[payment["payment_status"].eq("success")].copy()
    merged = eligible.merge(
        ticket[["payment_id", "ticket_status", "ticketing_error_code", "ticketing_delay_minutes"]],
        on="payment_id",
        how="left",
    )

    # Base refund likelihood plus operational risk adjustments.
    base_prob = np.full(len(merged), 0.045)
    ticket_failed = merged["ticket_status"].eq("failed")
    ticket_pending = merged["ticket_status"].eq("pending")
    ticket_delayed = pd.to_numeric(merged["ticketing_delay_minutes"], errors="coerce").fillna(0) > 180
    ticket_issue = merged["ticketing_error_code"].fillna("NONE").ne("NONE")

    refund_prob = (
        base_prob
        + np.where(ticket_failed, 0.30, 0.0)
        + np.where(ticket_pending, 0.09, 0.0)
        + np.where(ticket_delayed, 0.08, 0.0)
        + np.where(ticket_issue, 0.07, 0.0)
    )
    refund_prob = np.clip(refund_prob, 0.02, 0.85)

    requested = rng.random(len(merged)) < refund_prob
    merged["refund_requested"] = requested

    statuses_if_requested = ["approved", "rejected", "pending"]
    status_probs = [0.70, 0.18, 0.12]
    sampled_status = rng.choice(statuses_if_requested, size=len(merged), p=status_probs)
    merged["refund_status"] = np.where(merged["refund_requested"], sampled_status, "not_requested")

    reason_choices = [
        "customer_cancelled",
        "airline_schedule_change",
        "duplicate_booking",
        "payment_dispute",
        "ticketing_failure",
    ]
    reason_probs = [0.38, 0.19, 0.14, 0.11, 0.18]
    sampled_reasons = rng.choice(reason_choices, size=len(merged), p=reason_probs)
    merged["refund_reason"] = np.where(merged["refund_requested"], sampled_reasons, "not_requested")

    base_time = pd.to_datetime(merged.get("payment_attempt_time"), errors="coerce")
    base_time = pd.Series(base_time).fillna(pd.Timestamp("2014-01-01"))
    delay_days = rng.integers(1, 61, size=len(merged))
    request_time = base_time + pd.to_timedelta(delay_days, unit="D")
    merged["refund_request_time"] = np.where(merged["refund_requested"], request_time, pd.NaT)

    amount = pd.to_numeric(merged["amount"], errors="coerce").fillna(0).clip(lower=0)
    partial_factor = rng.uniform(0.25, 0.95, size=len(merged))
    refund_amount = np.where(
        merged["refund_status"].eq("approved"),
        np.where(rng.random(len(merged)) < 0.68, amount, amount * partial_factor),
        np.where(merged["refund_status"].eq("pending"), amount * rng.uniform(0.4, 1.0, size=len(merged)), 0),
    )
    merged["refund_amount"] = np.round(np.minimum(refund_amount, amount), 2)

    merged["refund_id"] = [f"REF{idx:09d}" for idx in range(1, len(merged) + 1)]

    output = merged[
        [
            "refund_id",
            "booking_id",
            "payment_id",
            "refund_requested",
            "refund_status",
            "refund_reason",
            "refund_amount",
            "refund_request_time",
        ]
    ].copy()

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(OUTPUT_PATH, index=False)

    requested_share = output["refund_requested"].mean() if len(output) else 0.0
    print(f"Saved refund events: {OUTPUT_PATH}")
    print(f"Rows: {len(output):,}")
    print(f"Refund requested share (eligible successful payments): {requested_share:.2%}")


if __name__ == "__main__":
    main()
