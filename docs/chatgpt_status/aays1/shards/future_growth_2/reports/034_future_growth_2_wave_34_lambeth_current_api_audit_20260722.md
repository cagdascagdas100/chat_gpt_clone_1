# future_growth_2 Wave 34 — Lambeth current and API audit

## Scope

Only `future_growth_2` source-candidate preparation was changed. No ownership, heartbeat, current task, runner, database, migration, deployment or other-slot state was claimed. Candidate points are not parcel boundaries and no product score was produced.

## Internet evidence

Official Planning Data API documentation was read for local-planning-authority geometry lookup, `geometry_entity`, `geometry_relation` and `period` query semantics. Lambeth is represented by geometry entity `626195` in that documentation.

A direct official JSON response was obtained from an unfiltered Lambeth `brownfield-land` geometry query. This strengthens transport and field-readback evidence, but it is not a `period=current` response. Currentness was therefore checked fail-closed from every official entity end-date field.

Twenty official Planning Data entity records were read back. Each selected record contains an official point and structured residential-capacity field.

## Decisions

- 14 blank-end, positive-capacity records are eligible for point-only source review.
- `BLR104` is held because the structured maximum residential capacity is zero.
- `BLR154`, `BLR157`, `BLR140`, `BLR136` and `BLR034` are excluded because their official end date is `2025-12-20`.
- Four eligible 2021-permission records remain explicitly marked for stale-delivery review.
- Twenty exact reference and entity code-index searches returned no indexed overlap. This is duplicate screening only, not repository-completeness proof.

## Validation

- Wave structural/API checks: `92/92 PASS`.
- Wave official remote-field checks: `84/84 PASS`.
- Cumulative source candidates: `264` researched, `168` eligible, `96` held or excluded.
- Verified product rows: `0/30761`.

## Remaining gates

The direct `period=current` response, real canonical shard extraction, current HMLR ZIP/GML acquisition, exact parcel intersection and an approved Future Growth score-decision contract remain unproven. Parcel IDs and product scores stay null.