# OHS Manuscript Revision — Current Status

- Total reviewer comments: 32
- Completed through: Comment 11
- Completion: 11/32 = 34.375%
- Next item: Comment 12

## Latest decision
The manuscript will not mechanically expand AUPRC. The verified output metadata identifies the implemented primary metric as `average_precision_weighted`; therefore, the manuscript-facing term is `class-support-weighted average precision (AP)` unless later source-code verification demonstrates trapezoidal integration of the precision–recall curve.

## Comment 11 corrections
- Removed the incorrect statement assigning mean absolute error and quantile-loss summaries to Analysis 2.
- Standardized the primary selection metric across the three analyses as class-support-weighted AP.
- Retained macro AP as a complementary equal-class-weight summary.
- Retained AUROC, weighted F1 score, accuracy, calibration metrics, and training time as secondary criteria.
- Added a methodological citation recommendation for precision–recall evaluation under class imbalance.

## Cross-comment consistency updates
- Comment 7: replace `weighted AUPRC` with `class-support-weighted average precision (AP)` unless code verification supports true AUPRC.
- Comment 10: use `within each analysis` and the Analysis 1/2/3 naming standard.
- Results tables and figures: use manuscript-facing labels `weighted AP` and `macro AP`; preserve original artifact column names only in the reproducibility archive.

## Next item
Comment 12 — determine whether an LLM was actually used; if retained, report the exact model name, version, access date, configuration, and role, and if not verified, remove the LLM-generation claim.
