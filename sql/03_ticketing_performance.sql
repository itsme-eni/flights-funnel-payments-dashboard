WITH ticket_base AS (
    SELECT *
    FROM read_csv_auto('data/processed/ticket_events.csv', HEADER=TRUE)
)
SELECT
    ticket_status,
    ticketing_error_code,
    COUNT(*) AS ticket_records,
    ROUND(AVG(ticketing_delay_minutes), 2) AS avg_delay_minutes,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY ticketing_delay_minutes), 2) AS median_delay_minutes,
    ROUND(PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY ticketing_delay_minutes), 2) AS p90_delay_minutes
FROM ticket_base
GROUP BY ticket_status, ticketing_error_code
ORDER BY ticket_records DESC, ticket_status;
