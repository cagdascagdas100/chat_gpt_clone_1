# OHS Manuscript Revision — Current Status

- Total reviewer comments: 32
- Processed through: Comment 32
- Processed: 32/32 = 100.0%
- Fully finalized: 29/32 = 90.625%
- Conditional-resolution phase: 4/7 items resolved = 57.143%
- Remaining conditional items: Comment 20 (worked-example composite and four-versus-five-region inconsistency), Comment 23 (original high-resolution landing-page and personal-input screenshots), and Comment 24 (meaning of `yz`)
- Next item: resolve Comment 20 by removing the unsupported `50.62%` scalar, correcting the regional-input inconsistency, and aligning the example with separate regional reporting

## Latest decision — Conditional Item 18 resolved
The fixed across-region exponential-decay value `0.60` and the corresponding weighted regional sum are removed. No prespecified rationale, expert-elicitation record, empirical derivation, validation result, or sensitivity analysis supports this value.

## Evidence and mathematical implications
- With five ranked regions, `0.60` creates normalized weights of approximately `0.434, 0.260, 0.156, 0.094, and 0.056`, so the scalar is strongly driven by the highest-ranked region.
- Reference `[103]` is a Brier-score source and does not justify regional rank-decay weighting.
- The within-region value near `0.80` and the across-region value `0.60` belong to different aggregation stages and cannot be treated as interchangeable.
- The worked example supplies four regions although the method claims five, so the reported scalar is not a reproducible five-region result.

## Final reporting rule
- Report body-region-specific risk percentages separately.
- Regions may be ordered from highest to lowest, and the maximum may be labeled `highest regional risk`.
- Do not call the maximum or any regional statistic an overall validated risk percentage.
- Do not substitute equal weights or another decay value without prespecification and validation.
- Delete the across-region weight, normalization, and weighted-sum equations and remove `[103]` from this context.

## Approved wording
`The application reports body-region-specific risk percentages separately. For presentation, the regions are ordered from highest to lowest and the highest regional value is identified to support prioritization. The regional values are not collapsed into a single overall score because the study did not prespecify or validate an across-region weighting rule.`

## Consequence for Comment 20
The worked-example value `50.62%` will not be retained as an overall or external composite. Comment 20 will remove that scalar, correct the four-versus-five-region inconsistency, and present the example only through region-specific outputs.

## Next item
Conditional Item 20 — finalize the worked example after the removal of both the 10/90 internal–external weighting and the 0.60 across-region decay rule.