# OHS Manuscript Revision — Current Status

- Total reviewer comments: 32
- Processed through: Comment 16
- Processed: 16/32 = 50.0%
- Fully finalized: 14/32 = 43.75%
- Conditional items: Comment 12 (scenario provenance) and Comment 15 (authoritative equipment inventory)
- Linked follow-up items: Comment 17 (0.10/0.90 weighting rationale) and Comment 18 (regional-decay parameter)
- Next item: Comment 17

## Latest decision — Comment 16
Every displayed equation will be followed immediately by a concise `where ...` statement defining every newly introduced symbol. Concatenated labels such as `RCSWA` will be standardized using structured subscripts such as `RC_{S,WA}`.

## Mathematical corrections
- Preserve the square roots in Equations (3)–(8), because these equations are geometric means rather than simple products.
- Preserve summation indices and limits in Equations (11)–(14).
- Preserve the explicit fractions `2/3` and `1/2` in Equations (15)–(16).
- Do not assign units, ranges, or dimensionless status to risk coefficients unless the normalization procedure verifies them.

## Major notation conflicts identified
- Equation (9) and Equation (12) currently use `RiskOverall` for two different constructions. Use `R_IE` for the internal–external composite and `R_BP` for the body-region aggregate until their relationship is explicitly defined.
- The symbol `α` is used both for regional decay and for the CVaR confidence level. Use `γ` for regional decay and reserve `α` for CVaR.
- Payment-day severity and monetary compensation cost must use different symbols and units.
- The text says feasibility was excluded, but Equation (1) still uses a feasibility-derived weight `λ`; this contradiction must be resolved.

## Cross-comment consistency updates
- Comment 17 will justify or revise the 0.10/0.90 internal–external weights in Equation (9).
- Comment 18 will explain the regional-decay parameter and where it enters Equations (10)–(12).
- Comments 8–9 continue to govern the distinction between recorded payment days, days away from work, and monetary compensation cost.
- The final Word and PDF exports must be checked for missing radicals, fractions, subscripts, and summation limits.

## Next item
Comment 17 — determine and document the methodological basis for weighting the internal component by 0.10 and the external component by 0.90.