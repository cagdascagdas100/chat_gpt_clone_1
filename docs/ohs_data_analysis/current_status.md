# OHS Manuscript Revision — Current Status

- Total reviewer comments: 32
- Processed through: Comment 18
- Processed: 18/32 = 56.25%
- Fully finalized: 14/32 = 43.75%
- Conditional items: Comment 12 (scenario provenance), Comment 15 (authoritative equipment inventory), Comment 17 (internal–external weighting), and Comment 18 (regional-decay value selection)
- Next item: Comment 19

## Latest decision — Comment 18
The value `0.60` is interpreted as an across-region exponential rank-decay parameter used to generate the normalized weights for combining the five body-region risk percentages. It is not a probability, risk coefficient, or threshold.

## Mathematical correction
- Sort the five regional scores as `BPRP_(1) ≥ ... ≥ BPRP_(5)`.
- Define `q_j = γ_R^(j-1)` and `v_j = q_j / Σ_(k=1)^5 q_k`.
- Calculate `R_BP = Σ_(j=1)^5 v_j BPRP_(j)`.
- Use `γ_R` for regional decay and reserve `α` for the CVaR confidence level.
- With `γ_R = 0.60`, the normalized regional weights are approximately `0.434, 0.260, 0.156, 0.094, 0.056`.

## Evidence and consistency findings
- Reference [103] concerns the Brier score and does not justify a regional-decay value of `0.60`; remove it from this statement.
- Distinguish the within-region decay value reported as `0.80` from the across-region value reported as `0.60` by using separate symbols.
- The manuscript's statements about the selected decay value are internally inconsistent; retention of `0.60` requires the exact candidate grid, objective function, validation design, and sensitivity results.
- Comment 17's 0.10/0.90 internal–external linear weighting is mathematically separate from this exponential rank-decay parameter.

## Next item
Comment 19 — standardize the F/E/A labels across the text, figures, legends, and captions using the Analysis 1/2/3 naming convention established in Comment 10.