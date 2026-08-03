"""Generate a synthetic ticket_events table from payment events.

Input:
- data/processed/payment_events.csv

Output:
- data/processed/ticket_events.csv
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = PROJECT_ROOT / "data" / "processed" / "payment_events.csv"
OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "ticket_events.csv"


def main() -> None:
    rng = np.random.default_rng(20260803)

    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Missing input file: {INPUT_PATH}")

    payment = pd.read_csv(INPUT_PATH)
    if "payment_attempt_time" in payment.columns:
        payment["payment_attempt_time"] = pd.to_datetime(payment["payment_attempt_time"], errors="coerce")

    required = {"payment_id", "booking_id", "payment_status", "payment_attempt_time"}
    missing_required = required - set(payment.columns)
    if missing_required:
        raise ValueError(f"payment_events missing required columns: {sorted(missing_required)}")

    ticket = payment[["payment_id", "booking_id", "payment_status", "payment_attempt_time"]].copy()

    success_mask = ticket["payment_status"].eq("success")
    n = len(ticket)
    n_success = int(success_mask.sum())

    # Default for failed payments: no issuance.
    ticket["ticket_status"] = np.where(success_mask, "pending", "not_issued_payment_failed")
    ticket["ticketing_error_code"] = "NONE"
    ticket["ticket_issued_time"] = pd.NaT
    ticket["ticketing_delay_minutes"] = np.nan

    if n_success > 0:
        success_idx = ticket.index[success_mask]
        status_choices = ["issued", "failed", "pending"]
        status_probs = [0.965, 0.015, 0.020]
        sampled_status = rng.choice(status_choices, size=n_success, p=status_probs)
        ticket.loc[success_idx, "ticket_status"] = sampled_status

        # Delay: mostly short, with a long tail.
        short_delay = rng.integers(3, 46, size=n_success)
        long_tail_flag = rng.random(n_success) < 0.06
        long_delay = rng.integers(120, 1441, size=n_success)
        delay_minutes = np.where(long_tail_flag, long_delay, short_delay)
        ticket.loc[success_idx, "ticketing_delay_minutes"] = delay_minutes

        issued_time = ticket.loc[success_idx, "payment_attempt_time"] + pd.to_timedelta(delay_minutes, unit="m")
        ticket.loc[success_idx, "ticket_issued_time"] = issued_time

        error_codes = [
            "AIRLINE_CONFIRMATION_FAILED",
            "INVENTORY_MISMATCH",
            "TICKETING_TIMEOUT",
            "SUPPLIER_ERROR",
        ]
        error_probs = [0.31, 0.19, 0.29, 0.21]
        sampled_error = rng.choice(error_codes, size=n_success, p=error_probs)

        issued_mask = ticket.loc[success_idx, "ticket_status"].eq("issued")
        ticket.loc[success_idx, "ticketing_error_code"] = np.where(issued_mask, "NONE", sampled_error)

    ticket["ticket_id"] = [f"TKT{idx:09d}" for idx in range(1, n + 1)]

    output = ticket[
        [
            "ticket_id",
            "booking_id",
            "payment_id",
            "ticket_status",
            "ticket_issued_time",
            "ticketing_error_code",
            "ticketing_delay_minutes",
        ]
    ].copy()

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(OUTPUT_PATH, index=False)

    issued_share = output["ticket_status"].eq("issued").mean() if len(output) else 0.0
    print(f"Saved ticket events: {OUTPUT_PATH}")
    print(f"Rows: {len(output):,}")
    print(f"Issued share: {issued_share:.2%}")


if __name__ == "__main__":
    main()
