# OHS Manuscript Revision Progress

## Overall status
- Total reviewer comments: 32
- Completed through: Comment 5
- Completion: 5/32 = 15.625%
- Next item: Comment 6

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

## Workflow rule
- Continue one reviewer comment at a time.
- Preserve American academic English.
- Avoid invented or obsolete terminology.
- In the final workbook, show only the newly inserted or replaced wording in red within the complete revised sentence or paragraph.
- Deliver the consolidated workbook only after all comments are processed.
