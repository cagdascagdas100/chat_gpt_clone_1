# Comment 28 — Removal of the unsupported LLM adaptability and continuous-update claim

## Reviewer comment
`LLM zaten bahsetmeyelim demiştik bu cümle de mefta.`

## Selected sentence
`The adaptability of LLMs ensures continuous updates to the knowledge base, keeping the system responsive to the evolving nature of construction processes.`

## Decision
Delete the sentence in full. Do not replace it with another statement implying that the deployed OSH-RA application uses an LLM, automatically updates its knowledge base, or adapts continuously during operation.

## Evidence check
The available manuscript package and analytical artifacts do not document:
- a deployed LLM provider, model identifier, dated model version, or access route;
- a retrieval-augmented generation pipeline or external knowledge store;
- an ingestion, indexing, versioning, approval, rollback, or audit process for knowledge-base updates;
- an update schedule, change-detection mechanism, or expert-governance procedure;
- an evaluation showing that updated knowledge improves application performance or remains safe and consistent over time.

The verified application architecture instead consists of structured inputs, offline-trained classifiers, deterministic aggregation and ranking rules, and presentation of decision-support outputs. This architecture does not support the claim of autonomous or continuous LLM-driven updating.

## Technical correction
An LLM does not by itself ensure that an external knowledge base is continuously updated. A defensible continuous-update claim would require an explicit data-ingestion and retrieval architecture, source validation, version control, expert approval, monitoring, and re-evaluation after each update. None of these mechanisms is documented for the current system.

## Citation finding
Reference `[121]` describes ChatGPT-assisted extraction of causal factors from crane-accident reports and subsequent complex-network analysis. It does not establish that the proposed OSH-RA application maintains a continuously updated knowledge base or adapts automatically to changing construction processes. It must not be used to support the deleted sentence.

## Manuscript-wide consistency actions
- Apply the same removal logic to claims that OSH-RA uses an LLM at runtime, generates scenarios dynamically, updates itself continuously, or operates through multimodal inference unless implementation evidence is supplied.
- Keep any RAG-, multimodal-, sensor-, or LLM-based capability strictly in a clearly labeled future-work paragraph, and only if the paragraph states that these functions were not implemented or evaluated in the present study.
- Do not transfer evidence from external LLM studies to the present application as though it demonstrated OSH-RA functionality.
- Re-audit references `[119]–[121]` after the paragraph is revised; retain them only where they support a precise literature-context statement.

## Preferred revised transition
After removing the unsupported paragraph-level claims addressed in Comments 27 and 28, transition directly to the verified decision-support contribution:

`The OSH-RA application integrates structured user and worksite inputs with offline-trained classifiers and deterministic risk-ranking rules to present risk summaries and related decision-support information. The present study did not evaluate runtime LLM inference, automatic knowledge-base updating, multimodal sensing, or adaptive model retraining.`

## Reviewer-response draft
`Revised. The sentence claiming that LLM adaptability ensures continuous knowledge-base updates was removed. The available implementation records do not document a runtime LLM, retrieval pipeline, governed update mechanism, or validation of continuously updated content. The application is therefore described only in terms of its verified structured inputs, offline-trained classifiers, deterministic aggregation rules, and decision-support outputs.`

## Status
Finalized. The unsupported sentence is removed and no replacement LLM-adaptability claim will be introduced.