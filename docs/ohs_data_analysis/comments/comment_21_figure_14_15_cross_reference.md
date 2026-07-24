# Comment 21 — Figure 14 versus Figure 15 cross-reference

## Reviewer comment
`Figür 15 yazıyordu, düzelttim bu doğru di mi?`

## Selected manuscript passage
`The model evaluated indemnity costs and the likelihood of indemnity payments for each risk scenario by prioritizing the highest risk scenario among three candidates. Using CVaR/ES as the decision metric, the riskiest scenario for each risk was selected as the candidate maximizing ... (Figure 14). This was carried forward for display in the OSH-RA application ...`

## Verification against the embedded figures
The correction from Figure 15 to Figure 14 is correct for the sentence discussing comparison of the cost-related decision rules and the CVaR-based prioritization step.

- Figure 14 contains a risk-level comparison with `Risk ID` on the vertical axis, a predicted payment-day quantity on the horizontal axis, and three plotted decision-rule series labeled `EV_add`, `EV_single`, and `CVaR × P(any)`.
- Figure 15 is not the decision-rule comparison. It is an illustrative test-case diagram showing the personal-risk inputs and the work-environment/equipment selection hierarchy used in the application example.

The original paragraph nevertheless combines two separate ideas and should not attach one figure number to both. Figure 14 should support the decision-rule comparison, whereas Figure 15 should support the subsequent application-case illustration.

## Preferred replacement wording
`Figure 14 compares the risk-specific outputs obtained under the additive expected-value, single-scenario expected-value, and probability-weighted conditional value-at-risk decision rules. The probability-weighted CVaR criterion was used in the prioritization step to identify the highest-priority candidate for subsequent use in the OSH-RA workflow. Figure 15 separately illustrates the personal and work-environment inputs used in the application test case.`

This version places each figure reference next to the content it actually depicts and avoids implying that Figure 14 is an application screenshot.

## Required caption corrections
The current Figure 14 caption, `Comparison of aggregation models by their risk-ranking overlap and agreement`, does not accurately describe the embedded plot. Replace it with:

`Figure 14. Risk-specific predicted payment-day outcomes under the additive expected-value, single-scenario expected-value, and probability-weighted CVaR decision rules.`

The current Figure 15 caption, `OSH-RA mobile app test application example`, is too general. Replace it with:

`Figure 15. Illustrative personal and work-environment input configuration for the OSH-RA application test case.`

## Terminology safeguards
- Do not describe the horizontal-axis quantity as a monetary indemnity cost unless a documented conversion from payment days to currency is available.
- Replace the unverified axis label `Predicted DAFW Days` with `Predicted payment days` or another source-verified label when Figure 14 is regenerated.
- Do not use `DAFW-monetized` unless the conversion rule, currency, price year, and units are reported.
- `CVaR` and `expected shortfall` may be treated as equivalent labels only after the exact implementation and confidence level are stated.
- The phrase `candidate maximizing ...` must contain the actual objective expression in the final Word and PDF exports; the current sentence contains a missing equation object.

## Cross-comment consistency updates
- Comments 8 and 9 govern replacement of unverified DAFW terminology with the recorded payment-day outcome.
- Comment 16 requires the missing objective expression and every symbol to be visible and defined.
- Comment 20 requires the body-region aggregate, payment-day output, and final internal–external composite to remain distinct.
- Comment 22 will describe Figures 16–18 separately rather than treating them as one undifferentiated group.

## Reviewer-response draft
`Revised. Figure 14 is the correct reference for the comparison of the expected-value and probability-weighted CVaR decision rules; Figure 15 instead presents the illustrative personal and work-environment inputs used in the application test case. We separated these two functions in the text and revised both captions so that each figure is cited immediately after the content it depicts. We also replaced the unverified DAFW/cost wording with payment-day terminology pending source-level confirmation of the outcome definition.`

## Status
Finalized. The embedded figures establish the correct cross-reference: Figure 14 for the decision-rule comparison and Figure 15 for the application test-case inputs.