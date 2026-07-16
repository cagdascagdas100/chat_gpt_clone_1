# OHS Manuscript Revision — Reassessment Status

- Total reviewer comments: 32
- Reassessed through: Comment 19
- Reassessed: 19/32 = 59.375%
- Fully finalized in reassessment: 19/32 = 59.375%
- Next item: Comment 20

## Latest decision — Comment 19
The legacy labels `Model F`, `Model E`, and `Model A` will be removed from all publication-facing text and graphics. They will not be replaced by `Model A/B/C`, because each label denotes a separate outcome-classification analysis containing multiple candidate classifiers rather than a single fitted model.

## Locked mapping
- `Model F` → Analysis 1: 64,999 records; zero-day class retained; 18 observed payment-day classes.
- `Model E` → Analysis 2: 13,570 records after zero-day exclusion; 17 positive payment-day classes.
- `Model A` → Analysis 3: 64,999 records; four project-defined grouped classes derived from `ODEME_GUNSAYISI`.

## Required publication audit
- Apply the mapping across Methods, Results, Discussion, Conclusion, tables, captions, legends, axes, panel labels, annotations, supplementary material, spreadsheets, and publication-facing filenames.
- Regenerate embedded raster figures containing the legacy labels; editing the Word captions alone is insufficient.
- Map every occurrence by sample size, zero-day rule, and class definition rather than by alphabetical or visual order.

## Figure decisions
- Figure 8: regenerate the heat map with Analysis 1/2/3 labels and payment-day outcome terminology.
- Figure 9: regenerate the performance summary with Analysis 1/2/3 legends and explicit task-difference caveats.
- Figure 10: do not simply relabel the connected-line plot. Remove it or rebuild it as separate non-connected descriptive summaries because a line from Analysis 1 to 2 to 3 falsely implies an ordered trend and stability across non-equivalent outcome formulations.

## Reporting boundary
Report the analysis label separately from the classifier/configuration, for example `the selected classifier within Analysis 1`. Do not rank the three analyses as directly interchangeable tasks without acknowledging their different samples and class structures.

## Next item
Comment 20 — reassess the reported 50.62% overall value and its relationship to the unsupported internal/external and cross-region weighting schemes; retain only reproducible region-specific values if no valid overall aggregation exists.