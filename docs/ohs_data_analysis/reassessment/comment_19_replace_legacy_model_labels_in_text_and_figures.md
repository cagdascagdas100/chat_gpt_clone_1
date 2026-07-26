# Comment 19 — Replace legacy Model F/E/A labels in text and figures

## Reviewer comment
`Bu model F,e,a her yerde, figürler dahil, a,b,c olsun.`

## Final decision
The legacy labels `Model F`, `Model E`, and `Model A` will be removed from all publication-facing material. They will not be replaced by `Model A/B/C`, because each label denotes a separate outcome-classification analysis within which multiple classifiers were evaluated; calling the analyses “models” would remain conceptually inaccurate.

## Verified mapping
- `Model F` → **Analysis 1**: all 64,999 records; zero-day class retained; 18 observed payment-day classes.
- `Model E` → **Analysis 2**: zero-day records excluded; 13,570 records; 17 positive payment-day classes.
- `Model A` → **Analysis 3**: all 64,999 records; four project-defined grouped classes derived from `ODEME_GUNSAYISI`.

Every replacement must be verified against the sample size, zero-day rule, and class definition. Legacy letters must not be converted by their visual or alphabetical order.

## Manuscript-wide audit
Replace or remove the legacy labels in:
- Methods, Results, Discussion, and Conclusion;
- tables, captions, cross-references, legends, axis labels, panel labels, annotations, and supplementary material;
- publication-facing spreadsheet outputs and image filenames;
- embedded raster figures, not only the surrounding Word captions.

Historical raw-artifact filenames may be retained solely for provenance, provided that the revision record explicitly maps them to Analysis 1/2/3.

## Figure-specific corrections
The embedded figures were inspected and contain legacy labels inside the images.

### Figure 8
Regenerate the heat map so that all row/column headers and the title use **Analysis 1**, **Analysis 2**, and **Analysis 3**. The title must describe payment-day outcome analyses rather than “occupational injury severity models.”

### Figure 9
Regenerate the performance-summary figure so that the legend uses Analysis 1/2/3. The panels must not imply that the three analyses are interchangeable models of the same target.

### Figure 10
Do not merely relabel the x-axis of the current connected-line plot. Connecting Analysis 1 → Analysis 2 → Analysis 3 visually implies an ordered trend and “stability across models,” although the analyses differ in sample inclusion and outcome class structure. The figure should either:
1. be removed, or
2. be rebuilt as separate, non-connected descriptive panels/point summaries by analysis, with no claim of temporal trend or scenario stability.

## Reporting rule
Use expressions such as:
- `the selected classifier/configuration within Analysis 1`,
- `performance within Analysis 2`,
- `the grouped payment-day formulation in Analysis 3`.

Avoid:
- `Model F/E/A`,
- `Model A/B/C`,
- `the best analysis` when the underlying tasks differ,
- direct cross-analysis performance rankings without an explicit comparability caveat.

## Approved wording
`Three separate payment-day outcome classification analyses were conducted. Analysis 1 retained all records and included the zero-day class; Analysis 2 excluded zero-day records; and Analysis 3 recoded the same source field into four project-defined grouped classes. Multiple candidate classifiers were evaluated within each analysis. Accordingly, the analysis label and the selected classifier are reported separately throughout the manuscript.`

## Cross-comment consistency
This implements the nomenclature decision established under Comment 10 and preserves the target definitions fixed under Comments 6, 8, and 9. It also prevents Figures 8–10 from presenting non-comparable target formulations as if they were three versions of one model.