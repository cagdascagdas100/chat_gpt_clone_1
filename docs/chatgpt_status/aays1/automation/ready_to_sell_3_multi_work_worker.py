from __future__ import annotations

import concurrent.futures
import hashlib
import html
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SLOT_ID = "ready_to_sell_3"
TASK_ID_DEFAULT = "aays1-ready-to-sell-3-automation-167-and-live-candidates-20260720"
WORKSTREAM_ID = "AAYS_21_SLOT_SAFE_PARALLEL_V1"
PARTITION = {"start": 61523, "end": 92283, "count": 30761, "canonical_count": 92283}

CANDIDATES = [
    {
        "candidate_id": "springvale-terrace-w14-live-20260720",
        "title": "1 Springvale Terrace",
        "location": "London, W14 0AE",
        "source_url": "https://www.rightmove.co.uk/properties/762013672911873",
        "publisher": "Rightmove / Savills",
        "source_class": "live_direct_listing",
        "expected_markers": ["1 Springvale Terrace", "6,250,000", "18 homes", "Freehold"],
        "price": "offers in excess of GBP 6,250,000",
        "marketing_status": "for_sale",
        "planning_signal": "resolution to grant planning permission for 18 homes; 50% affordable housing by unit number",
    },
    {
        "candidate_id": "broadway-ealing-w5-live-20260720",
        "title": "44-45 The Broadway",
        "location": "Ealing, W5 5JU",
        "source_url": "https://www.rightmove.co.uk/commercial-property-for-sale/W5.html",
        "publisher": "Rightmove / Savills",
        "source_class": "live_search_index",
        "expected_markers": ["44 - 45 The Broadway", "3,750,000", "residential-led planning permissions"],
        "price": "offers in excess of GBP 3,750,000",
        "marketing_status": "for_sale",
        "planning_signal": "residential-led planning permissions stated by live sales index",
    },
    {
        "candidate_id": "st-clare-court-tw12-live-20260720",
        "title": "St Clare Court",
        "location": "Hampton Hill, London, TW12",
        "source_url": "https://search.savills.com/property-detail/b5599839-9b12-43a3-8daf-b6f1aa6da90e",
        "publisher": "Savills",
        "source_class": "official_agent_direct_listing",
        "expected_markers": ["St Clare Court", "Under offer", "2.12 Ac", "22/2204/FUL", "100 homes"],
        "price": "price on application",
        "marketing_status": "under_offer",
        "planning_signal": "resolution to grant 86 flats, 14 houses and commercial floorspace; reference 22/2204/FUL",
    },
    {
        "candidate_id": "woodborough-road-sw15-live-20260720",
        "title": "22 & 24 Woodborough Road",
        "location": "London, SW15",
        "source_url": "https://www.rightmove.co.uk/properties/166553672",
        "publisher": "Rightmove / Savills",
        "source_class": "live_direct_listing",
        "expected_markers": ["22 & 24 Woodborough Road", "4,000,000", "residential development opportunity", "Lot 1", "Lot 2"],
        "price": "offers in excess of GBP 4,000,000",
        "marketing_status": "for_sale",
        "planning_signal": "development opportunity; planning history requires separate official review",
    },
    {
        "candidate_id": "woodborough-road-sw15-planning-history-20260720",
        "title": "22-24 Woodborough Road planning history",
        "location": "London, SW15 6PZ",
        "source_url": "https://planning.wandsworth.gov.uk/Northgate/PlanningExplorer/Generic/StdDetails.aspx?DAURI=PLANNING&FT=Planning+Application+Details&PARAM0=518807&PT=Planning+Applications+On-Line&PUBLIC=N&TYPE=PL%2FPlanningPK.xml&XMLSIDE=&XSLT=%2FNorthgate%2FPlanningExplorer%2FSiteFiles%2FSkins%2FWandsworth%2Fxslt%2FPL%2FPLDetailsSiteHistory.xslt",
        "publisher": "Wandsworth Council",
        "source_class": "official_planning_register",
        "expected_markers": ["22-24 Woodborough Road", "2019/2331", "Approve with Conditions", "2024/0589"],
        "price": null,
        "marketing_status": "planning_evidence_only",
        "planning_signal": "official site history includes approved 2019/2331 and later tree-work record 2024/0589",
    },
]

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()

def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return None

def repo_root() -> Path:
    completed = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if completed.returncode != 0 or not completed.stdout.strip():
        raise RuntimeError("REPO_ROOT_UNAVAILABLE")
    return Path(completed.stdout.strip()).resolve()

def fetch_source(candidate: dict[str, Any]) -> dict[str, Any]:
    request = urllib.request.Request(
        candidate["source_url"],
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; AAYS-TerraYield-Evidence/1.0; +https://github.com/cagdascagdas100/chat_gpt_clone_1)",
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-GB,en;q=0.9",
        },
    )
    started = utc_now()
    status = 0
    final_url = candidate["source_url"]
    raw = b""
    error = None
    headers: dict[str, str] = {}
    try:
        with urllib.request.urlopen(request, timeout=35) as response:
            status = int(response.status)
            final_url = response.geturl()
            headers = {str(k).lower(): str(v) for k, v in response.headers.items()}
            raw = response.read(8_000_000)
    except urllib.error.HTTPError as exc:
        status = int(exc.code)
        final_url = exc.geturl()
        error = f"HTTPError:{exc.code}"
        try:
            raw = exc.read(2_000_000)
        except Exception:
            raw = b""
    except Exception as exc:
        error = f"{type(exc).__name__}:{exc}"

    text = raw.decode("utf-8", errors="replace")
    normalized = re.sub(r"\s+", " ", html.unescape(text)).casefold()
    marker_results = {
        marker: marker.casefold() in normalized for marker in candidate["expected_markers"]
    }
    marker_count = sum(marker_results.values())
    marker_total = len(marker_results)
    live = status == 200 and marker_count >= max(2, marker_total - 1)
    if candidate["source_class"] == "official_planning_register":
        score = 98 if live and marker_count == marker_total else 90 if live else 0
    elif candidate["source_class"] == "official_agent_direct_listing":
        score = 97 if live and marker_count == marker_total else 90 if live else 0
    elif candidate["source_class"] == "live_direct_listing":
        score = 94 if live and marker_count == marker_total else 88 if live else 0
    else:
        score = 90 if live and marker_count == marker_total else 84 if live else 0

    return {
        **candidate,
        "retrieved_at": utc_now(),
        "request_started_at": started,
        "http_status": status,
        "final_url": final_url,
        "content_type": headers.get("content-type"),
        "content_length_bytes": len(raw),
        "sha256": sha256_bytes(raw) if raw else None,
        "marker_results": marker_results,
        "marker_match_count": marker_count,
        "marker_total": marker_total,
        "source_live_verified": live,
        "source_confidence_score": score,
        "parcel_match_confidence_score": 0,
        "geometry_match_status": "not_run",
        "promotion_allowed": False,
        "promotion_blocker": "CANONICAL_PARCEL_MATCH_AND_GEOMETRY_PROOF_NOT_RUN",
        "error": error,
    }

def http_status(url: str) -> tuple[int, str | None]:
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 AAYS-TerraYield"})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            response.read(1024)
            return int(response.status), None
    except urllib.error.HTTPError as exc:
        return int(exc.code), f"HTTPError:{exc.code}"
    except Exception as exc:
        return 0, f"{type(exc).__name__}:{exc}"

def find_browser(portable_root: Path | None) -> Path | None:
    candidates: list[Path] = []
    if portable_root:
        candidates.extend([
            portable_root / "runtime" / "browser" / "chrome.exe",
            portable_root / "runtime" / "chrome" / "chrome.exe",
            portable_root / "runtime" / "chromium" / "chrome.exe",
            portable_root / "runtime" / "msedge" / "msedge.exe",
        ])
    for env_name, relative in [
        ("PROGRAMFILES(X86)", "Microsoft/Edge/Application/msedge.exe"),
        ("PROGRAMFILES", "Microsoft/Edge/Application/msedge.exe"),
        ("PROGRAMFILES", "Google/Chrome/Application/chrome.exe"),
        ("PROGRAMFILES(X86)", "Google/Chrome/Application/chrome.exe"),
    ]:
        base = os.environ.get(env_name)
        if base:
            candidates.append(Path(base) / relative)
    for command in ("msedge", "chrome", "chromium"):
        discovered = shutil.which(command)
        if discovered:
            candidates.append(Path(discovered))
    return next((value for value in candidates if value.is_file()), None)

def read_int_attr(dom: str, name: str) -> int:
    match = re.search(rf'{re.escape(name)}=["\'](\d+)["\']', dom, flags=re.I)
    return int(match.group(1)) if match else 0

def build_html() -> str:
    return """<!doctype html>
<html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ReadyToSell 3 Canlı İşlem Akışı</title>
<style>
body{font-family:Segoe UI,Arial,sans-serif;margin:18px;background:#f5f7fa;color:#172033}
h1{margin:0 0 8px}.muted{color:#5b6678}.metrics{display:flex;gap:8px;flex-wrap:wrap;margin:12px 0}
.pill{background:#fff;border:1px solid #aab7c7;padding:7px}.ok{color:#08733f}.warn{color:#9a5b00}
table{border-collapse:collapse;width:100%;background:#fff;font-size:13px}th,td{border:1px solid #bdc7d4;padding:7px;vertical-align:top}
th{background:#dff7e9;position:sticky;top:0}.scroll{overflow:auto;max-height:72vh}
.event{padding:7px;background:#fff;border:1px solid #c3ccd8;margin:5px 0}
a{color:#075eb5;overflow-wrap:anywhere}
</style></head><body>
<h1>ReadyToSell 3 — İnternet Adayları ve İşlem Akışı</h1>
<div class="muted">SLOT_ID=ready_to_sell_3 · Parsel 61523-92283 · Adaylar canonical parsel/geometri kanıtı olmadan dataset'e yükseltilmez.</div>
<div id="metrics" class="metrics"></div><h2>İşlemler — satır satır</h2><div id="events"></div>
<h2>Doğrulanan adaylar</h2><div class="scroll"><table><thead><tr>
<th>Aday</th><th>Durum</th><th>Kaynak</th><th>HTTP / hash</th><th>İşaretler</th><th>Kaynak doğruluğu</th><th>Parsel</th><th>Sonraki iş</th>
</tr></thead><tbody id="rows"></tbody></table></div>
<script>
const esc=v=>String(v??'not_available').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const link=u=>`<a href="${esc(u)}" target="_blank" rel="noopener">${esc(u)}</a>`;
Promise.all([fetch('ready_to_sell_3_live_candidates_latest.json?v='+Date.now()).then(r=>r.json()),
fetch('ready_to_sell_3_progress_events_latest.json?v='+Date.now()).then(r=>r.json())]).then(([data,progress])=>{
const c=data.candidates||[], live=c.filter(x=>x.source_live_verified).length, hi=c.filter(x=>(x.source_confidence_score||0)>=90).length;
metrics.innerHTML=[`Aday: ${c.length}`,`Canlı doğrulanan: ${live}`,`≥90 kaynak doğruluğu: ${hi}`,
`Yükseltilen: ${c.filter(x=>x.promotion_allowed).length}`,`Genel ilerleme: ${progress.progress_percent}%`].map((x,i)=>`<span class="pill ${i<3?'ok':'warn'}">${esc(x)}</span>`).join('');
events.innerHTML=(progress.events||[]).map(e=>`<div class="event"><b>#${esc(e.sequence)} ${esc(e.event)}</b> — ${esc(e.result)}<br><span class="muted">${esc(e.detail)}</span></div>`).join('');
rows.innerHTML=c.map(x=>`<tr><td><b>${esc(x.title)}</b><br>${esc(x.location)}</td><td>${esc(x.marketing_status)}</td><td>${link(x.final_url||x.source_url)}<br>${esc(x.publisher)}</td>
<td>${esc(x.http_status)}<br><code>${esc((x.sha256||'').slice(0,16))}</code></td><td>${esc(x.marker_match_count)}/${esc(x.marker_total)}</td>
<td>${esc(x.source_confidence_score)}/100</td><td>${esc(x.geometry_match_status)} · ${esc(x.parcel_match_confidence_score)}/100</td>
<td>${esc(x.promotion_blocker)}</td></tr>`).join('');
}).catch(e=>{document.body.insertAdjacentHTML('beforeend',`<p class="warn">${esc(e.message)}</p>`)});
</script></body></html>
"""

def main() -> int:
    root = repo_root()
    slot_id = os.environ.get("AAYS_SLOT_ID", SLOT_ID)
    task_id = os.environ.get("AAYS_TASK_ID", TASK_ID_DEFAULT)
    if slot_id != SLOT_ID:
        raise RuntimeError(f"SLOT_ID_MISMATCH:{slot_id}")

    docs_root = root / "docs/chatgpt_status/aays1/shards/ready_to_sell_3"
    web_root = root / "england_map_web/data/aays_21_slots/ready_to_sell_3"
    docs_status = docs_root / "status/automation_167_and_live_candidates_latest.json"
    docs_report = docs_root / "reports/automation_167_and_live_candidates_latest.md"
    web_candidates = web_root / "ready_to_sell_3_live_candidates_latest.json"
    web_progress = web_root / "ready_to_sell_3_progress_events_latest.json"
    web_index = web_root / "index.html"
    evidence_root = docs_root / f"runner_outputs/{task_id}"
    evidence_root.mkdir(parents=True, exist_ok=True)

    started_at = utc_now()
    terminal_path = root / "docs/chatgpt_status/aays1/status/155_aays1_ready_to_sell_second_wave_dispatch_latest.json"
    terminal = read_json(terminal_path) or {}
    terminal_verified = (
        terminal.get("status") == "SECOND_WAVE_SITE_VISIBILITY_VERIFIED"
        and terminal.get("served_json_matches_source") is True
    )

    with concurrent.futures.ThreadPoolExecutor(max_workers=3, thread_name_prefix="ready-to-sell-web") as pool:
        candidate_rows = list(pool.map(fetch_source, CANDIDATES))

    candidate_count = len(candidate_rows)
    live_count = sum(1 for value in candidate_rows if value["source_live_verified"])
    high_count = sum(1 for value in candidate_rows if value["source_confidence_score"] >= 90)
    average_score = round(
        sum(value["source_confidence_score"] for value in candidate_rows) / max(1, candidate_count), 2
    )

    health_url = "http://127.0.0.1:8012/health"
    page_url = "http://127.0.0.1:8012/england_map_web/geometry_review_3of4_columns_1264.html"
    health_code, health_error = http_status(health_url)
    page_code, page_error = http_status(page_url)

    portable_value = os.environ.get("AAYS_PORTABLE_ROOT")
    browser = find_browser(Path(portable_value) if portable_value else None)
    dom_path = evidence_root / "browser_dom.html"
    browser_stderr_path = evidence_root / "browser_stderr.txt"
    browser_exit_code: int | None = None
    dom = ""
    browser_error = None
    if browser:
        try:
            completed = subprocess.run(
                [
                    str(browser), "--headless=new", "--disable-gpu", "--disable-extensions",
                    "--no-first-run", "--no-default-browser-check", "--virtual-time-budget=25000",
                    "--dump-dom", page_url,
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=45,
                check=False,
            )
            browser_exit_code = completed.returncode
            dom_path.write_bytes(completed.stdout)
            browser_stderr_path.write_bytes(completed.stderr)
            dom = completed.stdout.decode("utf-8", errors="replace")
        except Exception as exc:
            browser_error = f"{type(exc).__name__}:{exc}"
    else:
        browser_error = "HEADLESS_BROWSER_NOT_FOUND"

    load_ready = bool(re.search(r'data-load-state=["\']ready["\']', dom, re.I))
    mode_match = re.search(r'data-load-mode=["\'](canonical_geometry|ai_evidence_fallback)["\']', dom, re.I)
    load_mode = mode_match.group(1) if mode_match else None
    visible_rows = read_int_attr(dom, "data-visible-row-count")
    live_sources = read_int_attr(dom, "data-live-source-count")
    evidence_rows = len(re.findall(r"data-evidence-row=", dom))
    progress_events_rendered = len(re.findall(r"data-progress-sequence=", dom))
    research_candidates_rendered = len(re.findall(r"data-research-candidate=", dom))
    dom_pass = bool(
        terminal_verified
        and health_code == 200
        and page_code == 200
        and browser
        and browser_exit_code == 0
        and load_ready
        and load_mode
        and visible_rows >= 655
        and live_sources == 655
        and evidence_rows >= 1
        and progress_events_rendered >= 5
        and research_candidates_rendered >= 5
    )

    candidate_payload = {
        "schema_version": 3,
        "workstream_id": WORKSTREAM_ID,
        "slot_id": SLOT_ID,
        "task_id": task_id,
        "parcel_partition": PARTITION,
        "status": "RESEARCH_CANDIDATES_ONLY",
        "generated_at": utc_now(),
        "candidate_count": candidate_count,
        "source_live_verified_count": live_count,
        "high_source_confidence_count": high_count,
        "average_source_confidence": average_score,
        "promoted_row_count": 0,
        "promotion_policy": "canonical_parcel_match_and_geometry_proof_required",
        "candidates": candidate_rows,
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }
    write_json(web_candidates, candidate_payload)

    events = [
        {"sequence": 1, "event": "remote_business_state", "result": "pass" if terminal_verified else "blocked",
         "detail": "Task 155 remote terminal state read without replay.", "accuracy_score": 100},
        {"sequence": 2, "event": "concurrent_live_source_fetch", "result": "pass" if live_count >= 3 else "partial",
         "detail": f"{candidate_count} source fetched with max 3 concurrent requests; {live_count} passed marker verification.",
         "accuracy_score": round(100 * live_count / max(1, candidate_count), 2)},
        {"sequence": 3, "event": "source_hash_and_marker_proof", "result": "pass" if high_count >= 3 else "partial",
         "detail": f"{high_count} rows reached source confidence >=90; response SHA256 stored per row.",
         "accuracy_score": average_score},
        {"sequence": 4, "event": "parcel_promotion_gate", "result": "pass",
         "detail": "No candidate promoted because canonical parcel and geometry matching were not run.", "accuracy_score": 100},
        {"sequence": 5, "event": "shard_web_line_view", "result": "pass",
         "detail": "Slot-specific index.html and JSON evidence prepared for serial publisher.", "accuracy_score": 100},
        {"sequence": 6, "event": "automation_167_browser_dom_acceptance", "result": "pass" if dom_pass else "blocked",
         "detail": f"HTTP health/page={health_code}/{page_code}; DOM rows/live={visible_rows}/{live_sources}; mode={load_mode}.",
         "accuracy_score": 100 if dom_pass else 0},
        {"sequence": 7, "event": "remote_commit_push_readback", "result": "pending",
         "detail": "Single coordinator serial publisher must commit, push and verify remote HEAD.", "accuracy_score": 100},
    ]
    completed = sum(1 for event in events if event["result"] == "pass")
    progress = round(completed / len(events) * 100, 2)
    progress_payload = {
        "schema_version": 3,
        "workstream_id": WORKSTREAM_ID,
        "slot_id": SLOT_ID,
        "task_id": task_id,
        "updated_at": utc_now(),
        "events": events,
        "completed_events": completed,
        "total_events": len(events),
        "progress_percent": progress,
        "candidate_summary": {
            "researched": candidate_count,
            "live_verified": live_count,
            "high_source_confidence": high_count,
            "average_source_confidence": average_score,
            "promoted": 0,
        },
        "final_ready": False,
    }
    write_json(web_progress, progress_payload)
    web_index.parent.mkdir(parents=True, exist_ok=True)
    web_index.write_text(build_html(), encoding="utf-8")

    blockers = []
    if not terminal_verified:
        blockers.append("TERMINAL_155_REMOTE_STATE_NOT_VERIFIED")
    if live_count < candidate_count:
        blockers.append(f"LIVE_SOURCE_MARKER_VERIFICATION_PARTIAL:{live_count}/{candidate_count}")
    if not dom_pass:
        blockers.append("AUTOMATION_167_DOM_PROOF_NOT_VERIFIED")
    blockers.append("REMOTE_COMMIT_PUSH_READBACK_PENDING_SINGLE_COORDINATOR")

    status = {
        "schema_version": 3,
        "architecture_version": 3,
        "workstream_id": WORKSTREAM_ID,
        "slot_id": SLOT_ID,
        "base_slot_id": "ready_to_sell",
        "shard_index": 3,
        "task_id": task_id,
        "parcel_partition": PARTITION,
        "status": "READY_FOR_SERIAL_PUBLISH_AND_REMOTE_ACCEPTANCE",
        "terminal_reexecution": False,
        "source_scan_reexecution": False,
        "candidate_research": candidate_payload,
        "browser_dom": {
            "acceptance_pass": dom_pass,
            "health_http_status": health_code,
            "health_error": health_error,
            "page_http_status": page_code,
            "page_error": page_error,
            "browser_path": str(browser) if browser else None,
            "browser_exit_code": browser_exit_code,
            "browser_error": browser_error,
            "load_ready": load_ready,
            "load_mode": load_mode,
            "visible_row_count": visible_rows,
            "live_source_count": live_sources,
            "rendered_evidence_rows": evidence_rows,
            "rendered_progress_events": progress_events_rendered,
            "rendered_research_candidates": research_candidates_rendered,
            "dom_path": str(dom_path.relative_to(root)).replace("\\", "/") if dom_path.exists() else None,
            "stderr_path": str(browser_stderr_path.relative_to(root)).replace("\\", "/") if browser_stderr_path.exists() else None,
        },
        "web_view_path": "england_map_web/data/aays_21_slots/ready_to_sell_3/index.html",
        "progress_percent": progress,
        "completed_operations": completed,
        "total_operations": len(events),
        "blockers": blockers,
        "started_at": started_at,
        "finished_at": utc_now(),
        "final_ready": False,
        "product_final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
        "single_runner_only": True,
        "new_runner": False,
        "parallel_runner": False,
    }
    write_json(docs_status, status)

    report_lines = [
        "# ReadyToSell 3 — Automation 167 ve Canlı Aday Doğrulaması",
        "",
        f"- Task: `{task_id}`",
        f"- Aday: {candidate_count}",
        f"- Canlı doğrulanan: {live_count}",
        f"- Kaynak doğruluğu >=90: {high_count}",
        f"- Ortalama kaynak doğruluğu: {average_score}/100",
        "- Dataset'e yükseltilen: 0",
        f"- DOM acceptance: {dom_pass}",
        f"- İşlem: {completed}/{len(events)}",
        f"- İlerleme: {progress}%",
        f"- Web görünümü: `england_map_web/data/aays_21_slots/ready_to_sell_3/index.html`",
        f"- Blockers: {'; '.join(blockers)}",
        "",
        "`final_ready=false`; `fake_data=false`; `db_write=false`; `migration=false`; `production_deploy=false`.",
    ]
    docs_report.parent.mkdir(parents=True, exist_ok=True)
    docs_report.write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"status": "BLOCKED", "error": f"{type(exc).__name__}:{exc}", "final_ready": False}))
        raise
