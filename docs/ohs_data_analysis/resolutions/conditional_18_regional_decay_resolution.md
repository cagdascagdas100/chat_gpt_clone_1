# Conditional Resolution 18 — Across-Region Exponential Decay

## Issue
The manuscript combines five body-region risk percentages using rank-based exponential weights and a fixed decay value of `0.60`. The reviewer asked what this parameter means and where it is used.

## Evidence audit
- The parameter is used only in the second-stage aggregation that collapses the regional body-part risk percentages into one scalar.
- For five ranked regions, `gamma_R = 0.60` produces normalized weights of approximately `0.434, 0.260, 0.156, 0.094, and 0.056`; therefore the result is strongly driven by the highest-ranked region.
- No prespecified decision objective, expert-elicitation record, empirical derivation, optimization protocol, independent validation, or sensitivity analysis supports the value `0.60`.
- Reference `[103]` is a Brier-score source and is unrelated to regional rank-decay weighting.
- The manuscript separately discusses a within-region decay value near `0.80`; that value cannot be transferred to the across-region level because the two aggregation stages answer different questions.
- The manuscript states that five regions are used, but the worked example supplies only four. This prevents a reproducible five-region aggregate and is addressed further under Comment 20.

## Final decision
The fixed across-region value `0.60` and the corresponding weighted-sum equation are removed. The five body-region risk percentages will be reported separately rather than collapsed into an unsupported overall body-region score.

For presentation, regions may be ordered from highest to lowest and the highest regional value may be identified as the `highest regional risk`; this is a transparent descriptive summary and must not be labeled as an overall validated risk percentage.

No equal-weight or alternative decay rule will be substituted, because doing so would replace one arbitrary choice with another.

## Approved manuscript wording
`The application reports body-region-specific risk percentages separately. For presentation, the regions are ordered from highest to lowest and the highest regional value is identified to support prioritization. The regional values are not collapsed into a single overall score because the study did not prespecify or validate an across-region weighting rule.`

## Equation and terminology actions
- Delete the across-region rank-weight definition, normalization equation, and weighted regional sum that use `0.60`.
- Remove the citation to `[103]` from this context.
- Do not reuse `alpha` for regional decay; reserve it for the CVaR confidence level where applicable.
- Keep within-region aggregation analytically separate from across-region reporting.
- Replace `overall risk percentage` with `body-region-specific risk percentages` or `highest regional risk` where the displayed value is derived only from regional outputs.

## Restoration rule
A scalar across-region score may be reintroduced only after the anatomical taxonomy is fixed, all regional values are on a documented common scale, the decision purpose is prespecified, weights are derived through a reproducible method, plausible alternatives are examined in sensitivity analyses, and the selected rule is evaluated prospectively or on an independent validation set.

## Consequence for Comment 20
The worked-example value `50.62%` will not be retained as an overall or external composite. Comment 20 will be resolved by removing that scalar example, correcting the four-versus-five-region inconsistency, and presenting regional outputs without the unsupported second-stage decay.