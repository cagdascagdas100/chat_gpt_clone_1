# 047 — Security Accuracy Source Catalog and Evidence Templates

Goal: Do not change active security scores. Create `security_accuracy_expansion/` with source catalog, evidence templates, schemas and QA manifests.

Steps:
1. Audit repo paths.
2. Copy this ZIP contents into `D:\topografik_map\security_module\security_accuracy_expansion`.
3. Validate JSON and CSV headers.
4. Create a run report.
5. PASS only if no existing frontend/data files are modified.

PASS:
- source catalog exists
- evidence templates exist
- schemas exist
- run report exists
- active security GeoJSON unchanged
