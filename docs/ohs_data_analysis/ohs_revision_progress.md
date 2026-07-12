# OHS Manuscript Revision Progress

## Overall status
- Total reviewer comments: 32
- Completed through: Comment 8
- Completion: 8/32 = 25.0%
- Next item: Comment 9

## Quality re-audit of Comments 1–7
- Comments 1–5 remain methodologically defensible after another review.
- Comment 1 remains provisionally complete because the manuscript still contains LLM claims outside the Abstract; final wording depends on verified scenario-generation provenance.
- Comment 2 remains unchanged: the Abstract should report concrete outputs rather than the vague phrase `interpretable risk coefficients`.
- Comment 3 remains best expressed as `predict occupational injury outcomes, including injury severity`; do not use `safety exposure` unless exposure itself is measured.
- Comment 4 remains unchanged; `augmented reality` should be written in full because the abbreviation is not reused meaningfully.
- Comment 5 remains unchanged; the BIM sentence should describe specific information flows and decision-support functions rather than `manage risk factors`.
- Comment 6 is strengthened by Comment 8: continue using the neutral term `recorded payment-day outcome` rather than DAFW until source-level equivalence is demonstrated.
- Comment 7 remains unchanged in model scope and rationale; its phrase `within each outcome encoding` is consistent with the clarified target-variable treatment in Comment 8.
- Model 01 contains 18 observed nonzero-frequency outcome categories, including the zero-day category.
- Model 02 contains 17 observed positive-day categories after zero-day cases are excluded.
- Model 03 contains four observed injury-severity classes.
- Earlier references to 21 and 20 observed categories reflected the encoded label space rather than categories represented by nonzero observations and must not be used in the manuscript.

## Comment 1 — Abstract / LLM wording
- Status: Completed pending final consistency check
- Decision: Remove the unsupported LLM-based scenario-generation claim from the Abstract.
- Literature: No new citation required because the sentence describes the authors' own method.
- Final manuscript wording should use verified machine-learning-based accident-consequence modeling and risk-scenario prioritization terminology.
- Final audit note: retain no sentence that indirectly implies automated LLM generation, such as `simulates high-priority accident sequences`, unless the runtime implementation is verified.

## Comment 2 — “interpretable risk coefficients”
- Status: Completed
- Decision: Replace the ambiguous phrase with the actual reported outputs: normalized internal, external, and overall risk percentages.
- Literature: No new citation required; this is an internal model-output description.
- Final audit note: use `risk percentages` only where the manuscript has already defined the normalization procedure and scale.

## Comment 3 — “risk coefficients that quantify individualized safety exposure”
- Status: Completed
- Decision: Replace nonstandard and potentially misleading terminology with established U.S.-journal wording focused on prediction of occupational injury outcomes.
- Preferred revision:
  - Old: `generate risk coefficients that quantify individualized safety exposure`
  - New: `predict occupational injury outcomes, including injury severity`
- Citation handling: Retain and reposition existing reference [2] to support the revised predictive-modeling statement.
- Terminology rule: Do not use `safety exposure` unless exposure frequency, duration, dose, or contact with a hazard is actually measured.

## Comment 4 — AR abbreviation
- Status: Completed
- Reviewer request: Remove the abbreviation `(AR)` and write the term in full.
- Existing sentence:
  - `At the same time, emerging digital technologies such as building information modeling (BIM), digital twin, augmented reality (AR), and virtual reality can be integrated into mobile platforms, enhancing interactive safety management capabilities [18,24].`
- Recommended revision:
  - `At the same time, emerging digital technologies such as building information modeling (BIM), digital twins, augmented reality, and virtual reality can be integrated into mobile platforms to support interactive safety management [18,24].`
- Red-highlighted replacement segment for the final workbook:
  - `digital twins, augmented reality, and virtual reality can be integrated into mobile platforms to support interactive safety management`
- Literature: No new source required; existing references [18,24] remain attached to the technology-integration claim.
- Reviewer-response draft:
  - `Revised. The abbreviation “AR” was removed, and the term “augmented reality” is now written in full. The sentence was also streamlined for clarity while retaining the existing references.`

## Comment 5 — Vague BIM risk-management wording
- Status: Completed
- Reviewer comment: `Incorporate and manage risk factors böyle çok genel bir ifade`
- Selected wording:
  - `due to its capability to incorporate and manage risk factors`
- Recommended full replacement sentence:
  - `In mobile construction-safety applications, BIM provides a project-specific digital environment in which hazard locations, worker-location data, safety records, and preventive measures can be organized and visualized to support location-based safety decisions [18,19,27].`
- Red-highlighted replacement segment for the final workbook:
  - The entire revised sentence should be red because the original sentence is being replaced in full.
- Citation handling:
  - No new literature source is required.
  - Expand the citation from [18] to [18,19,27], because the revised synthesis combines the distinct BIM functions documented by the three studies already cited in the subsection.
- Reviewer-response draft:
  - `Revised. The general statement that BIM can “incorporate and manage risk factors” was replaced with a specific description of the information handled in mobile BIM-based safety applications, including hazard locations, worker-location data, safety records, and preventive measures. The revised sentence also clarifies that these functions support location-based hazard visualization and safety decision-making. Existing references [18,19,27] were used; no new source was added.`

## Comment 6 — Meaning of “multiple target formulations”
- Status: Completed after quality re-audit
- Reviewer comment:
  - `Bu multiple target combination’dan kasıt nedir?`
- Exact selected wording:
  - `multiple target formulations`
- Verified analytical design:
  - Model 01 uses the complete 64,999-record dataset and the observed categories of the recorded payment-day outcome, including zero-day cases; 18 categories have nonzero observations.
  - Model 02 excludes zero-day cases and uses the remaining 13,570 records; 17 positive-day categories have nonzero observations.
  - Model 03 uses the complete 64,999-record dataset and converts the outcome into four classes: first aid, temporary incapacity, permanent incapacity, and fatality.
  - The same 14 predictors are used across all three analyses.
- Terminology decision:
  - Replace `multiple target formulations` with `three prespecified encodings of the outcome variable`.
  - Avoid `target combination`, which does not describe the implemented design.
- Corrected recommended sentence:
  - `In contrast, this study used a large historical accident dataset and a controlled comparative modeling framework to evaluate three prespecified encodings of the recorded payment-day outcome using the same predictor set: the observed categories including zero-day cases, the corresponding positive-day categories after zero-day cases were excluded, and a four-level injury-severity classification comprising first aid, temporary incapacity, permanent incapacity, and fatality.`
- Red-highlighted replacement segment for the final workbook:
  - `three prespecified encodings of the recorded payment-day outcome using the same predictor set: the observed categories including zero-day cases, the corresponding positive-day categories after zero-day cases were excluded, and a four-level injury-severity classification comprising first aid, temporary incapacity, permanent incapacity, and fatality`
- Literature: No new source required because this sentence describes the authors' analytical design.
- Reviewer-response draft:
  - `Revised. The phrase “multiple target formulations” was replaced with an explicit description of the three prespecified outcome encodings evaluated using the same predictor set: the observed payment-day categories including zero-day cases, the corresponding positive-day categories after zero-day cases were excluded, and a four-level injury-severity classification.`

## Comment 7 — Algorithms evaluated and reasons for their selection
- Status: Completed, with a critical cross-validation consistency flag
- Reviewer comment:
  - `Sadece bu üç yöntem mi kullanıldı? Eğer öyleyse neden bu üçü, birer ikişer cümleyle bu yöntemlerin seçimlerinin sebeplerini verelim.`
- Exact selected wording:
  - `Adaboost, extremly randomized trees (ERT), and GBDT`
- Verified model portfolio from all three result workbooks:
  - Random Forest
  - Extremely Randomized Trees (Extra Trees)
  - Gradient Boosting Decision Trees (GBDT)
  - Histogram-Based Gradient Boosting
  - AdaBoost
  - Logistic Regression
  - Support Vector Machine (SVM)
  - k-Nearest Neighbors (k-NN)
  - Multilayer Perceptron (MLP)
  - A majority-class classifier was also evaluated as a noninformative baseline and should not be described as a substantive candidate model.
- Main correction:
  - The manuscript is incorrect in implying that only three algorithms were evaluated.
  - Use `Extremely Randomized Trees (Extra Trees)`, not the misspelled `Extremly Randomized Trees` and not the uncommon abbreviation `ERT`.
  - Use `AdaBoost`, not `Adaboost`.
- Selection rationale:
  - Tree-based bagging and boosting models were included to capture nonlinear effects and higher-order interactions in mixed tabular predictors without imposing a single linear functional form.
  - Logistic regression provides a regularized linear benchmark.
  - Support vector machines provide a margin-based benchmark capable of representing nonlinear decision boundaries through kernels.
  - k-nearest neighbors provides a local, instance-based benchmark.
  - The multilayer perceptron provides a flexible neural-network benchmark.
  - The portfolio therefore compares complementary inductive biases under a common preprocessing and evaluation protocol rather than selecting algorithms arbitrarily.
- Preferred full replacement paragraph:
  - `Nine supervised classifiers were evaluated within a common preprocessing and repeated cross-validation framework: random forest, extremely randomized trees (Extra Trees), gradient boosting decision trees, histogram-based gradient boosting, AdaBoost, logistic regression, support vector machines, k-nearest neighbors, and multilayer perceptrons. A majority-class classifier was included as a noninformative baseline. The candidate set was selected to compare complementary model classes: tree ensembles for nonlinear effects and feature interactions, logistic regression as a regularized linear benchmark, support vector machines as a margin-based benchmark, k-nearest neighbors as an instance-based benchmark, and multilayer perceptrons as a flexible neural-network benchmark. Within each outcome encoding, all candidates were trained using identical preprocessing steps and the same cross-validation splits. Model selection was based primarily on the weighted area under the precision–recall curve (AUPRC), while AUROC, F1 score, calibration, and training time were retained as secondary evaluation criteria.`
- Red-highlighted replacement treatment for the final workbook:
  - The entire paragraph should be red because the original algorithm sentence and the adjacent model-selection statement are both materially inaccurate.
- Citation handling:
  - Existing references [57] and [79] can support the use of comparative ML portfolios in construction and occupational-accident prediction.
  - No new literature source is strictly necessary for the reviewer response.
  - A software citation to Pedregosa et al. (2011) may be added later if the journal requires citation of the scikit-learn implementation.
- Critical method consistency finding:
  - The manuscript currently states `stratified 5-fold cross-validation with optional repeats`.
  - The generated Markdown summaries report repeated two-fold evaluation for Models 01 and 02 and group-aware two-fold evaluation for Model 03, whereas parts of the YAML runtime metadata list five splits.
  - The generated quality checks also flag the cross-validation configuration as inconsistent.
  - Therefore, the phrase `stratified 5-fold cross-validation` must not be retained until the implementation, YAML metadata, and report summaries are reconciled.
  - The final manuscript should either report the exact verified protocol or the models should be rerun under the intended stratified five-fold design.
- Model-selection consistency finding:
  - The manuscript currently says that the model with the highest AUROC was selected.
  - The generated result summaries identify weighted AUPRC as the primary selection metric and retain AUROC, F1, calibration, and training time as supporting criteria.
  - The revised paragraph therefore uses weighted AUPRC as the primary metric.
- Reviewer-response draft:
  - `Revised. The original sentence listed only three algorithms, although nine supervised classifiers were evaluated. The Methods section now reports the complete candidate set and explains that the portfolio was designed to compare complementary tree-based, linear, margin-based, instance-based, and neural-network model classes under the same preprocessing and cross-validation splits. A majority-class classifier is also identified as a noninformative baseline. Algorithm names and capitalization were standardized, and the model-selection criterion was aligned with the generated results.`

## Comment 8 — Definition and validity of DAFW
- Status: Completed with a manuscript-wide terminology safeguard
- Reviewer comment:
  - `Bu nedir?`
- Exact selected wording:
  - `DAFW`
- Original sentence:
  - `The model with the highest area under the receiver operating characteristic (AUROC) curve score was chosen, with DAFW as the target variable, reflecting the injury severity of workers involved in an occupational accident.`
- Core finding:
  - In U.S. occupational-injury recordkeeping, DAFW conventionally means `days away from work`.
  - OSHA 29 CFR 1904.7(b)(3) defines this as the number of calendar days an employee is unable to work because of a work-related injury or illness, beginning the day after the event and including weekends, holidays, and other nonworkdays when the employee would have remained unable to work.
  - The verified project artifacts do not document the target field as this OSHA calendar-day construct.
  - The implemented target is the administrative field `ODEME_GUNSAYISI`, represented in Models 01 and 02 as categorized payment-day outcomes and recoded in Model 03 into four injury-severity classes.
  - Model 03 includes fatality and permanent-incapacity classes, so `DAFW as the target variable` cannot accurately describe all three analyses.
- Terminology decision:
  - Do not use DAFW as a synonym for `ODEME_GUNSAYISI` unless the source-data dictionary explicitly verifies that the field records calendar days away from work.
  - In the modeling section, introduce the field by its verified administrative meaning rather than assigning an unverified U.S. recordkeeping label.
  - Use `recorded payment-day outcome` as the neutral manuscript term until the exact institutional definition is documented.
- Preferred full replacement text:
  - `The outcome variable was derived from the recorded payment-day field (ODEME_GUNSAYISI) in the administrative accident data. In the first two analyses, this field was represented as categorized payment-day outcomes with and without zero-day cases; in the third analysis, it was recoded into four injury-severity classes: first aid, temporary incapacity, permanent incapacity, and fatality.`
- Red-highlighted replacement treatment for the final workbook:
  - The full two-sentence replacement should be red because the original sentence incorrectly identifies both the outcome name and the model-selection criterion.
- Citation handling:
  - No new citation is required for the internal field definition; the authoritative source is the study data dictionary or administrative metadata.
  - If the authors later verify that `ODEME_GUNSAYISI` is identical to calendar days away from work, DAFW may be introduced as `days away from work (DAFW)` and supported with the applicable official recordkeeping definition.
  - An OSHA citation should not be used to relabel Turkish social-insurance payment days as DAFW without demonstrated equivalence.
- Manuscript-wide consistency consequences:
  - The subsection title `Days Away from Work (DAFW) and indemnity benefit probability` must be reconsidered.
  - Unless equivalence is verified, use a title such as `Payment-day severity and indemnity-benefit probability`.
  - `Indemnity cost expressed in DAFW days` is dimensionally incorrect: days represent a duration or severity proxy, whereas monetary cost must be reported in currency after the documented wage/benefit conversion.
  - Replace `DAFW severity` with `payment-day severity` unless source-level validation supports DAFW.
  - Never expand DAFW as `Damage and Financial Waiver`; that expansion is incorrect and must not appear in any manuscript version.
- Reviewer-response draft:
  - `Revised. DAFW was not sufficiently defined and did not precisely match the administrative outcome field used in the analyses. The Methods section now introduces the recorded payment-day field (ODEME_GUNSAYISI) at its first occurrence and explains how it was encoded in the three analyses. The term DAFW is reserved for documented calendar days away from work and is not used as a synonym for benefit-payment days without source-level verification.`
- Link to Comment 9:
  - Comment 9 is partly anticipated by this change because the outcome is now introduced at its first occurrence; Comment 9 will separately determine the optimal placement and wording of the formal definition.

## Workflow rule
- Continue one reviewer comment at a time.
- Re-audit earlier decisions whenever new project evidence exposes an inconsistency.
- Preserve American academic English.
- Avoid invented, obsolete, or implementation-inconsistent terminology.
- In the final workbook, show only the newly inserted or replaced wording in red within the complete revised sentence or paragraph.
- Deliver the consolidated workbook only after all comments are processed.
