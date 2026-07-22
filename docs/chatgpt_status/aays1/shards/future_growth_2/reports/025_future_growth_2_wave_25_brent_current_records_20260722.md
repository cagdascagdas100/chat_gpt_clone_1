# future_growth_2 — official source wave 25

Scope remains parcel rows 30,762–61,522. This wave adds source candidates only; it does not claim canonical parcel identity, product scores, business rows, database writes, migration, deployment, or final readiness.

## Official readback

The official Planning Data brownfield dataset was revalidated at 37,666 records from 354 providers. Seven London Borough of Brent entity records were reviewed from official entity pages. Repository code-search returned no indexed overlap for the seven exact references; this is recorded only as an index result, not exhaustive historical proof.

## Candidate decisions

| Candidate | Site | Capacity | Source confidence | Decision |
|---|---|---:|---:|---|
| BR00185 | Former Malcolm House Site | 100 | 98 | eligible review |
| BR00227 | Cricklewood Broadway Retail Park | 380 | 99 | eligible pending-decision review |
| BR00092 | Ark Elvin Academy, Cecil Avenue | 250 | 99 | held: structured status/narrative conflict |
| BR00175 | 462–466 High Road, Wembley | 8 | 98 | eligible stale-delivery review |
| BR00190 | BEGA2 Staples Corner Growth Area | 1,989 | 99 | eligible allocation review |
| BR00248 | Former Wembley Youth Centre / Dennis Jackson Centre | 170 | 98 | eligible application review |
| BR00191 | 5 Blackbird Hill | 57 | 98 | eligible pending-decision review |

BR00092 is fail-closed because the structured status is `pending-decision` while the official narrative says permission was granted. No confidence or product uplift is applied.

## Validation and totals

Wave validation: 32/32 structural checks and 28/28 manual official-readback field checks. Cumulative researched candidates: 156; eligible: 114; held/excluded: 42; average eligible source confidence: 97.8/100. Product rows, parcel matches, Future Growth scores, and business rows remain zero.

## Remaining gates

The existing single runner must execute the materialized/content/blob/scope/stage/preflight chain, extract the real 30,761-row shard from the 61 MB canonical source, obtain direct `period=current` Planning Data evidence, download actual HMLR GML, perform exact intersections, and apply an approved score-decision contract. Product scores remain null.
