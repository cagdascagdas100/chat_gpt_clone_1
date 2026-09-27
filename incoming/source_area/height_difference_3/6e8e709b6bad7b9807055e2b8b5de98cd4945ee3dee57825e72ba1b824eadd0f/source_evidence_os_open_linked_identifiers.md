# Ordnance Survey OS Open Linked Identifiers — source-area / identifier-bridge evidence

Slot: height_difference_3
Lineage: 6e8e709b6bad7b9807055e2b8b5de98cd4945ee3dee57825e72ba1b824eadd0f
Accessed: 2026-09-27T22:55:00+03:00

Official identifiers
- Publisher: Ordnance Survey
- Product: OS Open Linked Identifiers
- National Data Library dataset ID: d6467386-a08f-48f8-9e91-2e1e6531cce7
- Harvest GUID: 0c11b4a1-0ece-4ad4-bccb-77ae890238e6
- Coverage: Great Britain
- Format: CSV join tables
- Current OS documentation update cadence: every six weeks
- National Data Library harvested metadata frequency: quarterly
- Metadata extent: west -8.45, south 49.86, east 1.78, north 60.86

Relationship relevant to Height Difference
- Relationship ID: BLPU_UPRN_TopographicArea_TOID_5
- Relationship: BLPU (UPRN) <-> TopographicArea (TOID)
- OS technical specification describes TopographicArea here as an OS MasterMap Topographic Layer polygon limited to either a building outline or road surface area.
- OS states these identifier relationships are authoritative and spatially matched to OS MasterMap features.

Public no-login access
- OS Open Linked Identifiers is an OS OpenData product.
- OS Downloads API documentation states that OpenData endpoints do not require an API key.
- Product: https://www.ordnancesurvey.co.uk/products/os-open-linked-identifiers
- Technical specification: https://docs.os.uk/os-downloads/products/buildings-and-infrastructure-portfolio/os-open-linked-identifiers/os-open-linked-identifiers-technical-specification
- Product structure: https://docs.os.uk/os-downloads/products/buildings-and-infrastructure-portfolio/os-open-linked-identifiers/os-open-linked-identifiers-technical-specification/product-structure
- Downloads API: https://docs.os.uk/os-apis/accessing-os-apis/os-downloads-api/technical-specification
- National Data Library: https://www.data.gov.uk/dataset/d6467386-a08f-48f8-9e91-2e1e6531cce7/os-open-linked-identifiers

Scope and acceptance semantics
The product is a non-spatial linked-identifier join-table product; the polygon stored in records.geojson is only the official metadata extent envelope. No canonical parcel is accepted.

Height Difference next step
If local canonical rows expose UPRN, the BLPU_UPRN_TopographicArea_TOID_5 relationship can bridge UPRN to a TopographicArea TOID associated with a building outline or road-surface polygon. Local OpenCode still must verify the canonical UPRN/geometry field, retain only building-present canonical parcels using real footprint geometry, then intersect official DEM/LIDAR sources and calculate min/max/mean/max-min.
