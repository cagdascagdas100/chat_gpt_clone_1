$ErrorActionPreference='Continue'
$TaskId='ty137-contractor-exports-api-smoke'
$Bridge='C:\AAYS1_GITHUB_BRIDGE\chat_gpt_clone_1'
$Project='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$Out=Join-Path $Bridge 'ai-results'
New-Item -ItemType Directory -Force -Path $Out | Out-Null
$py=Join-Path $Out 'ty137_contractor_exports_api_smoke.py'
@'
from pathlib import Path
import importlib
import json
import os
import sys
import traceback

project = Path(r"C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence")
out = Path(r"C:\AAYS1_GITHUB_BRIDGE\chat_gpt_clone_1\ai-results")
os.environ.setdefault("AAYS_CONTRACTOR_EXPORT_ROOT", r"E:\AAYS_DATA\contractor\exports")
sys.path.insert(0, str(project))

results = []
errors = []
progress = 75

try:
    svc = importlib.import_module("app.services.contractor_export_service")
    status = svc.export_status()
    files = status.get("files", {})
    all_present = all(v.get("exists") for v in files.values())
    companies = svc.read_csv_rows("companies", limit=3, offset=0)
    projects = svc.read_csv_rows("projects", limit=3, offset=0)
    matches = svc.read_csv_rows("parcel_matches", limit=3, offset=0)
    manifest = svc.read_manifest()
    results.append({"check": "service_import", "ok": True})
    results.append({"check": "export_files_present", "ok": all_present, "files": files})
    results.append({"check": "companies_rows", "ok": companies.get("count", 0) > 0, "count": companies.get("count")})
    results.append({"check": "projects_rows", "ok": projects.get("count", 0) > 0, "count": projects.get("count")})
    results.append({"check": "parcel_match_rows", "ok": matches.get("count", 0) > 0, "count": matches.get("count")})
    results.append({"check": "manifest_read", "ok": bool(manifest.get("exists")), "manifest_exists": manifest.get("exists")})
except Exception as exc:
    errors.append({"stage": "service_smoke", "error": repr(exc), "traceback": traceback.format_exc()})

try:
    from fastapi.testclient import TestClient
    from app.main import app
    client = TestClient(app)
    endpoints = [
        "/api/contractors/status",
        "/api/contractors/companies?limit=2",
        "/api/contractors/projects?limit=2",
        "/api/contractors/parcel-matches?limit=2",
        "/api/contractors/manifest",
    ]
    for ep in endpoints:
        r = client.get(ep)
        results.append({"check": "endpoint", "endpoint": ep, "ok": r.status_code == 200, "status_code": r.status_code})
except Exception as exc:
    errors.append({"stage": "fastapi_testclient", "error": repr(exc), "traceback": traceback.format_exc()})

ok = bool(results) and all(item.get("ok") for item in results) and not errors
if ok:
    progress = 90
elif any(item.get("ok") for item in results):
    progress = 82
else:
    progress = 75

audit = {
    "task_id": "ty137-contractor-exports-api-smoke",
    "results": results,
    "errors": errors,
    "ok": ok,
    "plan_progress_percent": progress,
    "plan_percent_remaining": 100 - progress,
    "next_action": "Commit app API patch and run dashboard/UI wiring." if ok else "Fix smoke-test errors before UI wiring.",
}
(out / "ty137-contractor-exports-api-smoke.audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
md = ["# TY137 Contractor Exports API Smoke", "", f"Plan completed: {progress}%", f"Plan remaining: {100-progress}%", f"Smoke OK: {ok}", "", "## Results"]
for item in results:
    md.append(f"- {item}")
md += ["", "## Errors"]
if errors:
    for err in errors:
        md.append(f"- stage={err.get('stage')} error={err.get('error')}")
        md.append("```text")
        md.append((err.get("traceback") or "")[:4000])
        md.append("```")
else:
    md.append("(none)")
md += ["", "## Next Action", audit["next_action"]]
(out / "ty137-contractor-exports-api-smoke.report.md").write_text("\n".join(md), encoding="utf-8")
print("PLAN_PROGRESS_PERCENT=" + str(progress))
print("PLAN_PERCENT_REMAINING=" + str(100-progress))
'@ | Set-Content -Encoding UTF8 $py
python $py
exit 0
