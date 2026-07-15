# OHS Manuscript Revision — Reassessment Status

- Total reviewer comments: 32
- Reassessed through: Comment 10
- Reassessed: 10/32 = 31.25%
- Fully finalized in reassessment: 10/32 = 31.25%
- Next item: Comment 11

## Latest decision — Comment 10
The unexplained labels `Model F`, `Model E`, and `Model A` will be retired. They will not be replaced by `Model A/B/C`, because each label denotes a separate outcome-classification analysis in which multiple classifiers were evaluated rather than a single fitted model.

## Locked nomenclature
- Analysis 1: all 64,999 records; zero-day class retained; 18 observed payment-day classes.
- Analysis 2: zero-day records excluded; 13,570 records; 17 positive payment-day classes.
- Analysis 3: all 64,999 records; four project-defined grouped classes derived from `ODEME_GUNSAYISI`.

## Naming rule
The manuscript will distinguish the analysis, classifier, preprocessing/imbalance configuration, selected configuration, and downstream application output. A result will therefore be reported as, for example, `the selected [classifier/configuration] within Analysis 1`, not as `Model F` or simply `Analysis 1 achieved...`.

## Required audit
The mapping will be applied across Methods, Results, Discussion, Conclusion, tables, figures, captions, panel labels, legends, axes, equations, supplementary material, cross-references, and publication-facing filenames. Historical raw-artifact filenames may be retained for provenance but must be mapped explicitly in the revision record.

## Reporting boundary
Raw performance values from the three analyses will not be treated as directly interchangeable without acknowledging their different record-inclusion rules and class structures. Legacy letters will not be converted by visual order alone; each occurrence must be verified against sample size and target definition.

## Next item
Comment 11 — identify the abbreviation requiring expansion, verify whether the reported quantity is class-support-weighted average precision rather than trapezoidal AUPRC, and align the metric name, definition, and interpretation across the manuscript.
