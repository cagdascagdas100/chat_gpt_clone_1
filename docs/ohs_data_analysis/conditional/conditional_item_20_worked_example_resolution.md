# Conditional Item 20 — Worked-example composite and regional-input inconsistency

## Reviewer issue
The worked example linked a reported value of `50.62%` to the earlier `0.10/0.90` internal–external weighting and also relied on an across-region decay rule. The example additionally supplied four body-region outputs although the Methods text referred to five regions.

## Final decision
The value `50.62%` will be removed from the manuscript, tables, captions, and application screenshots as an `overall risk`, `external composite`, or otherwise validated scalar. Both rules that generated the composite have already been removed:

- the unsupported `0.10/0.90` internal–external weighting under Conditional Item 17;
- the unsupported across-region exponential-decay value `0.60` under Conditional Item 18.

No replacement composite, equal-weight average, maximum-as-overall-score, or inferred fifth-region value will be introduced.

## Region-specific example retained
The four auditable region-specific outputs in the worked example may be reported separately and in descending order:

1. arms: `56.48%`;
2. head: `50.56%`;
3. legs: `49.49%`;
4. torso: `25.57%`.

These values must be described as illustrative outputs of the implemented region-specific calculation, not as externally validated probabilities or a complete five-region aggregate. The arms value may be identified as the `highest regional value`, but not as the overall risk.

## Four-versus-five-region correction
The example contains only four reported regions. A fifth value will not be fabricated. The manuscript must therefore do one of the following:

- present the case explicitly as a four-region illustrative example; or
- add the fifth region only if its original input, calculation trace, and output can be supplied from the application records.

Until such evidence is available, no five-region claim or five-region aggregate will be attached to this example.

## Figure and interface rule
Any manuscript figure or screenshot that displays `50.62%` under an `Overall Risk` label must be regenerated after the calculation logic and interface label are corrected. If a corrected original screenshot cannot be produced, that panel should be omitted or cropped rather than digitally relabeled in a way that misrepresents the deployed interface.

## Approved replacement wording
`In the illustrative case, the application displayed region-specific values of 56.48% for the arms, 50.56% for the head, 49.49% for the legs, and 25.57% for the torso. The values were reported separately and ordered to support prioritization; they were not combined into an overall percentage. Because the example contained four reported regions, no fifth-region value or five-region aggregate was inferred.`

## Cross-comment consistency
- Conditional Item 17 requires separate reporting of internal and external components.
- Conditional Item 18 requires separate reporting of body-region values.
- Comment 16 requires unique notation and immediate symbol definitions for any retained equations.
- Comments 21–23 govern figure numbering, application-screen descriptions, and screenshot evidence.

## Resolution status
Conditional Item 20 is resolved. The worked example will contain region-specific outputs only, with no `50.62%` composite and no fabricated fifth region.
