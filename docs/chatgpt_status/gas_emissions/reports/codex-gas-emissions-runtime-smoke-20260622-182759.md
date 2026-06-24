# Gas Emissions Runtime Smoke

- date: 2026-06-22 18:27:59 Europe/Istanbul
- repo_root: `C:\Users\cagda\Documents\GitHub\AAYS`
- branch: `feature/terrayield-aays-integration`
- layer: `Gas Emissions`

## Handoff truth check

The provided handoff/report chain claimed `FINAL_READY` and `completion_percent=100`, but the active checkout did not actually contain the required runtime state.

Observed before repair:

- `england_map_web/data/parcel_emissions_scores.geojson` was missing in the active checkout.
- `england_map_web/app.js` contained icon/control markers, but the visible Gas Emissions worth-menu item still pointed to `worth-trend.svg`.
- The live layer did not have a real parcel/point data bridge tied to `parcel_emissions_scores.geojson`.

## Changes applied in active checkout

File: `C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\app.js`

- added inline gas-emissions runtime bridge
- added GeoJSON source and layer ids:
  - `aays-gas-emissions-source`
  - `gas-emissions-fill`
  - `gas-emissions-line`
  - `gas-emissions-point`
- bound gas layer to `./data/parcel_emissions_scores.geojson`
- added legend/popup field mapping for:
  - emission percent
  - level
  - risk color
  - confidence
  - source type
  - source evidence
  - source date
  - matching method
  - calculation explanation
- aligned visible worth-menu icon to `./assets/icons/terrayield_icons/air.png`
- added guards for an existing noisy `selectedParcelFeature` warning path in a legacy overlay patch

Data copied into active checkout:

- `C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\data\parcel_emissions_scores.geojson`
- `C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\data\parcel_emissions_scores.csv`
- `C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\data\parcel_emissions_score_manifest.json`
- `C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\data\parcel_emissions_source_registry.csv`

## Data verification

- `feature_count=4246`
- first `parcel_id=35729957`
- first `emission_percent=43.6`
- first `source_type=air_quality_proxy`
- first `confidencePercent=65.0`

## Runtime verification

HTTP probes:

- `http://127.0.0.1:8010/health` -> `200`
- `http://127.0.0.1:8010/england_map_web/` -> `200`
- `http://127.0.0.1:8010/england_map_web/app.js` -> `200`
- `http://127.0.0.1:8010/england_map_web/data/parcel_emissions_scores.geojson` -> `200`
- `http://127.0.0.1:8010/england_map_web/assets/icons/terrayield_icons/air.png` -> `200`

Static syntax:

- `node --check england_map_web/app.js` -> pass

Browser smoke:

- local app opened at `http://127.0.0.1:8010/england_map_web/`
- visible Gas Emissions worth-menu icon is now `air.png`
- clicking the gas item opens the layer
- map legend appears with:
  - `Gas Emissions`
  - `Katman hazir | proxy source`
  - `0-20% Very Low`
  - `21-40% Low`
  - `41-60% Medium`
  - `61-80% High`
  - `81-100% Very High`
  - `No Data`

## Remaining limitation

The browser session used in this smoke was already persisted to a viewport where the gas layer reported `Bu gorunumde veri yok`, so this run confirmed:

- app opens
- icon is correct
- data file is served
- layer toggle works
- legend is rendered

This smoke did **not** finish a parcel click on a data-bearing gas feature in the same browser session. Because of that, the original handoff claim of full `100%` completion is still stronger than the evidence currently available in this active checkout.

Also note:

- browser dev logs contained older `selectedParcelFeature` warnings from previous app loads
- guard patches were added in source, but a clean post-fix runtime proof for that unrelated legacy warning was not isolated in this smoke

## Practical status

- app_open: `true`
- gas_icon_contract: `true`
- gas_data_served: `true`
- gas_toggle_runtime: `true`
- gas_legend_visible: `true`
- gas_popup_on_data_feature_clicked_in_this_smoke: `false`
- honest_status: `PARTIAL_RUNTIME_CONFIRMED`
