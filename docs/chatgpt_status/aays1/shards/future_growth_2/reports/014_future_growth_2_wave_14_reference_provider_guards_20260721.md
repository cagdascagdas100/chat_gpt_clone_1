# future_growth_2 wave 14, reference conflict and provider endpoint guards

- Scope remains `future_growth_2` only.
- Six official Redbridge brownfield records researched: four current eligible source candidates, one current record held for an official site-plan reference conflict, and one historical record excluded.
- `BRLBR0177` is held because the official entity reference is `BRLBR0177` while its official site-plan URL terminates in `BRLBR0182`.
- `BRLBR0163` is excluded because the official end date is `2024-02-14`.
- All wave records expose points with empty geometry fields. Points are not treated as site boundaries and eligible evidence remains capped at 65 after exact point-in-polygon.
- Narrative housing/allocation text is not copied into missing structured dwelling fields.
- Redbridge provider quality reports `1/13` authoritative datasets, `1` URL error, `2` datasets that can improve and a Brownfield endpoint `404`; this is a quality warning, not a promoted confidence source.
- Wave registry validation: `12/12 PASS`.
- Wave point-only geometry validation: `8/8 PASS`.
- Site-plan reference conflict guard: `8/8 PASS`.
- Provider endpoint error/no-uplift guard: `8/8 PASS`.
- New executed controls this wave: `36/36 PASS`; cumulative executed tests: `262/262 PASS`.
- Remote official evidence/API/HMLR audit: `14/14 PASS`; cumulative remote checks: `128/128 PASS`.
- Website branch view now contains `148` operation rows, `89` candidate rows and `11` source-contract records.
- Direct `period=current` responses, actual HMLR downloads, exact intersections, real shard exports, product parcel matches and product scores remain `0`.
- `final_ready=false`.
