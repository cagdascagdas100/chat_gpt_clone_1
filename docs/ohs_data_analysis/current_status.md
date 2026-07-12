# OHS Manuscript Revision — Current Status

- Total reviewer comments: 32
- Processed through: Comment 29
- Processed: 29/32 = 90.625%
- Fully finalized: 22/32 = 68.75%
- Conditional items: Comment 12 (scenario provenance), Comment 15 (authoritative equipment inventory), Comment 17 (internal–external weighting), Comment 18 (regional-decay value selection), Comment 20 (final composite depends on Comment 17 and the missing fifth-region input), Comment 23 (original high-resolution landing-page and personal-input screenshots), and Comment 24 (meaning of `yz`)
- Next item: Comment 30

## Latest decision — Comment 29
The paragraph presenting ECE and the Brier score as a principal contribution will be deleted. Probability agreement will be described in plain language as a secondary internal-validation check; technical definitions and full values will be confined to the Methods or supplementary materials.

## Calibration-reporting corrections
- Remove the unsupported statement that ECE and Brier score `ensure` reliable or decision-useful probabilities.
- Do not compare calibration values directly across Analysis 1, Analysis 2, and Analysis 3 because their outcome structures and class prevalences differ.
- The detailed reports include ECE values up to approximately `0.032`; the current blanket `0–0.02` statement is incomplete unless restricted to the subset displayed in Figure 9.
- Undefined or missing Brier/ECE values for baseline records must not be treated as zero.
- No independent holdout or external calibration validation is documented.

## Critical Figure 13 correction
Figure 13 evaluates a continuous observed-versus-predicted overall-risk score but reports Brier score, ECE, c-index, and decision-curve net benefit. These probability-classification diagnostics will be removed unless a valid probabilistic event target and threshold definition are documented. The regenerated figure should use regression-appropriate diagnostics such as predicted-versus-observed agreement, calibration slope/intercept, MAE or RMSE, MAPE, R², residual analysis, and uncertainty intervals.

## Main-text approach
The revised text will state that predicted class probabilities were compared with observed class frequencies during internal validation because those probabilities enter later ranking calculations. The checks will be described as secondary diagnostics and not as evidence of external validity, application reliability, or practical effectiveness.

## Citation and terminology corrections
- References `[103]` and `[104]` may remain only where calibration metrics are formally defined.
- Correct `Brie, G.W.` to `Brier, G.W.` in the reference list.
- Keep classifier probability calibration separate from the continuous risk-score aggregation analysis.

## Next item
Comment 30 — rebuild Section 5.3 around practical use: intended users, workflow, modules, decision points, and realistic field deployment without unsupported effectiveness claims.
