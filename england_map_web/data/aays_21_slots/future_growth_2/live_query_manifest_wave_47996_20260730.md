# future_growth_2 live official query manifest

Continuation key: `5c59c5cee91d859c9e09480645ef8b17efe264568f2a4e312dd49d70e2958462`
Generated: `2026-07-30T21:43:00+03:00`

Read-only official ArcGIS `returnIdsOnly` point-intersects queries. Transport failure is not interpreted as a positive or negative result.

Transport: 123 attempts; parallelism 123; exit counts {6: 6, 28: 117}; HTTP counts {'000': 123}; body bytes 0; JSON 0/123; raw-response SHA-256 0/123.

Query manifest SHA-256: `9a3f76a7d94a9f06be90c4d9df8ac11340b8e449d5478b930b1065eb60f337c3`
Transport results SHA-256: `9660eeff78a685652981f3700053a7adac8a0cf70e0678ccf5e2cc53940343e9`
Operation-chain SHA-256: `e10710d2d0b813195465fdd2f99446cbfa15980780d074345d7670396268489a`

Layers crossed with rows 30762, 46142 and 61522:
- OPDC 0 Existing Enhanced Routes (UNRESOLVED_IN_SEARCH_SNAPSHOT, NEW, SERVICE_INVENTORY_ONLY)
- OPDC 1 Places (UNRESOLVED_IN_SEARCH_SNAPSHOT, NEW, SERVICE_INVENTORY_ONLY)
- OPDC 4 Neighbourhood Town Centres (UNRESOLVED_IN_SEARCH_SNAPSHOT, NEW, SERVICE_INVENTORY_ONLY)
- OPDC 5 Article 4 Direction 2017 (Storage and distribution uses to residential) (UNRESOLVED_IN_SEARCH_SNAPSHOT, NEW, SERVICE_INVENTORY_ONLY)
- OPDC 20 Article 4 Direction 2022 (Commercial, Business and Service to residential) (UNRESOLVED_IN_SEARCH_SNAPSHOT, NEW, SERVICE_INVENTORY_ONLY)
- OPDC 35 Article 4 Direction 2023 (C3 dwelling house to C4 house in multiple occupation) (UNRESOLVED_IN_SEARCH_SNAPSHOT, NEW, SERVICE_INVENTORY_ONLY)
- OPDC 6 Conservation Areas (esriGeometryPolygon, NEW, COMPLETE_LAYER_EXTENT)
- OPDC 8 Statutory Listed Asset (designated heritage asset) (UNRESOLVED_IN_SEARCH_SNAPSHOT, NEW, SERVICE_INVENTORY_ONLY)
- OPDC 9 Local Heritage Listing (non-designated heritage asset) (UNRESOLVED_IN_SEARCH_SNAPSHOT, NEW, SERVICE_INVENTORY_ONLY)
- OPDC 11 1 in 200 Year Flood Risk > 0.1m (UNRESOLVED_IN_SEARCH_SNAPSHOT, NEW, SERVICE_INVENTORY_ONLY)
- OPDC 12 1 in 200 Year Flood Risk > 0.3m (UNRESOLVED_IN_SEARCH_SNAPSHOT, NEW, SERVICE_INVENTORY_ONLY)
- OPDC 13 National Floodzone 3 (UNRESOLVED_IN_SEARCH_SNAPSHOT, NEW, SERVICE_INVENTORY_ONLY)
- OPDC 14 National Floodzone 2 (UNRESOLVED_IN_SEARCH_SNAPSHOT, NEW, SERVICE_INVENTORY_ONLY)
- OPDC 16 HS2 Extended Homeowner Protection Zones (August 2016) (UNRESOLVED_IN_SEARCH_SNAPSHOT, NEW, SERVICE_INVENTORY_ONLY)
- OPDC 17 HS2 Safeguarding (August 2016) (UNRESOLVED_IN_SEARCH_SNAPSHOT, NEW, SERVICE_INVENTORY_ONLY)
- OPDC 18 Strategic Industrial Locations (UNRESOLVED_IN_SEARCH_SNAPSHOT, NEW, SERVICE_INVENTORY_ONLY)
- OPDC 30 SINC - Local Importance (UNRESOLVED_IN_SEARCH_SNAPSHOT, NEW, SERVICE_INVENTORY_ONLY)
- OPDC 21 SINC - Borough Importance 2 (UNRESOLVED_IN_SEARCH_SNAPSHOT, NEW, SERVICE_INVENTORY_ONLY)
- OPDC 22 SINC - Borough Importance 1 (UNRESOLVED_IN_SEARCH_SNAPSHOT, NEW, SERVICE_INVENTORY_ONLY)
- OPDC 23 SINC - Metropolitan Importance (UNRESOLVED_IN_SEARCH_SNAPSHOT, NEW, SERVICE_INVENTORY_ONLY)
- OPDC 24 Metropolitan Open Land (UNRESOLVED_IN_SEARCH_SNAPSHOT, NEW, SERVICE_INVENTORY_ONLY)
- OPDC 25 Site Allocations (esriGeometryPolygon, NEW, COMPLETE_LAYER_EXTENT)
- OPDC 27 Waste site (London Borough of Hammersmith and Fulham 2018) (UNRESOLVED_IN_SEARCH_SNAPSHOT, NEW, SERVICE_INVENTORY_ONLY)
- OPDC 28 Waste site (West London Waste Plan 2015) (UNRESOLVED_IN_SEARCH_SNAPSHOT, NEW, SERVICE_INVENTORY_ONLY)
- OPDC 29 Safeguarded Gypsy and Traveller Site (UNRESOLVED_IN_SEARCH_SNAPSHOT, NEW, SERVICE_INVENTORY_ONLY)
- OPDC 31 Old Oak Neighbourhood Area (UNRESOLVED_IN_SEARCH_SNAPSHOT, NEW, SERVICE_INVENTORY_ONLY)
- OPDC 32 Harlesden Neighbourhood Area (Inside OPDC Boundary) (esriGeometryPolygon, NEW, COMPLETE_LAYER_EXTENT)
- OPDC 33 Harlesden Neighbourhood Area (Outside OPDC Boundary) (UNRESOLVED_IN_SEARCH_SNAPSHOT, NEW, SERVICE_INVENTORY_ONLY)
- PRS 1 housing_prs_licence_checker_mandatory (esriGeometryPolygon, NEW, COMPLETE_LAYER_EXTENT)
- PRS 2 housing_prs_licence_checker_additional (esriGeometryPolygon, NEW, COMPLETE_LAYER_EXTENT)
- PRS 3 housing_prs_licence_checker_selective (esriGeometryPolygon, NEW, COMPLETE_LAYER_EXTENT)
- PRS 5 core_gla_boundary (esriGeometryPolygon, MIRROR, COMPLETE_LAYER_EXTENT)
- PRS 6 core_london_borough (esriGeometryPolygon, MIRROR, COMPLETE_LAYER_EXTENT)
- WORKSPACE 0 GLA Funding (esriGeometryPoint, NEW, COMPLETE_POINT_LAYER_EXTENT)
- WORKSPACE 1 Floorspace (esriGeometryPoint, REPRESENTATION, COMPLETE_POINT_LAYER_EXTENT)
- WORKSPACE 2 Type of Workspace (esriGeometryPoint, REPRESENTATION, COMPLETE_POINT_LAYER_EXTENT)
- WORKSPACE 3 London Borough (esriGeometryPolygon, MIRROR, COMPLETE_LAYER_EXTENT)
- PARKS 0 Spaces to Visit 2025 (esriGeometryPolygon, NEW, COMPLETE_LAYER_EXTENT)
- PARKS 1 Registered Parks and Gardens (esriGeometryPolygon, NEW, COMPLETE_LAYER_EXTENT)
- FLOOD_BASE 0 Flood Risk Base Scenario (esriGeometryPolygon, NEW, COMPLETE_LAYER_EXTENT)
- FLOOD_CC 0 Flood Risk Climate Change Scenario (UNRESOLVED_IN_SEARCH_SNAPSHOT, NEW, SERVICE_INVENTORY_ONLY)

Every request used the official layer `/query` endpoint with `where=1=1`, point geometry, `esriSpatialRelIntersects`, `returnIdsOnly=true`, and `f=json`. EPSG:27700 was used except the two flood services, which used EPSG:3857.

Inventory-only OPDC and climate-scenario entries were not assigned fabricated geometry, display fields or layer extents. Point extents, mirrors and representations were not counted as parcel proximity, membership or duplicate exact negatives.
