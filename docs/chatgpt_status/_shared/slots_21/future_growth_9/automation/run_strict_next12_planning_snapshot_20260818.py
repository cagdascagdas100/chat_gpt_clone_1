#!/usr/bin/env python3
import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path

import requests

HERE = Path(__file__).resolve().parent
BASE = HERE / "run_strict_next12_20260818.py"
spec = importlib.util.spec_from_file_location("fg9_strict_base", BASE)
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)

API = "https://www.planning.data.gov.uk/entity.json"
SNAPSHOT_PARAMS = {
    "dataset": "brownfield-land",
    "organisation_entity": 58,
    "period": "current",
    "limit": 500,
}
SWITCH_REASON = "PRIMARY_OFFSET_SEQUENCE_UNRESOLVED; FROZEN_OFFICIAL_SNAPSHOT_SELECTION_USED_INSTEAD_OF_REPLAYING_LIVE_OFFSETS"
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "AAYS-future-growth-9-planning-snapshot/1.0"})
_selected = None
_snapshot_url = None
_snapshot_hash = None
_snapshot_total = None
_start_window = None


def _entities_from_payload(data):
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("entities", "entity", "results"):
            val = data.get(key)
            if isinstance(val, list):
                return val
    return []


def _fetch_snapshot():
    global _snapshot_url, _snapshot_hash, _snapshot_total
    last = None
    for attempt in range(4):
        try:
            r = SESSION.get(API, params=SNAPSHOT_PARAMS, timeout=90)
            r.raise_for_status()
            payload = r.json()
            entities = _entities_from_payload(payload)
            if not entities:
                raise RuntimeError("OFFICIAL_PLANNING_DATA_SNAPSHOT_EMPTY")
            canonical = json.dumps(entities, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
            _snapshot_url = r.url
            _snapshot_hash = hashlib.sha256(canonical).hexdigest()
            _snapshot_total = len(entities)
            return entities
        except Exception as exc:
            last = exc
            if attempt == 3:
                raise
            time.sleep(2 ** attempt)
    raise last


def _global_future_growth_identities():
    refs, entities = set(), set()
    root = base.REPO / "AAYS/england_map_web/data/future_growth"
    for p in root.rglob("*.geojson"):
        try:
            obj = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        for feat in obj.get("features", []):
            props = feat.get("properties") or {}
            ref = props.get("source_feature_id") or props.get("site_reference")
            ent = props.get("planning_data_entity")
            if ref:
                refs.add(str(ref).strip())
            if ent is not None:
                try:
                    entities.add(int(ent))
                except Exception:
                    entities.add(str(ent))
    return refs, entities


def _prepare_selection():
    global _selected, _start_window
    cp = base.load(base.CHECKPOINT)
    _start_window = int((cp.get("next_unused_window") or {}).get("window_index", -1))
    if _start_window != 91 or int(cp.get("feature_count_after", -1)) != 91:
        raise RuntimeError(f"LIVE_STATE_CHANGED expected_window=91/count=91 actual_window={_start_window}/count={cp.get('feature_count_after')}")

    rows = _fetch_snapshot()
    global_refs, global_entities = _global_future_growth_identities()
    seen_refs, seen_entities = set(), set()
    candidates = []

    def sort_key(e):
        ent = e.get("entity")
        try:
            ent_key = (0, int(ent))
        except Exception:
            ent_key = (1, str(ent))
        return ent_key + (str(e.get("reference") or e.get("name") or "").casefold(),)

    for e in sorted(rows, key=sort_key):
        ref, ent = base.ref_entity(e)
        point = base.parse_point(e)
        if not ref or ent is None or point is None:
            continue
        ref = str(ref).strip()
        try:
            ent_norm = int(ent)
        except Exception:
            ent_norm = str(ent)
        if ref in seen_refs or ent_norm in seen_entities:
            continue
        seen_refs.add(ref)
        seen_entities.add(ent_norm)
        if ref in global_refs or ent_norm in global_entities:
            continue
        candidates.append(e)
        if len(candidates) == 12:
            break

    if len(candidates) != 12:
        raise RuntimeError(
            "INSUFFICIENT_NEW_UNIQUE_BRADFORD_SNAPSHOT_RECORDS "
            f"snapshot_total={_snapshot_total} selected={len(candidates)} global_refs={len(global_refs)} global_entities={len(global_entities)}"
        )
    _selected = candidates


def choose_query_variant():
    if _selected is None:
        _prepare_selection()
    selected_pairs = [base.ref_entity(e) for e in _selected]
    diagnostics = [{
        "name": "bradford_official_period_current_frozen_snapshot_entity_reference_sorted",
        "ok": True,
        "historical_offset_sequence_replayed": False,
        "switch_reason": SWITCH_REASON,
        "snapshot_url": _snapshot_url,
        "snapshot_sha256": _snapshot_hash,
        "snapshot_entity_count": _snapshot_total,
        "selection_order": "entity ascending then reference casefold ascending after exact global identity exclusion",
        "selected_reference_entity_pairs": selected_pairs,
        "source_authority": "City of Bradford Metropolitan District Council via Planning Data",
        "source_dataset": "brownfield-land",
        "nearest_match_used": False,
        "cross_parcel_identity_inference_used": False,
    }]
    return "bradford_official_frozen_snapshot_entity_reference_sorted", {"snapshot": True}, diagnostics


def api_entities(logical_window, _params):
    if _selected is None:
        _prepare_selection()
    idx = int(logical_window) - int(_start_window)
    if idx < 0 or idx >= len(_selected):
        return [], _snapshot_url
    e = _selected[idx]
    ent = e.get("entity")
    return [e], f"https://www.planning.data.gov.uk/entity/{ent}"


base.choose_query_variant = choose_query_variant
base.api_entities = api_entities

if __name__ == "__main__":
    try:
        base.main()
    except Exception as exc:
        print("FG9_SNAPSHOT_EXECUTOR_ERROR=" + repr(exc), file=sys.stderr, flush=True)
        raise
