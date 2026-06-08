# AAYS Real Topography Source Acquisition Plan

PAGE_KEY=AAYS_REAL_TOPOGRAPHY_PRODUCT
MODE=REAL_TOPOGRAPHY_SOURCE_ACQUISITION_PLAN
STATUS=SOURCE_PLAN_CREATED_NO_FAKE_DATA
PRODUCT_PROGRESS_ESTIMATE=84

## Goal
Obtain a real elevation source for parcel-level topography lookup v2 without creating fake or synthetic elevation values.

## Required output artifact

`parcel_elevation_lookup_v2.json`

Each parcel entry must include:

- parcel_id
- center_elevation_m
- region_average_elevation_m
- elevation_difference_from_region_average_m
- region_sample_count
- datum
- source_dataset
- status

## Approved source priority

1. Existing project/local verified elevation artifact, if present.
2. Environment Agency National LIDAR / LIDAR Composite DTM for England, where downloadable for project tiles.
3. Ordnance Survey OS Terrain 50 as broad fallback for Great Britain, clearly labelled lower resolution.

## Source rules

- Do not fabricate center_elevation_m.
- Do not fabricate region_average_elevation_m.
- Do not write DB, run migrations, or deploy.
- If source download needs login/manual browser approval, write blocker instead of fake output.
- If using OS Terrain 50 fallback, source_dataset must clearly say OS Terrain 50 and datum/resolution metadata must be recorded.

## Application plan

### Step 1: Inventory local data
Search F:\AAYS_GITHUB_WORK\AAYS and C:\Users\cagda\Documents\GitHub\AAYS for:

- parcel_elevation_lookup_v2.json
- elevation lookup json/csv/geopackage
- DTM / DSM / lidar / terrain files
- EA LIDAR / OS Terrain files

If found, validate schema and produce a manifest.

### Step 2: Source acquisition
If no artifact is found, use official public source:

- Preferred: Environment Agency LIDAR Composite DTM for England when tile download is available.
- Fallback: OS Terrain 50 OpenData/OS Data Hub download, broad 50m post spacing.

### Step 3: Build artifact
For each parcel:

- sample center elevation from DTM grid at parcel center
- calculate region_average_elevation_m from a defensible local region/window or parcel-neighbour group
- calculate elevation_difference_from_region_average_m = center_elevation_m - region_average_elevation_m
- record region_sample_count, datum, source_dataset, status

### Step 4: Smoke
Run:

- /lookup?parcel_id=<known>
- /topography/lookup?parcel_id=<known>

Expected structured fields:

- center_elevation_m
- region_average_elevation_m
- elevation_difference_from_region_average_m
- status=ok when real data exists

### Step 5: Browser proof
Open parcel popup and verify both lines show real numbers:

- Denizden yükseklik
- Bölge ortalamasından fark

## Progress logic

- Source plan created: 84
- Real source/artifact found or downloaded: 88
- lookup v2 API smoke passes: 92
- popup browser proof passes: 100 FINAL_READY

## Current blocker

BLOCKER=WAITING_FOR_REAL_ELEVATION_SOURCE_OR_LOCAL_ARTIFACT
NEXT_ACTION=inventory local F/C data and acquire official DTM source if absent
