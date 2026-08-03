# Flights Funnel + Payments Dashboard

Portfolio project (Booking.com-style Data Analyst II case study) focused on end-to-end funnel analytics:

Search -> Booking -> Payment Attempt -> Payment Success -> Ticket Issued -> Refund

The project combines Python, SQL, and Tableau to explain where users drop off, where revenue is at risk, and what product/ops actions can improve conversion.

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
- `src/build_search_booking_events.py` (cleaning + profiling script)
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

Planned outputs:

- `data/processed/payment_events.csv`
- `data/processed/ticket_events.csv`
- `data/processed/refund_events.csv`

### Step 4: SQL Analysis Layer

What:

- Build reusable SQL queries for funnel conversion, failure rates, and segment-level KPIs.

Why:

- SQL provides transparent, auditable metric logic and production-style analysis flow.

Planned outputs:

- SQL scripts in `sql/`

### Step 5: Python Exploratory Analysis

What:

- Segment analysis, distribution checks, anomaly spotting, and visual diagnostics.

Why:

- Helps explain metric movements and surface actionable drivers.

Planned outputs:

- Analysis scripts/notebooks in `src/` and/or `notebooks/`

### Step 6: Tableau Dashboard

What:

- Build an executive-facing dashboard for funnel progression, failures, refunds, and revenue at risk.

Why:

- Turns analysis into fast, decision-ready monitoring views.

Planned outputs:

- Tableau workbook/screenshots in `dashboard/`

### Step 7: Stakeholder Memo + Recommendations

What:

- Summarize findings, business impact, and prioritized recommendations.

Why:

- Good analytics is measured by decision quality, not only technical output.

Planned outputs:

- `reports/stakeholder_memo.md`

## Deliverables Checklist

- [x] Cleaned dataset
- [ ] Synthetic payment/ticket/refund event tables
- [ ] SQL analysis
- [ ] Python exploratory analysis
- [ ] Tableau dashboard
- [ ] Stakeholder memo with recommendations
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
