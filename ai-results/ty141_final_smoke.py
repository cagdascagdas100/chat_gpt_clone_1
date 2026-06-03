import os, sys, json
from pathlib import Path

project = Path(r"C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence")
os.environ.setdefault("AAYS_CONTRACTOR_EXPORT_ROOT", r"E:\AAYS_DATA\contractor\exports")
sys.path.insert(0, str(project))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
endpoints = [
    "/api/contractors/status",
    "/api/contractors/companies?limit=1",
    "/api/contractors/projects?limit=1",
    "/api/contractors/parcel-matches?limit=1",
    "/api/contractors/manifest",
]

results = []
ok = True
for ep in endpoints:
    r = client.get(ep)
    item = {"endpoint": ep, "status_code": r.status_code, "ok": r.status_code == 200}
    results.append(item)
    ok = ok and item["ok"]

print(json.dumps({"ok": ok, "results": results}, indent=2))
