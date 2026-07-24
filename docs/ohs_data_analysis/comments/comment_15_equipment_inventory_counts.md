# Comment 15 — Exact equipment-inventory counts and NACE separation

## Reviewer comment
`1800’den fazla değil yaklaşık 500 değil, tam kaçsa rakamlar öğrenilip yazılacak.`

## Selected manuscript wording
`An initial scan identified over 1,800 headings, and approximately 500 that are directly used in construction were mapped to the NACE hierarchy.`

## Evidence audit
The currently available manuscript and analytical artifacts do not contain the source equipment table, database export, or counting script needed to verify exact values for either the total number of headings or the construction-relevant subset. Therefore, replacing the approximate values with guessed integers would create a false precision problem.

The manuscript also contains a second inventory description stating that the construction-specific lexicon includes approximately 4,000 operated-machine entries and that a cross-sector extension includes approximately 16,000 options. These quantities are not defined using the same counting unit as the later `over 1,800 headings` and `approximately 500` statement. The manuscript does not explain whether the totals count canonical equipment records, aliases, machine–work-area combinations, language variants, or raw headings before deduplication.

The risk-model preprocessing manifests provide 25 or 26 broad observed operated-machine category labels, depending on the analysis subset. Those category counts describe model features in the accident dataset; they do not establish the size of the mobile application's detailed equipment inventory and must not be substituted for the requested exact counts.

## Methodological correction
NACE Rev. 2 classifies economic activities. It can define that the study concerns Section F and Divisions 41–43, but it should not be described as the hierarchy used to classify individual machines. The equipment inventory is an application-specific taxonomy and must be reported separately from the NACE sector classification.

## Final decision
Comment 15 is processed but remains conditional until the version-controlled equipment inventory is supplied or exported. Until then:

1. Remove the unverified numerical statement from the submission draft rather than retaining approximate values or inventing exact ones.
2. Separate the NACE-defined construction-sector scope from the application-specific equipment taxonomy.
3. Retain only the verified five-domain grouping and the alias-normalization procedure.
4. Report exact counts only after applying a documented counting rule to the authoritative inventory.

## Preferred interim replacement paragraph
`Operated-machine records were harmonized with the application-specific equipment taxonomy and grouped into five domains: building and infrastructure machines; hand tools and portable machines; production and manufacturing machines; transport vehicles and logistics equipment; and environmental risks and hazardous substances. NACE Rev. 2 was used only to define the construction-sector scope of the study and was not used as an equipment classification. Synonymous equipment names were mapped to canonical labels, and records outside the predefined scope were assigned to an “Other” category.`

This paragraph is suitable for the manuscript only while the authoritative inventory and exact counts remain unavailable.

## Exact-count reporting template after verification
Once the source inventory is available, replace the interim wording with a sentence following this structure:

`The version-controlled source inventory contained [X] raw equipment headings. After normalization of spelling variants, consolidation of aliases, and removal of duplicate records, [Y] unique canonical equipment records remained, of which [Z] were classified as construction-relevant and assigned to the five application-specific equipment domains.`

The final values must be generated from one reproducible inventory version, and the manuscript should state:

- inventory file or database version and extraction date;
- whether counts refer to raw rows or unique canonical records;
- whether aliases and language variants are counted separately;
- duplicate-handling rule;
- inclusion rule for construction relevance;
- treatment of the `Other` category;
- whether machine–work-area combinations are counted as separate entries.

## Manuscript-wide consistency actions
- Do not retain both `over 1,800 / approximately 500` and `approximately 4,000 / approximately 16,000` without defining their distinct units and scopes.
- Do not state that machines were mapped to the NACE hierarchy.
- Use `NACE Rev. 2` for sector scope and `application-specific equipment taxonomy` for machine classification.
- Align Section 3.2.1, Section 3.4.1, Figure 4, captions, and supplementary inventory descriptions to the same verified source counts.
- Preserve the distinction between detailed application inventory records and the 25–26 broad operated-machine feature levels used in the predictive models.

## Reviewer-response draft
`Revised. We removed the approximate equipment totals because the current revision package did not contain the authoritative inventory needed to calculate exact counts reproducibly. The text now separates the NACE Rev. 2 construction-sector definition from the application-specific equipment taxonomy and retains only the verified five-domain classification and alias-normalization procedure. Exact totals will be inserted from the version-controlled equipment inventory after duplicate, alias, and inclusion rules have been applied consistently.`

## Quality re-audit of earlier comments
- Comment 14 is strengthened: NACE defines economic-activity scope and must not be presented as an equipment hierarchy.
- Comment 12 remains conditional because equipment-inventory counts do not establish scenario provenance.
- The Section 3.2.1 claims of approximately 4,000 and 16,000 entries are now flagged for the same source-count verification required by this comment.
- No previous exact count should be inferred from the model preprocessing manifests.

## Status
Processed conditionally. Finalization requires the authoritative equipment inventory or a reproducible export/counting script.