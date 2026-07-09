# Raw Data Guide: `travel.csv`

This document explains the raw dataset used in this project:

- Source file: `data/raw/travel.csv`
- Profile snapshot date: 2026-07-09
- Rows: 100,000
- Columns: 25
- Time window (search event timestamp): 2013-01-07 00:33:47 to 2014-12-31 23:47:14

## What this dataset is

`travel.csv` is a sample of hotel search and booking events (Expedia-style structure). Each row is a user interaction tied to a hotel market and cluster label. Not every row is a booking; many rows are clicks/views.

This means:

- `is_booking = 1` are conversions (bookings)
- `is_booking = 0` are non-booking interactions
- `cnt` is an event weight/count for aggregated interactions

## Quick profile summary

- Booking rate (`is_booking=1`): 7.99%
- Mobile share (`is_mobile=1`): 13.38%
- Package share (`is_package=1`): 24.81%
- Main missingness issue: `orig_destination_distance` is 36.09% null
- Light missingness: `srch_ci` and `srch_co` are each 0.12% null
- Most fields are coded IDs (country, region, destination, hotel market, hotel cluster)

## Column-by-column dictionary

| Column | Type (raw) | Meaning | Data quality / notes |
|---|---|---|---|
| `Unnamed: 0` | Integer-like ID | Row identifier from source extract | 100% present; unique per row in this sample. Safe to treat as technical key only. |
| `date_time` | Datetime string | Timestamp when search event happened | 100% present; very high cardinality (near-unique). |
| `site_name` | Categorical code | Expedia site/brand identifier where event occurred | 41 unique values. Dominated by code `2`. |
| `posa_continent` | Categorical code | Point-of-sale continent (user market) | 5 unique values. Mostly code `3`. |
| `user_location_country` | Categorical code | User country code | 201 unique values. Mostly code `66`. |
| `user_location_region` | Categorical code | User region/state code | 779 unique values. |
| `user_location_city` | Categorical code | User city code | 10,779 unique values. |
| `orig_destination_distance` | Float-like | Distance between user origin and searched destination | 36.09% null; numeric when present; high cardinality. |
| `user_id` | Integer-like ID | Anonymous user identifier | 100% present; 88,863 unique users in 100,000 rows. |
| `is_mobile` | Binary flag (`0/1`) | Event came from mobile channel | 100% present; 13.38% are mobile. |
| `is_package` | Binary flag (`0/1`) | Search/booking was part of package flow | 100% present; 24.81% are package. |
| `channel` | Categorical code | Marketing/acquisition channel code | 11 unique values; mostly code `9`. |
| `srch_ci` | Date string | Search check-in date | 0.12% null; range 2013-01-07 to 2016-05-10. |
| `srch_co` | Date string | Search check-out date | 0.12% null; range 2013-01-08 to 2016-05-13. |
| `srch_adults_cnt` | Integer-like | Number of adults in request | 100% present; mostly 1-2 adults. |
| `srch_children_cnt` | Integer-like | Number of children in request | 100% present; mostly 0 children. |
| `srch_rm_cnt` | Integer-like | Number of rooms requested | 100% present; mostly 1 room. |
| `srch_destination_id` | Categorical code | Destination identifier used by source system | 8,827 unique values. |
| `srch_destination_type_id` | Categorical code | Destination type hierarchy code | 8 unique values; mostly code `1` then `6`. |
| `is_booking` | Binary target-like flag (`0/1`) | Indicates whether row is a booking | 100% present; positive class is 7.99%. |
| `cnt` | Integer-like weight | Count/weight of similar events represented by row | 32 unique values; mostly `1`. |
| `hotel_continent` | Categorical code | Hotel continent code | 7 unique values; mostly code `2`. |
| `hotel_country` | Categorical code | Hotel country code | 178 unique values; mostly code `50`. |
| `hotel_market` | Categorical code | Hotel market identifier | 1,843 unique values. |
| `hotel_cluster` | Categorical code / label | Hotel cluster (often used as recommendation/class label) | 100 unique cluster labels. |

## Practical interpretation tips

- Most geo/location fields are encoded IDs, not human-readable names.
- `hotel_cluster` is categorical and should not be treated as ordered numeric magnitude.
- `is_booking` is strongly imbalanced (~8% positive), so metrics like accuracy can be misleading.
- Because `cnt` is an event count, some analyses should consider weighted aggregations.
- `date_time` is event time, while `srch_ci`/`srch_co` are stay dates. Feature engineering should keep this distinction.
- `orig_destination_distance` has significant missingness and may need imputation or missing-indicator features.

## Recommended cleaning for downstream analysis

1. Drop or ignore `Unnamed: 0` as a feature.
2. Parse `date_time`, `srch_ci`, `srch_co` to datetime types.
3. Create derived features: booking lead time, length of stay, weekend check-in, etc.
4. Handle missing `orig_destination_distance` with either:
	- imputation (median by market/region), or
	- a missing flag + imputed value.
5. Treat coded numeric fields as categorical where appropriate (`site_name`, `channel`, `hotel_cluster`, etc.).
6. Decide early whether to use `cnt` as sample weight in KPIs/models.

## Profiling artifact

Detailed machine-readable profile was generated at:

- `data/raw/raw_profile_summary.json`

This file contains per-column non-null counts, null percentages, unique counts, and top values.
