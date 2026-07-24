# Comment 25 — Rebuild Section 5.1 as a results-linked machine-learning discussion

## Reviewer comment
`Bu bölüm çok zayıf bir tartışma. Kaynaklar vb arttırılmalı ve sonuçlarla bağlantılı daha güzel tartışma yapılmalı. Figür 8 ile ilgili tartışılacak ek bir şey bulunmalı veya en yüksek performans gösteren modelde feature importance falan verilip en önemli parametreler tartışılmalı.`

## Editorial decision
Section 5.1 will be rewritten around the verified analytical outputs and directly linked to Figures 8–10. The original claims that tree ensembles `consistently outperformed` all alternatives, that Analysis 3 was uniformly the most robust, and that low ECE values confirmed practical validity are stronger than the available evidence and will be removed or qualified.

The reviewer request can be answered defensibly through a deeper interpretation of Figure 8. A new feature-importance result will not be invented because the supplied `Ozellik_Onemi` worksheets contain an `Önem_Skoru` column but no populated importance values, and no auditable permutation-importance or SHAP output is present.

## What Figure 8 actually represents
Figure 8 reports, for every feature–classifier pair, the highest AUROC observed across the three outcome analyses; the parenthetical label identifies the analysis that produced that maximum. It is therefore a post-selected, feature-wise discrimination map. It is not:

- a feature-importance plot from one multivariable final model;
- evidence of a causal relationship;
- a direct comparison of three analyses with the same target and class structure; or
- proof that one classifier is globally superior.

Because maxima are selected across different outcome definitions, Figure 8 should be interpreted descriptively and should not be used alone for model selection.

## Verified Figure 8 findings
The strongest feature-wise AUROC values are concentrated in a small number of variables:

- injury type reached `0.694` with Extremely Randomized Trees and Random Forest in Analysis 2;
- company accident history reached `0.661` with Extremely Randomized Trees, histogram-based gradient boosting, and Random Forest in Analysis 1;
- work area reached `0.595` in Analysis 1;
- the age–wage interaction reached `0.588` in Analysis 2;
- injury location reached `0.573` in Analysis 3;
- gender remained approximately non-discriminative (`0.502–0.504`).

These results do not support the sentence that one family of algorithms dominated every feature. Tree ensembles frequently appear among the leaders, but MLP, logistic regression, SVM, and KNN also lead or tie for particular feature–analysis combinations. The correct conclusion is model and feature dependence, not universal ensemble dominance.

## Critical prospective-validity issue
The strongest feature, injury type, and the related injury-location variable are determined after an accident has occurred. They can legitimately support retrospective payment-day or injury-severity classification, but they cannot support a pre-accident forecasting claim. The preprocessing manifest currently marks these variables as available before the accident even though its own descriptions identify them as accident outcomes; that access-table classification must be corrected.

This distinction is consistent with Baker et al. (2020), who explicitly noted that injury type, body part, and similar post-event variables are outcomes rather than valid pre-event predictors. If the application is intended for prospective prevention, model performance must be re-estimated using only information genuinely available before the event. Company accident history, work area, planned equipment, and worker characteristics are more plausible prospective inputs, subject to final provenance checks.

## Literature-linked interpretation
The frequent appearance of Random Forest, Extremely Randomized Trees, and boosting methods is broadly compatible with prior construction-safety studies, but cross-study metric values should not be compared as if they came from identical prediction tasks.

- Poh, Ubeynarayana, and Goh (2018) found Random Forest to be the best of five algorithms for a three-level construction-site safety indicator using pre-incident project and inspection variables (Automation in Construction 93, 375–386; DOI: 10.1016/j.autcon.2018.03.022).
- Kang and Ryu (2019) used Random Forest to classify construction accident types and reported model-based feature importance (Safety Science 120, 226–236; DOI: 10.1016/j.ssci.2019.06.034).
- Kang, Koo, and Ryu (2022) used permutation importance and LIME to study factors associated with lost-workday severity, demonstrating that interpretable importance requires a separately specified and validated procedure rather than reading importance from AUROC values (Journal of Building Engineering 53, 104534; DOI: 10.1016/j.jobe.2022.104534).
- Baker et al. (2020) separated pre-event attributes from safety outcomes and warned against treating post-accident variables as prospective predictors (Automation in Construction 118, 103146; DOI: 10.1016/j.autcon.2020.103146).

## Metrics and validation corrections
The analytical outputs identify class-support-weighted average precision as the primary selection metric. Section 5.1 must therefore discuss weighted and macro average precision first and use AUROC as a secondary discrimination summary. Figure 8 may remain as an exploratory AUROC visualization, but it must not override the prespecified primary metric.

Low ECE values should be described only as preliminary calibration evidence for the evaluated predictions. They do not by themselves establish external validity, decision benefit, or generalizability. Calibration discussion should be paired with Brier scores and reliability plots and should acknowledge that the current package contains no independent external validation cohort.

Similarly, lift-at-top-5% values describe concentration of observed outcomes within the highest-ranked predictions for a specified analysis; they do not prove that an intervention will prevent accidents. Claims about operational benefit require prospective impact evaluation.

## Preferred replacement for Section 5.1
`The results indicate that predictive performance depended more strongly on the selected feature and outcome definition than on a single universally superior classifier. In Figure 8, the highest feature-wise AUROC values were observed for injury type (up to 0.694) and company accident history (up to 0.661), whereas gender remained close to chance discrimination (approximately 0.50). Tree-based ensembles frequently achieved the leading or co-leading values, but neural-network, linear, instance-based, and margin-based classifiers also performed best for particular feature–analysis combinations. The findings therefore support comparison of complementary model classes rather than a general claim that one algorithm family dominated all settings.`

`The strong discrimination associated with injury type and injury location must be interpreted cautiously because these variables are observed after an accident. Their performance is relevant to retrospective classification of payment-day or injury-severity outcomes, but it does not establish pre-accident predictive capability. For prospective risk assessment, performance should be evaluated using only variables available before the event, such as verified worker, organizational, work-area, and planned-equipment information. This distinction is consistent with prior construction-safety research emphasizing the separation of pre-event attributes from accident outcomes.`

`The model-selection outputs used class-support-weighted average precision as the primary metric because the outcome classes were imbalanced; macro average precision was retained to reveal performance across less prevalent classes, while AUROC, F1 score, calibration, and lift were interpreted as complementary measures. The generally small calibration errors provide preliminary evidence that some fitted probabilities tracked observed frequencies within the evaluated data, but they do not replace external validation. Likewise, lift at the top 5% indicates concentration of recorded outcomes among high-ranked cases rather than demonstrated intervention effectiveness.`

`Prior studies have also reported useful performance from Random Forest and related ensemble methods in construction-safety classification, while interpretable studies have used formal permutation importance or local explanation methods to identify influential variables. In the present analysis, Figure 8 is not a feature-importance estimate, and the supplied importance-score tables are unpopulated. Accordingly, no ranking of multivariable feature importance is reported. If interpretability is added, it should be generated from a prespecified final multivariable model using out-of-fold permutation importance or SHAP values with uncertainty estimates and with post-event variables excluded from any prospective model.`

## Figure and table revisions
- Rename the Figure 8 caption to clarify that it shows feature–classifier AUROC maxima across analyses, not feature importance.
- Replace `Model F/E/A` with `Analysis 1/2/3` in all cell labels.
- Add a caption note that targets and class structures differ across analyses and that values are descriptive.
- Correct the preprocessing access table for injury type and injury location.
- Do not populate the manuscript with feature-importance claims until a reproducible importance analysis exists.

## Reviewer-response draft
`Revised. Section 5.1 was rebuilt to discuss the verified results directly and was expanded with construction-safety machine-learning literature. Figure 8 is now interpreted as a feature–classifier AUROC summary rather than feature importance. The revised discussion reports the strongest and weakest feature-wise discrimination, qualifies the frequent but non-universal performance of tree ensembles, prioritizes average precision as the prespecified selection metric, and distinguishes preliminary calibration from external validation. We also clarified that injury type and injury location are post-accident variables and therefore cannot substantiate prospective risk prediction. Because the supplied feature-importance tables contain no importance scores, no unsupported importance ranking was added; a reproducible out-of-fold permutation-importance or SHAP analysis is specified as the appropriate method if a multivariable interpretability analysis is later included.`

## Status
Finalized. The reviewer request is addressed through a results-linked Figure 8 discussion and literature comparison; feature importance is deliberately not fabricated.