from pathlib import Path
import json, os, re, subprocess, sys
project = Path(r"C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence")
out = Path(r"C:\AAYS1_GITHUB_BRIDGE\chat_gpt_clone_1\ai-results")
service_path = project / "app" / "services" / "contractor_export_service.py"
service_path.parent.mkdir(parents=True, exist_ok=True)
service_code = r'''
from __future__ import annotations

import csv
import json
import os
from pathlib import Path
from typing import Any

EXPORT_ROOT = Path(os.environ.get("AAYS_CONTRACTOR_EXPORT_ROOT", r"E:\AAYS_DATA\contractor\exports"))

FILES = {
    "companies": "contractors_for_app.csv",
    "companies_jsonl": "contractors_for_app.jsonl",
    "projects": "contractor_projects_for_app.csv",
    "parcel_matches": "contractor_parcel_matches_for_app.csv",
    "manifest": "export_manifest.json",
}

CONTACT_SUPPRESSION_NOTE = (
    "DO_NOT_CONTACT gate is enforced upstream in contractor_export_for_app.py; "
    "this API only serves app-ready export files and does not rehydrate suppressed contact fields."
)


def _path(key: str) -> Path:
    if key not in FILES:
        raise KeyError(key)
    return EXPORT_ROOT / FILES[key]


def export_status() -> dict[str, Any]:
    files: dict[str, Any] = {}
    for key, filename in FILES.items():
        path = EXPORT_ROOT / filename
        files[key] = {
            "filename": filename,
            "path": str(path),
            "exists": path.exists(),
            "bytes": path.stat().st_size if path.exists() else 0,
            "modified_at": path.stat().st_mtime if path.exists() else None,
        }
    return {"export_root": str(EXPORT_ROOT), "files": files, "contact_rule": CONTACT_SUPPRESSION_NOTE}


def read_csv_rows(key: str, *, limit: int = 100, offset: int = 0) -> dict[str, Any]:
    limit = max(1, min(int(limit), 1000))
    offset = max(0, int(offset))
    path = _path(key)
    if not path.exists():
        return {"key": key, "exists": False, "rows": [], "count": 0, "limit": limit, "offset": offset}
    rows: list[dict[str, Any]] = []
    total = 0
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if total >= offset and len(rows) < limit:
                rows.append(dict(row))
            total += 1
    return {"key": key, "exists": True, "count": total, "limit": limit, "offset": offset, "rows": rows}


def read_manifest() -> dict[str, Any]:
    path = _path("manifest")
    if not path.exists():
        return {"exists": False, "manifest": None}
    with path.open("r", encoding="utf-8-sig") as f:
        return {"exists": True, "manifest": json.load(f)}
'''
service_path.write_text(service_code, encoding='utf-8')
route_dir_candidates = [project/'app'/'api'/'routes', project/'app'/'routers', project/'app'/'routes']
route_dir = next((p for p in route_dir_candidates if p.exists()), project/'app'/'api'/'routes')
route_dir.mkdir(parents=True, exist_ok=True)
route_path = route_dir / 'contractor_exports.py'
rel = route_path.relative_to(project).with_suffix('')
import_module = '.'.join(rel.parts)
route_code = r'''
from __future__ import annotations

from fastapi import APIRouter, Query

from app.services.contractor_export_service import export_status, read_csv_rows, read_manifest

router = APIRouter(prefix="/api/contractors", tags=["contractors"])


@router.get("/status")
def contractor_export_status():
    return export_status()


@router.get("/companies")
def contractor_companies(limit: int = Query(100, ge=1, le=1000), offset: int = Query(0, ge=0)):
    return read_csv_rows("companies", limit=limit, offset=offset)


@router.get("/projects")
def contractor_projects(limit: int = Query(100, ge=1, le=1000), offset: int = Query(0, ge=0)):
    return read_csv_rows("projects", limit=limit, offset=offset)


@router.get("/parcel-matches")
def contractor_parcel_matches(limit: int = Query(100, ge=1, le=1000), offset: int = Query(0, ge=0)):
    return read_csv_rows("parcel_matches", limit=limit, offset=offset)


@router.get("/manifest")
def contractor_manifest():
    return read_manifest()
'''
route_path.write_text(route_code, encoding='utf-8')
main_path = project/'app'/'main.py'
main_changed = False
if main_path.exists():
    text = main_path.read_text(encoding='utf-8')
    import_line = f"from {import_module} import router as contractor_exports_router"
    if import_line not in text:
        lines = text.splitlines()
        insert_at = 0
        for i, line in enumerate(lines):
            if line.startswith('from ') or line.startswith('import '):
                insert_at = i + 1
        lines.insert(insert_at, import_line)
        text = '\n'.join(lines) + '\n'
        main_changed = True
    if 'contractor_exports_router' not in re.sub(r'^from .*contractor_exports.*$', '', text, flags=re.M):
        text = text.rstrip() + "\n\napp.include_router(contractor_exports_router)\n"
        main_changed = True
    main_path.write_text(text, encoding='utf-8')
compile_targets = [str(service_path), str(route_path)] + ([str(main_path)] if main_path.exists() else [])
compile_result = subprocess.run([sys.executable, '-m', 'py_compile', *compile_targets], cwd=str(project), capture_output=True, text=True)
progress = 75 if compile_result.returncode == 0 else 65
report = {
    'task_id': 'ty136-patch-contractor-exports-api',
    'service_path': str(service_path),
    'route_path': str(route_path),
    'route_import_module': import_module,
    'main_path': str(main_path),
    'main_changed': main_changed,
    'compile_returncode': compile_result.returncode,
    'compile_stdout': compile_result.stdout,
    'compile_stderr': compile_result.stderr,
    'plan_progress_percent': progress,
    'plan_percent_remaining': 100-progress,
    'endpoints': ['/api/contractors/status','/api/contractors/companies','/api/contractors/projects','/api/contractors/parcel-matches','/api/contractors/manifest'],
}
(out/'ty136-patch-contractor-exports-api.audit.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
md = ['# TY136 Patch Contractor Exports API','',f"Plan completed: {progress}%",f"Plan remaining: {100-progress}%",'',f"Service: {service_path}",f"Router: {route_path}",f"Main changed: {main_changed}",f"Compile return code: {compile_result.returncode}",'','## Endpoints'] + [f'- {e}' for e in report['endpoints']] + ['', '## Compile stderr', compile_result.stderr or '(none)', '', '## Next Action', 'Run FastAPI smoke test against contractor export endpoints.']
(out/'ty136-patch-contractor-exports-api.report.md').write_text('\n'.join(md), encoding='utf-8')
print('PLAN_PROGRESS_PERCENT='+str(progress))
print('PLAN_PERCENT_REMAINING='+str(100-progress))
