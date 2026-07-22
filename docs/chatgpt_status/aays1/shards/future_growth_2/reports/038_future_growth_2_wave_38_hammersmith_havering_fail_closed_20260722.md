# future_growth_2 — Wave 38 Hammersmith & Fulham / Havering fail-closed audit

## Scope

This wave reviews 24 official Planning Data entities: 22 from the London Borough of Hammersmith & Fulham and 2 from the London Borough of Havering. These are source-review candidates only. Official points are not site boundaries, HMLR parcels or Future Growth product rows.

## Result

- 24 researched
- 14 eligible source-review candidates
- 10 held fail-closed
- all 14 eligible candidates have source confidence at least 90; wave eligible average 99.0/100
- structural validation: 104/104 PASS
- official remote field evidence: 96/96 PASS

## Eligible examples

- `LBHF022`, M&S White City Site: structured maximum 1,814, pending decision
- `LBHF016`, Centre House: structured maximum 527, permissioned
- `LBHF003`, Former Dairy Crest Site: structured maximum 373, pending decision
- `LBHF001`, Carnwath Road Industrial Estate: structured maximum 257, pending decision
- `LBHF011`, Watermeadow Court: structured maximum 219, pending decision

## Fail-closed decisions

- `LBHF002`, `LBHF005` and `LBHF010`: blank official end date conflicts with explicit lapsed notes
- `LBHF008`: official readbacks conflict over the lapsed-note state
- `LBHF012` and `LBHF015`: commencement evidence is ambiguous
- `LBHF019`: structured maximum 132 conflicts with narrative capacity 192
- `LBHF 023`: structured dates, status and capacity are incomplete
- `GOO6`: structured maximum is missing
- `STA1/19`: structured maximum and permission date are missing

## Duplicate screening

Five grouped GitHub code-index searches, including a separate `1733500/LBHF013` check, returned no indexed matches. This is a duplicate-screening aid and not proof of repository completeness.

## Product state

- canonical shard rows exported: 0
- canonical parcel matches: 0
- Future Growth scores: 0
- actual business rows: 0
- direct `period=current` API responses: 0
- actual HMLR downloads/intersections: 0

Real product execution remains blocked by canonical runtime access, a direct current-period response, actual HMLR geometry and an approved Future Growth score-decision contract.
