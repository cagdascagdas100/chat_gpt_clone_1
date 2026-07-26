# Comment 18 — Remove unsupported α = 0.60 overall aggregation

## Reviewer comment
`Bu ne demek ve nerede kullanıyoruz, formülde de yok?`

## Verified manuscript anchor
The comment is attached to the sentence:

`Finally, the overall risk score was calculated with default α ≈ 0.60 [103]:`

The surrounding equations are:

- Equation (10): region weights are written as proportional to an exponential decay term, `v_j ∝ α^(Overall_j−1)`.
- Equation (11): the region weights are normalized to sum to one.
- Equation (12): the overall value is written as a weighted sum, `Risk_Overall = Σ_j v_j · BPRP_j`.

Therefore, α is not shown directly in Equation (12); it enters only indirectly through the undefined region-weight construction in Equation (10). The exponent term `Overall_j−1` is itself not defined clearly as a rank, and the manuscript does not document how the five anatomical regions are ordered before applying the decay.

## Evidence assessment
The archived project materials contain no auditable code, configuration, optimization record, expert-elicitation protocol, sensitivity analysis, or validation result supporting an across-region decay parameter of 0.60. The cited reference [103] resolves in the manuscript metadata to Brier's 1950 probability-forecast verification paper, which does not establish a default exponential rank-decay value for anatomical-region aggregation.

The manuscript is also internally inconsistent: it later refers to α ≈ 0.8 as a selected weighting specification, then states that α = 0.60 was used to combine the five regional values. These statements do not provide a reproducible derivation for the cross-region value.

## Final decision
Do not attempt to preserve the sentence by adding a superficial definition of α. Remove the α = 0.60 statement and the unsupported cross-region aggregation represented by Equations (10)–(12). Report the retained body-region-specific scores separately.

This decision is narrower than a blanket rejection of all rank weighting: any within-region rank-decay procedure must be documented and justified independently. It does not validate the separate α = 0.8 claim.

## Approved replacement wording
`The application reports the retained body-region-specific priority scores separately. No single cross-region overall score was calculated because the available study materials did not provide a reproducible rule or validated weighting scheme for combining anatomically distinct regional scores.`

## Required manuscript corrections
- Delete `default α ≈ 0.60 [103]`.
- Delete or rewrite Equations (10)–(12) so that no unsupported cross-region overall score remains.
- Remove `overall risk percentage` from application outputs, figures, captions, examples, Discussion, and Conclusion unless a new validated aggregation is supplied.
- Preserve regional values as separate descriptive decision-support outputs.
- Reserve `α` for a single clearly defined role; do not reuse it for both rank decay and the later CVaR confidence level.
- Remove the irrelevant use of reference [103] as support for the 0.60 decay value.

## Scientific boundary
The regional outputs are not probabilities or additive shares of total occupational risk. Combining them requires a defensible common scale, an explicit weighting rationale, and validation; none is currently documented.
