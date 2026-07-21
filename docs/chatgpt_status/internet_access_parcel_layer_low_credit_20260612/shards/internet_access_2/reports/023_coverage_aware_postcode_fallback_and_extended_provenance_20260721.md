# internet_access_2 coverage-aware postcode fallback and extended provenance

- Scope: canonical rows 30,762–61,522 only.
- Official source remains Ofcom Connected Nations Spring 2026, January 2026 snapshot, corrected V2/r2 payload.
- New fail-closed rule: when the canonical postcode is syntactically valid but absent from current r2, a different valid legacy postcode may be selected only when that legacy postcode is present in current r2.
- Such a row remains `LEGACY_POSTCODE_PROXY`, confidence `0.70`, and pending spatial QA. It can never be promoted to a direct canonical match.
- Canonical current-r2 evidence retains precedence over conflicting legacy evidence.
- Selected origin, canonical/legacy current-r2 membership, conflict state and coverage-fallback reason remain visible in every candidate row.
- The runtime carrier creates a work-root copy of the existing inner runner, requires exactly one extractor substitution and records base/runtime SHA-256 values.
- Provenance is extended from 12 to 16 artifacts by adding the carrier, review-consistency audit, coverage-aware postcode audit and complete candidate-integrity audit.
- Deterministic contract: 404/404.
- Website: operations 1–145; 144 complete; only #145 remains blocked on the existing shared runner and readiness gates.
- Real slot rows produced: 0/30,761.
- Business rows, scores, DB writes, migrations and deployments: 0.
- `final_ready=false`.
