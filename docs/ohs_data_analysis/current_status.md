# OHS Manuscript Revision — Current Status

- Total reviewer comments: 32
- Processed through: Comment 20
- Processed: 20/32 = 62.5%
- Fully finalized: 15/32 = 46.875%
- Conditional items: Comment 12 (scenario provenance), Comment 15 (authoritative equipment inventory), Comment 17 (internal–external weighting), Comment 18 (regional-decay value selection), and Comment 20 (final composite depends on Comment 17 and the missing fifth-region input)
- Next item: Comment 21

## Latest decision — Comment 20
The paragraph currently conflates two different calculations. The reported `50.62%` is the external body-region component produced by the two-stage rank-weighted aggregation; it is not the final internal–external composite.

## Verified calculation pathway
- Within-region decay `0.80` produces approximately: head `50.5556%`, arms `56.4754%`, legs `49.4851%`, and torso `25.5738%`.
- Across-region decay `0.60`, with weights renormalized over the four supplied regions, produces `50.6192%`, which rounds to `50.62%`.
- This confirms that `50.62%` is independent of the separate 10/90 internal–external weighting rule.

## Required wording and notation corrections
- Replace `overall risk of 50.62%` with `external body-region component of 50.62%`.
- If the 10/90 allocation is retained after Comment 17 is resolved, define the final composite separately as `P_overall = 0.10 P_INT + 0.90 P_EXT`.
- Because the example does not provide `P_INT`, no numerical final composite can be reported.
- Remove the unsupported phrase `accurate risk percentages` and the claim that restricting variables mathematically generated the 10/90 split.
- Use exact rather than approximate weights if 0.10/0.90 is retained.

## Additional inconsistency
The Methods section describes five body regions, but the example provides only four. The final version must either add the fifth-region input and recalculate the example or state that the illustration uses four available regions with renormalized weights.

## Cross-comment consistency updates
- Comment 16: keep distinct notation for the body-region aggregate and the final internal–external composite.
- Comment 17: controls whether the 0.10/0.90 weighting remains in the manuscript.
- Comment 18: controls the within-region and across-region decay parameters.
- Comment 20 is processed but remains conditional until the weighting rule and the four-versus-five-region issue are resolved.

## Next item
Comment 21 — verify whether the corrected figure reference is Figure 14 rather than Figure 15 and align the text with the actual figure content and numbering.