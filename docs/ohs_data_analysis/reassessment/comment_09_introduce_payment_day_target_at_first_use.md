# Reassessment — Comment 9: introduce the modeled outcome at first use

## Reviewer comment
`Bununla ilgili bölümümüz vardı ama ilk burada bahsedilmiş, o zaman tanıtımı buraya göre al çağdaş`

## Final editorial decision
The definition of the modeled outcome will be moved to its first substantive occurrence in the Methods section, before preprocessing, class construction, resampling, model fitting, performance metrics, or later references to the three analyses. The reader should not encounter an unexplained target name or abbreviation and be expected to recover its meaning from a later subsection.

The first-use paragraph will identify:
1. the source-data field name;
2. the neutral manuscript term used for that field;
3. the administrative and non-causal nature of the outcome;
4. the treatment of zero-day records;
5. the three analysis-specific outcome formulations;
6. the fact that each formulation was fitted and evaluated independently.

## Approved first-use paragraph
`The modeling target was the source-data field ODEME_GUNSAYISI, referred to in this manuscript as the payment-day outcome. The available project documentation does not establish that this administrative field is equivalent to Days Away From Work, temporary-incapacity duration, financial loss, or absolute accident risk. Three separate classification analyses were therefore defined from this field. Analysis 1 retained all 64,999 records and represented the observed outcome as 18 classes, including the zero-day class. Analysis 2 excluded zero-day records and represented the remaining 13,570 cases as 17 positive payment-day classes. Analysis 3 retained all 64,999 records and recoded the same source field into four project-defined grouped categories. The three outcome formulations were modeled and evaluated independently.`

## Recommended placement
Insert the paragraph immediately after the dataset and predictor description and before any subsection that discusses:
- target encoding;
- class imbalance;
- train/test splitting or cross-validation;
- resampling;
- model selection;
- evaluation metrics;
- Analysis 1, Analysis 2, or Analysis 3 results.

A later subsection may explain the recoding algorithm in greater detail, but it should refer back to this first-use definition rather than introduce the target for the first time.

## Section-order correction
The Methods narrative should follow this order:
1. data source and unit of analysis;
2. predictor set;
3. target definition and analysis-specific class construction;
4. preprocessing and missing-value handling;
5. train/test partitioning and cross-validation;
6. imbalance handling and resampling;
7. candidate classifiers and tuning;
8. evaluation metrics;
9. application-level use of model outputs.

This sequence separates the historical-data prediction task from the later mobile-application calculations and prevents the payment-day target from being confused with application risk components or scenario-priority scores.

## Required manuscript-wide corrections
- Remove any unexplained first occurrence of `DAFW`, `payment days`, `injury severity`, `target combination`, or `Model F/E/A`.
- At first use, write `payment-day outcome (source field: ODEME_GUNSAYISI)`.
- State explicitly that the zero-day class is retained in Analysis 1 and excluded in Analysis 2.
- State explicitly that Analysis 3 is a four-class project-defined grouping derived from the same source field.
- Do not call the four groups validated clinical or legal severity categories unless an independent class-definition source and provenance record are supplied.
- Keep outcome definition separate from predictor descriptions and from application-level risk calculations.
- Use Analysis 1, Analysis 2, and Analysis 3 consistently in prose, tables, captions, and figures.
- Avoid repeating the full definition in every later section; use a concise cross-reference after the first complete definition.

## Recommended reviewer response
`Thank you for this suggestion. We agree that the outcome should be defined when it is first introduced rather than in a later subsection. We therefore moved the target definition to the beginning of the Methods workflow, immediately after the dataset and predictor description. The revised text now identifies the source field ODEME_GUNSAYISI, uses the neutral term “payment-day outcome,” explains the treatment of zero-day records, and defines the three independently evaluated class formulations before preprocessing and model evaluation are described. Later sections now refer back to this definition, which removes the previous ambiguity and improves the logical sequence of the Methods section.`

## Turkish explanation for the tracking workbook
`Hedef değişkenin açıklaması, okuyucunun ilk kez karşılaştığı noktaya taşınmıştır. Kaynak veri alanı ODEME_GUNSAYISI olarak belirtilmiş ve doğrulanmamış DAFW eşdeğerliği kurulmadan “payment-day outcome” terimi kullanılmıştır. Aynı paragrafta Analiz 1’de sıfır-gün sınıfının korunduğu, Analiz 2’de sıfır-gün kayıtlarının çıkarıldığı ve Analiz 3’te aynı alanın dört proje-tanımlı gruba dönüştürüldüğü açıklanmıştır. Bu tanım; ön işleme, sınıf dengesizliği, modelleme ve performans değerlendirmesinden önce verilecek; sonraki bölümlerde gereksiz tekrar yerine bu ilk tanıma atıf yapılacaktır.`

## Cross-comment consistency
- Comment 6 defines the three independent outcome formulations.
- Comment 8 removes the unsupported DAFW equivalence.
- Comment 10 and Comment 19 replace Model F/E/A labels with Analysis 1/2/3.
- Comment 11 determines the correct classification metric terminology.
- Comment 16 requires all symbols and transformations to be defined.
- Comments 17, 18, and 20 prevent the historical target from being confused with an unsupported overall application-risk percentage.

## Status
Fully finalized. No additional data are required for the structural revision. The detailed four-class mapping should be reproduced exactly from the auditable project artifacts when the manuscript is implemented; no class meaning will be invented.