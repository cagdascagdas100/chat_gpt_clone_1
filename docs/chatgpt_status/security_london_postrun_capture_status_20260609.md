# Security London Postrun Capture
Task: security-asayis-london-postrun-capture-20260609
Started: 2026-06-09T20:54:36.2675903+03:00
RepoRoot: C:\AAYS_GITHUB_BRIDGE_CLEAN2
FWorkRoot: F:\chatgpt\AAYS_WORK\security_asayis_london_pilot_20260609

## Pilot Script
Path: C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-task-scripts\security_asayis_london_pilot_001_20260609.ps1
Exists: True

## Pilot Script Output
# Security / AsayiÅY London-only Pilot Status â?" F Drive Work Root

Task: security-asayis-london-pilot-001-fdrive-20260609
Started: 2026-06-09T20:54:37.9675288+03:00
Completed: 2026-06-09T20:54:40.1289095+03:00
F work root: F:\chatgpt\AAYS_WORK\security_asayis_london_pilot_20260609
Repo root: C:\AAYS_GITHUB_BRIDGE_CLEAN2

## Guardrails
- DB write: false
- DDL: false
- Migration: false
- Production deploy: false
- Fake data: false

## Storage Policy
- New/heavy processing outputs are written to F drive only.
- Existing C-drive repo files are not moved.
- GitHub-readable repo outputs are limited to lightweight status/summary files under ai-results and docs/chatgpt_status.
- All-England outputs are not overwritten.

## Scope
- London only / Greater London bounding box plus London borough/property-name fallback.
- Police.uk locations are anonymised/approximate; UI must label results as area/LSOA-based safety estimates, not exact parcel crime evidence.

## Results
- Point input exists: False
- Point total features: 0
- Point London features: 0
- Point output on F: F:\chatgpt\AAYS_WORK\security_asayis_london_pilot_20260609\data\parcel_security_scores_london_pilot_points.geojson
- Polygon input exists: False
- Polygon total features: 0
- Polygon London features: 0
- Polygon output on F: F:\chatgpt\AAYS_WORK\security_asayis_london_pilot_20260609\data\parcel_security_scores_london_pilot_polygons.geojson

## F Outputs
- F:\chatgpt\AAYS_WORK\security_asayis_london_pilot_20260609\data\parcel_security_scores_london_pilot_points.geojson
- F:\chatgpt\AAYS_WORK\security_asayis_london_pilot_20260609\data\parcel_security_scores_london_pilot_polygons.geojson
- F:\chatgpt\AAYS_WORK\security_asayis_london_pilot_20260609\data\parcel_security_london_pilot_summary.json
- F:\chatgpt\AAYS_WORK\security_asayis_london_pilot_20260609\data\security_london_pilot_method_manifest.json
- F:\chatgpt\AAYS_WORK\security_asayis_london_pilot_20260609\qa\london_security_color_level_matrix.csv
- F:\chatgpt\AAYS_WORK\security_asayis_london_pilot_20260609\qa\london_security_acceptance.md

## Next Step
If London feature counts are valid, create London-only frontend overlay wiring and popup evidence note. Keep all-England files untouched.

## Exit
Pilot exit code: 0

## Repo Outputs
- C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-results\security_london_pilot_latest_status.md: exists=True size=2290
- C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-results\security_london_pilot_latest_status.json: exists=True size=5711
- C:\AAYS_GITHUB_BRIDGE_CLEAN2\docs\chatgpt_status\security_london_pilot_status_20260609.md: exists=True size=2290

## F Outputs
- F:\chatgpt\AAYS_WORK\security_asayis_london_pilot_20260609\data\parcel_security_scores_london_pilot_points.geojson: exists=False size=0
- F:\chatgpt\AAYS_WORK\security_asayis_london_pilot_20260609\data\parcel_security_scores_london_pilot_polygons.geojson: exists=False size=0
- F:\chatgpt\AAYS_WORK\security_asayis_london_pilot_20260609\data\parcel_security_london_pilot_summary.json: exists=True size=5711
- F:\chatgpt\AAYS_WORK\security_asayis_london_pilot_20260609\data\security_london_pilot_method_manifest.json: exists=True size=1277
- F:\chatgpt\AAYS_WORK\security_asayis_london_pilot_20260609\qa\london_security_color_level_matrix.csv: exists=True size=438
- F:\chatgpt\AAYS_WORK\security_asayis_london_pilot_20260609\qa\london_security_acceptance.md: exists=True size=2290

## Decision
FINAL_READY_CANDIDATE: true
Next: create London-only frontend overlay/popup/legend validation task.
