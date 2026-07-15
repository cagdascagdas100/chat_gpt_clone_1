# OHS Manuscript Revision — Reassessment Status

- Total reviewer comments: 32
- Reassessed through: Comment 6
- Reassessed: 6/32 = 18.75%
- Fully finalized in reassessment: 6/32 = 18.75%
- Next item: Comment 7

## Latest decision — Comment 6
The vague phrase `multiple target formulations/combination` will be replaced by an explicit description of three independently fitted classification analyses based on the same source target column, `ODEME_GUNSAYISI`, under different inclusion and recoding rules. The analyses do not constitute a combined target, multi-output model, or target ensemble.

## Verified analysis definitions
- Analysis 1: 64,999 records, 14 predictors, zero-day class retained, 18 observed payment-day classes.
- Analysis 2: 13,570 records, the same 14-predictor set, zero-day records excluded, 17 positive payment-day classes.
- Analysis 3: 64,999 records, the same 14-predictor set, payment-day outcome recoded into four project-defined grouped classes.

## Terminology boundary
- Replace `three occupational injury severity models` with `three separate outcome-classification analyses`.
- Analyses 1 and 2 are payment-day classifications, not injury-severity models.
- Analysis 3 should be described as a four-class grouped payment-day outcome formulation unless the independent provenance and substantive validity of the severity labels are documented.
- Do not claim an identical validation protocol across all three analyses until the recorded cross-validation configuration difference is reconciled.

## Approved wording
`To examine how outcome definition and the treatment of zero-day records affected model performance, three separate classification analyses were conducted using the same 14-predictor set. Analysis 1 included all 64,999 records and treated ODEME_GUNSAYISI as an 18-class outcome, including the zero-day class. Analysis 2 excluded zero-day records and classified the remaining 13,570 cases into 17 positive payment-day classes. Analysis 3 retained all 64,999 records but recoded the payment-day outcome into four project-defined grouped categories. The three analyses were fitted and evaluated independently; they do not represent a combined target, a multi-output model, or an ensemble of target definitions.`

## Next item
Comment 7 — verify the full classifier portfolio and provide concise, technically accurate reasons for selecting the algorithm families used in the comparative analysis.