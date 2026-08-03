-- Funnel overview query
-- Purpose: produce stage counts and each stage's percentage relative to total search events.
WITH search_base AS (
    -- Base search/booking dataset
    SELECT *
    FROM read_csv_auto('data/processed/search_booking_events.csv', HEADER=TRUE)
),
payment_base AS (
    -- Synthetic payment attempts and outcomes
    SELECT *
    FROM read_csv_auto('data/processed/payment_events.csv', HEADER=TRUE)
),
ticket_base AS (
    -- Synthetic ticketing outcomes after payment
    SELECT *
    FROM read_csv_auto('data/processed/ticket_events.csv', HEADER=TRUE)
),
refund_base AS (
    -- Synthetic refund lifecycle outcomes
    SELECT *
    FROM read_csv_auto('data/processed/refund_events.csv', HEADER=TRUE)
),
counts AS (
    -- Stage 1: all search events
    SELECT 'search_events' AS stage, COUNT(*)::DOUBLE AS stage_count FROM search_base
    UNION ALL
    -- Stage 2: booking units (weighted by cnt)
    SELECT 'bookings', SUM(CASE WHEN is_booking = 1 THEN cnt ELSE 0 END)::DOUBLE FROM search_base
    UNION ALL
    -- Stage 3: payment attempts
    SELECT 'payment_attempts', COUNT(*)::DOUBLE FROM payment_base
    UNION ALL
    -- Stage 4: successful payments
    SELECT 'payment_successes', SUM(CASE WHEN payment_status = 'success' THEN 1 ELSE 0 END)::DOUBLE FROM payment_base
    UNION ALL
    -- Stage 5: tickets successfully issued
    SELECT 'tickets_issued', SUM(CASE WHEN ticket_status = 'issued' THEN 1 ELSE 0 END)::DOUBLE FROM ticket_base
    UNION ALL
    -- Stage 6: refund requests
    SELECT 'refund_requests', SUM(CASE WHEN refund_requested THEN 1 ELSE 0 END)::DOUBLE FROM refund_base
),
base AS (
    -- Pull search event denominator for rate calculations
    SELECT stage_count AS search_events
    FROM counts
    WHERE stage = 'search_events'
)
SELECT
    c.stage,
    c.stage_count,
    -- Percentage of each funnel stage relative to the search-event baseline
    ROUND(100.0 * c.stage_count / NULLIF(b.search_events, 0), 2) AS pct_of_search_events
FROM counts c
CROSS JOIN base b
-- Keep output in funnel progression order
ORDER BY CASE c.stage
    WHEN 'search_events' THEN 1
    WHEN 'bookings' THEN 2
    WHEN 'payment_attempts' THEN 3
    WHEN 'payment_successes' THEN 4
    WHEN 'tickets_issued' THEN 5
    WHEN 'refund_requests' THEN 6
    ELSE 99
END;
