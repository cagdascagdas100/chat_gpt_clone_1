# Comment 29 — Calibration terminology, placement, and validity

## Reviewer comment
`ECE brier falan zaten onlar ne bilmiyoruz ve teknik terim, bunlara hiç yer vermememiz gerek. Başlı başına çok kötü. Baştan ele almak lazım.`

## Anchor paragraph
`Another contribution of the framework is its emphasis on probabilistic calibration. By incorporating reliability metrics such as ECE and the Brier score [103,104], the model ensures that predicted risk probabilities closely align with observed outcomes, enhancing the credibility and decision value of safety predictions in construction environments.`

## Editorial decision
Delete this paragraph from the contribution discussion. Probability calibration is not an independent contribution of the framework, and neither expected calibration error nor the Brier score can justify the claim that the model `ensures` reliable probabilities or improved decision value.

Calibration assessment should not be removed from the analytical record, because the application uses predicted class probabilities in later ranking and decision-support calculations. It should instead be reported as a secondary internal-validation check, explained in plain language in the main text, with technical metric definitions and full values moved to the Methods, a supplementary table, or a supplementary reliability figure.

## Why the original paragraph is not defensible
1. `ECE` is introduced without expansion or explanation.
2. The Brier score is named without defining the prediction target, scale, averaging rule, or reference value.
3. The verb `ensures` is too strong. Internal calibration summaries cannot establish calibration in an independent population, transportability, application reliability, or practical decision benefit.
4. A small ECE can coexist with weak discrimination, especially in imbalanced multiclass settings or after averaging; it must not be interpreted in isolation.
5. ECE depends on binning and aggregation choices. The number of bins, classwise versus pooled calculation, weighting, and treatment of multiclass probabilities must be documented for reproducibility.
6. Brier scores depend on the outcome distribution, number of classes, and scoring convention. Values from Analysis 1, Analysis 2, and Analysis 3 must not be compared directly because the outcome structures and class prevalences differ.
7. The available model reports contain internal resampling and calibration summaries but no independent holdout or external validation report. The `final_holdout_report` objects are empty.

## Evidence check against project outputs
- Calibration diagnostics are present in the three analytical reports, so the metrics were not merely mentioned without computational output.
- Across the detailed model–feature records, ECE values are not uniformly restricted to `0–0.02`; at least one Analysis 2 record is approximately `0.032`. The current blanket range statement is therefore incomplete unless it is explicitly limited to the subset plotted in Figure 9.
- Brier values differ markedly across the analyses, approximately in the `0.34–0.59` range for the selected classification records, which reinforces that cross-analysis numerical comparison is inappropriate.
- Dummy-majority records frequently contain `NaN` for Brier and ECE. Missing values must not be silently treated as zero or omitted without explanation.

## Critical additional finding — Figure 13 and Section 4.3
Figure 13 plots a continuous observed overall-risk score against a continuous predicted overall-risk score and reports MAPE, correlation, and R². In the same panel it also reports Brier score, ECE, c-index, and decision-curve net benefit.

These probability-classification diagnostics are not justified for a continuous risk-score regression unless the manuscript defines a probabilistic event target, thresholding rule, probability model, and outcome coding. No such definition is currently present. Therefore:

- remove Brier score and ECE from the continuous aggregation-model paragraph and Figure 13;
- remove c-index unless a valid ranking or time-to-event interpretation is defined;
- remove decision-curve net-benefit values unless each binary decision threshold and event definition is prespecified;
- retain regression-appropriate diagnostics such as predicted-versus-observed plots, the identity line, calibration slope and intercept, MAE or RMSE, MAPE, R², correlation, residual plots, and uncertainty intervals.

The classifier-calibration analysis and the continuous aggregation-model diagnostics must remain separate.

## Main-text replacement
Recommended plain-language wording:

`Because predicted class probabilities are used in subsequent ranking and decision-support calculations, we also examined whether the predicted probabilities corresponded to the observed class frequencies during internal validation. The degree of agreement varied across model–feature combinations, and no independent validation dataset was available; these checks were therefore treated as secondary diagnostics rather than evidence of application-level reliability.`

This sentence may appear in the Results or limitations-oriented Discussion, not in the contribution list.

## Methods or supplementary wording
If technical calibration metrics are retained outside the main narrative:

`Probability agreement was evaluated for the selected classifiers using reliability plots and secondary summary measures. Expected calibration error summarizes the average difference between predicted and observed frequencies across probability bins, whereas the multiclass Brier score summarizes squared error in the predicted class-probability vector. Lower values indicate better agreement within the same outcome analysis. Because the three analyses used different class structures and prevalences, these values were not compared directly across analyses.`

The final Methods text must additionally specify:
- whether calibration used isotonic regression, sigmoid scaling, or no recalibration;
- whether calibration was fitted only within training folds;
- the number and construction of ECE bins;
- classwise, macro, weighted, or pooled aggregation;
- the multiclass Brier formula and scaling convention;
- how missing or undefined values were handled.

## Figure 9 treatment
Preferred revision:
- keep the main figure focused on the primary discrimination measure and, if retained, operational concentration;
- move technical calibration bars to a supplementary table or replace them with a clearly explained reliability plot;
- if an ECE panel remains, expand the term in the title/caption and state that lower values indicate smaller average probability-frequency discrepancies within the same analysis;
- do not label low ECE as proof of `good calibration`, `credibility`, or `decision value`.

## Citation treatment
- References `[103]` and `[104]` may be retained only where the metrics are formally defined in Methods or supplementary materials.
- They should be removed from the deleted contribution paragraph.
- Correct the reference-list author name `Brie, G.W.` to `Brier, G.W.`

## Reviewer-response draft
`Revised. We deleted the paragraph that presented ECE and the Brier score as a principal contribution and removed the unsupported statement that these measures ensure reliable or decision-useful probabilities. In the main text, calibration is now described in plain language as a secondary internal-validation check. Full technical definitions and values are confined to the Methods or supplementary materials. We also identified that ECE and Brier score were inappropriately reported for the continuous overall-risk aggregation analysis; those diagnostics will be removed from Figure 13 and replaced with regression-appropriate measures.`

## Status
Finalized. The contribution paragraph will be deleted, classifier probability agreement will be described cautiously as secondary internal validation, and probability-classification diagnostics will be removed from the continuous risk-score aggregation analysis unless a valid probabilistic target is documented.
