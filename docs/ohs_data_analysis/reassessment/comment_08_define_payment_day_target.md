# Reassessment — Comment 8: define the target variable and remove unsupported `DAFW` equivalence

## Reviewer comment
`Bu nedir?`

## Anchored manuscript context
The queried term is `DAFW`, which is used in the manuscript as though it were the verified modeling target and as though it were interchangeable with the source-data field.

## Evidence reviewed
The three auditable analysis artifacts identify the target column consistently as `ODEME_GUNSAYISI`:
- Analysis 1: `ODEME_GUNSAYISI`, 64,999 records, zero-day values retained;
- Analysis 2: `ODEME_GUNSAYISI`, 13,570 records, zero-day values excluded;
- Analysis 3: `ODEME_GUNSAYISI`, 64,999 records, values recoded into four project-defined grouped categories.

The supplied project files do not contain a source-data dictionary, variable-definition sheet, administrative coding manual, or provenance note demonstrating that `ODEME_GUNSAYISI` is identical to a standard `Days Away From Work` variable. The manuscript therefore cannot safely translate or relabel the field as `DAFW`.

## Final editorial decision
For the study's own analyses, replace `DAFW` with:

`payment-day outcome (source field: ODEME_GUNSAYISI)`

After the first definition, use `payment-day outcome` or the exact analysis-specific formulation.

`DAFW` may remain only when accurately describing an external study that explicitly used that term. It will not be used as a synonym for this project's target unless an authoritative source-data definition is later supplied.

## Approved Methods wording
`The modeling target was the source-data field ODEME_GUNSAYISI. In this manuscript, it is referred to as the payment-day outcome. Because the available project documentation does not establish that this administrative field is equivalent to Days Away From Work, the abbreviation DAFW is not used as a synonym for the modeled target.`

## Approved analysis-specific wording
- Analysis 1: `18-class payment-day outcome, including the zero-day class`;
- Analysis 2: `17-class positive payment-day outcome after exclusion of zero-day records`;
- Analysis 3: `four-class grouped payment-day outcome derived from ODEME_GUNSAYISI`.

## Required manuscript changes
- Replace `DAFW as the target variable` with the verified source-field terminology.
- Replace `days away from work and fatalities` as a joint target description; the auditable pipeline records one target column, `ODEME_GUNSAYISI`.
- Remove statements that Analysis 1 and Analysis 2 model a continuous DAFW variable; the project outputs document multiclass classification formulations.
- Rename Section 3.3.4 from `Days Away from Work (DAFW) and indemnity benefit probability` to `Payment-day outcome and compensation-related reporting`, subject to the separate validation of the compensation calculations.
- Remove `DAFW-monetized`, `DAFW-equivalent days`, and similar expressions unless their mathematical and administrative derivation is independently documented.
- Keep payment-day classification outputs separate from accident probability, individual exposure, compensation probability, and financial-loss estimates.
- Audit figure labels, table headers, equations, captions, and application screens for the same terminology.

## Why this correction is necessary
- The manuscript currently gives a familiar English expansion to a field whose administrative meaning has not been documented.
- `Payment days`, `lost workdays`, `days away from work`, `temporary-incapacity days`, and `compensable days` are not interchangeable labels without a source definition.
- Using `DAFW` would make the outcome appear more standardized and clinically interpretable than the available provenance supports.
- The safer approach is to preserve the source variable's operational identity and state the limits of interpretation.

## Recommended reviewer response
`Thank you for identifying this undefined term. We reviewed the analysis files and confirmed that the modeled target is the source-data field ODEME_GUNSAYISI. The available project documentation does not establish that this field is equivalent to the standard Days Away From Work construct. We therefore removed DAFW as a synonym for the study target and now define the variable as the payment-day outcome, with the original field name reported at first use. We also revised the descriptions of the three analyses, section headings, tables, figures, and equations so that payment-day classification is not conflated with lost workdays, accident probability, fatality prediction, or compensation probability.`

## Turkish explanation for the tracking workbook
`DAFW kısaltması, proje dosyalarında doğrulanmış hedef değişken adı değildir. Üç analizde de hedef kolon ODEME_GUNSAYISI olarak kayıtlıdır. Bu alanın standart Days Away From Work göstergesiyle aynı olduğunu kanıtlayan veri sözlüğü veya idari tanım bulunmadığından DAFW eşdeğerliği kaldırılmıştır. İlk kullanımda “payment-day outcome (source field: ODEME_GUNSAYISI)” ifadesi kullanılacak; sonraki bölümlerde analiz yapısına göre ödeme-günü sonucu açıkça tanımlanacaktır. Kayıp iş günü, geçici iş göremezlik günü, tazmin edilebilir gün, ölüm ve ödeme olasılığı kavramları bu hedefle birleştirilmeyecektir.`

## Cross-comment consistency
This decision is aligned with:
- Comment 3: no individualized-exposure interpretation;
- Comment 6: three independent classification analyses;
- Comment 9: move the target definition to its first occurrence;
- Comment 11: use classification metrics rather than regression framing;
- Comments 27 and 32: remove unsupported application-level prediction and financial-superiority claims.

## Status
Fully finalized. A source-data dictionary could later support a more specific administrative interpretation, but it is not required for the present correction because the manuscript can accurately report the operational source-field terminology.