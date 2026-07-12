# Comment 11 — Precision–recall metric terminology

## Reviewer comment
`Açılımı?`

## Selected manuscript text
`The leading models selected based on AUPRC for Model F, Mean Absolute Error and quantile-loss-based summaries for Model E, and macro F1 score and macro AUPRC for Model A.`

## Verified findings
- All three analytical settings are classification analyses.
- The generated quality checks state that regression metrics such as mean absolute error and quantile loss are absent.
- The reports identify `average_precision_weighted` as the primary model-selection metric.
- Macro-averaged precision–recall performance is complementary rather than a separate primary rule for only one analysis.

## Final terminology decision
The manuscript should use **class-support-weighted average precision (AP)** rather than mechanically expanding AUPRC. The current output metadata identifies the implemented quantity as average precision. AP summarizes the precision–recall curve by weighting precision values by increases in recall and is not necessarily identical to trapezoidal area under the precision–recall curve. Retain AUPRC only if later source-code verification confirms direct curve-area integration.

## Preferred replacement paragraph
`Within each analysis, candidate classifiers were ranked primarily by class-support-weighted average precision (AP). AP summarizes precision–recall performance across decision thresholds and was emphasized because the outcome classes were imbalanced. Macro-averaged AP was reported as a complementary measure that gives equal weight to each class, whereas weighted and macro-averaged area under the receiver operating characteristic curve (AUROC), weighted F1 score, accuracy, calibration metrics, and training time were treated as secondary evaluation criteria.`

## Why this is preferable
1. Defines the metric at first use.
2. Matches `average_precision_weighted` in the verified outputs.
3. Removes incorrectly assigned regression metrics from Analysis 2.
4. Distinguishes support-weighted and macro averaging.
5. Avoids claiming that precision–recall metrics eliminate class imbalance.
6. Preserves AUROC, F1, accuracy, calibration, and training time as secondary measures.

## Red-highlight treatment
The entire replacement paragraph should be red because the original sentence contains both terminology and methodology errors.

## Literature decision
Add Saito and Rehmsmeier (2015), PLOS ONE 10(3): e0118432, DOI 10.1371/journal.pone.0118432, to support the use of precision–recall evaluation under class imbalance. For the exact AP calculation and averaging definitions, follow the verified scikit-learn implementation metadata. A software citation may be added if required by the journal.

## Cross-comment consistency
- Comment 7: replace `weighted AUPRC` with `class-support-weighted average precision (AP)` unless code verification demonstrates trapezoidal AUPRC.
- Comment 10: use `within each analysis`, not Model F/E/A.
- Manuscript tables and figures: use `weighted AP` and `macro AP`; preserve original artifact column names only in the reproducibility archive.
- Remove `Mean Absolute Error and quantile-loss-based summaries for Model E`; those metrics are not present in the verified classification reports.

## Reviewer-response draft
`Revised. The metric was defined at first use and the sentence was corrected to match the implemented evaluation pipeline. Because the output metadata identifies the primary metric as support-weighted average precision, the manuscript now uses “class-support-weighted average precision (AP)” rather than the less precise abbreviation AUPRC. Macro-averaged AP is reported as a complementary class-balanced summary, and AUROC, weighted F1 score, accuracy, calibration metrics, and training time are retained as secondary measures. The incorrect references to mean absolute error and quantile loss were removed.`
