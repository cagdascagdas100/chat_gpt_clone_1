# Conditional Resolution — Comment 17: Internal–External Weighting

## Reviewer issue
`Neden internal 0.1 external ise 0.9 ile çarpıldı.`

## Final decision
The fixed `0.10/0.90` internal–external weighting will be removed from the manuscript and from any claim of a validated overall risk percentage. The auditable project package contains no prespecified rationale, expert-elicitation protocol, optimization result, outcome-linked derivation, or sensitivity analysis that supports assigning 10% of the composite to internal factors and 90% to external factors.

A numerical replacement such as `0.50/0.50` will not be introduced, because equal weighting would also be an unsupported normative choice. Until a transparent weighting study is completed, internal and external risk components will be reported separately.

## Evidence audit
- The manuscript gives a qualitative statement that external factors are more observable or actionable, but this does not derive the exact numerical weights.
- No protocol documents stakeholder elicitation, pairwise comparison, Delphi consensus, analytic hierarchy process, regression-based estimation, utility calibration, or another reproducible weighting procedure.
- No held-out or external analysis compares alternative weights against a prespecified performance or decision criterion.
- No sensitivity analysis shows whether worker/scenario rankings, risk bands, or recommended controls are stable across plausible weights.
- The equation is a linear convex combination; it must not be described as exponential weighting.

## Manuscript-wide actions
1. Delete the fixed equation `RiskOverall = 0.10 × RCINT + 0.90 × RCEXT` from the validated framework description.
2. Remove statements that internal factors account for 10% and external factors for 90% of total risk.
3. Replace the single combined percentage with two explicitly named outputs:
   - `Internal-risk component`;
   - `External-risk component`.
4. Remove or relabel any application screenshot, figure, table, worked example, Results statement, Discussion statement, or Conclusion claim that presents the 10/90 result as an overall validated risk percentage.
5. Treat the `50.62%` value discussed under Comment 20 as an external body-region component, not as the final overall risk score.
6. Do not infer that one component is more important merely because it contains more variables.

## Approved Methods wording
`Internal and external risk components were calculated and reported separately. The study did not combine them into a single overall percentage because the available project records did not provide an empirically derived or prospectively specified weighting rule. This separation prevents an arbitrary weighting choice from determining the final risk ranking.`

## Approved Results wording
`The application output should distinguish the internal-risk and external-risk components. Any combined prototype display based on the former 0.10/0.90 rule is not interpreted as a validated overall risk estimate in the present study.`

## Future restoration rule
A combined score may be reintroduced only after:
- internal and external components are placed on a documented common scale;
- the decision purpose of the composite is prespecified;
- weights are elicited or estimated using a reproducible method;
- plausible alternatives are evaluated using sensitivity analysis;
- rank changes and risk-category changes are reported;
- the chosen rule is evaluated prospectively or on an independent validation set.

A generic parameterization may be used in future methodological work:

`P_overall(w) = w P_internal + (1-w) P_external`, where `0 ≤ w ≤ 1`.

This expression is not a fitted or validated equation in the current study.

## Resolution status
Comment 17 is finalized by removing the unsupported fixed weighting and reporting the two components separately. This decision constrains Comment 20: no numerical final composite can be reported from the current evidence.
