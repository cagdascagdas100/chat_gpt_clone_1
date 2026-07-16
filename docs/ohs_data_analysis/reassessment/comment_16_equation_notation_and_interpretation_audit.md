# Reassessment — Comment 16: define every symbol and repair the equation system

## Reviewer comment
`Her formulden sonra where … diye bu notasyonalrın ne demek olduğu yazılmalı.`

## Final editorial decision
The reviewer is correct, but the required revision is broader than adding a short `where ...` clause. The manuscript currently contains sixteen numbered equations, several undefined quantities, a malformed injury-type subscript, repeated symbols with different meanings, and equations that support claims already rejected elsewhere in the reassessment. The mathematically defensible solution is therefore to:

1. remove equations whose inputs, provenance, or interpretation are unsupported;
2. retain only equations that correspond to an auditable analytical operation;
3. replace the ambiguous `RC` coefficient notation with score/component notation;
4. define every symbol immediately after first use;
5. state the source, scale, direction, unit of analysis, and permissible interpretation of every derived value;
6. prevent the same symbol from representing different concepts.

Adding definitions to an invalid or unsupported formula would make the presentation look clearer without making the method valid. Equation retention must therefore precede notation repair.

## Audit of the current numbered equations

### Equation 1 — feasibility-adjusted frequency
Current structure:
`F* = λF + (1 − λ)μ_F`

The equation depends on an LLM-derived feasibility value `G` and an undocumented segmented mapping from `G` to `λ`. No auditable prompt protocol, mapping function, model record, or runtime implementation is available. In addition, Comment 12 removes the implemented-LLM claim. Equation 1 and the associated feasibility-adjustment narrative will therefore be deleted unless the original code and complete mapping are supplied.

### Equations 2–8 — category and component scores
These equations can be retained only after complete renaming and definition. The current `RC` label is misleading because the quantities are not estimated regression coefficients. Equations 3–7 also contain a malformed injury-type subscript that renders as `RC¿` in the publication-facing PDF.

The revised notation will use:
- `s_c`: severity score for category `c`;
- `f_c`: frequency score derived from observed records for category `c`;
- `q_c`: category-specific combined score;
- `WA`: work area;
- `OM`: operated machine;
- `IR`: injury region;
- `IT`: injury type.

For a category with both severity and frequency information:

`q_c = sqrt(s_c f_c),  c ∈ {WA, IR, IT}`

For the operated-machine category, where no defensible exposure-frequency denominator is available:

`q_OM = s_OM`

The component calculations will then be written as:

`q_context = sqrt(q_WA q_OM)`

`q_scenario = sqrt(q_IR q_IT)`

`q_ext = sqrt(q_context q_scenario)`

Immediately after these equations, the manuscript must state:
- what source records produce each severity and frequency score;
- whether the score is based on counts, proportions, ranks, or another transformation;
- the exact numerical range of each input and output;
- whether all inputs were placed on a common scale before geometric aggregation;
- that larger values indicate greater relative severity, frequency, or scenario priority;
- that the values are dimensionless scores, not probabilities, causal effects, exposure rates, or validated personal-risk percentages;
- the unit represented by each output: selected work area, selected machine category, injury-region category, injury-type category, or equipment–malfunction scenario.

The geometric mean may be retained only if its inputs are non-negative and measured on a common or explicitly normalized scale. If the source scores are on different scales, the normalization mapping must be shown before aggregation.

### Equation 9 — 0.10/0.90 internal–external composite
The equation combining the internal and external components with fixed weights of 0.10 and 0.90 will be deleted. Comment 17 establishes that these weights have no documented empirical, expert-elicitation, legal, or validation basis. The internal and external components will be reported separately rather than hidden inside one overall percentage.

### Equations 10–12 — rank weights and overall regional composite
The current notation incorrectly uses `j` both as an anatomical-region index and as a rank position, hard-codes a sum over five terms, and uses `α` for rank decay even though `α` is later reused as the CVaR confidence level.

If within-region exponential rank aggregation is retained, the only approved notation is:

`w_(r,k) = λ^(k−1) / Σ_(h=1)^(K_r) λ^(h−1)`

`B_r = Σ_(k=1)^(K_r) w_(r,k) x_(r,k)`

where:
- `r` identifies the body region;
- `k` is the descending rank within region `r`;
- `K_r` is the number of retained values in that region;
- `x_(r,k)` is the `k`th ranked value in region `r`;
- `λ`, with `0 < λ ≤ 1`, is the rank-decay parameter;
- `w_(r,k)` is the normalized weight and the weights sum to one within each region;
- `B_r` is the region-specific aggregated score.

The manuscript must report each `B_r` separately. The equations that combine all regions into one `Risk_Overall` value will be deleted in accordance with Comments 18 and 20. A region-specific aggregated score must not be called a probability or an overall risk percentage unless an explicit validated transformation to a 0–100 probability scale exists.

### Equations 13–14 — indemnity expected-value and CVaR quantities
The present equations introduce `cost_i`, `p_i`, `p_any`, `EV_add`, `EV_single`, `CVaR_α`, and `Score_α`, but the verified modeling target is `ODEME_GUNSAYISI`, not an independently documented indemnity-payment event or monetary loss variable. The manuscript also reports that summed candidate probabilities frequently exceed one, which prevents the sum from being interpreted automatically as the expected cost of one mutually exclusive event.

These equations will be removed from the main analytical narrative unless an auditable derivation establishes:
- the event represented by each probability;
- how `p_i` and `p_any` were estimated and calibrated;
- whether candidate events are mutually exclusive, independent, or overlapping;
- the monetary or day unit of `cost_i`;
- the sample and time horizon to which the quantities refer;
- the exact CVaR estimator and tail distribution;
- the decision rule linking these quantities to application output.

If such evidence is later supplied, the confidence level must use a separate symbol such as `τ`, not `α`, to avoid collision with the rank-decay parameter. An overlapping-event sum may be described as an additive impact score, but not as a conventional expected value without the required event structure.

### Equations 15–16 — outpatient and inpatient allowance formulas
These equations may remain only if an authoritative legal source verifies the formulas, their jurisdiction, effective period, and scope. The text must define:
- `ADE`: average daily earnings in currency per day;
- the formula output: daily allowance amount in the same currency;
- the distinction between outpatient and inpatient treatment;
- the legal source and applicable date.

If these conditions cannot be met, the equations should be removed because they are not part of the verified machine-learning analysis and could create an unsupported legal or financial claim.

## Non-equation notation that also requires correction
Mathematical quantities embedded in prose must follow the same rule. The manuscript currently uses terms such as `F2_85`, `Recall_85`, `MAE_ref`, `ρ_severity`, and `ρ_support` without a complete operational definition. Each must either be defined with its formula, threshold, reference data, range, and interpretation or removed. A metric name alone is not a definition.

## Locked notation rules for implementation
- Use one symbol for one concept throughout the manuscript.
- Use `λ` only for rank decay; use a different symbol for any confidence level.
- Use `r` for body region and `k` for within-region rank.
- Use roman descriptive subscripts (`WA`, `OM`, `IR`, `IT`, `context`, `scenario`, `ext`) consistently.
- Do not use `RC`, `coefficient`, `Risk_Overall`, or percentage labels for dimensionless derived scores.
- Do not call record-count frequency an exposure rate.
- Define index sets and summation limits explicitly.
- State whether missing values, zero values, and ties are possible and how they are handled.
- Place every displayed equation on its own line with one equation number and an immediate explanatory paragraph.
- Recheck equations after DOCX-to-PDF rendering so subscripts, radicals, multiplication symbols, and Greek letters display correctly.

## Required post-equation template
Every retained equation will be followed by a paragraph covering all six items:

`where [symbols and indices] are defined; the inputs are derived from [source]; the quantity is calculated on [unit of analysis]; its range is [range]; larger values indicate [direction]; and the output is interpreted as [score/probability/rate/amount], not as [excluded interpretations].`

This template is a content requirement, not a sentence that must be copied mechanically.

## Approved reviewer response
`Thank you for this observation. We conducted a complete audit of all numbered equations rather than adding isolated symbol definitions. Unsupported equations were removed, including the undocumented feasibility adjustment, the fixed 0.10/0.90 internal–external composite, and the across-region overall-risk aggregation. The remaining score equations were rewritten with consistent notation, the malformed injury-type subscript was corrected, and every symbol, index, source variable, scale, direction, unit of analysis, and interpretation is now defined immediately after the relevant equation. We also separated the rank-decay parameter from the CVaR confidence-level notation and ensured that derived scores are not presented as probabilities, exposure rates, causal effects, or validated personal-risk percentages.`

## Turkish explanation for the tracking workbook
`Yalnızca formüllerin altına kısa sembol açıklamaları eklemek yeterli görülmemiştir. Makaledeki 16 numaralı denklem bütünüyle denetlenmiş; dayanağı olmayan formüllerin çıkarılmasına, korunacak denklemlerde “risk coefficient” yerine açık skor/bileşen adları kullanılmasına ve her sembol için kaynak, ölçek, yön, analiz birimi ve yorum sınırının yazılmasına karar verilmiştir. 0,10/0,90 bileşik formülü ile bölgeler arası tek toplam risk denklemleri kaldırılacak; bölgesel skorlar ayrı raporlanacaktır. Aynı sembolün farklı anlamlarda kullanılması, j indeksinin hem bölge hem sıra olarak tanımlanması ve injury-type alt indisinin bozuk görünmesi düzeltilecektir.`

## Status
Fully finalized as an editorial and mathematical specification. During manuscript integration, every retained formula must be checked against the original computation artifacts; a formula without reproducible inputs or an auditable calculation path will be removed rather than completed by assumption.