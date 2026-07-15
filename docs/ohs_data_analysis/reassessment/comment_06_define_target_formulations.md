# Reassessment — Comment 6: define the three target formulations precisely

## Reviewer comment
`Bu multiple target combination’dan kasıt nedir?`

## Anchored manuscript wording
The manuscript refers to a `controlled comparative framework with a consistent feature set and multiple target formulations` and later describes `three occupational injury severity models (Full Dataset, Excluding Zero Payment, and Aggregated Payment Days)`.

## Core problem
The phrase `multiple target formulations` is too abstract, and `multiple target combination` can incorrectly suggest that several outcomes were combined in one multi-output, multi-task, or ensemble model. That is not what the auditable project artifacts show.

The project contains three separate classification analyses built from the same source target column, `ODEME_GUNSAYISI`, under different inclusion and recoding rules. Each analysis was fitted and evaluated independently. They should therefore be called **Analysis 1, Analysis 2, and Analysis 3**, not three combined targets and not three injury-severity models.

## Verified definitions

### Analysis 1 — full payment-day classification
- Source file: `Rebuilded_Data_Class_0lı.xlsx`.
- Records: 64,999.
- Predictors: 14.
- Target: `ODEME_GUNSAYISI`.
- Inclusion rule: the zero-day class is retained.
- Observed target structure: 18 classes in total, including `0` and 17 positive payment-day classes.
- Analytical purpose: assess classification across the complete recorded outcome distribution, including the dominant zero-day category.

### Analysis 2 — positive payment-day classification
- Source file: `Rebuilded_Data_Class_0sız.xlsx`.
- Records: 13,570.
- Predictors: the same 14-predictor set.
- Target: `ODEME_GUNSAYISI`.
- Inclusion rule: 51,429 zero-day records are excluded.
- Observed target structure: 17 positive payment-day classes.
- Analytical purpose: assess discrimination among cases with a positive payment-day outcome without the dominant zero-day class.

### Analysis 3 — four-class grouped outcome formulation
- Source file: `Rebuilded_Data_Class_0lı.xlsx`.
- Records: 64,999.
- Predictors: the same 14-predictor set.
- Source target: `ODEME_GUNSAYISI`, recoded through the project-defined mapping.
- Grouped classes and counts: `First aid cases` 51,429; `Temporary incapacity` 8,384; `Permanent incapacity` 3,799; `Fatality` 1,387.
- Analytical purpose: evaluate a lower-dimensional four-class grouped outcome rather than the original payment-day categories.

Because Analysis 3 is derived from a project-defined recoding of the payment-day target, the manuscript should not imply that it uses an independently observed injury-severity or mortality variable unless the provenance and substantive validity of that mapping are documented. The safest current description is `four-class grouped payment-day outcome formulation`.

## Approved manuscript replacement
`To examine how outcome definition and the treatment of zero-day records affected model performance, three separate classification analyses were conducted using the same 14-predictor set. Analysis 1 included all 64,999 records and treated ODEME_GUNSAYISI as an 18-class outcome, including the zero-day class. Analysis 2 excluded zero-day records and classified the remaining 13,570 cases into 17 positive payment-day classes. Analysis 3 retained all 64,999 records but recoded the payment-day outcome into four project-defined grouped categories. The three analyses were fitted and evaluated independently; they do not represent a combined target, a multi-output model, or an ensemble of target definitions.`

## Recommended compact table
| Analysis | Records | Outcome definition | Zero-day handling | Purpose |
|---|---:|---|---|---|
| Analysis 1 | 64,999 | 18 payment-day classes | Retained | Full recorded outcome distribution |
| Analysis 2 | 13,570 | 17 positive payment-day classes | Excluded | Positive-outcome discrimination |
| Analysis 3 | 64,999 | Four project-defined grouped classes | Retained and recoded | Lower-dimensional grouped classification |

## Terminology corrections
- Delete `multiple target combination`.
- Replace `multiple target formulations` at first mention with the explicit three-analysis description.
- Replace `three occupational injury severity models` with `three separate outcome-classification analyses`.
- Replace `Full Dataset`, `Excluding Zero Payment`, and `Aggregated Payment Days` labels with `Analysis 1`, `Analysis 2`, and `Analysis 3`, followed by descriptive subtitles at first use.
- Do not call Analyses 1 and 2 injury-severity models; their direct target is the payment-day field.
- Do not state that all three analyses were compared under an identical validation protocol until the recorded cross-validation configuration difference has been reconciled.

## Recommended reviewer response
`Thank you for requesting clarification. We agree that the phrase “multiple target formulations” was too vague and could be interpreted as a combined or multi-output target. We therefore replaced it with an explicit description of three independently fitted classification analyses. Analysis 1 used all 64,999 records and retained the zero-day category in an 18-class payment-day outcome. Analysis 2 excluded zero-day records and used 13,570 cases with 17 positive payment-day classes. Analysis 3 used all 64,999 records but recoded the payment-day outcome into four project-defined grouped categories. We also renamed the analyses consistently as Analysis 1, Analysis 2, and Analysis 3 and clarified that they are separate outcome definitions rather than a combined target model.`

## Turkish explanation for the tracking workbook
`“Multiple target formulations/combination” ifadesi kaldırılmıştır. Burada birden fazla hedefin tek modelde birleştirilmesi söz konusu değildir. Aynı kaynak hedef değişkeni olan ODEME_GUNSAYISI, üç ayrı analizde farklı dâhil etme ve yeniden sınıflandırma kurallarıyla kullanılmıştır. Analiz 1 sıfır günü de içeren 64.999 kayıtta 18 sınıflı ödeme-günü sonucunu; Analiz 2 sıfır günleri dışlayan 13.570 kayıtta 17 pozitif ödeme-günü sınıfını; Analiz 3 ise 64.999 kaydı dört proje-tanımlı gruba dönüştürülmüş sonuç yapısıyla incelemektedir. Analizler ayrı ayrı eğitilmiş ve değerlendirilmiştir; birleşik hedef, multi-output model veya hedef ensemble’ı değildir.`

## Manuscript-wide actions
- Insert the explicit three-analysis definition in the first Methods passage where the analytical framework is introduced.
- Add the compact comparison table before detailed model descriptions.
- Align all section headings, figures, tables, captions, and Results references with Analysis 1/2/3.
- Keep payment-day classification separate from the four-class grouped formulation.
- Audit the source and validity of the four-class labels before treating them as independently observed clinical or legal severity outcomes.

## Status
Fully finalized for Comment 6. The ambiguity is resolved by replacing the generic phrase with exact sample sizes, target structures, inclusion rules, and analytical purposes.