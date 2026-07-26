# Comment 26 — Remove repetitive Fine–Kinney framing

## Reviewer comment
`Yani hala fine kinney diyoruz, yeter diyesi geliyor okuyanın ☺️`

## Selected text
`the Fine–Kinney method, conceptualize risk as the product of probability, exposure, and severity`

## Evidence audit
The reviewer comment is anchored to a tracked-deletion paragraph at the beginning of Section 5.2. That paragraph repeats a long explanation of Fine–Kinney and contrasts it with the proposed framework. The current accepted manuscript text already removes that paragraph, and it should not be restored.

A manuscript-wide audit found one remaining live body-text mention in the Introduction: conventional safety-management approaches are described using Fine–Kinney as an example of a periodic likelihood–severity–exposure assessment. Earlier Background passages and the Section 5.2 discussion paragraph containing detailed Fine–Kinney explanations are present only as tracked deletions.

## Final editorial decision
1. Do not reintroduce the deleted Fine–Kinney paragraph in Section 5.2.
2. Fine–Kinney may be mentioned at most once in the manuscript body, only as a brief example of a conventional semi-quantitative method. It must not be used repeatedly as the principal contrast for the study's novelty.
3. The preferred contribution framing should state what the study actually contributes rather than repeatedly explaining what Fine–Kinney does not provide.
4. Do not state that the proposed method is derived from, extends, or replaces Fine–Kinney unless a formal mapping between its probability/exposure/severity scales and the study's variables is documented.
5. The current citation `[51]` at the opening of Section 5.2 is a Fine–Kinney-based occupational-health study and does not support the manuscript's claims about a dynamic, real-time, ML-based framework. It should be removed from that sentence or replaced with a source that actually supports the stated claim. A citation is not needed when the sentence describes the present study's own verified design.
6. After tracked deletions are accepted, references devoted only to removed Fine–Kinney passages must be checked for orphaned citations and deleted from the bibliography if they are no longer cited elsewhere.

## Preferred concise contextual sentence
If one named mention is retained, use only a single sentence in the Introduction or Background:

`Conventional semi-quantitative risk-assessment methods, including Fine–Kinney, typically combine ordinal estimates of likelihood, exposure, and consequence; in construction settings, their results may remain sensitive to expert judgment and may not represent changing worker-, task-, and site-level conditions.`

The sentence should be supported by one directly relevant source or a compact citation group, not by a long method-by-method literature review.

## Preferred opening for Section 5.2
`The contribution of this study lies in linking a large administrative accident dataset to three prespecified outcome analyses and translating the resulting model outputs into a structured mobile decision-support workflow. Within each analysis, complementary classifiers were evaluated under a common preprocessing and validation pipeline, and the application organizes worker-, work-area-, equipment-, and accident-related information into interpretable risk outputs. The framework should therefore be presented as a study-specific data-driven prioritization and application-integration approach rather than as a universal replacement for established risk-assessment methods.`

This wording deliberately avoids unsupported claims of real-time adaptation, universal superiority, multimodal operation, or external validation. Those claims are governed by Comments 1, 12, 25, and 27.

## Manuscript-wide consistency actions
- Retain either the concise Introduction mention or a concise Background mention, not both.
- Remove repeated definitions of `R = P × E × S` unless the equation is directly required by the proposed method.
- Replace phrases such as `unlike Fine–Kinney` and `building on Fine–Kinney logic` with direct descriptions of the study's verified design.
- Reframe Section 5.2 around auditable contributions: outcome definitions, comparative ML evaluation, structured risk components, and application integration.
- Conduct a final citation audit for references `[40]–[46]`, `[51]`, and `[52]` after accepting tracked deletions.

## Reviewer-response draft
`Revised. The repeated Fine–Kinney discussion was removed from Section 5.2, and the contribution section was refocused on the study's own verified data, modeling analyses, and application-integration workflow. Fine–Kinney is retained, if at all, only as one concise contextual example in the introductory literature framing. We also removed the mismatched Fine–Kinney citation from the sentence describing the proposed ML framework and will delete any references that become uncited after the tracked deletions are accepted.`

## Status
Finalized. The Section 5.2 Fine–Kinney paragraph will remain deleted, and the manuscript will use no more than one concise contextual mention in the body.