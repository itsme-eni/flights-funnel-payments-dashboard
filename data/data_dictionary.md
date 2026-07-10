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

## Column-by-column dictionary (name + actual interpretation)

| Column | What it is | Actual interpretation (how to read it) |
|---|---|---|
| `Unnamed: 0` | Technical row ID from source extract | Unique row key from the original file export. Use it only for tracking rows; do not use as a business feature. |
| `date_time` | Search event timestamp | The exact time the user performed the search action. This is event time (not travel date). |
| `site_name` | Site/brand code | Which Expedia site/brand captured the event. Different codes represent different storefronts/local sites. |
| `posa_continent` | Point-of-sale continent code | Continent of the sales market where the booking/search was made (user purchase market context). |
| `user_location_country` | User country code | Country code of the user at search time. Useful for demand source segmentation. |
| `user_location_region` | User region/state code | Sub-country location for the user (state/province-like code, system-defined). |
| `user_location_city` | User city code | City-level location code for the searching user. High-cardinality location identifier. |
| `orig_destination_distance` | Distance value | Approximate distance between user origin and destination. Larger values generally indicate long-haul intent; missing in many rows. |
| `user_id` | Anonymous user identifier | Pseudonymous customer ID. Lets you count distinct users and repeated behavior over time. |
| `is_mobile` | Binary flag | `1` means the event came from mobile; `0` means non-mobile (desktop/web). |
| `is_package` | Binary flag | `1` means the interaction was package-related (bundle flow); `0` means stand-alone travel flow. |
| `channel` | Acquisition channel code | Marketing/distribution channel for the session (internal numeric channel taxonomy). |
| `srch_ci` | Check-in date | Intended trip start date the user searched for. Compare with `date_time` to compute booking/search lead time. |
| `srch_co` | Check-out date | Intended trip end date. `srch_co - srch_ci` gives stay length (nights). |
| `srch_adults_cnt` | Adults count | Number of adults in the requested trip/room search party. |
| `srch_children_cnt` | Children count | Number of children included in the search party. |
| `srch_rm_cnt` | Rooms count | Number of hotel rooms requested in the search. |
| `srch_destination_id` | Destination code | System destination identifier the user searched for (city/area-level destination grouping). |
| `srch_destination_type_id` | Destination type code | Type/hierarchy of destination (for example city/region/other internal grouping). |
| `is_booking` | Conversion flag | `1` means this interaction ended in a booking; `0` means it did not convert. |
| `cnt` | Event count weight | Number of similar events represented by this row. Use as weight in totals/rates when appropriate. |
| `hotel_continent` | Hotel continent code | Continent where the candidate/booked hotel is located. |
| `hotel_country` | Hotel country code | Country where the candidate/booked hotel is located. |
| `hotel_market` | Hotel market code | Internal market/geography grouping for hotels. Useful for market-level performance reporting. |
| `hotel_cluster` | Hotel cluster label code | Cluster/category assigned to hotels (modeling/recommendation label), not a numeric ranking. |

## Practical interpretation tips

- Most geo/location fields are encoded IDs, not human-readable names.
- `hotel_cluster` is categorical and should not be treated as ordered numeric magnitude.
- `is_booking` is strongly imbalanced (~8% positive), so metrics like accuracy can be misleading.
- Because `cnt` is an event count, some analyses should consider weighted aggregations.
- `date_time` is event time, while `srch_ci`/`srch_co` are stay dates. Feature engineering should keep this distinction.
- `orig_destination_distance` has significant missingness and may need imputation or missing-indicator features.

## Profiling artifact

Detailed machine-readable profile was generated at:

- `data/raw/raw_profile_summary.json`

This file contains per-column non-null counts, null percentages, unique counts, and top values.
