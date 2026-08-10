# Stakeholder Memo: Flights Core Services Health

## Executive Summary

This analysis evaluated the end-to-end funnel from search to refund for Flights Core Services. The largest conversion loss occurs at the top of funnel (search to booking), while a second meaningful loss appears in payment processing and ticket issuance reliability. Downstream refund activity is relatively concentrated in a smaller share of successful payments, but approved and pending refunds represent material revenue leakage in impacted cohorts.

This memo is based on a static practice dataset. Recommendations and timelines below are presented as a hypothetical production roadmap to demonstrate decision-making from analytics outputs.

Priority actions should focus on:

1. Improving booking conversion on high-intent search traffic.
2. Reducing mobile payment failures (especially card and wallet paths).
3. Tightening ticketing reliability and reducing long-delay tail risk.
4. Containing refund leakage through proactive failure prevention and case handling policies.

## Scope and Data

Sources used:

- `data/processed/search_booking_events.csv`
- `data/processed/payment_events.csv`
- `data/processed/ticket_events.csv`
- `data/processed/refund_events.csv`
- SQL output tables in `reports/sql_outputs/`

## Key Funnel Findings

From `reports/sql_outputs/01_funnel_overview.csv`:

- Search events: 100,000
- Bookings: 8,122 (8.12% of searches)
- Payment successes: 7,402 (7.40% of searches)
- Issued tickets: 7,147 (7.15% of searches)
- Refund requests: 380 (0.38% of searches)

Interpretation:

- The biggest drop is pre-booking (search to booking).
- Post-booking operations are comparatively strong but still produce measurable leakage in payment and ticketing.

## Payment and Ticketing Reliability

From `reports/sql_outputs/02_payment_performance.csv`:

- Most payment method/device combinations are around 90-93% success.
- Mobile credit card and mobile Apple Pay are notably weaker (failure rates near 13%).
- Desktop channels carry most payment volume and therefore the largest absolute revenue impact.

From `reports/sql_outputs/03_ticketing_performance.csv`:

- Most successful payments result in issued tickets.
- Non-issuance is concentrated in `AIRLINE_CONFIRMATION_FAILED`, `TICKETING_TIMEOUT`, `SUPPLIER_ERROR`, and `INVENTORY_MISMATCH` categories.
- Delay distribution is right-skewed: median around 24 minutes for issued tickets, with longer tail cases in pending/error groups.

## Refund and Revenue Risk

From `reports/sql_outputs/04_refund_revenue_risk.csv`:

- Most successful transactions are not refunded (expected baseline).
- Approved and pending refund cohorts show high refund-to-revenue ratios in those cohorts, indicating concentrated leakage.

From `reports/sql_outputs/05_segment_diagnostics.csv`:

- Several country-destination segments have elevated payment failure rates.
- Some routes show both non-trivial refund request rates and measurable refund amounts, making them good candidates for targeted intervention.

## Recommendations (Prioritized)

### 1) Reduce mobile payment failures first

Action:

- Add targeted retry/fallback paths for mobile card and wallet failures.
- Improve mobile authentication/3DS flows and timeout handling.

Expected impact:

- Increased payment success rate with direct lift to downstream issued tickets.

### 2) Introduce payment error-code playbooks

Action:

- Define code-specific handling for top failure codes (retry window, alternate method prompt, clearer user messaging).
- Monitor failure-rate deltas weekly by method and device.

Expected impact:

- Lower preventable declines and fewer abandoned payment attempts.

### 3) Improve ticketing resilience and delay SLAs

Action:

- Add operational alerts for ticketing timeout and supplier/inventory failure spikes.
- Establish escalation thresholds for long-delay tails.

Expected impact:

- Lower post-payment non-issuance and reduced operational friction.

### 4) Focus refund prevention on high-risk segments

Action:

- Use segment diagnostics to prioritize routes/countries with combined failure and refund risk.
- Trigger proactive support workflows for at-risk bookings.

Expected impact:

- Lower approved/pending refund leakage and improved net retained revenue.

### 5) Address top-of-funnel conversion loss

Action:

- Run conversion experiments on high-intent search traffic (pricing transparency, checkout UX, trust signals, payment method prominence).

Expected impact:

- Largest potential volume lift because search-to-booking is the biggest drop point.

## Hypothetical 30-Day Production Action Plan

Week 1:

- Launch monitoring dashboard for payment and ticketing KPIs by device/method/segment.
- Finalize failure-code and ticketing incident taxonomy with operations.

Week 2:

- Implement mobile checkout/payment fallback experiments.
- Deploy alerting for ticketing timeout and supplier error spikes.

Week 3:

- Pilot segment-targeted mitigation on top risk routes/countries.
- Introduce proactive support rules for high-risk bookings.

Week 4:

- Measure KPI deltas vs baseline:
	- payment success rate
	- ticket issuance rate
	- refund request rate
	- refund amount rate
	- net retained revenue
- Decide scale-up roadmap for successful interventions.

## Hypothetical Success Metrics to Track

1. Search to booking conversion rate
2. Payment success rate (overall and mobile)
3. Ticket issuance rate after successful payment
4. Refund request and approval rates
5. Net retained revenue and revenue-at-risk trend

