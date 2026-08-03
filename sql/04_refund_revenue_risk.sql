WITH payment_base AS (
    SELECT *
    FROM read_csv_auto('data/processed/payment_events.csv', HEADER=TRUE)
),
refund_base AS (
    SELECT *
    FROM read_csv_auto('data/processed/refund_events.csv', HEADER=TRUE)
),
joined AS (
    SELECT
        p.payment_id,
        p.booking_id,
        p.device,
        p.country,
        p.route_or_destination,
        p.amount,
        p.payment_status,
        r.refund_requested,
        r.refund_status,
        r.refund_reason,
        r.refund_amount
    FROM payment_base p
    LEFT JOIN refund_base r
        ON p.payment_id = r.payment_id
    WHERE p.payment_status = 'success'
)
SELECT
    device,
    refund_status,
    COUNT(*) AS records,
    ROUND(SUM(amount), 2) AS successful_revenue_usd,
    ROUND(SUM(COALESCE(refund_amount, 0)), 2) AS refund_amount_usd,
    ROUND(SUM(amount) - SUM(COALESCE(refund_amount, 0)), 2) AS net_retained_revenue_usd,
    ROUND(100.0 * SUM(COALESCE(refund_amount, 0)) / NULLIF(SUM(amount), 0), 2) AS refund_rate_pct_of_success_revenue
FROM joined
GROUP BY device, refund_status
ORDER BY records DESC;
