#!/usr/bin/env python3
"""Fail-closed current-period validator for future_growth_2 Planning Data waves."""
from __future__ import annotations
import argparse, json, time, urllib.error, urllib.parse, urllib.request
from pathlib import Path
from typing import Any, Callable

API_BASE = "https://www.planning.data.gov.uk/entity.json"
OFFICIAL_HOST = "www.planning.data.gov.uk"
DEFAULT_TIMEOUT = 30.0
DEFAULT_RETRIES = 3
MAX_RESPONSE_BYTES = 5 * 1024 * 1024
TRANSIENT_HTTP = {429, 500, 502, 503, 504}

def build_current_url(entity_id: int) -> str:
    if int(entity_id) <= 0:
        raise ValueError("entity id must be positive")
    query = urllib.parse.urlencode([
        ("entity", str(int(entity_id))),
        ("dataset", "brownfield-land"),
        ("period", "current"),
        ("limit", "2"),
    ])
    url = f"{API_BASE}?{query}"
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != OFFICIAL_HOST or parsed.path != "/entity.json":
        raise ValueError("unexpected Planning Data API target")
    params = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
    if params.get("period") != ["current"] or params.get("dataset") != ["brownfield-land"]:
        raise ValueError("current-period query contract missing")
    return url

def _content_type(response: Any) -> str:
    headers = getattr(response, "headers", None)
    if headers is None:
        return ""
    value = headers.get("Content-Type") if hasattr(headers, "get") else ""
    return str(value or "").split(";", 1)[0].strip().lower()

def _final_url(response: Any, requested_url: str) -> str:
    getter = getattr(response, "geturl", None)
    return str(getter() if callable(getter) else requested_url)

def _read_limited(response: Any, maximum: int = MAX_RESPONSE_BYTES) -> bytes:
    data = response.read(maximum + 1)
    if len(data) > maximum:
        raise ValueError(f"Planning Data response exceeds {maximum} bytes")
    return data

def _parse_json_response(response: Any, requested_url: str) -> dict[str, Any]:
    status = int(getattr(response, "status", 200))
    if status != 200:
        raise RuntimeError(f"Planning Data returned HTTP {status}")
    final = urllib.parse.urlparse(_final_url(response, requested_url))
    if final.scheme != "https" or final.hostname != OFFICIAL_HOST or final.path != "/entity.json":
        raise ValueError("Planning Data response redirected off the official entity endpoint")
    ctype = _content_type(response)
    if ctype not in {"application/json", "application/geo+json"} and not ctype.endswith("+json"):
        raise ValueError(f"Planning Data response content type is not JSON: {ctype!r}")
    raw = _read_limited(response)
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("Planning Data response is not valid UTF-8 JSON") from exc
    if not isinstance(payload, dict):
        raise ValueError("Planning Data response is not an object")
    return payload

def fetch_current(
    entity_id: int,
    timeout: float,
    *,
    retries: int = DEFAULT_RETRIES,
    opener: Callable[..., Any] | None = None,
    sleeper: Callable[[float], None] = time.sleep,
) -> dict[str, Any]:
    url = build_current_url(entity_id)
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "TerraYield-AAYS-future-growth-2/1.1"},
        method="GET",
    )
    open_call = opener or urllib.request.urlopen
    attempts = max(1, int(retries))
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            response = open_call(request, timeout=timeout)
            context = response if hasattr(response, "__enter__") else None
            if context is not None:
                with response as active:
                    return _parse_json_response(active, url)
            return _parse_json_response(response, url)
        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code not in TRANSIENT_HTTP or attempt + 1 >= attempts:
                raise RuntimeError(f"Planning Data returned HTTP {exc.code}") from exc
        except urllib.error.URLError as exc:
            last_error = exc
            if attempt + 1 >= attempts:
                raise RuntimeError(f"Planning Data network failure: {exc.reason}") from exc
        if attempt + 1 < attempts:
            sleeper(min(4.0, 0.5 * (2 ** attempt)))
    raise RuntimeError(f"Planning Data request failed: {last_error}")

def entities_from(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows = payload.get("entities")
    if rows is None:
        rows = payload.get("data")
    if not isinstance(rows, list):
        raise ValueError("Planning Data response lacks an entities/data array")
    return [row for row in rows if isinstance(row, dict)]

def value(row: dict[str, Any], *names: str) -> Any:
    for name in names:
        if name in row:
            return row[name]
    return None

def validate_candidate(candidate: dict[str, Any], timeout: float) -> dict[str, Any]:
    candidate_id = str(candidate.get("candidate_id") or "").strip()
    entity_id = int(candidate["source_entity"])
    expected_reference = str(candidate.get("source_reference") or "").strip()
    eligibility = str(candidate.get("eligibility") or "")
    if not candidate_id or not expected_reference:
        raise ValueError("candidate identity is incomplete")
    if candidate.get("canonical_row_no") is not None or candidate.get("canonical_parcel_id") is not None:
        raise ValueError(f"{candidate_id}: parcel assignment present before exact crosswalk")
    if candidate.get("future_growth_score") is not None or candidate.get("future_growth_confidence") not in (0, None):
        raise ValueError(f"{candidate_id}: score/confidence present before approval")
    if not eligibility.startswith("eligible"):
        return {"candidate_id":candidate_id,"source_entity":entity_id,"state":"SKIPPED_NOT_ELIGIBLE",
                "eligibility":eligibility,"parcel_promoted":False,"score_written":False}
    payload = fetch_current(entity_id, timeout)
    rows = entities_from(payload)
    exact = [row for row in rows if int(value(row, "entity") or -1) == entity_id]
    if len(exact) != 1:
        raise ValueError(f"{candidate_id}: expected one current entity row, got {len(exact)}")
    row = exact[0]
    dataset = str(value(row, "dataset") or "")
    reference = str(value(row, "reference") or "")
    quality = str(value(row, "quality") or "")
    end_date = str(value(row, "end-date", "end_date") or "").strip()
    point = str(value(row, "point") or "").strip()
    failures=[]
    if dataset != "brownfield-land": failures.append(f"dataset={dataset!r}")
    if reference != expected_reference: failures.append(f"reference={reference!r}")
    if quality != "authoritative": failures.append(f"quality={quality!r}")
    if end_date: failures.append(f"end_date={end_date!r}")
    if not point.startswith("POINT"): failures.append("point_missing")
    if failures:
        raise ValueError(f"{candidate_id}: current-period validation failed: {';'.join(failures)}")
    return {"candidate_id":candidate_id,"source_entity":entity_id,"source_reference":reference,
            "state":"CURRENT_AUTHORITATIVE_ENTITY_VALIDATED","quality":quality,"end_date":None,
            "point_present":True,"parcel_promoted":False,"score_written":False}

def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--candidate-wave",type=Path,required=True)
    parser.add_argument("--output-json",type=Path,required=True)
    parser.add_argument("--timeout",type=float,default=DEFAULT_TIMEOUT)
    parser.add_argument("--delay-seconds",type=float,default=0.25)
    args=parser.parse_args()
    payload=json.loads(args.candidate_wave.resolve().read_text(encoding="utf-8"))
    if payload.get("slot_id")!="future_growth_2": raise ValueError("wrong slot_id")
    candidates=payload.get("candidates")
    if not isinstance(candidates,list) or not candidates: raise ValueError("candidate wave is empty")
    ids=[int(c["source_entity"]) for c in candidates]; refs=[str(c["source_reference"]) for c in candidates]
    if len(ids)!=len(set(ids)) or len(refs)!=len(set(refs)): raise ValueError("duplicate entity or reference inside wave")
    results=[]
    for index,candidate in enumerate(candidates):
        results.append(validate_candidate(candidate,args.timeout))
        if index+1<len(candidates): time.sleep(max(0.0,args.delay_seconds))
    validated=sum(r["state"]=="CURRENT_AUTHORITATIVE_ENTITY_VALIDATED" for r in results)
    output={"schema_version":2,"slot_id":"future_growth_2","source_contract":"PLANNING_DATA_ENTITY_API_PERIOD_CURRENT",
            "official_host":OFFICIAL_HOST,"candidate_count":len(candidates),
            "validated_current_eligible":validated,"results":results,
            "transport_contract":{"https_only":True,"official_host_locked":True,"json_content_type_required":True,
                                  "max_response_bytes":MAX_RESPONSE_BYTES,"transient_retries":DEFAULT_RETRIES},
            "actual_parcel_matches":0,"actual_business_data_rows_written":0,
            "future_growth_scores_produced":0,"nearest_point_promotion_used":False,
            "final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False}
    args.output_json.parent.mkdir(parents=True,exist_ok=True)
    args.output_json.write_text(json.dumps(output,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"ok":True,"validated_current_eligible":validated,"matches":0}))
    return 0
if __name__=="__main__": raise SystemExit(main())
