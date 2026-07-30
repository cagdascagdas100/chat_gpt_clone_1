# future_growth_2 live official query manifest

Continuation key: `5c59c5cee91d859c9e09480645ef8b17efe264568f2a4e312dd49d70e2958462`
Generated: `2026-07-31T00:13:00+03:00`

Read-only official ArcGIS layer queries, raster identify requests and service-root metadata probes. Transport failure is not interpreted as a positive or negative result.

Transport: 108 attempts; parallelism 108; exit counts {'28': 103, '6': 5}; HTTP counts {'000': 108}; body bytes 0; JSON 0/108; raw-response SHA-256 0/108.

Query manifest SHA-256: `00c60667e2f85fd104a4f60c561403be4da4d65a72f2d8b9e0cbb17198b79303`
Transport results SHA-256: `0440d8b8ed3b5bcbf9cb3d9b69e3a9a6cd243890bb9068be48e90361efb45d67`
Layer manifest SHA-256: `a0a6ad3e18d6066cb8e4f703440ce031e740cb0177c7b3642c9b53c2a3524a7c`

Layers/probes crossed with rows 30762, 46142 and 61522:
- IMA03 0 SuDS Completed Projects (esriGeometryPoint, NEW, COMPLETE_POINT_LAYER_EXTENT)
- IMA03 1 TfL Bus Stops (esriGeometryPoint, NEW, COMPLETE_POINT_LAYER_EXTENT)
- IMA03 2 TfL Bus Garages (esriGeometryPoint, NEW, COMPLETE_POINT_LAYER_EXTENT)
- IMA03 3 TfL Bus Routes (esriGeometryPolyline, NEW, COMPLETE_LINE_LAYER_EXTENT)
- IMA03 4 Supply Flow Monitoring Zones (esriGeometryPolygon, NEW, COMPLETE_LAYER_EXTENT)
- IMA03 5 Supply District Metering Area (esriGeometryPolygon, NEW, COMPLETE_LAYER_EXTENT)
- IMA03 6 Sewerage Drainage Area Catchment (esriGeometryPolygon, NEW, COMPLETE_LAYER_EXTENT)
- IMA03 7 UKPN Grid Sites (esriGeometryPoint, NEW, COMPLETE_POINT_LAYER_EXTENT)
- IMA03 8 UKPN Primary Sites (UNRESOLVED, NEW, SERVICE_INVENTORY_ONLY)
- IMA03 10 TfL Strategic Road Network (esriGeometryPolyline, MIRROR, COMPLETE_LINE_LAYER_EXTENT)
- IMA03 11 UKPN Secondary Sites (esriGeometryPoint, NEW, COMPLETE_POINT_LAYER_EXTENT)
- FUTURE 0 ima_future_works_points_public (UNRESOLVED, NEW, SERVICE_INVENTORY_ONLY)
- FUTURE 1 ima_future_works_lines_public (UNRESOLVED, NEW, SERVICE_INVENTORY_ONLY)
- FUTURE 2 ima_future_works_polygons_public (UNRESOLVED, NEW, SERVICE_INVENTORY_ONLY)
- FUTURE 3 tfl_road_network_tlrn (UNRESOLVED, MIRROR, SERVICE_INVENTORY_ONLY)
- FUTURE 4 tfl_lane_rental (UNRESOLVED, MIRROR, SERVICE_INVENTORY_ONLY)
- FUTURE 5 tfl_strategic_road_network (UNRESOLVED, MIRROR, SERVICE_INVENTORY_ONLY)
- FUTURE 6 dtf_section_58s_lines (UNRESOLVED, REPRESENTATION, SERVICE_INVENTORY_ONLY)
- FUTURE 7 dft_section_58s_polygons (UNRESOLVED, NEW, SERVICE_INVENTORY_ONLY)
- FUTURE 8 london_boroughs (UNRESOLVED, MIRROR, SERVICE_INVENTORY_ONLY)
- LOTI2 0 Community Centres (esriGeometryPoint, TEMPORAL, COMPLETE_POINT_LAYER_EXTENT)
- LOTI2 1 Libraries (UNRESOLVED, TEMPORAL, SERVICE_INVENTORY_ONLY)
- LOTI2 3 Pilot Boroughs (UNRESOLVED, MIRROR, SERVICE_INVENTORY_ONLY)
- LOTI2 4 London Borough (UNRESOLVED, MIRROR, SERVICE_INVENTORY_ONLY)
- LOTI2 5 London Wards (UNRESOLVED, MIRROR, SERVICE_INVENTORY_ONLY)
- LOTI2 6 Ward names (zoom in if grey) (UNRESOLVED, REPRESENTATION, SERVICE_INVENTORY_ONLY)
- LOTI2 8 Residents 65+ top 10% 2011 Census (UNRESOLVED, TEMPORAL, SERVICE_INVENTORY_ONLY)
- LOTI2 9 Residents 65+ top 10% 2019 ONS (UNRESOLVED, TEMPORAL, SERVICE_INVENTORY_ONLY)
- LOTI2 10 Residents 65+ top 20% 2019 ONS (UNRESOLVED, TEMPORAL, SERVICE_INVENTORY_ONLY)
- LOTI2 11 Residents 75+ top 20% 2019 ONS (UNRESOLVED, TEMPORAL, SERVICE_INVENTORY_ONLY)
- LOTI2 12 IMD deprivation affecting older people 2019 (UNRESOLVED, TEMPORAL, SERVICE_INVENTORY_ONLY)
- LOTI2 14 Income Deprivation Affecting Children 2019 (UNRESOLVED, TEMPORAL, SERVICE_INVENTORY_ONLY)
- PDM04 0 Flood Risk cached tiles (Raster Layer, NEW, COMPLETE_RASTER_LAYER_EXTENT)
- BASEBLUE -1 blue_cover_web_service_01 service root (UNRESOLVED, NEW, SERVICE_INVENTORY_ONLY)
- DIGADD -1 Digital_Exclusion_2023_adds service root (UNRESOLVED, NEW, SERVICE_INVENTORY_ONLY)
- OFFEPC -1 Office_EPC_Map service root (UNRESOLVED, NEW, SERVICE_INVENTORY_ONLY)

Layer requests used official `/query` endpoints with point geometry and `returnIdsOnly=true`. The flood raster used `/identify`. Service-root-only checks used metadata probes and were never interpreted spatially.

Point, polyline, raster, service-root, mirror, representation and temporal extents were not counted as parcel proximity, membership or duplicate exact negatives. Known eligible IMA polygon extents contained all three candidate points, so no new extent negative was created.