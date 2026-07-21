# future_growth_2 wave 21 — Islington and critical blob integrity

- Six official Planning Data Brownfield land entities were read back from London Borough of Islington.
- Four blank-end permissioned records are eligible only for stale-delivery review and remain point-only with parcel confidence capped at 65.
- Entity `1700550` is held fail-closed because structured capacity is 48 while the official narrative states 54 dwellings.
- Entity `1700546` is excluded as historical because its official end date is `2021-12-14`.
- Exact repository searches for all six entity/reference pairs returned no overlap.
- The Islington provider overview reports 4/18 authoritative datasets, 3 URL access errors, 6 datasets that can improve and 4 Brownfield issues; it is published as a quality warning with no confidence uplift.
- HMLR lists London Borough of Islington in the 5 July 2026 INSPIRE publication; no live file download or exact intersection is claimed.
- Direct `period=current` and HMLR container retries still fail DNS resolution.
- Wave registry and critical-content-manifest regression: 28/28 PASS.
- Remote official evidence audit: 18/18 PASS.
- A SHA-based critical port content manifest is required to reject altered blobs during safe porting. It does not perform merge, rebase, ref movement, ownership or runner changes.
- Product rows, parcel matches and scores remain zero. `final_ready=false`.
