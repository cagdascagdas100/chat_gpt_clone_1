# OHS Manuscript Revision — Current Status

- Total reviewer comments: 32
- Processed through: Comment 28
- Processed: 28/32 = 87.5%
- Fully finalized: 21/32 = 65.625%
- Conditional items: Comment 12 (scenario provenance), Comment 15 (authoritative equipment inventory), Comment 17 (internal–external weighting), Comment 18 (regional-decay value selection), Comment 20 (final composite depends on Comment 17 and the missing fifth-region input), Comment 23 (original high-resolution landing-page and personal-input screenshots), and Comment 24 (meaning of `yz`)
- Next item: Comment 29

## Latest decision — Comment 28
The sentence claiming that LLM adaptability ensures continuous knowledge-base updates will be deleted in full. No replacement wording will imply that the deployed OSH-RA application uses runtime LLM inference, autonomous updating, or continuous adaptation.

## Evidence and architecture findings
- No deployed LLM provider, model identifier, dated version, access route, or generation log is documented.
- No retrieval pipeline, external knowledge store, ingestion process, versioning, approval, rollback, monitoring, or revalidation mechanism is documented.
- The verified architecture consists of structured inputs, offline-trained classifiers, deterministic aggregation and ranking rules, and presentation of decision-support outputs.
- An LLM alone does not ensure that an external knowledge base is updated; such a claim would require an explicit governed update architecture and validation evidence.

## Citation and wording corrections
- Reference `[121]` concerns ChatGPT-assisted causal-factor extraction from crane-accident reports and complex-network analysis; it does not support continuous knowledge-base updating in OSH-RA.
- References `[119]–[121]` must be re-audited after the paragraph is revised and retained only for precise literature-context statements.
- RAG, multimodal sensing, sensor integration, dynamic scenario generation, and adaptive retraining may be mentioned only as unimplemented future work, not as present-system capabilities.

## Cross-comment consistency updates
- Comments 1 and 12 govern manuscript-wide removal of unverified LLM claims.
- Comment 27 defines the verified application architecture and removes unsupported multimodal and superiority claims.
- The revised transition will describe structured inputs, offline-trained classifiers, deterministic rules, and decision-support outputs, while explicitly stating that runtime LLM inference and automatic updating were not evaluated.

## Next item
Comment 29 — rebuild the calibration and technical-metric discussion so ECE and Brier score are either explained in plain language and used only where necessary or removed from the main narrative.