# future_growth_2 — HMLR exact crosswalk readiness and official source wave 2

## Scope

- Slot: `future_growth_2`
- Parcel partition: `30762–61522` (`30,761` rows)
- Canonical scope: `LONDON_CANONICAL_92283_NOT_ALL_ENGLAND`
- Updated: `2026-07-21T05:45:00+03:00`
- `final_ready=false`

## Remote readback

Authoritative ownership, checkpoint, status, heartbeat and current-task were re-read. The slot remained `UNCLAIMED`; owner, lease, heartbeat timestamp, task and attempt were null. No other slot was modified.

## New official source evidence

1. HM Land Registry INSPIRE Index Polygons current download page reports a `5 July 2026` publication and monthly local-authority GML files.
2. The current page lists the London authorities required by the candidate set.
3. HM Land Registry technical guidance confirms British National Grid (`EPSG:27700`) and warns that reprojection to WGS84 may shift positions by up to 15 metres. The exact intersection therefore stays in the HMLR source CRS.
4. Planning Data entity pages expose an official per-entity GeoJSON endpoint at `/entity/<id>.geojson`.

## Candidate wave 2

- Researched: **6**
- Eligible: **6**
- Source confidence ≥90: **6**
- Average source confidence: **98.0/100**
- Cumulative researched: **14**
- Cumulative eligible: **12**
- Cumulative average eligible source confidence: **98.2/100**
- Canonical parcel matches: **0**
- Product scores: **0**
- Actual business rows: **0**

New records: Battersea Power Station / South Lambeth Goods Depot, 148–154 Streatham High Road, Former Parcel Force Depot Geron Way, Giffin Street / Former Tidemill School, Springfield Hospital, and Thames Road.

## Fail-closed automation

- `003_acquire_hmlr_inspire_authority_gml.py` accepts only exact authority rows from the official HMLR host, validates XML/GML signatures, and hashes downloads.
- `004_fetch_planning_geojson_then_exact_hmlr_intersection.py` requires one exact HMLR INSPIRE ID and the same explicit ID in the canonical shard.
- Point geometry is confidence-capped at `65`; polygon geometry at `90`.
- Multiple intersections, missing IDs, non-official hosts, absent geometry and IDs outside the shard remain blocked.
- Nearest-point promotion is forbidden.
- Offline helper tests: **8/8 PASS**.
- Live downloads/intersections: **not executed in this session**.

## Progress

- Operational preparation: **25/29 = 86.21%** (**+16.21 points**)
- Verified product rows: **0/30,761 = 0.00%**
- Next verified step: `RUN_EXISTING_SINGLE_RUNNER_CONTRACT_001_THEN_003_THEN_004`

Safety remains unchanged: `fake_data=false`, `db_write=false`, `migration=false`, `production_deploy=false`, `final_ready=false`.
