# Comment 27 — Define the application system and remove unsupported accuracy/flexibility claims

## Reviewer comment
`Çok ezbere yazılmış. Uygulama modeli sistemi ne öncelikle? Ayrıca daha doğru risk değerlendirmesi yaptığına dair bir veri var mı elimizde validation yaptın mı ki?`

## Selected sentence
`By utilizing multimodal data, the application provides more accurate and flexible risk assessments compared to studies which were limited to audio and visual data [121].`

## Decision
The sentence will be removed. The available evidence does not support the claims that the application is multimodal, more accurate, or more flexible than prior systems.

## What the application system actually is
The term `application model` is ambiguous because it conflates the fitted statistical models with the mobile software layer. The manuscript should instead use `OSH-RA mobile decision-support application` or `application architecture`.

The OSH-RA application is a software integration layer that operationalizes several already-defined analytical components:
1. offline-trained classifiers and derived coefficients from the three prespecified outcome analyses;
2. deterministic normalization and internal–external aggregation rules;
3. scenario scoring, ranking, and body-region aggregation procedures;
4. presentation of prioritized scenarios, preventive measures, legal-information content, and payment-day/cost-related fields.

The verified application inputs are structured categorical, numerical, and binary entries concerning worker characteristics, work areas, equipment or malfunction selections, and historical site information. The available project artifacts do not document runtime ingestion or inference from images, video, or audio.

## Validation audit
- The analytical artifacts document internal resampling/cross-validation, classifier comparison, discrimination metrics, and calibration summaries.
- The preprocessing manifests contain empty `final_holdout_report` objects.
- No independent external test cohort, prospective validation, head-to-head comparison with another application, usability study, adaptability test, or field-effectiveness analysis is available.
- The manuscript itself states that quantitative pilot results remain under evaluation; that statement cannot support a completed superiority claim.
- Internal classifier-level performance does not establish application-level accuracy, usability, flexibility, or safety impact.

## Why `more accurate` is unsupported
A comparative accuracy claim would require:
- the same target definition;
- the same evaluation population or an appropriately harmonized benchmark;
- a prespecified metric;
- a common test set or statistically valid comparative design;
- uncertainty estimates and a documented significance or noninferiority/superiority criterion.

None of these conditions is demonstrated for the cited comparison. Weighted and macro average precision, AUROC, F1, Brier score, and ECE from the internal analytical pipeline cannot be used to claim that the mobile application is more accurate than unrelated published systems evaluated on different tasks and datasets.

## Why `more flexible` is unsupported
`Flexibility` is not defined or measured. It could refer to input variety, configurability, adaptability to new hazards, cross-site portability, user customization, or software interoperability. The available artifacts provide no prespecified flexibility criterion or comparative test. The manuscript may describe concrete capabilities, such as accepting several structured input domains or permitting multiple work-area selections, but it must not convert those capabilities into an unmeasured superiority claim.

## Citation audit
Reference `[121]` concerns ChatGPT-assisted extraction of causal factors from crane-accident text reports followed by complex-network analysis. It is not an audio-and-visual-only risk-assessment system and therefore does not support the comparison made in the selected sentence.

References `[119]` and `[120]` concern multimodal large-language-model safety-inspection or report-generation workflows. Those studies do not establish that OSH-RA itself is multimodal, and they cannot be used as direct accuracy benchmarks without a common task and evaluation design.

## Preferred manuscript wording
`The OSH-RA mobile application is a decision-support interface that operationalizes the study's prespecified analytical pipeline. Users enter structured worker, work-environment, and equipment-related information; the application applies the selected offline-trained classifiers and deterministic normalization, aggregation, and ranking rules; and it displays component-level risk estimates, prioritized scenarios, body-region outputs, preventive measures, legal information, and cost-related fields. The present evaluation characterizes model discrimination and calibration under the reported internal resampling design. It does not establish superior application-level accuracy, flexibility, usability, or effectiveness relative to existing systems.`

## Shorter alternative
`The mobile application integrates structured user and worksite inputs with the study's offline-trained classifiers and deterministic risk-aggregation procedures to present decision-support outputs. Comparative application-level accuracy, flexibility, usability, and effectiveness were not evaluated in the present study.`

## Manuscript-wide consistency actions
- Replace `application model` with `mobile decision-support application` or `application architecture` when referring to the software system.
- Reserve `model` for a specified fitted classifier, aggregation function, or statistical formulation.
- Remove claims of real-time adaptation, continuous learning, multimodal operation, and universal superiority unless implementation and validation evidence is supplied.
- Do not infer prospective safety effectiveness from retrospective classifier metrics.
- Align the description with Comments 12, 17, 20, 25, and 26.

## Reviewer-response draft
`Revised. We now define OSH-RA as a mobile decision-support application that integrates structured worker, work-environment, and equipment inputs with offline-trained classifiers and deterministic aggregation and ranking procedures. We removed the claims that the application is multimodal, more accurate, or more flexible than existing systems because no common-task comparative validation, external test cohort, or application-level usability/effectiveness study was available. The revised text reports only the capabilities and internal model-evaluation evidence supported by the project records.`

## Status
Finalized. The unsupported superiority statement is removed and the application system is defined using evidence-bounded terminology.