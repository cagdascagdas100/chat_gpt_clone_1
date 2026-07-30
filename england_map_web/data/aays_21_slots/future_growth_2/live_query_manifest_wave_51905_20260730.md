# future_growth_2 live official query manifest

Continuation key: `5c59c5cee91d859c9e09480645ef8b17efe264568f2a4e312dd49d70e2958462`
Generated: `2026-07-30T22:58:00+03:00`

Read-only official ArcGIS `returnIdsOnly` point-intersects queries. Transport failure is not interpreted as a positive or negative result.

Transport: 129 attempts; parallelism 129; exit counts {6: 1, 28: 128}; HTTP counts {'000': 129}; body bytes 0; JSON 0/129; raw-response SHA-256 0/129.

Query manifest SHA-256: `16ff90bbfaefcfc29bd271b079cc6726abb2200956c9d88709c719b655dd9400`
Transport results SHA-256: `71f9b926ae754c6dbba115de89fdc9cc044af90039339bdcb10f4529a048392a`
Layer manifest SHA-256: `9d19a5de4101fa78a99d70fcc3985bc9ee09ba58a7602d65a82196d3500b40ea`

Layers crossed with rows 30762, 46142 and 61522:
- CULT 0 Archives (UNRESOLVED_IN_SEARCH_SNAPSHOT, NEW, SERVICE_INVENTORY_ONLY)
- CULT 1 Artists workspaces (UNRESOLVED_IN_SEARCH_SNAPSHOT, NEW, SERVICE_INVENTORY_ONLY)
- CULT 2 Arts centres (UNRESOLVED_IN_SEARCH_SNAPSHOT, NEW, SERVICE_INVENTORY_ONLY)
- CULT 3 Cinemas (UNRESOLVED_IN_SEARCH_SNAPSHOT, NEW, SERVICE_INVENTORY_ONLY)
- CULT 4 Commercial galleries (UNRESOLVED_IN_SEARCH_SNAPSHOT, NEW, SERVICE_INVENTORY_ONLY)
- CULT 5 Community centres (UNRESOLVED_IN_SEARCH_SNAPSHOT, NEW, SERVICE_INVENTORY_ONLY)
- CULT 6 Creative co-working desk space (UNRESOLVED_IN_SEARCH_SNAPSHOT, NEW, SERVICE_INVENTORY_ONLY)
- CULT 7 Creative workspaces (UNRESOLVED_IN_SEARCH_SNAPSHOT, NEW, SERVICE_INVENTORY_ONLY)
- CULT 8 Dance performance venues (UNRESOLVED_IN_SEARCH_SNAPSHOT, NEW, SERVICE_INVENTORY_ONLY)
- CULT 9 Dance rehearsal studios (UNRESOLVED_IN_SEARCH_SNAPSHOT, NEW, SERVICE_INVENTORY_ONLY)
- CULT 10 Fashion and design (UNRESOLVED_IN_SEARCH_SNAPSHOT, NEW, SERVICE_INVENTORY_ONLY)
- CULT 11 Heritage at risk (UNRESOLVED_IN_SEARCH_SNAPSHOT, NEW, SERVICE_INVENTORY_ONLY)
- CULT 12 Jewellery design (UNRESOLVED_IN_SEARCH_SNAPSHOT, NEW, SERVICE_INVENTORY_ONLY)
- CULT 13 Large media production studios (UNRESOLVED_IN_SEARCH_SNAPSHOT, NEW, SERVICE_INVENTORY_ONLY)
- CULT 14 Legal street art walls (UNRESOLVED_IN_SEARCH_SNAPSHOT, NEW, SERVICE_INVENTORY_ONLY)
- CULT 15 LGBT+ night time venues (UNRESOLVED_IN_SEARCH_SNAPSHOT, NEW, SERVICE_INVENTORY_ONLY)
- CULT 16 Libraries (UNRESOLVED_IN_SEARCH_SNAPSHOT, NEW, SERVICE_INVENTORY_ONLY)
- CULT 17 Listed buildings (UNRESOLVED_IN_SEARCH_SNAPSHOT, NEW, SERVICE_INVENTORY_ONLY)
- CULT 18 Live in artists' workspace (UNRESOLVED_IN_SEARCH_SNAPSHOT, NEW, SERVICE_INVENTORY_ONLY)
- CULT 19 Makerspaces (UNRESOLVED_IN_SEARCH_SNAPSHOT, NEW, SERVICE_INVENTORY_ONLY)
- CULT 20 Making and manufacturing (UNRESOLVED_IN_SEARCH_SNAPSHOT, NEW, SERVICE_INVENTORY_ONLY)
- CULT 21 Museums and public galleries (UNRESOLVED_IN_SEARCH_SNAPSHOT, NEW, SERVICE_INVENTORY_ONLY)
- CULT 22 Music (office based businesses) (UNRESOLVED_IN_SEARCH_SNAPSHOT, NEW, SERVICE_INVENTORY_ONLY)
- CULT 23 Music recording studios (UNRESOLVED_IN_SEARCH_SNAPSHOT, NEW, SERVICE_INVENTORY_ONLY)
- CULT 24 Music rehearsal studios (UNRESOLVED_IN_SEARCH_SNAPSHOT, NEW, SERVICE_INVENTORY_ONLY)
- CULT 25 Music venues (all) (UNRESOLVED_IN_SEARCH_SNAPSHOT, NEW, SERVICE_INVENTORY_ONLY)
- CULT 26 Music venues (grassroots) (UNRESOLVED_IN_SEARCH_SNAPSHOT, NEW, SERVICE_INVENTORY_ONLY)
- CULT 27 Outdoor spaces for cultural use (esriGeometryPoint, NEW, COMPLETE_POINT_LAYER_EXTENT)
- CULT 28 Prop and costume making (UNRESOLVED_IN_SEARCH_SNAPSHOT, NEW, SERVICE_INVENTORY_ONLY)
- CULT 29 Pubs (UNRESOLVED_IN_SEARCH_SNAPSHOT, NEW, SERVICE_INVENTORY_ONLY)
- CULT 30 Scheduled monuments (UNRESOLVED_IN_SEARCH_SNAPSHOT, NEW, SERVICE_INVENTORY_ONLY)
- CULT 31 Set and exhibition building (UNRESOLVED_IN_SEARCH_SNAPSHOT, NEW, SERVICE_INVENTORY_ONLY)
- CULT 32 Skate Parks (UNRESOLVED_IN_SEARCH_SNAPSHOT, NEW, SERVICE_INVENTORY_ONLY)
- CULT 33 Textile design (UNRESOLVED_IN_SEARCH_SNAPSHOT, NEW, SERVICE_INVENTORY_ONLY)
- CULT 34 Theatre rehearsal studio (UNRESOLVED_IN_SEARCH_SNAPSHOT, NEW, SERVICE_INVENTORY_ONLY)
- CULT 35 Theatres (UNRESOLVED_IN_SEARCH_SNAPSHOT, NEW, SERVICE_INVENTORY_ONLY)
- CULT 36 Nightclubs (UNRESOLVED_IN_SEARCH_SNAPSHOT, NEW, SERVICE_INVENTORY_ONLY)
- ATLAS 0 planning_call_for_sites_atlas (esriGeometryPolygon, NEW, COMPLETE_LAYER_EXTENT)
- ATLAS 1 planning_call_for_sites_nha_1 (esriGeometryPolygon, NEW, COMPLETE_LAYER_EXTENT)
- PCALL 0 call_for_sites_all (UNRESOLVED_IN_SEARCH_SNAPSHOT, NEW, SERVICE_INVENTORY_ONLY)
- OFFICE 0 London Borough (esriGeometryPolygon, MIRROR, COMPLETE_LAYER_EXTENT)
- COMMUNITY 0 core_gla_boundary (esriGeometryPolygon, MIRROR, COMPLETE_LAYER_EXTENT)
- CTX 27 Street markets (esriGeometryPoint, REPRESENTATION, COMPLETE_POINT_LAYER_EXTENT)

Every request used the official layer `/query` endpoint with `where=1=1`, EPSG:27700 point geometry, `esriSpatialRelIntersects`, `returnIdsOnly=true`, and `f=json`.

Inventory-only entries were not assigned fabricated geometry, display fields or layer extents. Point extents, mirrors and representations were not counted as parcel proximity, membership or duplicate exact negatives.

Exact named-layer extent negatives: Enfield 2; Havering 0; Lambeth 0. These are limited to the two complete call-for-sites atlas polygon extents and do not establish allocation, planning permission, current availability or delivery certainty.
