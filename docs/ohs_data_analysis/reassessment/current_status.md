# OHS Manuscript Revision — Reassessment Status

- Total reviewer comments: 32
- Reassessed through: Comment 11
- Reassessed: 11/32 = 34.375%
- Fully finalized in reassessment: 11/32 = 34.375%
- Next item: Comment 12

## Latest decision — Comment 11
The undefined precision–recall abbreviation will be corrected to the metric name supported by the project artifacts. The machine-readable outputs use `average_precision`, `average_precision_weighted`, and `average_precision_macro`, while `AUPRC` appears only as a presentation label. In the absence of documented curve-area integration, the manuscript will report `class-support-weighted average precision (weighted AP)` and `macro-average precision (macro AP)` rather than AUPRC or PR-AUC.

## Interpretation rule
- Weighted AP is the class-support-weighted mean of class-specific one-versus-rest AP values.
- Macro AP gives each class equal weight.
- Weighted AP must be interpreted with macro AP and the DummyMajority baseline because frequent classes can dominate the weighted summary.
- AP is a ranking/discrimination metric; it is not accuracy, calibration, absolute accident probability, or application-level validation.

## Approved first-use wording
`Model discrimination was assessed primarily using class-support-weighted average precision (weighted AP), calculated as the support-weighted mean of the one-versus-rest average-precision values across outcome classes. Macro-average precision (macro AP), which assigns equal weight to each class, was reported as a complementary measure of performance across minority and majority classes.`

## Required audit
Replace publication-facing `AUPRC (weighted)` and `AUPRC (macro)` labels in the text, tables, figures, captions, and regenerated spreadsheet outputs. Keep AP distinct from AUROC, F1, accuracy, Brier score, and ECE.

## Next item
Comment 12 — verify whether any implemented large-language-model component has an auditable provider, model name, version, prompt protocol, runtime integration, or provenance record; otherwise remove the model-name/version requirement by deleting the unsupported LLM implementation claim.