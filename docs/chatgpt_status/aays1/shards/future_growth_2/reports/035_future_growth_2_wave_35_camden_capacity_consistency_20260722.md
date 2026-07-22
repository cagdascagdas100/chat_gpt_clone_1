# future_growth_2 — Wave 35 Camden capacity consistency audit

## Scope

Wave 35 reviews 24 official Planning Data brownfield-land entity records for the London Borough of Camden. These are source-review candidates only; official point locations are not site boundaries, parcel identities or Future Growth product rows.

## Result

- 24 official entity readbacks.
- 17 eligible source-review candidates.
- 7 records held fail-closed.
- All 17 eligible records have source-evidence confidence at least 90; wave average is 98.2/100.
- 104/104 structural checks and 96/96 official field readbacks passed.
- Exact entity searches returned no indexed repository overlap, with the explicit limitation that GitHub code search is not a completeness proof.

## Eligible examples

- LBCBLR006, 24-58 Royal College Street — structured maximum 250.
- LBCBLR068, Former Liddell Industrial Estate — 106.
- LBCBLR115, Former Royal National Throat Nose and Ear Hospital — 76.
- LBCBLR028, Tybald Estate — 56.
- LBCBLR121, St Pancras Commercial Centre — 33.

## Fail-closed records

- LBCBLR043: structured and narrative permission dates conflict.
- LBCBLR110, LBCBLR007 and LBCBLR107: structured and narrative capacities conflict.
- LBCBLR059: structured minimum exceeds maximum.
- LBCBLR113.2: structured site capacity conflicts with the narrower reserved-matters narrative scope.
- LBCBLR072: near-identical official same-site reference reports different capacity and permission evidence.

## API contract evidence

Official Planning Data API documentation exposes a `period` contract and the Camden local-planning-authority entity is 626188. No successful `period=current` brownfield response was obtained, so currentness remains independently fail-closed from official entity end-date fields.

## Product state

Canonical shard extraction, HMLR ZIP/GML download, exact parcel intersection and approved Future Growth score decisions were not executed. Product rows remain 0/30,761 and scores remain null.
