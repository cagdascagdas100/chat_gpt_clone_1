# OHS Manuscript Revision — Current Status

- Total reviewer comments: 32
- Processed through: Comment 27
- Processed: 27/32 = 84.375%
- Fully finalized: 20/32 = 62.5%
- Conditional items: Comment 12 (scenario provenance), Comment 15 (authoritative equipment inventory), Comment 17 (internal–external weighting), Comment 18 (regional-decay value selection), Comment 20 (final composite depends on Comment 17 and the missing fifth-region input), Comment 23 (original high-resolution landing-page and personal-input screenshots), and Comment 24 (meaning of `yz`)
- Next item: Comment 28

## Latest decision — Comment 27
The phrase `application model` will be replaced with `OSH-RA mobile decision-support application` or `application architecture` when referring to the software system. The application is defined as an integration layer that combines structured user and worksite inputs, offline-trained classifiers, deterministic risk aggregation and ranking rules, and presentation of decision-support outputs.

## Validation findings
- The project artifacts document internal resampling/cross-validation, discrimination metrics, and calibration summaries for the analytical models.
- The preprocessing manifests contain empty `final_holdout_report` objects.
- No independent external cohort, prospective validation, common-task comparison with another application, usability study, flexibility test, or field-effectiveness analysis is available.
- Internal classifier metrics do not establish application-level superiority.

## Required wording corrections
- Remove the claim that OSH-RA is `more accurate and flexible` than prior systems.
- Remove the unsupported description of OSH-RA as multimodal; the verified inputs are structured categorical, numerical, and binary fields rather than runtime image, video, or audio inference.
- Replace vague superiority language with a concrete description of inputs, analytical operations, and displayed outputs.
- State explicitly that the present evaluation does not establish superior application-level accuracy, flexibility, usability, or effectiveness.

## Citation correction
Reference `[121]` analyzes causal-factor extraction from crane-accident text reports using ChatGPT and complex networks. It is not an audio-and-visual-only comparator and does not support the selected sentence. References `[119]` and `[120]` concern multimodal LLM inspection or report-generation systems but do not demonstrate that OSH-RA itself is multimodal or more accurate.

## Cross-comment consistency updates
- Comment 12 controls unverified LLM and multimodal claims.
- Comments 17 and 20 control the unresolved composite-score calculation.
- Comment 25 controls model-performance and validation interpretation.
- Comment 26 controls evidence-bounded contribution framing.

## Next item
Comment 28 — remove the remaining LLM adaptability and continuously updated knowledge-base sentence in accordance with the manuscript-wide provenance decision.