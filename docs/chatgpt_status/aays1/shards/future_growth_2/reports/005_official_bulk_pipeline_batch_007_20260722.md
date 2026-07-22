# future_growth_2 — Official bulk pipeline Batch 007

- Continuation key: `5c59c5cee91d859c9e09480645ef8b17efe264568f2a4e312dd49d70e2958462`
- Generated: `2026-07-22T18:55:00Z`
- Candidate rows: 30762 / 46142 / 61522
- Batch operations: **109/109**
- Cumulative operations: **363**
- Official dataset pages revalidated: **9**
- Exact official bulk endpoints: **34**
- Planning Data bulk spatial jobs: **24**
- ArcGIS exact-intersection jobs: **31**
- System validations: **8**
- Preparation failures: **0**
- Exact parcel-bound rows: **0**
- Business rows: **0**

## Quality gates

The official page, dataset authority, geometry semantics and parcel applicability remain separate. Brownfield and flood-risk data are authoritative or authoritative indicators; five datasets are mixed, incomplete or point-only; local-plan and local-plan-boundary are MHCLG-created scope/metadata sources. Listed-building data is explicitly point-only and cannot establish an affected-area polygon.

The bulk runner uses an official-host allowlist, atomic `.part` downloads, `fsync`, SHA-256 hashes, fail-closed dependency checks and zero-result caution. It never emits a future-growth score.

## Environment result

The exact official URL `https://files.planning.data.gov.uk/dataset/brownfield-land.geojson` was tested. The current execution environment returned `Temporary failure in name resolution`; no body or false result was committed. The existing single-runner/browser route remains required for current live evidence.

## Next verified step

Run the published bulk runner on the existing canonical host, commit the raw download/hash/intersection output, read it back from GitHub, cross-check every positive intersection against the primary authority, and only then consider scoring.
