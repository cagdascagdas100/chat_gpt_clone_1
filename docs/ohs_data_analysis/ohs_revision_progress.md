# OHS Manuscript Revision Progress

## Overall status
- Total reviewer comments: 32
- Completed through: Comment 6
- Completion: 6/32 = 18.75%
- Next item: Comment 7

## Comment 1 — Abstract / LLM wording
- Status: Completed pending final consistency check
- Decision: Remove unsupported LLM-based scenario-generation claim from the Abstract.
- Literature: No new citation required because the sentence describes the authors' own method.
- Final manuscript wording uses verified machine-learning-based accident consequence modeling and risk-scenario prioritization terminology.

## Comment 2 — “interpretable risk coefficients”
- Status: Completed
- Decision: Replace the ambiguous phrase with the actual reported outputs: normalized internal, external, and overall risk percentages.
- Literature: No new citation required; this is an internal model-output description.

## Comment 3 — “risk coefficients that quantify individualized safety exposure”
- Status: Completed
- Decision: Replace nonstandard and potentially misleading terminology with established U.S.-journal wording focused on prediction of incident outcomes, including injury severity.
- Preferred revision:
  - Old: `generate risk coefficients that quantify individualized safety exposure`
  - New: `predict incident outcomes such as injury severity`
- Citation handling: Retain and reposition existing reference [2] to support the revised predictive-modeling statement.
- Terminology rule: Do not use “safety exposure” unless exposure frequency, duration, dose, or contact with a hazard is actually measured.

## Comment 4 — AR abbreviation
- Status: Completed
- Reviewer request: Remove the abbreviation `(AR)` and write the term in full.
- Existing sentence:
  - `At the same time, emerging digital technologies such as building information modeling (BIM), digital twin, augmented reality (AR), and virtual reality can be integrated into mobile platforms, enhancing interactive safety management capabilities [18,24].`
- Recommended revision:
  - `At the same time, emerging digital technologies such as building information modeling (BIM), digital twins, augmented reality, and virtual reality can be integrated into mobile platforms to support interactive safety management [18,24].`
- Red-highlighted replacement segment for the final workbook:
  - `digital twins, augmented reality, and virtual reality can be integrated into mobile platforms to support interactive safety management`
- Rationale:
  - The abbreviation is used only incidentally and does not improve readability.
  - `Digital twins` is preferred in the plural when referring to the technology category.
  - `To support interactive safety management` is more direct and idiomatic than the participial phrase `enhancing interactive safety management capabilities`.
- Literature: No new source required; existing references [18,24] remain attached to the technology-integration claim.
- Reviewer-response draft:
  - `Revised. The abbreviation “AR” was removed, and the term “augmented reality” is now written in full. The sentence was also streamlined for clarity while retaining the existing references.`

## Comment 5 — Vague BIM risk-management wording
- Status: Completed
- Reviewer comment: `Incorporate and manage risk factors böyle çok genel bir ifade`
- Selected wording:
  - `due to its capability to incorporate and manage risk factors`
- Problem identified:
  - `Incorporate and manage risk factors` does not specify what information BIM contains, how that information is used, or what decision process it supports.
  - `BIM is widely used` is a broad prevalence claim that is not necessary and is not established by reference [18] alone.
  - The claim that BIM reduces `time and cost losses` is too broad for the cited fall-risk application and should not be retained without direct quantitative evidence.
- Citation-specific evidence already present in the manuscript:
  - [18] supports BIM–augmented-reality visualization of fall hazards and corresponding preventive measures.
  - [19] supports BIM-based organization and retrieval of construction-safety records.
  - [27] supports linking BIM-defined hazard zones with real-time worker-location data for mobile safety monitoring.
- Recommended full replacement sentence:
  - `In mobile construction-safety applications, BIM provides a project-specific digital environment in which hazard locations, worker-location data, safety records, and preventive measures can be organized and visualized to support location-based safety decisions [18,19,27].`
- Red-highlighted replacement segment for the final workbook:
  - The entire revised sentence should be red because the original sentence is being replaced in full.
- Citation handling:
  - No new literature source is required.
  - Expand the citation from [18] to [18,19,27], because the revised synthesis combines the distinct BIM functions documented by the three studies already cited in the same subsection.
- American academic-language choices:
  - Use `construction-safety applications`, `project-specific digital environment`, `worker-location data`, `preventive measures`, and `location-based safety decisions`.
  - Avoid vague phrases such as `manage risk factors`, `improve performance`, and `reduce time and cost losses` unless the relevant outcomes were directly measured.
- Reviewer-response draft:
  - `Revised. The general statement that BIM can “incorporate and manage risk factors” was replaced with a specific description of the information handled in mobile BIM-based safety applications, including hazard locations, worker-location data, safety records, and preventive measures. The revised sentence also clarifies that these functions support location-based hazard visualization and safety decision-making. Existing references [18,19,27] were used; no new source was added.`
- Consistency note:
  - The following examples by Tariq et al. [19], Park et al. [27], and Aksu and Ofluoğlu [18] should remain because they provide the study-level evidence underlying the revised synthesis sentence.

## Comment 6 — Meaning of “multiple target formulations”
- Status: Completed
- Reviewer comment:
  - `Bu multiple target combination’dan kasıt nedir?`
- Exact selected wording in the manuscript:
  - `multiple target formulations`
- Interpretation based on the verified project outputs:
  - Model 01 uses the complete dataset, including zero-day cases, and retains categorized indemnity-payment-day values as the outcome.
  - Model 02 excludes zero-day cases and evaluates the remaining categorized indemnity-payment-day values.
  - Model 03 converts the outcome into four injury-severity classes: first aid, temporary incapacity, permanent incapacity, and fatality.
  - All three analyses use the same 14-predictor set, so the comparison changes the outcome definition rather than the predictors.
- Terminology decision:
  - Replace the vague phrase `multiple target formulations` with the standard and explicit phrase `three definitions of the outcome variable`.
  - Use `outcome variable` or `outcome definition` rather than `target combination`; the latter is not the actual design used in the study.
- Existing sentence:
  - `In contrast, this study deployed large-scale historical accident data and adopted a controlled comparative modeling framework, where multiple target formulations were evaluated using consistent feature sets.`
- Recommended full replacement sentence:
  - `In contrast, this study used a large historical accident dataset and a controlled comparative modeling framework to evaluate three definitions of the outcome variable using the same predictor set: categorized indemnity-payment days including zero-day cases, the corresponding categories after zero-day cases were excluded, and a four-level injury-severity outcome comprising first aid, temporary incapacity, permanent incapacity, and fatality.`
- Red-highlighted replacement segment for the final workbook:
  - The full revised sentence should be shown, with the following newly inserted explanatory segment in red: `three definitions of the outcome variable using the same predictor set: categorized indemnity-payment days including zero-day cases, the corresponding categories after zero-day cases were excluded, and a four-level injury-severity outcome comprising first aid, temporary incapacity, permanent incapacity, and fatality`
- Rationale:
  - The reviewer should not have to infer what the three models represent from their later labels.
  - `Definitions of the outcome variable` is standard U.S. academic terminology and directly describes what changed across the three analyses.
  - The revision separates the outcome definition from the predictor set and makes the controlled comparison transparent.
  - `Large historical accident dataset` is more idiomatic than `deployed large-scale historical accident data`.
- Literature and citation handling:
  - No new literature source is required because the sentence describes the authors' own analytical design.
  - Do not attach an external citation to the three outcome definitions unless the source is being cited only for the general comparative-modeling rationale.
- Internal evidence retained for the final workbook:
  - Risk_01: 64,999 records; zero-day cases included; 21 observed outcome categories; 14 predictors.
  - Risk_02: 13,570 records; zero-day cases excluded; 20 observed outcome categories; the same 14 predictors.
  - Risk_03: 64,999 records; four outcome classes; the same 14 predictors.
- Reviewer-response draft:
  - `Revised. The phrase “multiple target formulations” was replaced with an explicit description of the three outcome definitions evaluated in the comparative framework: categorized indemnity-payment days including zero-day cases, the corresponding categories after zero-day cases were excluded, and a four-level injury-severity outcome. The revised sentence also clarifies that the same predictor set was used across the three analyses.`
- Consistency note:
  - The same three definitions must be described consistently in Section 3.1.3, figure captions, tables, and the Results section.
  - Model labels F/E/A should not be finalized here because Comments 10 and 19 separately require a manuscript-wide naming standard.

## Workflow rule
- Continue one reviewer comment at a time.
- Preserve American academic English.
- Avoid invented or obsolete terminology.
- In the final workbook, show only the newly inserted or replaced wording in red within the complete revised sentence or paragraph.
- Deliver the consolidated workbook only after all comments are processed.