# Runner Task Queue Templates (TR)

Bu dosya, watchdog uzerinden "devam et" akisinda kullanilacak ornek task JSON payloadlarini verir. Secret alan yazilmaz.

## Template 1 - 079 Preflight
```json
{
  "id": "terrayield-079-contractor-db-env-loader-preflight",
  "title": "TerraYield Contractor DB Env Loader Preflight",
  "progress": 58,
  "working_directory": "C:\\AAYS1_GITHUB_BRIDGE\\chat_gpt_clone_1",
  "timeout_seconds": 300,
  "created_by": "Codex",
  "script_path": "terrayield_079_contractor_db_env_loader_preflight.ps1",
  "note": "Load DB credentials from safe local env locations or runner secrets without logging secret values, then run DB preflight."
}
```

## Template 2 - Schema Apply
```json
{
  "id": "terrayield-080-contractor-schema-apply",
  "title": "TerraYield Contractor Schema Apply",
  "progress": 65,
  "working_directory": "C:\\AAYS1_GITHUB_BRIDGE\\chat_gpt_clone_1",
  "timeout_seconds": 600,
  "created_by": "Codex",
  "script_path": "terrayield_080_contractor_schema_apply.ps1",
  "note": "Apply contractor schema to target PostgreSQL/Supabase with secret-safe logging."
}
```

## Template 3 - DB Load
```json
{
  "id": "terrayield-081-contractor-db-load",
  "title": "TerraYield Contractor DB Load",
  "progress": 72,
  "working_directory": "C:\\AAYS1_GITHUB_BRIDGE\\chat_gpt_clone_1",
  "timeout_seconds": 1200,
  "created_by": "Codex",
  "script_path": "terrayield_081_contractor_db_load.ps1",
  "note": "Load normalized contractor datasets into DB tables using safe env loader."
}
```

## Template 4 - Parcel Match + Export
```json
{
  "id": "terrayield-082-contractor-match-export",
  "title": "TerraYield Contractor Parcel Match and App Export",
  "progress": 86,
  "working_directory": "C:\\AAYS1_GITHUB_BRIDGE\\chat_gpt_clone_1",
  "timeout_seconds": 1200,
  "created_by": "Codex",
  "script_path": "terrayield_082_contractor_match_export.ps1",
  "note": "Run parcel match and app export, then write secret-free audit summary."
}
```

## Template 5 - Final Audit
```json
{
  "id": "terrayield-083-contractor-final-audit",
  "title": "TerraYield Contractor Final Audit",
  "progress": 100,
  "working_directory": "C:\\AAYS1_GITHUB_BRIDGE\\chat_gpt_clone_1",
  "timeout_seconds": 300,
  "created_by": "Codex",
  "script_path": "terrayield_083_contractor_final_audit.ps1",
  "note": "Collect final booleans and counts; do not output secret values."
}
```

## Template 6 - Future Growth Fixture All + Frontend Smoke
```json
{
  "id": "terrayield-084-future-growth-all-fixture",
  "title": "TerraYield Future Growth Fixture All Pipeline",
  "progress": 92,
  "working_directory": "C:\\AAYS1_GITHUB_BRIDGE\\chat_gpt_clone_1",
  "timeout_seconds": 1800,
  "created_by": "Codex",
  "script_path": "terrayield_084_future_growth_all_fixture.ps1",
  "note": "Run future-growth:all --mode fixture and frontend layer+popup smoke, then write sanitized audit."
}
```

Bridge script source (repo): `C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\scripts\terrayield_084_future_growth_all_fixture.ps1`

## Kullanım
1. Istenen template'i `ai-tasks/aays1-current-task.json` dosyasina yaz.
2. Watchdog polling durumunda task'i alir.
3. Sonuc `ai-results` veya `ai-handoff` altinda dogrulanir.
4. Rapor sadece boolean/status + sayim alanlari icerir.
