# Comment 10 — Standardizing the three analytical settings

## Reviewer comment
`Neden modeller F, E, A şeklinde de A, B, C şeklinde değil?`

## Selected manuscript text
`This was conducted using three different occupational injury severity models: full dataset model (Model F), the excluding zero payment days model (Model E), and the aggregated payment days model (Model A).`

## Final decision
The labels `Model F`, `Model E`, and `Model A` should be removed. They are mnemonic labels based on `full`, `excluding`, and `aggregated`, but this logic is not transparent to readers and is not used consistently in the project outputs. A simple change to `Model A`, `Model B`, and `Model C` would improve order but would retain a more important methodological problem: each setting evaluates a portfolio of nine classifiers rather than representing one fitted model.

The clearest and most technically accurate terminology is therefore:

- **Analysis 1 — all-case payment-day classification:** uses all records, including zero-day cases.
- **Analysis 2 — positive payment-day classification:** excludes zero-day cases and models the remaining positive payment-day categories.
- **Analysis 3 — four-level injury-severity classification:** classifies cases as first aid, temporary incapacity, permanent incapacity, or fatality.

Use the full labels `Analysis 1`, `Analysis 2`, and `Analysis 3` in the manuscript, tables, figure legends, and captions. Do not introduce the abbreviations `A1`, `A2`, and `A3` unless figure-space limitations make them unavoidable.

## Why this is preferable to A/B/C

1. `Analysis` accurately describes a complete modeling task in which multiple classifiers are compared.
2. `Model A/B/C` could be misread as three individual fitted algorithms.
3. Sequential numbering is easier to follow across Methods, Results, tables, and figures.
4. Descriptive subtitles preserve the substantive difference among the three outcome encodings.
5. The convention aligns naturally with the project artifacts `Risk_01`, `Risk_02`, and `Risk_03` and with existing M1/M2/M3 figure-generation labels, while avoiding opaque F/E/A mnemonics in the final article.

## Preferred replacement sentence

`Three prespecified modeling analyses were conducted: Analysis 1 classified the recorded payment-day outcome using all cases, including zero-day cases; Analysis 2 classified the positive payment-day outcome after zero-day cases were excluded; and Analysis 3 classified cases into four injury-severity levels—first aid, temporary incapacity, permanent incapacity, and fatality.`

## Red-highlight treatment for the final workbook
The entire replacement sentence should be red because both the naming system and the substantive description of the three analyses are being rewritten.

## Manuscript-wide replacements

- `Model F` → `Analysis 1`
- `Model E` → `Analysis 2`
- `Model A` → `Analysis 3`

These replacements must be applied in:

- Section 3.1.3
- all performance tables
- Figure 9 and Figure 10 captions and legends
- Results statements comparing the three settings
- Discussion statements referring to the strongest analysis
- supplementary files and exported plots used in the final submission package

## Important consistency safeguard
The following statements should not be changed by simple search-and-replace alone:

- `Model A remains the highest`
- `Model A demonstrates the most consistent improvement over the baseline`
- `a slight decrease from Model F to Model A`

Each must be rewritten to identify the exact metric and the relevant analysis. Terms such as `highest`, `best`, and `improvement` should not remain without naming the evaluation measure and confirming the result from the final validated tables.

## Link to earlier comments

- Comment 6 should now describe `three prespecified modeling analyses, each defined by a distinct outcome encoding`.
- Comments 8 and 9 remain valid because the neutral term `recorded payment-day outcome` is retained.
- Comment 7 should use `within each analysis` and `across the three analyses` when discussing classifier comparison and model selection.

## Literature decision
No literature citation is required. This is an internal nomenclature and study-design clarification.

## Reviewer-response draft
`Revised. The opaque F/E/A labels were replaced with sequential labels. Because each setting evaluates several classifiers rather than representing a single fitted model, the manuscript now uses Analysis 1, Analysis 2, and Analysis 3 instead of Model A, Model B, and Model C. Each analysis is defined at first mention by its outcome encoding: all cases including zero-day cases, positive-day cases after zero-day cases were excluded, and a four-level injury-severity classification. The terminology was standardized throughout the text, tables, figures, and captions.`

## Quality re-audit conclusion
The earlier terminology decisions remain defensible. The strongest improvement introduced by this comment is to treat the three settings as analyses rather than individual models. This resolves the reviewer's concern while also correcting a deeper methodological ambiguity in the manuscript.