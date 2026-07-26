# Distance Property Types Runner Notes

Executable runner script could not be committed from this ChatGPT environment.

Required behavior for the local single shared runner:

- Do not create parcel/property facts without evidence.
- Read a real source batch with parcel_id, geometry or centroid, distance fields, and official/web/map/photo evidence.
- Accept only rows with a valid property type and accuracy_score_4 at least 3.0.
- Put weak, unknown, or conflicting rows into manual review.
- Keep fake_data=false, db_write=false, ddl=false, migration_apply=false, and prod_deploy=false.
- Keep final_ready=false until GeoJSON parsing, site layer rendering, popup/right-panel fields, and the Guncel degisiklikler filter are verified.

Expected executable path to create locally:

docs/chatgpt_status/distance_property_types/automation/distance_property_types_batch_runner.ps1
