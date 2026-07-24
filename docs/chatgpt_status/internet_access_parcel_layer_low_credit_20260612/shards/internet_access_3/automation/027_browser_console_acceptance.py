#!/usr/bin/env python3
"""Single-session browser-console acceptance for the internet_access_3 progress page.

Requires Playwright and Chromium on the existing canonical runner. Polygon-popup
acceptance remains separate and final_ready is never set true.
"""
from __future__ import annotations
import argparse, json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
SLOT_ID="internet_access_3"
DEFAULT_URL="http://127.0.0.1:8012/data/aays_18_slots/internet_access_3/index.html"
REQUIRED_SELECTORS={"metrics":"#metrics .metric","operations":"#operations tr","runtime_gates":"#runtime tr","runtime_result_counts":"#runtimeResults tr","sources":"#sources tr","examples":"#examples tr"}
MINIMUM_COUNTS={"metrics":10,"operations":12,"runtime_gates":8,"runtime_result_counts":1,"sources":10,"examples":13}
class GateError(RuntimeError): pass

def require(condition:bool,message:str)->None:
    if not condition: raise GateError(message)

def validate_browser_snapshot(snapshot:dict[str,Any])->None:
    require(snapshot.get("title")=="internet_access_3 ilerleme","unexpected page title"); require(snapshot.get("load_error_visible") is False,"page reported a load error"); require(snapshot.get("undefined_visible") is False,"page rendered undefined"); require(not snapshot.get("console_errors"),"console errors were emitted"); require(not snapshot.get("page_errors"),"page errors were emitted")
    counts=snapshot.get("selector_counts") or {}
    for name,minimum in MINIMUM_COUNTS.items(): require(int(counts.get(name,-1))>=minimum,f"{name}: expected at least {minimum}")

def run_browser(url:str,*,timeout_ms:int)->dict[str,Any]:
    try: from playwright.sync_api import sync_playwright
    except Exception as exc: raise GateError(f"Playwright is unavailable: {exc}") from exc
    console_errors=[]; page_errors=[]
    with sync_playwright() as playwright:
        browser=playwright.chromium.launch(headless=True)
        try:
            page=browser.new_page(); page.on("console",lambda message:console_errors.append(message.text) if message.type=="error" else None); page.on("pageerror",lambda error:page_errors.append(str(error)))
            response=page.goto(url,wait_until="networkidle",timeout=timeout_ms); require(response is not None and response.ok,f"navigation failed: {response.status if response else 'no response'}")
            page.wait_for_selector("#operations tr",state="attached",timeout=timeout_ms); page.wait_for_selector("#runtimeResults tr",state="attached",timeout=timeout_ms)
            selector_counts={name:page.locator(selector).count() for name,selector in REQUIRED_SELECTORS.items()}; body_text=page.locator("body").inner_text()
            snapshot={"title":page.title(),"url":page.url,"selector_counts":selector_counts,"load_error_visible":"Görünüm yüklenemedi:" in body_text,"undefined_visible":"undefined" in body_text.lower(),"console_errors":console_errors,"page_errors":page_errors}; validate_browser_snapshot(snapshot); return snapshot
        finally: browser.close()

def main()->int:
    parser=argparse.ArgumentParser(); parser.add_argument("--url",default=DEFAULT_URL); parser.add_argument("--output",required=True,type=Path); parser.add_argument("--timeout-ms",type=int,default=30_000); args=parser.parse_args(); require(1_000<=args.timeout_ms<=120_000,"timeout-ms out of range")
    snapshot=run_browser(args.url,timeout_ms=args.timeout_ms)
    receipt={"schema_version":1,"slot_id":SLOT_ID,"state":"PASS_BROWSER_CONSOLE_AND_PROGRESS_DOM","accepted_at":datetime.now(timezone.utc).isoformat(),"snapshot":snapshot,"http_8012_acceptance":True,"browser_console_acceptance":True,"progress_page_dom_acceptance":True,"polygon_popup_acceptance":False,"actual_business_data_rows_written":0,"scores_written":0,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False,"final_ready":False}
    args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"); print(json.dumps({"state":receipt["state"],"selector_counts":snapshot["selector_counts"]},sort_keys=True)); return 0

if __name__=="__main__": raise SystemExit(main())
