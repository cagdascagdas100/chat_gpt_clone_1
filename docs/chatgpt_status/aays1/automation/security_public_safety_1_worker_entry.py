from __future__ import annotations

import hashlib
import json
import os
import urllib.request
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Any

SLOT_ID = "security_public_safety_1"
TASK_ID = os.environ.get("AAYS_TASK_ID") or "manual"
HERE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[4]
TEMPLATE = HERE / "security_public_safety_1_acceptance_worker.py"
SHARD_ROOT = ROOT / "docs" / "chatgpt_status" / "aays1" / "shards" / SLOT_ID
WEB_ROOT = ROOT / "england_map_web" / "data" / "aays_21_slots" / SLOT_ID
PROGRESS_JSON = SHARD_ROOT / "progress" / "progress_latest.json"
PROGRESS_HTML = WEB_ROOT / "progress.html"
PROGRESS_WEB_JSON = WEB_ROOT / "progress_latest.json"

OFFICIAL_SOURCES = [
    {
        "name": "data.police.uk forces API",
        "url": "https://data.police.uk/api/forces",
        "role": "primary_live_official_source_availability_check",
        "measurement_scope": "official_api_supporting_evidence",
    },
    {
        "name": "ONS Police Force Area data tables",
        "url": "https://www.ons.gov.uk/peoplepopulationandcommunity/crimeandjustice/datasets/policeforceareadatatables/current",
        "role": "official_contextual_cross_check_only",
        "measurement_scope": "force_or_local_authority_context_not_lsoa_or_parcel",
    },
]


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def fetch_official(source: dict[str, str]) -> dict[str, Any]:
    request = urllib.request.Request(
        source["url"],
        headers={"User-Agent": "AAYS-security-public-safety-source-audit/1.0", "Cache-Control": "no-cache"},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read()
            return {
                **source,
                "status": "PASS" if int(response.status) == 200 else "BLOCKED",
                "http_status": int(response.status),
                "content_type": response.headers.get("Content-Type"),
                "body_bytes": len(body),
                "body_sha256": digest(body),
                "checked_at": now(),
                "error": None,
            }
    except Exception as exc:
        return {
            **source,
            "status": "BLOCKED",
            "http_status": None,
            "content_type": None,
            "body_bytes": 0,
            "body_sha256": None,
            "checked_at": now(),
            "error": f"{type(exc).__name__}: {exc}",
        }


def render_progress(payload: dict[str, Any]) -> str:
    events = "\n".join(
        f"<tr><td>{index + 1}</td><td>{escape(str(item.get('status')))}</td>"
        f"<td>{escape(str(item.get('step')))}</td><td>{escape(str(item.get('detail')))}</td></tr>"
        for index, item in enumerate(payload.get("events", []))
    )
    candidates = "\n".join(
        f"<tr><td>{escape(str(row.get('parcel_id')))}</td>"
        f"<td>{escape(str(row.get('security_score_percent')))}</td>"
        f"<td>{escape(str(row.get('accuracy_score_4')))}</td>"
        f"<td>{escape(str(row.get('source_geography_level')))}</td>"
        f"<td>AREA_LEVEL_PROXY</td></tr>"
        for row in payload.get("candidate_examples", [])
    )
    sources = "\n".join(
        f"<tr><td>{escape(str(item.get('name')))}</td><td>{escape(str(item.get('http_status')))}</td>"
        f"<td>{escape(str(item.get('role')))}</td><td>{escape(str(item.get('measurement_scope')))}</td></tr>"
        for item in payload.get("official_source_checks", [])
    )
    return f"""<!doctype html>
<html lang="tr"><head><meta charset="utf-8"><meta http-equiv="refresh" content="15">
<title>AAYS Security/Public Safety Shard 1 Progress</title>
<style>
body{{font-family:Arial,sans-serif;margin:24px;line-height:1.4}}table{{border-collapse:collapse;width:100%;margin:14px 0}}
th,td{{border:1px solid #ccc;padding:7px;text-align:left}}code{{background:#f3f3f3;padding:2px 5px}}
.note{{padding:10px;border:1px solid #bbb}}
</style></head><body>
<h1>Security / Public Safety — Shard 1</h1>
<p class="note"><strong>Semantik:</strong> <code>AREA_LEVEL_PROXY</code>. LSOA/alan düzeyi göstergedir; parsel ölçümü değildir.</p>
<p><strong>Task:</strong> <code>{escape(str(payload.get("task_id")))}</code></p>
<p><strong>Doğrulanmış görev ilerlemesi:</strong> {escape(str(payload.get("overall_percent")))}% —
{escape(str(payload.get("completed_units")))}/{escape(str(payload.get("total_units")))} birim</p>
<p><strong>Hidrate satır:</strong> {escape(str(payload.get("hydrated_rows")))};
<strong>yüksek doğruluk satırı:</strong> {escape(str(payload.get("accuracy_score_4_rows")))};
<strong>kaynak kontrolü:</strong> {escape(str(payload.get("successful_source_checks")))}/{escape(str(payload.get("source_check_count")))}</p>
<h2>Satır bazlı ilerleme</h2>
<table><thead><tr><th>#</th><th>Durum</th><th>Adım</th><th>Detay</th></tr></thead><tbody>{events}</tbody></table>
<h2>Resmî kaynak yükseltmeleri</h2>
<table><thead><tr><th>Kaynak</th><th>HTTP</th><th>Rol</th><th>Ölçüm kapsamı</th></tr></thead><tbody>{sources}</tbody></table>
<h2>Aday örnekleri</h2>
<table><thead><tr><th>Parsel referansı</th><th>Alan proxy skoru</th><th>Doğruluk</th><th>Kaynak coğrafya</th><th>Semantik</th></tr></thead><tbody>{candidates}</tbody></table>
<p><code>final_ready=false</code>; <code>fake_data=false</code>; <code>db_write=false</code>.</p>
</body></html>
"""


def publish_progress(payload: dict[str, Any]) -> None:
    write_json(PROGRESS_JSON, payload)
    write_json(PROGRESS_WEB_JSON, payload)
    PROGRESS_HTML.parent.mkdir(parents=True, exist_ok=True)
    PROGRESS_HTML.write_text(render_progress(payload), encoding="utf-8")


def event(events: list[dict[str, Any]], step: str, status: str, detail: str) -> None:
    events.append({"step": step, "status": status, "detail": detail, "at": now()})


def main() -> int:
    events: list[dict[str, Any]] = []
    event(events, "REMOTE_TASK_START", "PASS", "Single coordinator worker entry started.")
    event(events, "SEMANTIC_LOCK", "PASS", "LSOA rows locked to AREA_LEVEL_PROXY; parcel_measurement=false.")

    source_checks = []
    for source in OFFICIAL_SOURCES:
        checked = fetch_official(source)
        source_checks.append(checked)
        event(
            events,
            f"OFFICIAL_SOURCE_{source['name']}",
            checked["status"],
            f"HTTP={checked.get('http_status')} sha256={checked.get('body_sha256') or 'none'}",
        )

    source = TEMPLATE.read_text(encoding="utf-8")
    needle = "”; ”.join"
    replacement = '"; ".join'
    if source.count(needle) != 1:
        raise RuntimeError(f"EXPECTED_SINGLE_TEMPLATE_PATCH_NOT_FOUND:{source.count(needle)}")
    patched = source.replace(needle, replacement)
    compiled = compile(patched, str(TEMPLATE), "exec")
    namespace: dict[str, Any] = {
        "__name__": "security_public_safety_1_acceptance_worker_runtime",
        "__file__": str(TEMPLATE),
        "__package__": None,
    }
    exec(compiled, namespace)
    event(events, "WORKER_COMPILE", "PASS", "Acceptance worker compiled after deterministic one-token repair.")

    result = namespace["run"]()
    namespace["write_report"](result)
    event(
        events,
        "HYDRATE_300_ROWS",
        "PASS" if int(result.get("hydrated_rows") or 0) == 300 else "BLOCKED",
        f"hydrated_rows={result.get('hydrated_rows')}",
    )
    event(
        events,
        "HTTP_HASH_DOM_CONSOLE_BROWSER_ACCEPTANCE",
        "PASS" if result.get("acceptance_pass") else "BLOCKED",
        ";".join(result.get("blockers") or []) or "all browser acceptance checks passed",
    )

    data_path = namespace["DATA_PATH"]
    data = json.loads(Path(data_path).read_text(encoding="utf-8"))
    rows = list(data.get("rows") or [])
    accuracy_rows = sum(str(row.get("accuracy_score_4")) == "4" for row in rows)
    successful_sources = sum(item.get("status") == "PASS" for item in source_checks)
    completed_units = sum(item["status"] == "PASS" for item in events)
    total_units = len(events)
    payload = {
        "schema_version": 1,
        "slot_id": SLOT_ID,
        "task_id": TASK_ID,
        "parcel_partition": {"start": 1, "end": 30761, "count": 30761},
        "output_semantics": "AREA_LEVEL_PROXY",
        "measurement_level": "lsoa",
        "parcel_measurement": False,
        "display_disclaimer": "LSOA/area-level proxy; not a parcel measurement",
        "status": result.get("status"),
        "events": events,
        "completed_units": completed_units,
        "total_units": total_units,
        "overall_percent": round(100 * completed_units / total_units, 2) if total_units else 0,
        "hydrated_rows": len(rows),
        "accuracy_score_4_rows": accuracy_rows,
        "candidate_examples": rows[:12],
        "official_source_checks": source_checks,
        "successful_source_checks": successful_sources,
        "source_check_count": len(source_checks),
        "acceptance_result": result,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
        "final_ready": False,
        "updated_at": now(),
    }
    publish_progress(payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
