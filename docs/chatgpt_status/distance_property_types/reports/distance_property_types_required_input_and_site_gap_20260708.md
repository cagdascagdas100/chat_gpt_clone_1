# Distance Property Types Required Input and Site Gap

page_key: distance_property_types
status: blocked_waiting_real_source_candidates
final_ready: false
fake_data: false
db_write: false
migration: false
production_deploy: false

## Current result

The shared runner picked up the page task and wrote an output report. The page task is blocked because there are no real evidence rows for this layer.

## Missing required file

docs/chatgpt_status/distance_property_types/inputs/distance_property_types_source_candidates.csv

## Why the site is still empty

The site data files exist as bootstrap files, but the verified CSV has only a header and the verified GeoJSON has no features. This means the user cannot observe real map changes yet.

## Required source candidates

The input file must contain real parcel level evidence. At minimum each usable row needs a parcel id, a property type candidate, source evidence text or URL, source date, and matching method. Rows without evidence must not be converted into verified site features.

Allowed property types are Industrial Unit, Detached Home, Retail Property, Apartment Building, Office Building, Mixed Building, and Unknown. Weak or conflicting evidence must be marked for manual review.

## Required output files after input is available

england_map_web/data/distance_property_types/distance_property_types_verified.csv
england_map_web/data/distance_property_types/distance_property_types_verified.geojson
england_map_web/data/distance_property_types/distance_property_types_evidence_manifest.json
docs/chatgpt_status/distance_property_types/reports/distance_property_types_manual_review_latest.csv
docs/chatgpt_status/distance_property_types/reports/distance_property_types_progress_latest.md

## Next action

Create the real source candidates file from official planning, registry, address, web listing, map label, or photo AI evidence. Then run the existing single shared runner again. Do not fabricate parcel ids, geometry, property types, distances, source URLs, or confidence scores.
