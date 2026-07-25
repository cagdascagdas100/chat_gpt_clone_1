# Reassessment — Comment 15: remove unsupported approximate equipment counts

## Reviewer comment
`1800’den fazla değil yaklaşık 500 değil, tam kaçsa rakamlar öğrenilip yazılacak.`

## Anchored manuscript wording
`An initial scan identified over 1,800 headings, and approximately 500 that are directly used in construction were mapped to the NACE hierarchy.`

## Final editorial decision
The expressions `over 1,800` and `approximately 500` will not be replaced with guessed exact values. The supplied project package contains no auditable source export, dictionary table, codebook, counting script, versioned classification file, or deduplication log from which these totals can be reproduced. The only available occurrences are narrative claims in the manuscript. Therefore, the two counts will be removed from the present revision.

This is preferable to reporting false precision. An exact number is publishable only when the underlying classification snapshot and counting rules are available and independently reproducible.

## Why the current numbers are not auditable
- The manuscript does not identify the source list from which the initial headings were counted.
- The unit of count is unclear: heading, canonical machine, alias, equipment option, category node, or raw string.
- The treatment of duplicate names, spelling variants, alternative names, parent headings, and `Other Machines` is not stated.
- The construction-selection criterion is not documented.
- The claim that items were mapped to the NACE hierarchy conflicts with Comment 14, because NACE classifies economic activities rather than machinery.
- The project package does not contain a dated, versioned machine-dictionary export supporting the figures.

## Approved replacement wording
`Construction-related machinery and equipment were organized in a project-specific classification comprising five domains: (1) building and infrastructure machinery, (2) hand tools and portable machinery, (3) production and manufacturing machinery, (4) transport vehicles and logistics equipment, and (5) environmental hazards and hazardous substances. Because the archived project materials did not contain a reproducible export of the underlying machine dictionary, unverified counts of candidate headings and construction-specific entries were omitted.`

If the second sentence is considered too procedural for the main manuscript, it may instead be placed in the reviewer response or limitations statement, while the main text retains only the five-domain description.

## Required manuscript-wide count audit
The same evidence rule must be applied to all dictionary-size claims, including:
- `61 sub-work areas under 10 main headings`;
- `about 4,000 operator-controlled machine entries`;
- `12 classes`;
- `162 sub-work areas`;
- `approximately 16,000 machine options`;
- `three alternative names for each machine`;
- any equivalent count repeated in the Discussion or Conclusion.

A count may remain only if its source file, version, counting unit, inclusion criteria, duplicate-handling rule, and exact reproducible total are documented. Otherwise, the number must be deleted and the taxonomy described qualitatively.

## Exact-count protocol if the source export is later supplied
1. Freeze and identify the source snapshot by filename, version, and date.
2. Define the counting unit before calculation.
3. Separate canonical entries from aliases and display labels.
4. Normalize case and whitespace and document duplicate removal.
5. State inclusion and exclusion rules for construction relevance.
6. Report the total candidate pool and construction-specific subset separately.
7. Provide a machine-readable count table or script as supplementary provenance.
8. Do not describe the machine taxonomy as a NACE hierarchy.

## Recommended reviewer response
`Thank you for identifying this problem. We agree that the expressions “over 1,800” and “approximately 500” were insufficiently precise. We re-examined the archived project materials and found that the underlying classification export and counting protocol needed to reproduce these figures were not available. To avoid introducing unsupported precision, we removed both numbers and revised the text to describe only the verified five-domain project-specific classification. We also audited the other dictionary-size claims and retained numerical totals only where a versioned source file and reproducible counting rule could be documented.`

## Turkish explanation for the tracking workbook
`Hakem değerlendirmesi doğrultusunda “1.800’den fazla” ve “yaklaşık 500” ifadeleri yeniden incelenmiştir. Mevcut proje paketinde bu sayıları yeniden üretecek sürümlü makine sözlüğü, kaynak tablo, sayım betiği veya tekilleştirme kuralı bulunmadığından kesin sayı uydurulmamıştır. İki sayı metinden çıkarılmış; yalnızca doğrulanabilen beş alanlı proje sınıflaması korunmuştur. Aynı kanıt ölçütü 61, 10, 4.000, 12, 162, 16.000 ve alternatif ad sayısı gibi diğer sözlük büyüklüğü iddialarına da uygulanacaktır.`

## Status
Fully finalized for the available evidence. No numerical count will be reported until a reproducible classification source is supplied.