# Height Difference 1 — revision 5 streaming polygon execution upgrade

- Slot: `height_difference_1`
- Existing task ID preserved: `height-difference-1-official-boundary-elevation-samples-20260720`
- New logical task: no
- New or parallel runner: no
- Active shared control overridden: no
- Payload revision: `5`
- Script SHA-256: `2b6efa6cd7265993b226d6c83034b7c0858318ad2605eb5401fafcac8569140c`

## Verified official contracts

- HM Land Registry INSPIRE monthly GML release: 5 July 2026.
- Barnet and Enfield are present in the current local-authority download list.
- HMLR bulk catalogue reports monthly GML delivery and no bulk API; average file size is 13.66 MB.
- Environment Agency documents persistent WCS 2.0.1 endpoints for DTM 1 m and 2 m.
- OS Terrain 50 July 2026 grid supply is 10 km tiles, 200 × 200 cells, 50 m cell size, heights to 0.1 m.
- The earlier 120 MB OS budget was lower than the current national archive observed size; revision 5 streams to disk with a 220 MB ceiling.

## Execution improvements

1. Three official source families may download concurrently, maximum three workers.
2. HMLR Barnet and Enfield GML files are streamed and parsed for real point-in-polygon matches.
3. HMLR WFS remains a multi-version, multi-type-name fallback.
4. EA 1 m, 2 m and 10 m requests cover all three candidates per request.
5. EA 1 m values are polygon-masked median/min/max/IQR statistics, not centroid-only values.
6. EA survey `TQ29SE` 5 km GeoTIFF discovery remains the 1 m fallback.
7. OS Terrain 50 is streamed to disk, then `TQ29.asc` is sampled from the exact ASCII header.
8. A measured row requires HMLR polygon + EA 1 m polygon numeric + independent OS numeric and an EA/OS difference no greater than 8 m.

## Validation

- Local deterministic tests: `8/8`
- Network execution: pending canonical F portable shared runner
- Measured rows written during preparation: `0`
- `final_ready=false`
