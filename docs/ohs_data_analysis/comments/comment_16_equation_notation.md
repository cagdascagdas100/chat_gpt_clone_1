# Comment 16 — Define all symbols after every equation

## Reviewer comment
`Her formulden sonra where … diye bu notasyonalrın ne demek olduğu yazılmalı.`

## Selected manuscript location
The comment is anchored to Equation (2), but the wording clearly applies to every displayed equation in the Methods section.

## Final editorial decision
Each equation must be followed immediately by a concise `where ...` statement that defines every symbol introduced in that equation. Symbols already defined in the immediately preceding equation may be referenced without repeating the full definition, but no new symbol may appear without an explicit definition.

A single notation system must be used throughout the manuscript. Concatenated forms such as `RCSWA` and `RCFWA` should be replaced with structured subscripts, for example `RC_{S,WA}` and `RC_{F,WA}`.

## Standard risk-coefficient notation
- `RC`: risk coefficient.
- `S`: severity component.
- `F`: frequency component.
- `WA`: work area.
- `OM`: operated machine.
- `IR`: injury region.
- `IT`: injury type.
- `IF`: inherent-factor aggregate.
- `SF`: scenario-factor aggregate.
- `EXT`: external-risk aggregate.
- `INT`: internal-risk aggregate.

Do not assign a numerical range, unit, or dimensionless status to any coefficient unless that property is explicitly documented by the normalization procedure.

## Equation-specific wording

### Equation (1)
`F* = λF + (1 − λ)μ_F`

Preferred definition:
`where F* is the credibility-adjusted frequency for a candidate scenario, F is the original scenario-frequency value, λ is the credibility weight derived from the feasibility input, and μ_F is the mean frequency across the nine candidate scenarios for the same equipment–malfunction pair.`

Consistency warning: the surrounding text currently states that feasibility was excluded from the final analysis while Equation (1) still uses a feasibility-derived weight. That contradiction must be resolved before final submission.

### Equation (2)
`RC_{OM} = RC_{S,OM}`

Preferred definition:
`where RC_{OM} is the operated-machine risk coefficient and RC_{S,OM} is its severity component. A frequency component is not included because the administrative data do not provide a machine-specific exposure denominator.`

### Equations (3)–(5)
`RC_{WA} = sqrt(RC_{S,WA} × RC_{F,WA})`

`RC_{IR} = sqrt(RC_{S,IR} × RC_{F,IR})`

`RC_{IT} = sqrt(RC_{S,IT} × RC_{F,IT})`

Preferred definitions:
- After Equation (3): `where RC_{WA} is the work-area risk coefficient, RC_{S,WA} is the work-area severity component, and RC_{F,WA} is the work-area frequency component.`
- After Equation (4): `where RC_{IR} is the injury-region risk coefficient, RC_{S,IR} is the injury-region severity component, and RC_{F,IR} is the injury-region frequency component.`
- After Equation (5): `where RC_{IT} is the injury-type risk coefficient, RC_{S,IT} is the injury-type severity component, and RC_{F,IT} is the injury-type frequency component.`

The square-root signs must remain visible because these equations use geometric means; plain-text exports that reduce them to simple products are mathematically incorrect.

### Equations (6)–(8)
`RC_{IF} = sqrt(RC_{WA} × RC_{OM})`

`RC_{SF} = sqrt(RC_{IR} × RC_{IT})`

`RC_{EXT} = sqrt(RC_{IF} × RC_{SF})`

Preferred definitions:
- After Equation (6): `where RC_{IF} is the inherent-factor aggregate, RC_{WA} is the work-area risk coefficient, and RC_{OM} is the operated-machine risk coefficient.`
- After Equation (7): `where RC_{SF} is the scenario-factor aggregate, RC_{IR} is the injury-region risk coefficient, and RC_{IT} is the injury-type risk coefficient.`
- After Equation (8): `where RC_{EXT} is the external-risk aggregate, RC_{IF} is the inherent-factor aggregate, and RC_{SF} is the scenario-factor aggregate.`

### Equation (9)
`R_IE = 0.10 RC_{INT} + 0.90 RC_{EXT}`

Preferred definition:
`where R_IE is the internal–external composite risk score, RC_{INT} is the internal-risk coefficient, and RC_{EXT} is the external-risk coefficient. The coefficients 0.10 and 0.90 are the assigned internal and external weights, respectively.`

Do not retain `RiskOverall` for Equation (9) because Equation (12) currently uses the same symbol for a different body-region aggregation. The justification for the 0.10/0.90 weighting is handled separately in Comment 17.

### Equations (10)–(12)
Use a distinct decay parameter `γ` rather than `α`, because `α` is also used later as the CVaR confidence level.

`v_j ∝ γ^{j−1}`

`sum_{j=1}^{5} v_j = 1`

`R_BP = sum_{j=1}^{5} v_j BPRP_j`

Preferred definitions:
- After Equation (10): `where j indexes the five anatomical regions, v_j is the unnormalized weight assigned to region j, and γ is the regional rank-decay parameter.`
- After Equation (11): `where the five regional weights are normalized to sum to one.`
- After Equation (12): `where R_BP is the body-region-aggregated risk score, BPRP_j is the body-parts risk percentage for region j, and v_j is the corresponding normalized regional weight.`

The relationship between `R_IE` and `R_BP` must be stated explicitly before either is called the final overall risk percentage.

### Equations (13)–(14)
`EV_add = sum_i C_i p_i`

`EV_single = p_any E[C | payment]`

`Score_α = CVaR_α(C) × p_any, α ∈ [0.90, 0.95]`

Preferred definition:
`where i indexes the candidate scenarios, C_i is the scenario-specific compensation-cost quantity, p_i is its estimated payment probability, p_any is the probability of at least one payment, E[C | payment] is the expected compensation cost conditional on payment, CVaR_α(C) is the conditional value at risk of compensation cost at confidence level α, and Score_α is the probability-scaled tail-cost score.`

Terminology safeguard: if the modeled quantity is measured in recorded payment days rather than currency, use a separate symbol such as `D_i` and call it a payment-day severity proxy. Do not label a duration as monetary cost.

### Equations (15)–(16)
`Outpatient allowance = ADE × 2/3`

`Inpatient allowance = ADE × 1/2`

Preferred definitions:
- After Equation (15): `where ADE is average daily earnings and 2/3 is the outpatient allowance rate.`
- After Equation (16): `where ADE is average daily earnings and 1/2 is the inpatient allowance rate.`

The fractions must be typeset explicitly. They must not appear as the ambiguous strings `23` and `12` in exported text.

## Major notation conflicts identified
1. `RiskOverall` is currently used for two different mathematical constructions in Equations (9) and (12). Use separate symbols until their relationship is formally defined.
2. `α` is currently used both for the regional decay parameter and for the CVaR confidence level. Use `γ` for regional decay and reserve `α` for CVaR.
3. Payment-day severity and monetary compensation cost are currently conflated. Use different symbols and units.
4. Feasibility is described as excluded but is still used through `λ` in Equation (1). The method text and equation must agree.
5. Every summation must display its index and limits; every radical and fraction must remain visible in the final Word and PDF versions.

## Preferred reviewer response
`Revised. Each displayed equation is now followed by a “where ...” statement defining every newly introduced symbol. The notation was standardized using structured subscripts, and ambiguous concatenated labels were removed. We also corrected several cross-equation conflicts: the two distinct overall-risk constructions now use different symbols, the regional decay parameter is distinguished from the CVaR confidence level, and duration-based payment-day quantities are separated from monetary cost variables. Radicals, summation limits, and fractional allowance rates were retained explicitly to prevent ambiguity in exported versions.`

## Status
Completed as a notation and consistency audit. Final manuscript implementation remains linked to Comments 17 and 18 for the weighting rationale and regional-decay parameter explanation.