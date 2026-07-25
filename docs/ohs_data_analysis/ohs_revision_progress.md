# OHS Manuscript Revision Progress

## Overall status
- Total reviewer comments: 32
- Completed through: Comment 9
- Completion: 9/32 = 28.125%
- Next item: Comment 10

## Global revision rules
- Preserve American academic English.
- Use established occupational-safety and machine-learning terminology.
- Do not introduce abbreviations that are not reused or not operationally verified.
- Re-audit earlier decisions whenever later evidence reveals a terminology or implementation inconsistency.
- In the final workbook, show only newly inserted or replaced wording in red within the complete revised sentence or paragraph.
- Deliver the consolidated workbook only after all reviewer comments have been processed.

## Quality re-audit after Comment 9
- Comments 1–5 remain methodologically defensible.
- Comment 1 remains provisionally complete because manuscript-wide LLM claims still require a final consistency pass.
- Comment 3 remains best expressed as `predict occupational injury outcomes, including injury severity`.
- Comment 6 must continue to use the neutral phrase `recorded payment-day outcome` rather than DAFW.
- Comment 7 remains valid in model scope and algorithm rationale, but the cross-validation description still requires implementation-level reconciliation.
- Comments 8 and 9 jointly establish that `ODEME_GUNSAYISI` must be introduced by its verified dataset role and must not be relabeled as DAFW without source-level equivalence.
- Model 01 contains 18 observed nonzero-frequency outcome categories, including the zero-day category.
- Model 02 contains 17 observed positive-day categories after zero-day cases are excluded.
- Model 03 contains four observed injury-severity classes.
- Earlier references to 21 and 20 observed categories reflected the encoded label space rather than categories represented by nonzero observations and must not be used in the manuscript.

## Comment 1 — Abstract / LLM wording
- Status: Completed pending final consistency check
- Decision: Remove the unsupported LLM-based scenario-generation claim from the Abstract.
- Literature: No new citation is required because the sentence describes the authors' own method.
- Final wording should use verified machine-learning-based accident-consequence modeling and risk-scenario prioritization terminology.
- Do not retain wording that indirectly implies automated LLM generation unless the runtime implementation is verified.

## Comment 2 — “interpretable risk coefficients”
- Status: Completed
- Decision: Replace the ambiguous phrase with the concrete outputs reported by the framework: normalized internal, external, and overall risk percentages.
- Literature: No new citation is required because this is an internal model-output description.
- Safeguard: Use `risk percentages` only where the normalization procedure and scale are defined.

## Comment 3 — “risk coefficients that quantify individualized safety exposure”
- Status: Completed
- Old wording: `generate risk coefficients that quantify individualized safety exposure`
- Preferred wording: `predict occupational injury outcomes, including injury severity`
- Citation handling: Retain and reposition existing reference [2].
- Terminology rule: Do not use `safety exposure` unless exposure frequency, duration, dose, or contact with a hazard is actually measured.

## Comment 4 — AR abbreviation
- Status: Completed
- Recommended sentence:
  - `At the same time, emerging digital technologies such as building information modeling (BIM), digital twins, augmented reality, and virtual reality can be integrated into mobile platforms to support interactive safety management [18,24].`
- Literature: Retain existing references [18,24].
- Reviewer-response draft:
  - `Revised. The abbreviation “AR” was removed, and the term “augmented reality” is now written in full. The sentence was also streamlined for clarity while retaining the existing references.`

## Comment 5 — Vague BIM risk-management wording
- Status: Completed
- Selected wording: `due to its capability to incorporate and manage risk factors`
- Recommended sentence:
  - `In mobile construction-safety applications, BIM provides a project-specific digital environment in which hazard locations, worker-location data, safety records, and preventive measures can be organized and visualized to support location-based safety decisions [18,19,27].`
- Literature: No new source is required; use existing references [18,19,27].
- Red-highlight treatment: The entire revised sentence should be red because the original sentence is replaced in full.

## Comment 6 — Meaning of “multiple target formulations”
- Status: Completed after quality re-audit
- Exact selected wording: `multiple target formulations`
- Verified design:
  - Model 01 uses the complete 64,999-record dataset and retains the observed categories of the recorded payment-day outcome, including zero-day cases; 18 categories have nonzero observations.
  - Model 02 excludes zero-day cases and uses 13,570 records; 17 positive-day categories have nonzero observations.
  - Model 03 uses the complete 64,999-record dataset and recodes the outcome into four classes: first aid, temporary incapacity, permanent incapacity, and fatality.
  - The same 14 predictors are used across all three analyses.
- Preferred terminology: `three prespecified encodings of the outcome variable`.
- Corrected sentence:
  - `In contrast, this study used a large historical accident dataset and a controlled comparative modeling framework to evaluate three prespecified encodings of the recorded payment-day outcome using the same predictor set: the observed categories including zero-day cases, the corresponding positive-day categories after zero-day cases were excluded, and a four-level injury-severity classification comprising first aid, temporary incapacity, permanent incapacity, and fatality.`
- Literature: No new source is required because the sentence describes the authors' own analytical design.

## Comment 7 — Algorithms evaluated and reasons for their selection
- Status: Completed, with a cross-validation consistency flag
- Verified candidate classifiers:
  - Random Forest
  - Extremely Randomized Trees (Extra Trees)
  - Gradient Boosting Decision Trees
  - Histogram-Based Gradient Boosting
  - AdaBoost
  - Logistic Regression
  - Support Vector Machine
  - k-Nearest Neighbors
  - Multilayer Perceptron
  - A majority-class classifier was evaluated only as a noninformative baseline.
- Naming corrections:
  - Use `AdaBoost`, not `Adaboost`.
  - Use `Extremely Randomized Trees (Extra Trees)`, not `Extremly Randomized Trees` or `ERT`.
- Selection rationale:
  - Tree ensembles represent nonlinear effects and interactions.
  - Logistic regression provides a regularized linear benchmark.
  - Support vector machines provide a margin-based benchmark.
  - k-nearest neighbors provides an instance-based benchmark.
  - Multilayer perceptrons provide a neural-network benchmark.
- Preferred replacement paragraph:
  - `Nine supervised classifiers were evaluated within a common preprocessing and repeated cross-validation framework: random forest, extremely randomized trees (Extra Trees), gradient boosting decision trees, histogram-based gradient boosting, AdaBoost, logistic regression, support vector machines, k-nearest neighbors, and multilayer perceptrons. A majority-class classifier was included as a noninformative baseline. The candidate set was selected to compare complementary model classes: tree ensembles for nonlinear effects and feature interactions, logistic regression as a regularized linear benchmark, support vector machines as a margin-based benchmark, k-nearest neighbors as an instance-based benchmark, and multilayer perceptrons as a flexible neural-network benchmark. Within each outcome encoding, all candidates were trained using identical preprocessing steps and the same cross-validation splits. Model selection was based primarily on the weighted area under the precision–recall curve (AUPRC), while AUROC, F1 score, calibration, and training time were retained as secondary evaluation criteria.`
- Critical consistency issue:
  - The manuscript states stratified five-fold cross-validation.
  - Generated summaries and YAML metadata contain conflicting two-fold and five-fold descriptions.
  - The final manuscript must report only the protocol verified from the implementation or the models must be rerun under the intended design.

## Comment 8 — Definition and validity of DAFW
- Status: Completed with a manuscript-wide terminology safeguard
- Original sentence:
  - `The model with the highest area under the receiver operating characteristic (AUROC) curve score was chosen, with DAFW as the target variable, reflecting the injury severity of workers involved in an occupational accident.`
- Core finding:
  - In U.S. occupational-injury recordkeeping, DAFW conventionally means `days away from work`.
  - The verified project artifacts do not document `ODEME_GUNSAYISI` as the OSHA calendar-day construct.
  - Models 01 and 02 use categorized values of `ODEME_GUNSAYISI`; Model 03 recodes the field into four injury-severity classes.
- Decision:
  - Do not use DAFW as a synonym for `ODEME_GUNSAYISI` unless the source-data dictionary verifies equivalence.
  - Use `recorded payment-day outcome` as the neutral term.
  - Never expand DAFW as `Damage and Financial Waiver`; that expansion is incorrect.
- Preferred replacement:
  - `The outcome variable was derived from the recorded payment-day field (ODEME_GUNSAYISI) in the administrative accident data. In the first two analyses, this field was represented as categorized payment-day outcomes with and without zero-day cases; in the third analysis, it was recoded into four injury-severity classes: first aid, temporary incapacity, permanent incapacity, and fatality.`
- Manuscript-wide consequence:
  - Reconsider the subsection title `Days Away from Work (DAFW) and indemnity benefit probability`.
  - Unless equivalence is verified, use `Payment-day severity and indemnity-benefit probability`.
  - Do not describe a duration measure as monetary cost; cost must be reported in currency after a documented conversion.

## Comment 9 — Introduce the outcome term at its first occurrence
- Status: Completed and integrated with Comment 8
- Reviewer concern:
  - The abbreviation/term appears without a proper first-use definition and without a clear connection to the actual dataset variable.
- Main decision:
  - Do not solve the issue by merely expanding DAFW at first use, because the available project evidence does not establish that the modeled field is days away from work.
  - Introduce the verified source field `ODEME_GUNSAYISI` immediately before the three model variants are described.
  - Define its manuscript role as the `recorded payment-day outcome` and explain all three encodings at that point.
  - State explicitly that the field is not labeled DAFW because the available metadata do not establish equivalence with calendar days away from work.
- Preferred first-use paragraph:
  - `Before model training, the administrative outcome field ODEME_GUNSAYISI was defined as the recorded payment-day outcome. Model 01 retained all observed categories, including zero-day cases; Model 02 used the corresponding positive-day categories after excluding zero-day cases; and Model 03 recoded the field into four injury-severity classes—first aid, temporary incapacity, permanent incapacity, and fatality. The field is not described as days away from work (DAFW), because the available source metadata do not establish equivalence with the calendar-day definition used in occupational-injury recordkeeping.`
- Placement:
  - Insert this paragraph in Section 3.1.3 immediately after the dataset/outcome description and before algorithm training, cross-validation, or model-label discussion.
  - Subsequent references should use `recorded payment-day outcome`, `payment-day categories`, or `injury-severity classes`, depending on the specific analysis.
- Red-highlight treatment for the final workbook:
  - The full inserted paragraph should be red because it adds the missing operational definition and replaces the unsupported DAFW label.
- Citation handling:
  - No new literature citation is required for the internal field definition.
  - The authoritative evidence should be the data dictionary or administrative metadata.
  - An official DAFW citation is appropriate only if a separate, genuinely measured days-away-from-work variable is introduced and its calculation is documented.
- Reviewer-response draft:
  - `Revised. The outcome field is now introduced at its first occurrence using its verified dataset name and operational role. The Methods section identifies ODEME_GUNSAYISI as the recorded payment-day outcome and explains its three encodings before model training is described. Because the available source metadata do not establish equivalence with calendar days away from work, DAFW is not used as a label for this variable.`
- Consistency consequence:
  - Comments 6, 8, and 9 must be implemented together so that the outcome definition, model descriptions, subsection headings, tables, figure captions, and Results section use the same terminology.
