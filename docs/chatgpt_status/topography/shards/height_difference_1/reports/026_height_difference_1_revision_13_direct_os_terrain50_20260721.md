# Height Difference 1 — Revision 13 direct OS Terrain 50 crosscheck

- Same logical task and idempotency key are preserved.
- Revision 12 direct EA DTM 1 m polygon sampling remains the parcel-range measurement source.
- Revision 13 resolves OS Terrain 50 from the official OS Downloads API and downloads the exact required area archive.
- The exact 10 km ASCII-grid tile is selected from the official HMLR polygon representative point.
- Acceptance requires a 200×200 grid, 50 m cells, EPSG:27700, ODN/EPSG:5701 vertical metadata, non-NoData elevation, and SHA-256 evidence for API responses, archive, grid, and vertical metadata.
- OS Terrain 50 remains an independent absolute-elevation and datum crosscheck only; it is never used to calculate parcel height range.
- EA median versus OS elevation above 8 m requires human review and blocks promotion.
- Synthetic/source validation: 24/24 passed. Runtime network execution has not occurred.
- `final_ready=false`
