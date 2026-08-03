WITH payment_base AS (
    SELECT *
    FROM read_csv_auto('data/processed/payment_events.csv', HEADER=TRUE)
)
SELECT
    device,
    payment_method,
    COUNT(*) AS payment_attempts,
    SUM(CASE WHEN payment_status = 'success' THEN 1 ELSE 0 END) AS payment_successes,
    SUM(CASE WHEN payment_status = 'failed' THEN 1 ELSE 0 END) AS payment_failures,
    ROUND(100.0 * SUM(CASE WHEN payment_status = 'success' THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 2) AS success_rate_pct,
    ROUND(100.0 * SUM(CASE WHEN payment_status = 'failed' THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 2) AS failure_rate_pct,
    ROUND(SUM(amount), 2) AS attempted_revenue_usd,
    ROUND(SUM(CASE WHEN payment_status = 'success' THEN amount ELSE 0 END), 2) AS successful_revenue_usd
FROM payment_base
GROUP BY device, payment_method
ORDER BY payment_attempts DESC, failure_rate_pct DESC;
