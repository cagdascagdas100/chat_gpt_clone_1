# OHS Manuscript Revision — Current Status

- Total reviewer comments: 32
- Processed through: Comment 19
- Processed: 19/32 = 59.375%
- Fully finalized: 15/32 = 46.875%
- Conditional items: Comment 12 (scenario provenance), Comment 15 (authoritative equipment inventory), Comment 17 (internal–external weighting), and Comment 18 (regional-decay value selection)
- Next item: Comment 20

## Latest decision — Comment 19
The F/E/A naming scheme will be removed throughout the manuscript and all visual outputs. The final convention is `Analysis 1`, `Analysis 2`, and `Analysis 3`, not Model A/B/C, because each analytical setting compares multiple fitted classifiers rather than representing one model.

## Standard mapping
- Model F → Analysis 1 — all-case payment-day classification
- Model E → Analysis 2 — positive payment-day classification
- Model A → Analysis 3 — four-level injury-severity classification

## Figure and interpretation corrections
- Figure 9 must be regenerated with Analysis 1/2/3 legend labels and a title describing classifier performance within the three outcome analyses.
- Figure 10 must replace F/E/A on the x-axis and remove the misleading phrase `scenario stability`.
- A grouped point plot or aligned panels are preferable to connecting the analyses with lines, because the targets and class structures differ.
- Absolute AUROC values across the three analyses should be interpreted descriptively rather than as directly comparable performance estimates.
- Statements using `best`, `highest`, `improvement`, or `decrease` must identify the metric and acknowledge differences in outcome definition.
- Figures must be regenerated from source data or plotting code; raster labels must not be edited manually.

## Cross-comment consistency updates
- Comment 10 is confirmed and extended to every text, table, figure, legend, caption, and supplementary output.
- Comment 11 metric terminology must be used in regenerated Figure 9.
- Discussion claims about Analysis 3 must be metric-specific and verified against the final validated tables.

## Next item
Comment 20 — explain the relationship between the later prose description of the internal/external allocation and the unresolved 0.10/0.90 weighting decision from Comment 17.