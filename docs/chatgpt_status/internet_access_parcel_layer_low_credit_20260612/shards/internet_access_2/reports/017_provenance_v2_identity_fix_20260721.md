# V2 identity provenance fix

The official Ofcom V2 validation report is a source report, not a slot-owned row artifact. The single-run provenance verifier therefore binds it by exact source identity instead of requiring a synthetic slot field:

- source: Ofcom Connected Nations Spring 2026 fixed broadband coverage
- snapshot: January 2026
- revision: v2-r2
- revision date: 7 July 2026

A wrong revision-date fixture is rejected. Provenance verifier contract: 20/20. Wrapper contract: 21/21. Combined deterministic contract: 178 checks. Real rows and business writes remain zero; final_ready remains false.
