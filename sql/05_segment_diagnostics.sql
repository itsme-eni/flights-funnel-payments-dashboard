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
        p.country,
        p.route_or_destination,
        p.device,
        p.payment_status,
        p.amount,
        COALESCE(r.refund_requested, FALSE) AS refund_requested,
        COALESCE(r.refund_amount, 0) AS refund_amount
    FROM payment_base p
    LEFT JOIN refund_base r
        ON p.payment_id = r.payment_id
)
SELECT
    country,
    route_or_destination,
    device,
    COUNT(*) AS payment_attempts,
    SUM(CASE WHEN payment_status = 'failed' THEN 1 ELSE 0 END) AS payment_failures,
    ROUND(100.0 * SUM(CASE WHEN payment_status = 'failed' THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 2) AS payment_failure_rate_pct,
    SUM(CASE WHEN payment_status = 'success' THEN 1 ELSE 0 END) AS payment_successes,
    SUM(CASE WHEN refund_requested THEN 1 ELSE 0 END) AS refund_requests,
    ROUND(100.0 * SUM(CASE WHEN refund_requested THEN 1 ELSE 0 END) / NULLIF(SUM(CASE WHEN payment_status = 'success' THEN 1 ELSE 0 END), 0), 2) AS refund_request_rate_pct_of_successes,
    ROUND(SUM(amount), 2) AS attempted_revenue_usd,
    ROUND(SUM(refund_amount), 2) AS refund_amount_usd
FROM joined
GROUP BY country, route_or_destination, device
HAVING COUNT(*) >= 20
ORDER BY payment_failure_rate_pct DESC, refund_amount_usd DESC
LIMIT 200;
