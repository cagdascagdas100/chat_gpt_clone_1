# Height Difference 1 — Official direct tile fallback revision 4

- Slot: `height_difference_1`
- Parcel partition: `1-30761`
- Existing task retained: `height-difference-1-official-boundary-elevation-samples-20260720`
- Queue payload revision: `4`
- New runner created: `false`
- Parallel task created: `false`

## New official-source execution paths

1. HMLR INSPIRE WFS is queried with WFS 1.0.0, 1.1.0 and 2.0.0 plus multiple CadastralParcel type-name variants.
2. If WFS returns no polygon, the current HMLR monthly download page is scanned for Barnet and Enfield GML files, which are parsed by point-in-polygon.
3. Environment Agency DTM 1 m, 2 m and 10 m WCS calls use multiple axis-label variants.
4. If EA WCS fails, all three candidate coordinates use the same 5 km National Grid fallback tile: `TQ29SE`.
5. OS Terrain 50 uses the July 2026 downloads API, selects 10 km tile `TQ29`, parses the ASCII grid and samples each candidate cell.
6. Every downloaded payload is bounded by a 120 MB limit and recorded with SHA-256 metadata.

## Acceptance guards

- A measured parcel row requires a real HMLR polygon match and an EA 1 m numeric DTM value.
- EA 2 m and 10 m values are same-provider resolution checks, not independent sources.
- Independent two-source validation requires OS Terrain 50 and an EA-versus-OS spread no greater than 8 m.
- Missing official bytes produce `NO_DATA_NOT_INFERRED`.
- No database writes, migrations or production deployment are permitted.

## Current blocker

The existing canonical F portable single coordinator has not claimed the slot. The queue remains pending, the heartbeat remains unclaimed/stale, and no revision 4 runner output is present yet.
