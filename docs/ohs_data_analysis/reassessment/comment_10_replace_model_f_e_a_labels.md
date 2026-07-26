# Reassessment — Comment 10: replace `Model F/E/A` with analysis-based nomenclature

## Reviewer comment
`Neden modeller F, E, A şeklinde de A, B, C şeklinde değil?`

## Final editorial decision
The labels `Model F`, `Model E`, and `Model A` will be retired from the manuscript. They are non-sequential, unexplained, and technically misleading because each outcome formulation was evaluated with multiple candidate classifiers rather than represented by one unique fitted model.

The manuscript will use the following stable nomenclature throughout:

- **Analysis 1 — all-record, 18-class payment-day classification**;
- **Analysis 2 — positive-payment-day, 17-class classification**;
- **Analysis 3 — four-class grouped payment-day classification**.

The replacement will be `Analysis 1/2/3`, not `Model A/B/C`. Alphabetic model labels would remain semantically empty and would continue to blur the distinction between an analytical task, an algorithm family, a fitted estimator, and a selected final configuration.

## Locked mapping
| Retired label | Final label | Dataset rule | Outcome structure |
|---|---|---|---|
| Model F | Analysis 1 | all 64,999 records; zero-day records retained | 18 observed payment-day classes, including zero days |
| Model E | Analysis 2 | zero-day records excluded; 13,570 records retained | 17 positive payment-day classes |
| Model A | Analysis 3 | all 64,999 records retained | four project-defined grouped classes derived from `ODEME_GUNSAYISI` |

This mapping will be applied only after checking the corresponding table, figure, and result block against the recorded sample size and class structure. A bare letter will never be converted by visual position alone when the underlying analysis cannot be verified.

## Naming hierarchy
The revised manuscript will distinguish the following levels:

1. **Analysis** — the dataset inclusion rule and target-class formulation;
2. **Classifier** — logistic regression, support vector machine, k-nearest neighbors, multilayer perceptron, random forest, extremely randomized trees, AdaBoost, gradient boosting decision trees, or histogram-based gradient boosting;
3. **Configuration** — preprocessing, imbalance-handling, hyperparameter, and validation settings applied to a classifier within an analysis;
4. **Selected configuration** — the highest-ranked configuration under the prespecified primary metric within that analysis;
5. **Application output** — any downstream score, regional value, or scenario-priority result, which must not be called a machine-learning model.

Accordingly, phrases such as `Model 1 achieved...` will be replaced by precise constructions such as:

- `Within Analysis 1, the highest weighted average-precision value was obtained by [classifier/configuration].`
- `The selected configuration for Analysis 2 was [classifier/configuration].`
- `Performance results for Analysis 3 are presented in Figure X.`

A selected classifier will not be renamed `Analysis 1`; the analysis and the winning classifier remain separate concepts.

## Approved Methods wording
`Three separate outcome-classification analyses were defined from ODEME_GUNSAYISI. Analysis 1 retained all 64,999 records and used 18 observed payment-day classes, including the zero-day class. Analysis 2 excluded zero-day records and used 17 positive payment-day classes among 13,570 cases. Analysis 3 retained all 64,999 records and recoded the same source field into four project-defined grouped classes. Each analysis compared the same candidate classifier families under its recorded preprocessing and evaluation procedure.`

## Required manuscript-wide audit
The following elements must be checked and corrected:

- section headings and subheadings;
- narrative references in Methods, Results, Discussion, Limitations, and Conclusion;
- table titles, column headings, row labels, footnotes, and cross-references;
- figure titles, panel labels, legends, axis labels, embedded annotations, and captions;
- equations and subscripts if any analysis letter is used;
- supplementary-material labels and appendix cross-references;
- interface screenshots that display Model F/E/A;
- filenames used for final publication exports.

Raw evidence files and original computational artifacts may retain their historical filenames for provenance. They will not be silently renamed in the audit trail; instead, the manuscript-facing label and the legacy source identifier will be mapped explicitly in the revision record.

## Figure and table rule
Figures or tables comparing the three tasks should use the order `Analysis 1`, `Analysis 2`, `Analysis 3`, matching the Methods presentation. When space permits, the first occurrence in each figure or table will include a short descriptor:

- `Analysis 1 (18 classes; zero day retained)`;
- `Analysis 2 (17 positive classes; zero day excluded)`;
- `Analysis 3 (four grouped classes)`.

Thereafter, the abbreviated forms `Analysis 1`, `Analysis 2`, and `Analysis 3` may be used. Colors, panel letters, and plotting order must not redefine the analytical mapping.

## Reporting safeguards
- Do not call the three analyses `three models`.
- Do not use `A`, `B`, and `C` as replacements merely to make the labels sequential.
- Do not imply that the three analyses share identical record counts, class structures, or cross-validation settings.
- Do not compare raw metric values across analyses without acknowledging their different class definitions and sample compositions.
- Do not use the analysis number as the name of a classifier.
- Do not preserve `F`, `E`, or `A` in captions as unexplained legacy labels.

## Recommended reviewer response
`Thank you for identifying this inconsistency. We agree that the labels Model F, Model E, and Model A were unexplained and difficult to follow. We did not replace them with Model A, Model B, and Model C because each label refers to a distinct outcome-classification analysis in which multiple classifiers were compared, rather than to a single fitted model. We therefore adopted the clearer labels Analysis 1, Analysis 2, and Analysis 3 and defined each at first use by its record-inclusion rule and class structure. The revised nomenclature has been applied consistently to the text, tables, figures, captions, legends, equations, and cross-references.`

## Turkish explanation for the tracking workbook
`Model F/E/A adları hem sıralı olmadığı hem de her birinin tek bir makine öğrenmesi modelini temsil ettiği izlenimini verdiği için kaldırılmıştır. Bunların yerine A/B/C kullanılması da kavramsal sorunu çözmeyecektir; çünkü her veri-hedef kurgusunda dokuz sınıflandırıcı karşılaştırılmıştır. Bu nedenle nihai adlandırma Analysis 1, Analysis 2 ve Analysis 3 olarak belirlenmiştir. Analysis 1 sıfır-gün sınıfı dâhil 64.999 kayıt ve 18 sınıfı; Analysis 2 sıfır-gün kayıtları hariç 13.570 kayıt ve 17 pozitif sınıfı; Analysis 3 ise 64.999 kaydın dört proje-tanımlı gruba dönüştürülmüş sonucunu ifade eder. Metin, tablo, şekil, açıklama, eksen, lejant ve çapraz atıfların tamamı bu eşlemeye göre denetlenecektir. En iyi sınıflandırıcı ayrıca kendi algoritma ve konfigürasyon adıyla belirtilecek; analiz adı ile model adı birbirine karıştırılmayacaktır.`

## Status
Fully finalized. No additional data are required for the nomenclature decision; implementation requires a manuscript-wide occurrence audit and verification of each legacy label against sample size and class structure.
