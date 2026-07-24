# future_growth_3 — Wave 43 Chelmsford

- continuation_key: `61383520c6a16ecbb0bd2f3d65f26f06ed73185e4b2d7845f096dbcd3a985d91`
- researched: 16
- eligible: 14
- excluded: 2 direct-page cache misses
- average source confidence: 96.50/100
- high source confidence: 8
- visible operations: 83
- official direct live readback: 14 PASS / 2 FAIL
- current rows: 8
- historical rows: 6
- search-cache/live drift rows: 12
- source families added: 0 (complete cross-wave proof unavailable)

## Quality decision

The direct live Planning Data entity page controls promoted values. Search-engine cached snippets were used only to discover candidate entities. Where cached entry/end dates or dwelling capacity differed from the direct live page, cached values were retained as audit-only evidence and were not promoted. Entities 1711439 and 1711382 were excluded because direct page readback returned cache miss.

## Guardrails

- Official POINT is a source location, not a canonical parcel polygon.
- Missing live capacity remains null.
- Past end dates remain historical controls.
- No canonical row identity, parcel intersection or future-growth score was produced.
- actual_business_data_rows_written=0
- fake_data=false
- final_ready=false

## Blocker

Two additional exact repository searches found no 30,761-row canonical export, stable parcel identifier, row-count/range receipt or CRS declaration. The manual action remains OPEN. Independent source research may continue safely, but canonical crosswalk and scoring remain blocked.
