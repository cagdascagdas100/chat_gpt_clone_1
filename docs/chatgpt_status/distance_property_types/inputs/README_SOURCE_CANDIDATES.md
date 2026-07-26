# Distance Property Types Source Candidates

Required file:

`docs/chatgpt_status/distance_property_types/inputs/distance_property_types_source_candidates.csv`

The runner chain is working. If this CSV is missing or contains only the header, the runner must stop safely with `completed_no_real_evidence_rows`.

Minimum required columns:

- parcel_id
- geometry_wkt
- candidate_property_type
- official_source_evidence
- web_source_evidence
- map_source_evidence
- photo_ai_evidence
- source_date
- matching_method

Allowed candidate property types:

- Industrial Unit
- Detached Home
- Retail Property
- Apartment Building
- Office Building
- Mixed Building
- Unknown

Rules:

- Do not create fake rows.
- Rows with no evidence stay manual review.
- Rows with evidence conflicts stay manual review.
- Verified rows need evidence and a valid category.
- Safety flags remain false for db writes, schema changes, migrations, deployments, and fake data.
