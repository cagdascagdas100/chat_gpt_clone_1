# Conditional Resolution — Comment 15: Exact Equipment Counts

## Reviewer comment
`1800’den fazla değil yaklaşık 500 değil, tam kaçsa rakamlar öğrenilip yazılacak.`

## Selected manuscript span
`over 1,800 headings, and approximately 500 that ...`

## Evidence audit
An exact equipment count cannot be reproduced from the auditable project package. The available materials do not contain a version-controlled equipment inventory, canonical-item table, database export, source-code catalogue, deduplication script, alias map, or documented counting rule.

The manuscript currently contains several incompatible scale claims:
- more than 1,800 headings and approximately 500 construction items;
- approximately 4,000 construction equipment entries;
- approximately 16,000 cross-sector equipment options;
- expansion from 4,000 to 16,000 items.

None of these values can be traced to an authoritative inventory in the supplied files. The machine-learning preprocessing manifests document only 25–26 broad `makine` category levels observed in the historical accident data. Those levels are analytical categories and must not be interpreted as the number of equipment items available in the mobile application.

Figure 4 supports the existence of five application domains and their correspondence with broad historical operated-machine categories, but it does not establish an item-level inventory count. NACE classifies economic activities and is not an equipment catalogue.

## Final editorial decision
All unverified equipment-count claims will be removed from the submission, including `1,800`, `500`, `4,000`, and `16,000`. The revision will retain only the taxonomy structure that is visible and documentable. This closes Comment 15 without inventing an exact number.

## Approved manuscript wording
`To align application inputs with the operated-machine categories recorded in the SSI accident data, equipment-related inputs were organized into five application domains: building and infrastructure machines; hand tools and portable machines; production and manufacturing machines; transport vehicles and logistics equipment; and environmental risks and hazardous substances. Figure 4 presents the correspondence between these application domains and the broader operated-machine categories used in the historical records.`

## Conditions for reporting a count in a later version
A numerical inventory claim may be restored only if the authors supply a dated, version-controlled export with:
- one canonical identifier per equipment item;
- explicit treatment of aliases, spelling variants, language variants, duplicates, and `Other` entries;
- a defined distinction among equipment items, work-area–equipment combinations, malfunction options, and display labels;
- a reproducible counting script or query;
- the inventory version and extraction date.

## Cross-comment consistency
- Comment 14: NACE must remain an economic-activity classification, not an equipment hierarchy.
- Comment 23: application screenshots document workflow, not inventory size.
- Comment 30: practical-use wording must not imply wider coverage than the verified taxonomy supports.

## Status
Resolved and finalized by permanent removal of unsupported counts.