# 049 — Evidence-backed Scoring Plan

Goal: Define a scoring update pipeline that can later produce a new candidate GeoJSON, but do not replace active data automatically.

Outputs:
- candidate_scoring_methodology.md
- candidate_output_schema.json
- no_downgrade_rules.json
- qa_acceptance_criteria.md

Rules:
- Candidate output must be separate from active `parcel_security_scores_rechecked_0_120m_spatial.geojson`.
- Low confidence records must remain review unless evidence threshold is met.
