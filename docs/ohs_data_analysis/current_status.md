# OHS Manuscript Revision — Current Status

- Total reviewer comments: 32
- Processed through: Comment 25
- Processed: 25/32 = 78.125%
- Fully finalized: 18/32 = 56.25%
- Conditional items: Comment 12 (scenario provenance), Comment 15 (authoritative equipment inventory), Comment 17 (internal–external weighting), Comment 18 (regional-decay value selection), Comment 20 (final composite depends on Comment 17 and the missing fifth-region input), Comment 23 (original high-resolution landing-page and personal-input screenshots), and Comment 24 (meaning of `yz`)
- Next item: Comment 26

## Latest decision — Comment 25
Section 5.1 will be rebuilt around verified model outputs and relevant construction-safety machine-learning literature. Figure 8 will be interpreted as a post-selected feature–classifier AUROC summary across three different outcome analyses, not as feature importance and not as evidence that one classifier family is universally superior.

## Verified results to discuss
- Injury type has the highest feature-wise AUROC (`0.694`), followed by company accident history (`0.661`).
- Work area reaches `0.595`, the age–wage interaction `0.588`, and injury location `0.573`.
- Gender remains close to chance (`0.502–0.504`).
- Tree ensembles frequently lead or tie, but MLP, logistic regression, SVM, and KNN also lead particular feature–analysis combinations; the original `consistently outperformed` claim is too broad.

## Critical methodological correction
- Injury type and injury location are post-accident outcomes. Their discrimination supports retrospective payment-day or severity classification, not prospective accident forecasting.
- The preprocessing manifest incorrectly marks these variables as available before the accident despite describing them as accident outcomes; the access table must be corrected.
- Any prospective application must be re-evaluated using only variables genuinely available before the event.

## Feature-importance decision
- The supplied `Ozellik_Onemi` worksheets contain an `Önem_Skoru` field but no populated scores.
- No auditable SHAP or permutation-importance output is available.
- No feature-importance ranking will be fabricated. If interpretability is added, it must use a prespecified multivariable model, out-of-fold permutation importance or SHAP, uncertainty estimates, and a leakage-safe feature set.

## Metrics and discussion safeguards
- Weighted and macro average precision should lead the discussion because weighted AP is the verified primary selection metric; AUROC is secondary.
- Low ECE values are preliminary calibration evidence, not proof of external validity or practical effectiveness.
- Lift at the top 5% describes concentration within ranked predictions, not demonstrated accident prevention.
- Figure 8, Figure 9, and Figure 10 interpretations must follow the Analysis 1/2/3 naming and cross-analysis comparability restrictions established in Comments 11 and 19.

## Literature integrated
The revised discussion will use the supplied literature package, including Poh et al. (2018), Kang and Ryu (2019), Baker et al. (2020), and Kang et al. (2022), to distinguish ensemble performance, prospective predictors, post-event outcomes, and formal feature-importance methods.

## Next item
Comment 26 — remove the repetitive Fine–Kinney framing and revise the contribution discussion so the manuscript does not repeatedly position the study against the same method.