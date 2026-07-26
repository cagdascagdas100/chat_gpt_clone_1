# Comment 17 — Methodological basis for the 0.10/0.90 internal–external weights

## Reviewer comment
`Neden internal 0.1 external ise 0.9 ile çarpıldı.`

## Selected equation
`Risk_Overall = 0.10 × RC_INT + 0.90 × RC_EXT`

## Evidence check
The available manuscript and analytical artifacts do not contain an auditable derivation, expert-elicitation protocol, optimization result, or sensitivity analysis supporting the exact values 0.10 and 0.90. The weights therefore must not be presented as empirically established or literature-derived.

The manuscript later describes the 10% internal and 90% external allocation as arising from a restriction to observable and actionable variables, but this statement does not mathematically derive the two numerical weights. A policy preference for emphasizing modifiable jobsite conditions may justify limiting the influence of individual-level variables, but it does not by itself justify the exact 10/90 split.

## Major mathematical issues
1. Equation (9) is a linear convex combination, not an `exponential weighting scheme`. That phrase must be removed unless an actual exponential transformation is shown.
2. The combination is meaningful only if the internal and external components have first been transformed to the same dimensionless scale. The manuscript currently alternates among raw coefficients on a 2–4 scale, normalized percentages, and capped contributions of 10% and 90%.
3. The notation must distinguish raw coefficients from normalized component scores. Raw `RC_INT` and `RC_EXT` should not be multiplied directly by 0.10 and 0.90 unless their normalization is explicitly defined.
4. The exact weights are a model-design parameter and can materially affect worker ranking, scenario ranking, and the reported overall percentage. They require justification and robustness analysis.

## Preferred methodological formulation
Replace the fixed equation with a parameterized convex combination:

`P_overall = 100 [w_INT r_INT + (1 - w_INT) r_EXT],  0 ≤ w_INT ≤ 1`

where `r_INT` and `r_EXT` are the normalized internal and external component scores on the interval [0,1], `w_INT` is the prespecified weight assigned to the internal component, and `1 - w_INT` is the weight assigned to the external component.

If the component values are already expressed as percentages on the same 0–100 scale, use:

`P_overall = w_INT P_INT + (1 - w_INT) P_EXT`

The manuscript must use only one of these two forms and define the normalization function immediately before the equation.

## Decision on the 0.10/0.90 values
The 0.10/0.90 split may be retained only if all of the following are documented:
- it was specified before examining the final results;
- its purpose was to cap the influence of personal or relatively nonmodifiable characteristics and prioritize modifiable jobsite conditions;
- the internal and external scores were normalized to the same scale before aggregation;
- a sensitivity analysis shows that the principal conclusions and rankings are not artifacts of the selected weight;
- the manuscript explicitly identifies the split as a normative design choice rather than a learned coefficient.

A suitable sensitivity analysis should evaluate a prespecified grid such as `w_INT ∈ {0, 0.05, 0.10, 0.20, 0.30, 0.50}` and report changes in overall-score distributions, rank correlations, risk-category assignments, and the identity of high-priority scenarios or workers.

If these conditions cannot be satisfied, the strongest defensible option is to remove the fixed 10/90 overall score and report the normalized internal and external components separately. Equal weighting must not be substituted automatically, because 0.50/0.50 would also be arbitrary without a stated rationale.

## Conditional manuscript wording if 0.10/0.90 is retained
`The overall risk percentage was calculated as a prespecified weighted combination of normalized internal and external component scores. The internal component was capped at 10% of the total score to limit the influence of individual-level characteristics, whereas 90% was assigned to modifiable work-environment and equipment-related conditions. This allocation was treated as a normative design choice rather than an empirically estimated coefficient and was evaluated in a sensitivity analysis across alternative weight settings.`

## Preferred wording if the weights are not validated
`Because no empirical or expert-derived basis was available for a fixed internal–external weighting, the normalized internal and external component scores were reported separately. An overall composite score was not calculated.`

## Red-highlight treatment for the final workbook
The entire sentence introducing Equation (9), Equation (9) itself, the corresponding `where ...` statement, and all later statements assigning maximum contributions of 10% and 90% should be shown as revised. The final wording depends on whether the authors can document the prespecification and sensitivity analysis.

## Manuscript-wide consistency actions
- Replace `exponential weighting scheme` with `weighted linear combination` where Equation (9) is discussed.
- Clarify whether the displayed case-example values are raw coefficients, normalized component percentages, or already weighted contributions.
- Recalculate the example in Section 4.5 after the normalization and weighting definition is finalized.
- Revise the statement that the model `assigned approximately 10%` and `90%`; the values are exact weights if retained, not approximate empirical findings.
- Link this decision to Comment 20, which questions the later prose description of the same 90/10 allocation.

## Reviewer-response draft
`Revised. The original manuscript did not provide a defensible derivation for the 0.10/0.90 split. We therefore reformulated the overall score as a weighted combination of normalized internal and external component scores and clarified that any retained 10/90 allocation is a prespecified normative design choice rather than an empirically learned coefficient. The terminology “exponential weighting” was corrected because the equation is linear. The fixed split will be retained only if its prespecification, common-scale normalization, and sensitivity analysis can be documented; otherwise, the two component scores will be reported separately.`

## Status
Processed but conditional. Finalization requires either documented prespecification plus sensitivity results for the 0.10/0.90 allocation or removal of the fixed composite score.