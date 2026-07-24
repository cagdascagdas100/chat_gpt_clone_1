# future_growth_2 — Official GIS machine-service preflight 004

- Workstream: `AAYS_21_SLOT_SAFE_PARALLEL_V1`
- Continuation: `5c59c5cee91d859c9e09480645ef8b17efe264568f2a4e312dd49d70e2958462`
- Generated: `2026-07-22T17:51:00Z`
- Candidate rows: `30762`, `46142`, `61522`
- Batch operations: `48/48`
- Official polygon query templates: `31`
- Failed preflight operations: `0`
- Exact parcel bindings: `0`
- Business scores written: `0`

## Verified official machine services

1. Enfield GLA Local Plan FeatureServer: `planning_local_plan_data_10`, item `ab69f020f7874f61a49f03ddf7c36e18`.
2. Havering GLA Local Plan FeatureServer: `planning_local_plan_data_16`, item `c5dce9022a944a7d805f125ddb7e6e1a`.
3. Lambeth GLA Local Plan FeatureServer: `planning_local_plan_data_22`, item `fb7c4ffee4374a2b8ba9500e63e0cabf`.
4. Lambeth Council ArcGIS REST service directory.
5. Lambeth Brownfield Land Register polygon layer, MapServer layer `2`.

The services expose polygon layers in British National Grid (`EPSG:27700`) and support ArcGIS query operations. The runner script submits each canonical WGS84 point with `inSR=4326` and `esriSpatialRelIntersects`.

## Layer coverage prepared

- Enfield: 10 layers including medium-growth housing/mixed use, housing locations, Green Belt, conservation, Crossrail 2, industrial land and place-making areas.
- Havering: 10 layers including retained and Romford allocations, Green Belt, flood zones, Beam Park station, Crossrail, conservation and minerals safeguarding.
- Lambeth: 11 layers including site allocations, opportunity areas, flood zones, conservation, KIBA potential, open land, special policy areas and the council brownfield register.

## Quality gates

- Only official council or GLA ArcGIS services are allowlisted.
- A source-authority result is not a parcel match.
- No score is created until a live ArcGIS response returns an intersecting polygon and required cross-checks pass.
- A successful zero-feature response means only “no intersection in this queried layer”; it is not evidence that the parcel has no planning constraints.
- Output remains `future_growth_score=null`, `confidence_pct=0`, `data_status=NO_DATA` until exact binding.

## Execution blocker

The existing canonical single runner has a stale heartbeat and must be restarted. The open manual action remains at `docs/chatgpt_status/_shared/manual_actions/future_growth_2.json`. No duplicate task or runner was created and the global `height_difference_2` task was not replaced.
