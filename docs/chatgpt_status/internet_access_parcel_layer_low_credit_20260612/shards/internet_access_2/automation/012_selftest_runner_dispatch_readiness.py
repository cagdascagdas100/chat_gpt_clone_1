#!/usr/bin/env python3
"""Deterministic contract tests for runner dispatch readiness."""
from __future__ import annotations

import importlib.util
from datetime import datetime, timezone
from pathlib import Path

SCRIPT = Path(__file__).with_name("011_runner_dispatch_readiness.py")
spec = importlib.util.spec_from_file_location("readiness", SCRIPT)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot import readiness module")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

NOW = datetime(2026, 7, 21, 5, 0, tzinfo=timezone.utc)
checkpoint = {"slot_id":"internet_access_2","sequence":0,"final_ready":False}
status = {"slot_id":"internet_access_2","state":"ready_for_claim","owner_page_session_id":None}
heartbeat = {"slot_id":"internet_access_2","state":"unclaimed","stale":True}
current = {"slot_id":"internet_access_2","state":"idle","task_id":None,"allowed_paths":["england_map_web/data/aays_18_slots/internet_access_2"],"direct_push_forbidden":True}
ownership = {"slot_id":"internet_access_2","state":"unclaimed","lease_version":0,"lease_token_hash":None}
watcher_ready = {"updated_at":"2026-07-21T04:59:30Z"}
runner_ready = {"slot_id":"internet_access_2","task_id":None,"status":"IDLE","runner_heartbeat_fresh":True,"runner_last_heartbeat_at":"2026-07-21T04:59:20Z"}
pr_ready = {"number":61,"state":"closed","merged":True,"base":"main","mergeable":True,"draft":False}

ready = module.evaluate(checkpoint,status,heartbeat,current,ownership,watcher_ready,runner_ready,pr_ready,now=NOW,freshness_seconds=900)
blocked_runner = dict(runner_ready, slot_id="security_public_safety_3", task_id="other", status="PICKUP_REQUESTED", runner_heartbeat_fresh=False)
blocked_pr = dict(pr_ready, state="open", merged=False, base="codex/aays-single-runner-v5-20260706", mergeable=False, draft=True)
blocked = module.evaluate(checkpoint,status,heartbeat,current,ownership,{"updated_at":"20260703_225536"},blocked_runner,blocked_pr,now=NOW,freshness_seconds=900)

checks = {
    "ready_dispatch_true": ready["dispatch_permitted"] is True,
    "ready_all_gates_pass": ready["passed_gate_count"] == ready["gate_count"] == 13,
    "ready_no_blockers": ready["blocked_gate_count"] == 0,
    "blocked_dispatch_false": blocked["dispatch_permitted"] is False,
    "blocked_watcher_gate": any(g["gate_id"] == "WATCHER_FRESH" and g["state"] == "BLOCKED" for g in blocked["gates"]),
    "blocked_runner_gate": any(g["gate_id"] == "RUNNER_FRESH" and g["state"] == "BLOCKED" for g in blocked["gates"]),
    "blocked_queue_head_gate": any(g["gate_id"] == "QUEUE_HEAD_FREE" and g["state"] == "BLOCKED" for g in blocked["gates"]),
    "blocked_merge_gate": any(g["gate_id"] == "REVIEW_MERGED" and g["state"] == "BLOCKED" for g in blocked["gates"]),
    "blocked_mergeable_gate": any(g["gate_id"] == "PR_MERGEABLE" and g["state"] == "BLOCKED" for g in blocked["gates"]),
    "slot_id_guard": all(g["state"] == "PASS" for g in blocked["gates"] if g["gate_id"] == "SLOT_ID"),
    "authorized_web_path_guard": all(g["state"] == "PASS" for g in blocked["gates"] if g["gate_id"] == "ALLOWED_PATH"),
    "direct_push_guard": all(g["state"] == "PASS" for g in blocked["gates"] if g["gate_id"] == "NO_DIRECT_PUSH"),
    "no_claim_side_effect": blocked["ownership_claimed"] is False,
    "no_queue_side_effect": blocked["queue_entry_written"] is False,
    "no_runner_side_effect": blocked["new_runner_started"] is False,
    "no_business_write": blocked["actual_business_data_rows_written"] == 0,
}
failed = [name for name, passed in checks.items() if not passed]
if failed:
    raise AssertionError(f"failed: {failed}")
print({"status":"PASS","tests_passed":len(checks),"tests_total":len(checks),"business_rows_written":0})
