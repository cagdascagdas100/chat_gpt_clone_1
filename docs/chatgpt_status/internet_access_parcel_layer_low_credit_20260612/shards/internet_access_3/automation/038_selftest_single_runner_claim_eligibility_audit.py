#!/usr/bin/env python3
"""Deterministic network-free tests for the read-only single-runner eligibility auditor."""
from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).parent


def load() -> Any:
    spec = importlib.util.spec_from_file_location("audit037", ROOT / "037_single_runner_claim_eligibility_audit.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load audit037")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def ownership() -> dict[str, Any]:
    return {"slot_id":"internet_access_3","parcel_partition":{"start":61523,"end":92283,"count":30761,"canonical_count":92283},"final_ready":False,"state":"unclaimed","lease_version":0,"owner_page_session_id":None,"lease_token_hash":None,"heartbeat_at":None,"lease_expires_at":None,"wrong_slot_write_forbidden":True}


def slot_task() -> dict[str, Any]:
    return {"slot_id":"internet_access_3","parcel_partition":{"start":61523,"end":92283,"count":30761,"canonical_count":92283},"final_ready":False,"state":"idle","task_id":None,"owner_page_session_id":None,"allowed_paths":["docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3","docs/chatgpt_status/_shared/slots_18/internet_access_3","england_map_web/data/aays_18_slots/internet_access_3"],"direct_push_forbidden":True}


def global_other() -> dict[str, Any]:
    return {"id":"aays1-height-difference-2","task_id":"aays1-height-difference-2","slot_id":"height_difference_2","status":"pickup_requested"}


def expect_fail(fn: Callable[[], None]) -> None:
    try:
        fn()
    except Exception:
        return
    raise AssertionError("expected failure")


def main() -> int:
    m = load(); results: list[str] = []
    blocked = m.validate(ownership(), slot_task(), global_other())
    assert blocked["status"] == "BLOCKED_BY_OTHER_GLOBAL_RUNNER_TASK"
    assert blocked["claim_eligible_for_manual_review"] is False
    results += ["other_task_blocked","blocked_not_eligible","auto_claim_false","queue_false"]
    assert blocked["auto_claim"] is False and blocked["queue_submission"] is False
    assert blocked["actual_business_data_rows_written"] == 0; results.append("business_rows_zero")

    idle = {"slot_id":None,"task_id":None,"status":"idle"}
    ready = m.validate(ownership(), slot_task(), idle)
    assert ready["status"] == "READY_FOR_MANUAL_CLAIM_REVIEW"
    assert ready["claim_eligible_for_manual_review"] is True and ready["global_runner_clear"] is True
    results += ["idle_ready","manual_review_true","runner_clear"]

    same = {"slot_id":"internet_access_3","task_id":"same","status":"running"}
    active = m.validate(ownership(), slot_task(), same)
    assert active["status"] == "ALREADY_ACTIVE_NO_NEW_CLAIM" and active["claim_eligible_for_manual_review"] is False
    results += ["same_slot_no_second_claim","same_slot_not_eligible"]

    runtime = {"slot_id":"internet_access_3","status":"WAITING_REAL_RUNTIME_BUNDLE","real_runtime_rows_validated":0}
    with_runtime = m.validate(ownership(), slot_task(), global_other(), runtime)
    assert with_runtime["real_runtime_rows_validated"] == 0 and len(with_runtime["gates"]) == 8
    results += ["runtime_zero_preserved","eight_gates"]

    cases: list[tuple[str, Callable[[dict[str, Any], dict[str, Any], dict[str, Any]], None]]] = [
        ("wrong_owner_slot", lambda o,s,g:o.update(slot_id="wrong")),
        ("wrong_task_slot", lambda o,s,g:s.update(slot_id="wrong")),
        ("bad_owner_start", lambda o,s,g:o["parcel_partition"].update(start=1)),
        ("bad_task_count", lambda o,s,g:s["parcel_partition"].update(count=1)),
        ("bad_allowed_paths", lambda o,s,g:s["allowed_paths"].reverse()),
        ("direct_push_guard", lambda o,s,g:s.update(direct_push_forbidden=False)),
        ("wrong_slot_guard", lambda o,s,g:o.update(wrong_slot_write_forbidden=False)),
        ("owner_final", lambda o,s,g:o.update(final_ready=True)),
        ("task_final", lambda o,s,g:s.update(final_ready=True)),
        ("unknown_global_state", lambda o,s,g:g.update(status="mystery")),
    ]
    for name, mutate in cases:
        o,s,g=ownership(),slot_task(),global_other(); mutate(o,s,g)
        expect_fail(lambda o=o,s=s,g=g:m.validate(o,s,g)); results.append(name)

    dirty_cases: list[tuple[str, Callable[[dict[str, Any], dict[str, Any]], None]]] = [
        ("claimed_owner", lambda o,s:o.update(state="claimed",lease_version=1)),
        ("owner_session", lambda o,s:o.update(owner_page_session_id="x")),
        ("lease_hash", lambda o,s:o.update(lease_token_hash="x")),
        ("heartbeat", lambda o,s:o.update(heartbeat_at="2026-07-21T00:00:00Z")),
        ("slot_busy", lambda o,s:s.update(state="running",task_id="x",owner_page_session_id="x")),
    ]
    for name, mutate in dirty_cases:
        o,s=ownership(),slot_task(); mutate(o,s)
        value=m.validate(o,s,{"slot_id":None,"task_id":None,"status":"idle"})
        assert value["status"] == "BLOCKED_SLOT_NOT_CLEANLY_UNCLAIMED" and value["claim_eligible_for_manual_review"] is False
        results.append(name)

    bad_runtime=copy.deepcopy(runtime); bad_runtime["real_runtime_rows_validated"]=30762
    expect_fail(lambda:m.validate(ownership(),slot_task(),global_other(),bad_runtime)); results.append("runtime_overflow")

    with tempfile.TemporaryDirectory() as td:
        out=Path(td)/"nested"/"audit.json"; m.atomic_write(out,blocked)
        assert json.loads(out.read_text(encoding="utf-8"))["status"] == blocked["status"]
        results.append("atomic_write_roundtrip")

    assert all(g["state"] in {"PASS","BLOCKED","READY","WAITING_EXISTING_RUNNER","ALREADY_ACTIVE"} for g in blocked["gates"])
    results.append("gate_states_bounded")
    assert len(results) == 30, (len(results),results)
    print(json.dumps({"passed":len(results),"total":30,"result":"PASS","tests":results}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
