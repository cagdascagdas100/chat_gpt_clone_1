# Reassessment — Comment 11: define the reported precision–recall metric correctly

## Reviewer comment
`Açılımı?`

## Context and evidence
The project artifacts use machine-readable metric names such as `average_precision`, `average_precision_weighted`, and `average_precision_macro`, but several presentation layers label the same values as `AUPRC (weighted)` or `AUPRC (macro)`. The auditable files do not document a separate trapezoidal integration of a precision–recall curve. Therefore, the presentation label `AUPRC` is not sufficiently supported and may misstate the implemented metric.

## Final editorial decision
The manuscript will use **class-support-weighted average precision (weighted AP)** as the primary metric name. The abbreviation will be introduced at first use as:

`class-support-weighted average precision (weighted AP)`

Where a class-balanced summary is also reported, it will be named:

`macro-average precision (macro AP)`

The terms `AUPRC`, `PR-AUC`, and `area under the precision–recall curve` will be removed unless the underlying analysis code is later shown to calculate curve area explicitly with a documented interpolation/integration rule.

## Technical definition to use
For each outcome class, a one-versus-rest average-precision value is obtained from the class-specific precision–recall sequence. The weighted summary is the support-weighted mean of the class-specific AP values:

`weighted AP = Σ_c (n_c / N) AP_c`

where `AP_c` is the average precision for class `c`, `n_c` is the number of observations in class `c`, and `N` is the total number of observations. The macro summary, when shown, is:

`macro AP = (1/C) Σ_c AP_c`

where `C` is the number of outcome classes.

The manuscript will not describe weighted AP as accuracy, calibration, probability correctness, or a direct estimate of accident risk.

## Why this correction is necessary
- `Average precision` and trapezoidal precision–recall curve area are related but not interchangeable metric names.
- The machine-readable project keys support AP terminology, whereas `AUPRC` appears only as a reporting label.
- Weighted AP gives greater influence to common classes and can therefore appear relatively high even when rare-class discrimination is weak.
- Macro AP gives each class equal weight and is needed as a complementary view of minority-class performance.
- A majority-class dummy classifier can have a non-zero weighted AP because the score depends on class prevalence and support weighting; its value must therefore be reported as a reference baseline rather than interpreted as useful discrimination.

## Approved Methods wording
`Model discrimination was assessed primarily using class-support-weighted average precision (weighted AP), calculated as the support-weighted mean of the one-versus-rest average-precision values across outcome classes. Macro-average precision (macro AP), which assigns equal weight to each class, was reported as a complementary measure of performance across minority and majority classes. Higher values indicate better precision–recall ranking performance; neither metric measures calibration or absolute accident probability.`

## Approved Results wording
`Performance values are reported as weighted AP and macro AP. Because weighted AP is influenced by class prevalence, the selected classifier is interpreted relative to both the macro AP result and the majority-class dummy baseline rather than from the weighted value alone.`

## Recommended reviewer response
`Thank you for noting that the abbreviation was not defined. We reviewed the machine-readable analysis outputs and found that the implemented and stored metric is average precision, reported as support-weighted and macro averages across classes. We therefore replaced the unsupported label “AUPRC” with “class-support-weighted average precision (weighted AP)” and defined it at first use. Macro-average precision (macro AP) is also reported to provide a class-balanced view. The revised text clarifies that these metrics summarize precision–recall ranking performance and do not measure calibration or absolute accident risk.`

## Turkish explanation for the tracking workbook
`Kısaltma ilk kullanımda “class-support-weighted average precision (weighted AP)” olarak açılmıştır. Proje YAML ve rapor dosyalarında makine tarafından kullanılan metrik adları average_precision, average_precision_weighted ve average_precision_macro şeklindedir; buna karşılık AUPRC ifadesi yalnızca bazı sunum etiketlerinde yer almaktadır. Eğri alanının trapezoidal veya başka bir yöntemle ayrıca hesaplandığını gösteren doğrulanabilir kod kaydı bulunmadığından AUPRC/PR-AUC terminolojisi kaldırılmıştır. Weighted AP sık görülen sınıflara daha fazla ağırlık verdiği için macro AP ve DummyMajority baseline ile birlikte yorumlanacaktır. AP değerleri kalibrasyon, doğruluk veya mutlak kaza olasılığı olarak sunulmayacaktır.`

## Required manuscript-wide audit
- Replace `AUPRC (weighted)` with `weighted AP`.
- Replace `AUPRC (macro)` with `macro AP`.
- Rename table and spreadsheet-facing labels where publication-facing output is regenerated.
- Define both averaging rules in Methods.
- Report DummyMajority values in the same metric for context.
- Interpret weighted and macro results together.
- Keep AP separate from AUROC, F1, accuracy, Brier score, and ECE.
- Do not use AP as evidence of application-level validity or field effectiveness.

## Status
Fully finalized. The available artifacts are sufficient to correct the abbreviation, metric name, definition, and interpretation without inventing a new calculation.