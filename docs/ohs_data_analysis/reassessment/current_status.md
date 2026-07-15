# OHS Manuscript Revision — Reassessment Status

- Total reviewer comments: 32
- Reassessed through: Comment 9
- Reassessed: 9/32 = 28.125%
- Fully finalized in reassessment: 9/32 = 28.125%
- Next item: Comment 10

## Latest decision — Comment 9
The modeled outcome will be defined at its first substantive occurrence in the Methods section, immediately after the dataset and predictor description and before preprocessing, class construction, model fitting, or evaluation. The first-use definition will identify the source field `ODEME_GUNSAYISI`, use the neutral term `payment-day outcome`, explain zero-day handling, and distinguish the three independently evaluated class formulations.

## Approved first-use wording
`The modeling target was the source-data field ODEME_GUNSAYISI, referred to in this manuscript as the payment-day outcome. The available project documentation does not establish that this administrative field is equivalent to Days Away From Work, temporary-incapacity duration, financial loss, or absolute accident risk. Three separate classification analyses were therefore defined from this field. Analysis 1 retained all 64,999 records and represented the observed outcome as 18 classes, including the zero-day class. Analysis 2 excluded zero-day records and represented the remaining 13,570 cases as 17 positive payment-day classes. Analysis 3 retained all 64,999 records and recoded the same source field into four project-defined grouped categories. The three outcome formulations were modeled and evaluated independently.`

## Required Methods order
1. data source and unit of analysis;
2. predictor set;
3. target definition and class construction;
4. preprocessing;
5. data partitioning and cross-validation;
6. imbalance handling;
7. classifiers and tuning;
8. evaluation metrics;
9. application-level use of outputs.

## Reporting boundaries
- Do not introduce `DAFW`, target combinations, injury severity, or Model F/E/A before defining the verified source field and analysis rules.
- Keep the historical-data outcome separate from application risk components and scenario-priority scores.
- Do not label the four grouped classes as validated clinical or legal severity categories without independent provenance.
- Reproduce the detailed four-class mapping exactly from auditable project artifacts during manuscript implementation; do not infer missing meanings.

## Next item
Comment 10 — replace the non-sequential Model F/E/A labels with a clear and consistent Analysis 1/2/3 nomenclature and audit every occurrence across text, figures, tables, and captions.