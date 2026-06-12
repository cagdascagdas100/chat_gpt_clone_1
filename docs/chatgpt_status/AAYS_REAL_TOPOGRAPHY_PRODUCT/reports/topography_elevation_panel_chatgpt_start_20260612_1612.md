# Topography / Elevation Panel — ChatGPT Start Report

Status: ENVIRONMENT_DEPENDENT, not final complete yet.

## Package verification

- ZIP SHA256 verified in ChatGPT sandbox: C5BE32533A5E65DA48AD06DE65543AA11D14E6CFBC49C3BD6B3A1857BDEE96DC
- Application code was not directly changed by ChatGPT in GitHub in this step.
- Generated local artifacts: frontend diff + local PowerShell patch script.

## Verified findings

- `england_map_web/app.js` has Topography menu item, but it still points to `./assets/icons/worth-waves.svg`.
- `fetchParcelElevationForPopup()` stores only numeric `center_elevation_m` in `parcelElevationCache`.
- Popup sea-level elevation exists, but full Topography output contract is not reliably displayed.
- Sales-only popup branch contains broken/unsafe `parcelId` / `properties` references in the Topography regional-difference row.
- Source-context `app.js` passed `node --check` before and after the proposed patch.

## Patch generated

Target: `england_map_web/app.js`

Patch contents:

1. Bind Topography icon to `./assets/icons/terrayield_icons/hight_differance.png`.
2. Cache normalized full lookup object instead of only numeric elevation.
3. Display required Topography fields in selected parcel popup:
   - `center_elevation_m`
   - `region_average_elevation_m`
   - `elevation_difference_from_region_average_m`
   - `region_scope_type`, `region_scope_value`, `region_sample_count`
   - `source_dataset`, `topography_source`, `source_date`, `calculated_at`
   - `datum`, `confidence_level`, `confidence_reason`, `matching_method`, `calculation_explanation`
4. Use `Veri yok` fail-closed fallback for missing fields.
5. Remove broken `parcelId` / `properties` references from sales-only popup branch.

## Required local validation

```powershell
Set-Location "C:\Users\cagda\Documents\GitHub\AAYS"
node --check england_map_web\app.js
powershell -ExecutionPolicy Bypass -File "terrayield_land_intelligence\docs\chatgpt_handoff\topography_elevation_panel_low_credit_20260612\07_LOCAL_READONLY_AUDIT.ps1"
Invoke-WebRequest "http://127.0.0.1:8765/lookup?parcel_id=61631825" -UseBasicParsing -TimeoutSec 8 | Select-Object -ExpandProperty Content
```

## Final completion gate

Do not mark Topography final-complete until local runtime/browser evidence confirms the selected parcel popup or panel displays sea-level elevation, regional average elevation, regional difference, source, confidence, matching method, and calculation explanation.

Flags: db_write=false, migration=false, production_deploy=false, fake_data=false.
