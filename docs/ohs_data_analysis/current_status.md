# OHS Manuscript Revision — Current Status

- Total reviewer comments: 32
- Processed through: Comment 17
- Processed: 17/32 = 53.125%
- Fully finalized: 14/32 = 43.75%
- Conditional items: Comment 12 (scenario provenance), Comment 15 (authoritative equipment inventory), and Comment 17 (0.10/0.90 weighting validation)
- Next item: Comment 18

## Latest decision — Comment 17
The exact 0.10/0.90 internal–external split is not supported by an auditable derivation, expert-elicitation protocol, optimization result, or sensitivity analysis in the available project records. It must not be described as empirically established.

## Mathematical corrections
- Equation (9) is a weighted linear combination, not an exponential weighting scheme.
- Internal and external components must be normalized to the same dimensionless scale before aggregation.
- Raw coefficients must be distinguished from normalized component scores and weighted percentage contributions.
- The general formulation should use a parameterized convex combination: `P_overall = 100 [w_INT r_INT + (1 - w_INT) r_EXT]`.
- Equal weighting must not be substituted automatically, because 0.50/0.50 would also be arbitrary without a stated rationale.

## Conditional retention rule
The 0.10/0.90 split may be retained only if it was prespecified as a normative design choice to limit the influence of individual-level characteristics, the common-scale normalization is documented, and sensitivity analysis demonstrates that conclusions and rankings are robust to alternative weights. Otherwise, internal and external component scores should be reported separately and the fixed composite score removed.

## Cross-comment consistency updates
- Comment 16 notation rules apply to the revised Equation (9) and its `where ...` statement.
- The Section 4.5 case example must be recalculated after normalization and weighting are finalized.
- The later statement that the model assigned approximately 10% and 90% must be revised; these are exact design weights if retained, not approximate empirical findings.
- Comment 20 will address the later prose description of the same allocation.

## Next item
Comment 18 — define the regional-decay parameter, explain its interpretation, and show exactly where it enters the body-region aggregation equations.