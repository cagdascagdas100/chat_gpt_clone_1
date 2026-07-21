# Height Difference 1 — Revision 14 direct HMLR monthly-GML refresh

## Result

Revision 14 closes the remaining inherited-boundary provenance gap. The same logical task now refreshes HM Land Registry INSPIRE geometry directly from the current monthly local-authority GML publication before trusting the EA DTM 1 m and OS Terrain 50 results.

## Acceptance contract

- Resolve exactly one download link each for London Borough of Barnet and London Borough of Enfield.
- Require the 5 July 2026 publication and first-Sunday monthly cadence.
- Hash the download page, raw downloads and extracted GML files with SHA-256.
- Require source CRS EPSG:27700.
- Match by exact HMLR INSPIRE ID and candidate point inside the polygon.
- Deduplicate identical geometry appearing in both authority files.
- Reject conflicting duplicate geometry, nearest/fuzzy matching and point-in-polygon-only fallback.
- Require the fresh GML geometry to be topologically equal to the geometry used by direct EA and OS sampling.
- A source or row-level HMLR refresh error is blocked and cannot become a valid NO_DATA terminal.

## Validation

- Source and synthetic GML tests: `55/55`
- Output-integrity tests: `29/29`
- Combined: `84/84`
- Runtime network execution on the F host: not yet performed
- Official measured rows: `0`
- `final_ready=false`
