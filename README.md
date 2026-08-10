# Flights Funnel + Payments Dashboard

Portfolio project (Booking.com-style Data Analyst II case study) focused on end-to-end funnel analytics:

Search -> Booking -> Payment Attempt -> Payment Success -> Ticket Issued -> Refund

The project combines Python, SQL, and Tableau to explain where users drop off, where revenue is at risk, and what product/ops actions can improve conversion.

Practice-project note:

- This is a static case-study dataset used for portfolio practice.
- Recommendations in the stakeholder memo are written as a hypothetical production roadmap.

## Why This Project

Travel funnels are multi-step and failure-prone. Looking only at bookings hides critical issues in payment processing and post-booking outcomes.

This project is designed to answer:

1. Where is the largest funnel drop-off?
2. Which segments (mobile, package, channel, market) underperform?
3. How much revenue is blocked by payment failures and refunds?
4. What operational recommendations could improve conversion and reduce leakage?

## Project Structure

- `data/raw/`: raw source data files
- `data/processed/`: cleaned and engineered analysis-ready tables
- `src/`: Python scripts for cleaning and analysis
- `sql/`: SQL queries/models for KPI and funnel analysis
- `dashboard/`: Tableau assets and screenshots
- `reports/`: stakeholder-facing write-ups

Current key files:

- `data/raw/travel_agency_data.csv` (raw source for this pipeline)
- `data/processed/search_booking_events.csv` (cleaned output)
- `data/processed/payment_events.csv` (synthetic payment attempts/outcomes)
- `data/processed/ticket_events.csv` (synthetic ticketing outcomes)
- `data/processed/refund_events.csv` (synthetic refund lifecycle outcomes)
- `src/build_search_booking_events.py` (cleaning + profiling script)
- `src/generate_payment_events.py` (Step 6: payment event generation)
- `src/generate_ticket_events.py` (Step 7: ticket event generation)
- `src/generate_refund_events.py` (Step 8: refund event generation)
- `notebooks/step5_exploratory_analysis.ipynb` (Step 5: exploratory analysis notebook)
- `data/data_dictionary.md` (column definitions and interpretation)

## Workflow: Steps and Whys

### Step 1: Understand Raw Data

What:

- Inspect schema, data types, missing values, duplicates, and column meaning.

Why:

- Prevents incorrect assumptions before modeling funnel metrics.
- Identifies data quality risks early (for example missing distance values).

Outputs:

- `data/data_dictionary.md`
- `data/raw/raw_profile_summary.json`

### Step 2: Build Cleaned Search/Booking Events Table

What:

- Parse date fields, normalize columns, keep relevant features, and derive core fields.

Why:

- Creates a stable base table for SQL, Python EDA, and dashboarding.
- Reduces repeated cleaning logic across tools.

Outputs:

- `data/processed/search_booking_events.csv`

### Step 3: Create Synthetic Payment/Ticket/Refund Event Tables

What:

- Generate realistic downstream operational events linked to booking events:
	- payment attempts
	- payment successes/failures
	- ticket issuance
	- refunds

Why:

- Raw file covers search/booking behavior but not full operations funnel.
- Needed to analyze post-booking reliability and revenue risk.

Outputs:

- `data/processed/payment_events.csv`
- `data/processed/ticket_events.csv`
- `data/processed/refund_events.csv`

## What Synthetic Operational Events Mean

The project adds three synthetic operational tables to extend the funnel beyond booking.

### Payment Events (`payment_events.csv`)

Each row is one payment attempt for a booked record.

What it tells you:

- whether the user successfully paid or failed (`payment_status`)
- why payments failed (`payment_error_code`)
- which payment methods/devices/countries underperform
- payment amount and transaction context for revenue impact

Typical KPIs:

- payment success rate
- payment failure rate by device/method/country/destination
- gross attempted revenue

### Ticket Events (`ticket_events.csv`)

Each row tracks post-payment ticketing outcome.

What it tells you:

- whether successful payment led to fulfillment (`ticket_status`)
- how long ticketing took (`ticketing_delay_minutes`)
- operational failure modes (`ticketing_error_code`)

Typical KPIs:

- ticket issuance rate after successful payment
- delayed ticket share
- ticketing failure rate and error mix

### Refund Events (`refund_events.csv`)

Each row tracks refund state for successful payment records.

What it tells you:

- whether refund was requested (`refund_requested`)
- final disposition (`refund_status`)
- reason categories (`refund_reason`)
- financial leakage (`refund_amount`)

Typical KPIs:

- refund request rate
- approved refund rate
- refund amount rate vs total successful payment amount
- net retained revenue

### Step 4: SQL Analysis Layer

What:

- Build reusable SQL queries for funnel conversion, failure rates, and segment-level KPIs.

Why:

- SQL provides transparent, auditable metric logic and production-style analysis flow.

Outputs:

- SQL scripts in `sql/`
- query result exports in `reports/sql_outputs/`

SQL query guide:

- `sql/01_funnel_overview.sql`: stage counts and stage-to-search conversion percentages.
- `sql/02_payment_performance.sql`: payment attempts, success/failure rates, and revenue by device/method.
- `sql/03_ticketing_performance.sql`: ticket status/error distribution and delay percentiles.
- `sql/04_refund_revenue_risk.sql`: refund impact on successful-payment revenue and net retained revenue.
- `sql/05_segment_diagnostics.sql`: high-risk country/destination/device segments for failures and refunds.

### Step 5: Python Exploratory Analysis

What:

- Segment analysis, distribution checks, anomaly spotting, and visual diagnostics.

Why:

- Helps explain metric movements and surface actionable drivers.

Outputs:

- `notebooks/step5_exploratory_analysis.ipynb`

Notebook coverage:

- loads all processed datasets
- validates row counts and key table relationships
- computes funnel metrics, conversion rates, and drop-offs
- analyzes payment failures, ticketing failures, and refund patterns
- calculates revenue at risk from failed payments
- creates matplotlib charts for core KPIs
- prints 5 plain-English business insights

### Step 6: Tableau Dashboard

What:

- Build an executive-facing dashboard for funnel progression, failures, refunds, and revenue at risk.

Why:

- Turns analysis into fast, decision-ready monitoring views.

Outputs:

- Tableau dashboard screenshots in `dashboard/tableau_screenshots/`
- `dashboard/tableau_screenshots/Flights Core Services Health Dashboard.png`

### Step 7: Stakeholder Memo + Recommendations

What:

- Summarize findings, business impact, and prioritized recommendations.

Why:

- Good analytics is measured by decision quality, not only technical output.

Outputs:

- `reports/stakeholder_memo.md`
- includes a hypothetical 30-day production action plan for portfolio demonstration

## Deliverables Checklist

- [x] Cleaned dataset
- [x] Synthetic payment/ticket/refund event tables
- [x] SQL analysis
- [x] Python exploratory analysis
- [x] Tableau dashboard
- [x] Stakeholder memo with recommendations
- [ ] Final polished README

## How To Run

### 1) Create/activate virtual environment

Windows (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Windows (Git Bash):

```bash
python -m venv .venv
source .venv/Scripts/activate
```

### 2) Install dependencies

```bash
pip install -r requirements.txt
```

### 3) Build cleaned dataset

```bash
python src/build_search_booking_events.py
```

Expected output:

- `data/processed/search_booking_events.csv`

### 4) Generate payment events

```bash
python src/generate_payment_events.py
```

Expected output:

- `data/processed/payment_events.csv`
- console summary: row count, success rate, mobile vs desktop failure rates

### 5) Generate ticket events

```bash
python src/generate_ticket_events.py
```

Expected output:

- `data/processed/ticket_events.csv`
- console summary: row count and issued share

### 6) Generate refund events

```bash
python src/generate_refund_events.py
```

Expected output:

- `data/processed/refund_events.csv`
- console summary: row count and refund requested share

### 7) Run SQL analysis pack

```bash
python src/run_sql_analysis.py
```

Expected output:

- CSV outputs in `reports/sql_outputs/`
- one result file per query in `sql/`:
	- `01_funnel_overview.csv`
	- `02_payment_performance.csv`
	- `03_ticketing_performance.csv`
	- `04_refund_revenue_risk.csv`
	- `05_segment_diagnostics.csv`

### 8) Run Step 5 exploratory notebook

Open and run all cells in:

- `notebooks/step5_exploratory_analysis.ipynb`

Expected output:

- validation prints for table counts and key joins
- funnel conversion and drop-off table
- payment/ticket/refund diagnostic tables
- 4 KPI charts (funnel counts, failure rates, top errors, revenue at risk)
- 5 plain-English insights at the end

## Quick Start (One-Pass Order)

Run this exact order for the current implemented pipeline:

```bash
python src/build_search_booking_events.py
python src/generate_payment_events.py
python src/generate_ticket_events.py
python src/generate_refund_events.py
python src/run_sql_analysis.py
# then run all cells in notebooks/step5_exploratory_analysis.ipynb
```

What you can inspect right after running:

1. Funnel stage counts from each output table size.
2. Payment reliability from `payment_status` and `payment_error_code`.
3. Ticket fulfillment quality from `ticket_status` and `ticketing_delay_minutes`.
4. Revenue leakage risk from `refund_requested`, `refund_status`, and `refund_amount`.
5. SQL KPI tables in `reports/sql_outputs/` ready for dashboard inputs.

## Current Progress Snapshot

Completed:

- Raw data understanding and dictionary
- Cleaned base events table
- Synthetic payment/ticket/refund event generation
- SQL KPI analysis outputs
- Python exploratory analysis notebook outputs
- Tableau dashboard and screenshot outputs
- Stakeholder memo with recommendations
- Project documentation and run workflow

Next:

- Optional portfolio packaging (publish repo, add Tableau/Public links, add resume bullets)
