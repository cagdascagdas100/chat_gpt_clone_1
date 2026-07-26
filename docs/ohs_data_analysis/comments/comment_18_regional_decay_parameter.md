# Comment 18 — Meaning and use of the regional-decay parameter

## Reviewer comment
`Bu ne demek ve nerede kullanıyoruz, formülde de yok?`

## Selected wording
`α ≈ 0.60`

## Core finding
The selected value is intended to be a rank-decay hyperparameter for combining the five body-region risk percentages, not a probability, risk coefficient, or decision threshold. The current presentation is confusing because the prose introduces `α ≈ 0.60`, Equation (10) uses a visually ambiguous `α_Overall`, Equation (12) contains only the normalized weights `v_j`, and the same symbol `α` is later reused for the CVaR confidence level.

## Required notation correction
Reserve `α` for the CVaR confidence level and denote the across-region rank-decay parameter by `γ_R`.

Let the five regional scores be sorted from highest to lowest:

`BPRP_(1) ≥ BPRP_(2) ≥ ... ≥ BPRP_(5)`

Define the unnormalized rank weight and its normalized form as:

`q_j = γ_R^(j-1),  j = 1,...,5`

`v_j = q_j / Σ_(k=1)^5 q_k`

Then calculate the body-region aggregate as:

`R_BP = Σ_(j=1)^5 v_j BPRP_(j)`

where `γ_R` is the across-region rank-decay parameter, `q_j` is the unnormalized weight assigned to rank `j`, `v_j` is the corresponding normalized weight, `BPRP_(j)` is the regional risk percentage at rank `j`, and `R_BP` is the aggregate body-region risk score.

## Interpretation of `γ_R = 0.60`
A value of `0.60` means that each successive ranked region receives 60% of the preceding region's unnormalized weight. Before normalization, the five weights are:

`1.000, 0.600, 0.360, 0.216, 0.1296`

After normalization, they are approximately:

`0.434, 0.260, 0.156, 0.094, 0.056`

Thus, the highest regional BPRP receives about 43.4% of the aggregate weight and the fifth-ranked region about 5.6%. Smaller values of `γ_R` concentrate more weight on the highest-ranked region; `γ_R = 1` gives equal weights.

## Important methodological requirement
The regions must be ranked by BPRP before these weights are applied. If `j` denotes a fixed anatomical label rather than rank position, the weighting becomes dependent on an arbitrary ordering of body regions and is not defensible.

## Distinguish the two decay stages
The manuscript later describes two exponential-rank weighting stages:

- within each body region, the top eight risk values are aggregated using a decay value reported as `0.80`;
- across the five regional BPRP values, the overall body-region aggregate uses the value reported as `0.60`.

These parameters must use different symbols, for example `γ_H = 0.80` for within-region hazard ranking and `γ_R = 0.60` for across-region ranking. They must not both be denoted by `α`.

## Evidence and citation audit
Reference [103] is the Brier-score paper and does not justify a regional rank-decay value of `0.60`. Remove `[103]` from the sentence introducing this parameter.

The manuscript also contains an unresolved selection inconsistency: it states that exponential weighting near `0.80` performed best under one composite criterion, that Top-K had the lowest MAPE, and that the final combined specification nevertheless retained `0.60`. The value `0.60` may be reported as selected only if the authors provide the exact candidate grid, objective function, validation data or simulation design, and tie-breaking rule that produced it.

If those records are unavailable, the defensible alternatives are:

1. treat `γ_R` as a prespecified sensitivity parameter and report results over a plausible grid; or
2. remove the claim that `0.60` was empirically selected and report an unweighted regional mean or the regional scores separately, with a clear rationale.

## Preferred manuscript replacement
`The five body-region risk percentages were ranked from highest to lowest and combined using normalized exponential rank weights. For rank j, the unnormalized weight was q_j = γ_R^(j−1), and the normalized weight was v_j = q_j/Σ_(k=1)^5 q_k. The aggregate body-region risk score was then calculated as R_BP = Σ_(j=1)^5 v_j BPRP_(j). The parameter γ_R controls the rate at which weight decreases across successive ranks; the value γ_R = 0.60 was retained only if supported by the documented validation and sensitivity analysis.`

## Red-highlight treatment for the final workbook
Revise the sentence introducing the parameter, Equations (10)–(12), and the complete `where ...` statement. The symbol change from `α` to `γ_R`, the sorting rule, and the normalized-weight formula should be shown as new text.

## Reviewer-response draft
`Revised. We clarified that the value 0.60 is an across-region rank-decay parameter used to construct the normalized weights in the body-region aggregation, rather than a risk coefficient or threshold. The equations now show explicitly how the parameter enters the unnormalized and normalized weights, and the five regional scores are stated to be ranked before weighting. The symbol was changed from α to γ_R to avoid conflict with the CVaR confidence level. The unrelated Brier-score citation was removed. Retention of the numerical value 0.60 is conditional on documenting the validation or sensitivity procedure used to select it.`

## Cross-comment consistency
- Comment 16: use `γ_R` for regional decay and reserve `α` for CVaR.
- Comment 17: the internal–external 0.10/0.90 weighting is a separate linear-combination issue and must not be conflated with exponential rank decay.
- Comment 20: later prose must explain the 90/10 allocation separately from `γ_R = 0.60`.

## Status
Processed but conditional. The parameter's meaning and mathematical location are resolved; finalization of the numerical value `0.60` requires a documented selection or sensitivity analysis.