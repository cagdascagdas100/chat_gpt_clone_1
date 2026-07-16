# OHS Manuscript Revision — Reassessment Status

- Total reviewer comments: 32
- Reassessed through: Comment 18
- Reassessed: 18/32 = 56.25%
- Fully finalized in reassessment: 18/32 = 56.25%
- Next item: Comment 19

## Latest decision — Comment 18
The reviewer comment is attached to `default α ≈ 0.60`. The parameter is not present directly in the displayed overall-score equation; it enters only indirectly through the preceding region-weight expression `v_j ∝ α^(Overall_j−1)`, whose exponent and region-ordering rule are not defined adequately.

## Evidence assessment
- No auditable code, configuration, expert-elicitation protocol, sensitivity analysis, optimization record, or validation supports an across-region decay value of 0.60.
- Reference [103] is Brier's 1950 probability-forecast verification paper and does not justify this weighting parameter.
- The manuscript is internally inconsistent because it also reports α ≈ 0.8 as a selected weighting specification before using α = 0.60 across regions.
- The same symbol α is later reused for the CVaR confidence level, creating a notation collision.

## Final correction
- Delete the `default α ≈ 0.60 [103]` sentence.
- Remove the unsupported cross-region aggregation and overall risk percentage represented by Equations (10)–(12).
- Report body-region-specific priority scores separately.
- Do not infer a replacement weight or equal-weight average without a new reproducible derivation and validation.

## Approved replacement
`The application reports the retained body-region-specific priority scores separately. No single cross-region overall score was calculated because the available study materials did not provide a reproducible rule or validated weighting scheme for combining anatomically distinct regional scores.`

## Next item
Comment 19 — replace every legacy Model F/E/A label, including figures and captions, with the verified Analysis 1/2/3 nomenclature and ensure that each plotted result is mapped by sample size and target definition rather than by visual order.
