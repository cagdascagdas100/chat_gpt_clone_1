# Comment 20 — Relationship between the body-region example and the 10/90 internal–external allocation

## Reviewer comment
`Bunun yukardaki 90/10 ile bağlantısı var sanırım. Yine karmaşık bir durum, verilecekse böyle bir şey açalım.`

## Selected manuscript paragraph
`For example, given regional inputs (head: 45, 55; arms: 55, 45, 65; legs: 50, 40, 40, 60; torso: 10, 20, 40), the procedure produced an overall risk of 50.62%. When restricted to observable and actionable variables, the occupational safety model assigned approximately 10% of total risk to internal factors and 90% to external factors. By incorporating multiple aggregation methods, the overall risk model calculated accurate risk percentages for different body parts, ensuring a comprehensive evaluation of safety risks on construction sites.`

## Core finding
The reviewer is correct that the two statements are conceptually connected, but the current paragraph incorrectly merges two distinct aggregation stages.

1. The value `50.62%` is produced by the two-stage rank-weighted aggregation of body-region values. It represents an **external body-region component**, not the final internal–external composite.
2. The `10%/90%` rule belongs to a later and separate combination of a normalized internal component with a normalized external component.
3. Because the example supplies no internal-component value, the final internal–external composite cannot be calculated from the information shown.

The value `50.62%` therefore must not be called the final `overall risk` in this paragraph.

## Reproducibility check of the reported 50.62%
Using the manuscript's stated within-region rank-decay value of `0.80`, the reported regional inputs produce approximately:

- head: `50.5556%`;
- arms: `56.4754%`;
- legs: `49.4851%`;
- torso: `25.5738%`.

Sorting these four regional values and applying the across-region decay value of `0.60` yields normalized weights of approximately `0.4596, 0.2757, 0.1654, 0.0993` and a combined value of `50.6192%`, which rounds to `50.62%`.

This reconstruction confirms that the reported `50.62%` comes from body-region aggregation alone and is mathematically independent of the 10/90 internal–external weighting.

## Additional inconsistency identified
The Methods section refers to five predefined body regions, whereas the example provides values for only four regions: head, arms, legs, and torso. The final manuscript must do one of the following:

- add the missing fifth-region input and recalculate the example; or
- state explicitly that the illustration contains four available regions and that the across-region weights were renormalized over those four regions.

Until this is resolved, the example should not be described as a complete five-region calculation.

## Correct relationship if the 10/90 allocation is retained
If Comment 17's conditional 10/90 allocation is ultimately validated, the two stages should be written separately:

`P_EXT = 50.62%`

`P_overall = w_INT P_INT + (1 - w_INT) P_EXT`

and, only when `w_INT = 0.10` is retained:

`P_overall = 0.10 P_INT + 0.90 P_EXT`

For the example shown:

`P_overall = 0.10 P_INT + 0.90(50.62)`

A numerical value for `P_overall` cannot be reported unless `P_INT` is supplied for the same case.

## Preferred replacement paragraph
`For the illustrative machine–malfunction record, the two-stage rank-weighted body-region aggregation yielded an external-component score of 50.62% from the four reported regional inputs. This value represents the external body-region component and is not the final internal–external composite. If the prespecified 10/90 allocation is retained after methodological validation, the final composite for the same case would be calculated as P_overall = 0.10P_INT + 0.90P_EXT, where P_EXT = 50.62%. Because the corresponding internal-component score is not reported in this example, a final composite percentage cannot be calculated.`

If the 10/90 allocation is not validated, omit the last two sentences and report the internal and external components separately, in accordance with Comment 17.

## Statements to remove or revise
- Replace `overall risk of 50.62%` with `external body-region component of 50.62%`.
- Remove `When restricted to observable and actionable variables`; this phrase does not mathematically produce the 10/90 allocation.
- Replace `approximately 10%` and `90%` with exact design weights only if those weights are retained and validated.
- Remove the claim that the model calculated `accurate risk percentages`; accuracy is an empirical validation claim and is not established by the illustrative calculation.
- Do not say that `multiple aggregation methods` produced the final value when the example uses one selected two-stage rank-weighting procedure.

## Placement recommendation
The body-region calculation example should remain in the Results subsection describing the external component. The rationale, equation, normalization, and sensitivity analysis for the internal–external weighting should be reported in Methods immediately after the revised Equation (9). Mixing both stages in one paragraph obscures the calculation pathway.

## Link to earlier comments
- Comment 16 governs notation and requires separate symbols for the body-region aggregate and the final internal–external composite.
- Comment 17 governs whether the 0.10/0.90 weights may be retained.
- Comment 18 governs the within-region and across-region decay parameters.
- Comments 8–9 continue to prevent unrelated payment-day or monetary-cost quantities from being conflated with these risk percentages.

## Reviewer-response draft
`Revised. We separated the two calculations that had been conflated in the original paragraph. The reported 50.62% is the external body-region component obtained from rank-weighted aggregation; it is not the final internal–external composite. The manuscript now explains that a final composite can be calculated only after combining this external component with the corresponding internal component under the weighting rule defined in the Methods. Because the illustrative example does not provide an internal-component value, no final composite percentage is reported. We also clarified that the example contains four reported regions and requires either the missing fifth-region input or explicit renormalization over the four available regions.`

## Status
Processed but conditional. The textual distinction is final, but the displayed composite formula and any numerical final score depend on the resolution of Comment 17 and on correction of the four-versus-five-region inconsistency.