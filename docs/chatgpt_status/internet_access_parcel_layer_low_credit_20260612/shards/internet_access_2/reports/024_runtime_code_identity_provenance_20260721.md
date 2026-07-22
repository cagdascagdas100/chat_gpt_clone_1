# Runtime execution-code identity and twenty-artifact provenance

A correctness gap was found in the sixteen-artifact review package: the carrier JSON contained base/runtime SHA-256 strings, but the extended verifier only checked their hexadecimal form. It did not recompute the hashes from actual runner files or prove that the generated runtime script contained only the intended extractor substitution.

The revised verifier recomputes and binds four execution-code artifacts: the canonical `009` base runner, generated runtime runner, coverage-aware `030` extractor and `036` carrier. It normalizes BOM and line endings, requires exactly one base extractor assignment, reconstructs the expected runtime script by replacing only `002` with `030`, and rejects every additional edit.

Deterministic fixtures pass 24/24 extended provenance, 54/54 wrapper, 22/22 website and 15/15 consistency checks; combined validation is 415/415. No official ZIP bytes, real parcel candidates, business rows, scores, database writes, migration, deployment, ownership, heartbeat, queue mutation or final-ready transition occurred.
