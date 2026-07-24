# AAYS1 115 - Source verified product integration

Status: `SOURCE_VERIFIED_PRODUCT_INTEGRATION_COMPLETED_PANEL_70_PENDING_BROWSER_SMOKE`

## What changed

- 24 candidates from 113 were already checked in 114.
- 18 were live-source accessible.
- 10 high-confidence source-backed rows were integrated into site data.
- Panel/product progress moved from 65% to 70%.

## New site outputs

- `england_map_web/data/aays1/aays1_114_source_verified_integrated.csv`
- `england_map_web/data/aays1/aays1_114_source_verified_integrated.geojson`
- `england_map_web/data/aays1/aays1_product_status_latest.json`
- `england_map_web/data/runner_panel/aays1_visible_positive_progress_latest.json`
- `england_map_web/data/runner_panel/page_status_index.json`

## Accuracy policy

Integrated rows have source verification scores from 3.0 to 3.25 out of 4. They are counted as source-backed rows, not as finalized parcel geometry rows.

## Geometry policy

No geometry was invented. The new GeoJSON features use `geometry:null` until canonical parcel/boundary geometry is proven.

## Safety

- final_ready=false
- product_final_ready=false
- fake_data=false
- db_write=false
- migration=false
- production_deploy=false

## Remaining blockers

- Browser smoke and popup/right panel proof required before final readiness.
- Canonical geometry/boundary evidence required before non-null geometry for the 10 newly integrated rows.
