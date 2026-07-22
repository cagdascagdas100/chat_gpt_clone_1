# future_growth_2 — Wave 36 Waltham Forest and Hackney current fail-closed audit

## Scope

This wave reviews 24 official Planning Data brownfield-land entities from the London Boroughs of Waltham Forest and Hackney. It creates source-review candidates only. It does not claim parcel identity, HMLR intersection, Future Growth score, or business-row completion.

## Outcome

- 24 official entities reviewed
- 16 eligible point-only source-review candidates
- 8 held fail-closed
- 24/24 records have blank official end dates
- 104/104 structural checks passed
- 96/96 official field readbacks passed

## Higher-capacity eligible examples

- SA08, Church Road and Estate Way LSIS: maximum 700 dwellings
- 193694, The Score Centre: maximum 750 dwellings
- HCAAP-A4, Hackney Central Bus Depot: maximum 142 dwellings
- 2013/3223, Woodberry Down Estate phases 2-8: maximum 2,696 dwellings
- SA14, Leyton Bus Depot: maximum 225 dwellings

## Fail-closed decisions

- SA04 is held as a same-site umbrella/duplicate and has no structured permission date; 193694 is retained for review.
- SA26, SA36, SA05 and BLR_036 are permissioned but lack structured permission dates.
- BLR_003 is held because the official spatial field readback is incomplete.
- BLR_116 is held because the structured planning-permission status was not available in the readback.
- 2017/1134 is held under the low-capacity small-site anomaly guard.

## Duplicate screening

Four grouped exact-entity GitHub code-index searches returned no indexed overlap. This is a screening aid, not proof of repository completeness.

## Product boundary

Canonical shard extraction, HMLR download, exact intersection, period=current API response, parcel match, scoring and business writes remain zero. All product fields remain null.
