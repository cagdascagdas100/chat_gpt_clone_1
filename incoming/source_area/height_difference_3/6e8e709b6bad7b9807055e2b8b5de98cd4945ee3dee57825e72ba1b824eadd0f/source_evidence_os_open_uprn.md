# Ordnance Survey OS Open UPRN — source-area / linking-identifier evidence

Slot: height_difference_3
Lineage: 6e8e709b6bad7b9807055e2b8b5de98cd4945ee3dee57825e72ba1b824eadd0f
Accessed: 2026-09-27T22:55:00+03:00

Official identifiers and coverage
- Publisher: Ordnance Survey
- Product: OS Open UPRN
- National Data Library dataset ID: c4f80d19-8cfa-4bf6-a283-83183842f876
- Harvest GUID: 649aa12c-8bcd-4ff2-9c02-0556a5be3d62
- Identifier: UPRN (Unique Property Reference Number)
- UPRN semantics: unique numeric identifier for every addressable location in Great Britain
- Coverage: Great Britain
- National metadata extent: west -8.45, south 49.86, east 1.78, north 60.86
- Supply formats: CSV and GeoPackage
- Current OS product documentation update cadence: every six weeks
- Product access: free to use for everyone

Public no-login access
OS Downloads API technical documentation states that OpenData endpoints do not require an API key.
- Product: https://www.ordnancesurvey.co.uk/products/os-open-uprn
- Documentation: https://docs.os.uk/os-downloads/products/addresses-and-names-portfolio/os-open-uprn
- Downloads API: https://docs.os.uk/os-apis/accessing-os-apis/os-downloads-api/technical-specification
- Download endpoint pattern: https://api.os.uk/downloads/v1/products/OpenUPRN/downloads
- National Data Library: https://www.data.gov.uk/dataset/c4f80d19-8cfa-4bf6-a283-83183842f876/os-open-uprn

Currency note
The current Ordnance Survey product/documentation pages state an every-six-weeks refresh cadence. The National Data Library harvested metadata still reports a quarterly frequency. Both observations are preserved; the current OS product documentation is treated as the current product cadence.

Scope decision
The polygon in records.geojson is only the official metadata extent envelope. It is not a property/parcel polygon and cannot increase accepted_count.

Height Difference next step
OS Open UPRN supplies a strong authoritative linking identifier and accurate location for addressable locations, but this execution context still does not expose a UPRN field or canonical geometry for partition rows 61523–92283. Local OpenCode must first establish a trusted canonical-row-to-UPRN or spatial link, then intersect official building footprints, retain building-present canonical parcels, and calculate official DEM/LIDAR min/max/mean/max-min statistics.
