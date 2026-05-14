# TY137 Contractor Exports API Smoke

Plan completed: 90%
Plan remaining: 10%
Smoke OK: True

## Results
- {'check': 'service_import', 'ok': True}
- {'check': 'export_files_present', 'ok': True, 'files': {'companies': {'filename': 'contractors_for_app.csv', 'path': 'E:\\AAYS_DATA\\contractor\\exports\\contractors_for_app.csv', 'exists': True, 'bytes': 63729, 'modified_at': 1778754098.979146}, 'companies_jsonl': {'filename': 'contractors_for_app.jsonl', 'path': 'E:\\AAYS_DATA\\contractor\\exports\\contractors_for_app.jsonl', 'exists': True, 'bytes': 280330, 'modified_at': 1778754102.369159}, 'projects': {'filename': 'contractor_projects_for_app.csv', 'path': 'E:\\AAYS_DATA\\contractor\\exports\\contractor_projects_for_app.csv', 'exists': True, 'bytes': 405940, 'modified_at': 1778754102.6041677}, 'parcel_matches': {'filename': 'contractor_parcel_matches_for_app.csv', 'path': 'E:\\AAYS_DATA\\contractor\\exports\\contractor_parcel_matches_for_app.csv', 'exists': True, 'bytes': 5688, 'modified_at': 1778754102.7469602}, 'manifest': {'filename': 'export_manifest.json', 'path': 'E:\\AAYS_DATA\\contractor\\exports\\export_manifest.json', 'exists': True, 'bytes': 867, 'modified_at': 1778754102.802961}}}
- {'check': 'companies_rows', 'ok': True, 'count': 317}
- {'check': 'projects_rows', 'ok': True, 'count': 421}
- {'check': 'parcel_match_rows', 'ok': True, 'count': 29}
- {'check': 'manifest_read', 'ok': True, 'manifest_exists': True}
- {'check': 'endpoint', 'endpoint': '/api/contractors/status', 'ok': True, 'status_code': 200}
- {'check': 'endpoint', 'endpoint': '/api/contractors/companies?limit=2', 'ok': True, 'status_code': 200}
- {'check': 'endpoint', 'endpoint': '/api/contractors/projects?limit=2', 'ok': True, 'status_code': 200}
- {'check': 'endpoint', 'endpoint': '/api/contractors/parcel-matches?limit=2', 'ok': True, 'status_code': 200}
- {'check': 'endpoint', 'endpoint': '/api/contractors/manifest', 'ok': True, 'status_code': 200}

## Errors
(none)

## Next Action
Commit app API patch and run dashboard/UI wiring.