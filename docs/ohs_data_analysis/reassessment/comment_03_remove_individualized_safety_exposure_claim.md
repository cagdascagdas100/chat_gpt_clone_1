# Reassessment — Comment 3: remove the unsupported `individualized safety exposure` claim

## Reviewer comment
`Yani “risk coefficients” ve “bireysel güvenlik maruziyetini sayısallaştırma” gibi ifadeleri çok mu düşündün ☺️`

## Anchored manuscript wording
`By leveraging historical accident records and structured preprocessing pipelines, ML algorithms can learn predictive patterns and generate risk coefficients that quantify individualized safety exposure.`

## Final editorial decision
The selected sentence will not be retained. Both `risk coefficients` and `individualized safety exposure` imply a type of measurement that the available data and analyses do not establish.

The revised text will describe the actual analytical task: supervised classification of accident-related payment-day and injury-severity outcomes among recorded construction-accident cases. It will not claim that the models estimate an individual worker's hazard exposure, absolute accident probability, or prospective personal risk.

## Why the original claim is not defensible
### 1. The target is an accident outcome, not exposure
The auditable Risk 01, Risk 02, and Risk 03 artifacts identify `ODEME_GUNSAYISI` as the target variable. The analyses concern payment-day categories and a four-category injury-severity formulation. No variable named or operationalized as `individualized safety exposure` is present.

### 2. Accident-case records cannot, by themselves, estimate absolute accident risk
The supplied analytical datasets consist of recorded accident cases. They do not provide a documented denominator such as worker-hours, task-hours, machine operating time, number of exposed workers, or person-time at risk. They also do not provide a prospectively sampled non-accident comparison population. Consequently, the analyses can characterize or classify outcomes within recorded cases, but they cannot estimate the absolute probability that a particular worker will experience an accident.

### 3. `Exposure` has a different methodological meaning
In occupational-risk analysis, exposure ordinarily requires an explicitly measured or assigned contact with a hazard, including its presence, intensity, frequency, or duration. Worker characteristics, work-area labels, machine categories, and recorded injury attributes are not automatically exposure measurements. Calling their model output `individualized safety exposure` therefore conflates predictors, context, and outcomes.

### 4. Some predictors are not prospectively available
The analytical feature sets include variables such as injury type and injury location. These may be informative for retrospective outcome classification after an accident has occurred, but they cannot support a pre-accident individual-risk claim because the information is not available before the event. This limitation must remain aligned with the leakage and prospective-use safeguards under Comment 25.

### 5. `Risk coefficient` remains technically ambiguous
As finalized under Comment 2, the project outputs must be named according to their actual role: classifier probabilities, category-specific severity/frequency scores, separately reported application components, or scenario-priority scores. None should be represented as a regression coefficient, causal effect, exposure metric, or externally validated personal-risk probability.

## Approved replacement for the selected sentence
`Using structured historical accident records, supervised machine-learning models were evaluated for classifying accident-related payment-day and injury-severity outcomes among recorded construction-accident cases.`

This is the most concise defensible replacement because it identifies:
- the data source;
- the analytical method;
- the verified outcomes;
- the case-based unit of analysis;
- and no unsupported individual-exposure or absolute-risk interpretation.

## Stronger two-sentence version for the Introduction
`Using structured historical accident records, supervised machine-learning models were evaluated for classifying accident-related payment-day and injury-severity outcomes among recorded construction-accident cases. Because the available data do not include person-time or task-level exposure denominators and an independently sampled non-accident population, these analyses do not estimate an individual worker's absolute accident probability or hazard exposure.`

The two-sentence version is recommended when space permits because it prevents readers from converting retrospective outcome classification into a prospective personal-risk claim.

## Recommended revision of the surrounding Introduction passage
`In response, data-driven safety-management approaches have received increasing attention. When applied to structured historical accident records, supervised machine-learning methods can identify multivariable patterns associated with recorded occupational-injury outcomes. In the present study, these methods were evaluated for classifying accident-related payment-day and injury-severity categories among recorded construction-accident cases. The analyses do not quantify an individual worker's hazard exposure or absolute probability of experiencing an accident.`

## Consequence for the study-purpose paragraph
The later Introduction paragraph must also be revised because it currently refers to `personalized risk coefficients`, `continuously incorporates real-time data`, `individualized risk assessments`, and an `overall risk percentage`. A defensible replacement is:

`This study presents OSH-RA as a mobile occupational-safety decision-support application for workers and safety personnel. The application collects structured worker, work-context, equipment, and observed machine-condition information and presents outputs from offline-trained classifiers together with prespecified calculation and scenario-ranking rules. The analytical evaluation concerns recorded payment-day and injury-severity outcomes and does not establish continuous real-time monitoring or an individual's absolute accident probability.`

## Recommended reviewer response
`Thank you for this observation. We agree that the expressions “risk coefficients” and “individualized safety exposure” were insufficiently defined and overstated what can be inferred from the available data. The analytical datasets comprise recorded accident cases, and the verified targets are accident-related payment-day and injury-severity categories. Because the study does not include person-time or task-level exposure denominators or an independently sampled non-accident population, it cannot estimate an individual worker's absolute accident probability or hazard exposure. We therefore deleted the original wording and replaced it with: “Using structured historical accident records, supervised machine-learning models were evaluated for classifying accident-related payment-day and injury-severity outcomes among recorded construction-accident cases.” We also removed corresponding claims of personalized risk coefficients, continuously updated individual risk, and real-time exposure quantification from the Introduction and aligned the terminology throughout the manuscript.`

## Turkish explanation for the tracking workbook
`“Risk coefficients that quantify individualized safety exposure” ifadesi kaldırılmıştır. Proje çıktılarında hedef değişken ODEME_GUNSAYISI olup analizler ödeme-günü kategorileri ve dört sınıflı yaralanma şiddeti sonuçlarını sınıflandırmaktadır. Veri seti kayıtlı kaza vakalarından oluşmakta; çalışan-saat, görev-saat, makine kullanım süresi, maruz kalan çalışan sayısı veya kişi-zaman gibi maruziyet paydaları ile bağımsız biçimde örneklenmiş kazasız bir karşılaştırma grubu içermemektedir. Bu nedenle çalışma, bir çalışanın mutlak kaza olasılığını veya bireysel tehlike maruziyetini sayısallaştırdığı iddiasında bulunamaz. Yeni cümle yalnızca doğrulanmış analitik görevi tanımlar: kayıtlı inşaat kazası vakalarında ödeme-günü ve yaralanma şiddeti sonuçlarının denetimli makine öğrenmesiyle sınıflandırılması. Aynı gerekçeyle Introduction bölümündeki kişiselleştirilmiş risk katsayısı, sürekli güncelleme, gerçek zamanlı değerlendirme ve tekil genel risk yüzdesi ifadeleri de çıkarılacaktır.`

## Manuscript-wide consistency actions
- Delete `individualized safety exposure`, `personal safety exposure`, and equivalent formulations unless an explicit exposure variable and denominator are documented.
- Replace `personalized risk coefficient` with the exact model output or application component, or delete it when no valid replacement exists.
- Use `classification of recorded accident outcomes` rather than `prediction of individual accident risk` for the current analytical evidence.
- State `among recorded accident cases` wherever needed to make the conditional scope clear.
- Keep post-event variables such as injury type and injury location from being described as prospectively available predictors.
- Remove `continuous`, `real-time`, and `adaptive` individual-risk language from the present-system description.
- Align this decision with Comments 2, 8, 9, 25, 27, and 32.

## Citation decision
No new external citation is required for the replacement sentence because it describes the study's own audited data and analytical target. Existing citations may remain only for surrounding literature claims that they directly support. No citation should be used to convert the current case-only analysis into an absolute individual-risk or exposure estimate.

## Status
Fully finalized. The reviewer can be answered without additional data by narrowing the claim to classification of recorded accident outcomes and explicitly removing the unsupported exposure and absolute-risk interpretation.