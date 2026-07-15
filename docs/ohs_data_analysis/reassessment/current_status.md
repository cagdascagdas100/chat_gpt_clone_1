# OHS Manuscript Revision — Reassessment Status

- Total reviewer comments: 32
- Reassessed through: Comment 8
- Reassessed: 8/32 = 25.0%
- Fully finalized in reassessment: 8/32 = 25.0%
- Next item: Comment 9

## Latest decision — Comment 8
The undefined abbreviation `DAFW` will not be used as a synonym for the study target. The auditable Risk 01/02/03 artifacts consistently identify the target column as `ODEME_GUNSAYISI`, while no source-data dictionary or administrative definition establishes equivalence with Days Away From Work.

## Approved terminology
- First use: `payment-day outcome (source field: ODEME_GUNSAYISI)`.
- Analysis 1: `18-class payment-day outcome, including the zero-day class`.
- Analysis 2: `17-class positive payment-day outcome after exclusion of zero-day records`.
- Analysis 3: `four-class grouped payment-day outcome derived from ODEME_GUNSAYISI`.

## Required corrections
- Remove `DAFW as the target variable` and the joint-target phrase `days away from work and fatalities`.
- Do not describe Analyses 1 and 2 as continuous-outcome models; the recorded tasks are multiclass classifications.
- Do not conflate payment days with lost workdays, temporary-incapacity days, compensable days, fatality prediction, accident probability, compensation probability, or financial loss.
- Rename Section 3.3.4 using payment-day terminology and audit all related tables, figures, equations, captions, and interface labels.
- Remove `DAFW-monetized` and `DAFW-equivalent days` unless an independently auditable derivation is supplied.

## Approved wording
`The modeling target was the source-data field ODEME_GUNSAYISI. In this manuscript, it is referred to as the payment-day outcome. Because the available project documentation does not establish that this administrative field is equivalent to Days Away From Work, the abbreviation DAFW is not used as a synonym for the modeled target.`

## Next item
Comment 9 — introduce the payment-day outcome at its first occurrence and reorganize the surrounding Methods text so that the target definition, zero-day handling, and analysis-specific recoding are explained before later use.