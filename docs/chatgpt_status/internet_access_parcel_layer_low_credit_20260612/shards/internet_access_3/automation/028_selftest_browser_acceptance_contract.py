#!/usr/bin/env python3
"""Static network-free tests for 027_browser_console_acceptance.py."""
from __future__ import annotations
import copy, importlib.util, json
from pathlib import Path
from typing import Any, Callable
ROOT=Path(__file__).parent

def load()->Any:
    spec=importlib.util.spec_from_file_location("browser027",ROOT/"027_browser_console_acceptance.py")
    if spec is None or spec.loader is None: raise RuntimeError("cannot load browser027")
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module

def fixture(module:Any)->dict[str,Any]:
    return {"title":"internet_access_3 ilerleme","url":"http://127.0.0.1:8012/data/aays_18_slots/internet_access_3/index.html","selector_counts":dict(module.MINIMUM_COUNTS),"load_error_visible":False,"undefined_visible":False,"console_errors":[],"page_errors":[]}

def expect_fail(fn:Callable[[],None])->None:
    try: fn()
    except Exception: return
    raise AssertionError("expected failure")

def main()->int:
    module=load(); base=fixture(module); results=[]; module.validate_browser_snapshot(copy.deepcopy(base)); results.append("valid_snapshot")
    cases=[("title",lambda x:x.update(title="wrong")),("load_error",lambda x:x.update(load_error_visible=True)),("undefined",lambda x:x.update(undefined_visible=True)),("console_error",lambda x:x.update(console_errors=["boom"])),("page_error",lambda x:x.update(page_errors=["boom"])),("operation_count",lambda x:x["selector_counts"].update(operations=11)),("source_count",lambda x:x["selector_counts"].update(sources=9)),("example_count",lambda x:x["selector_counts"].update(examples=12))]
    for name,change in cases:
        broken=copy.deepcopy(base); change(broken); expect_fail(lambda broken=broken:module.validate_browser_snapshot(broken)); results.append(name)
    source=(ROOT/"027_browser_console_acceptance.py").read_text(encoding="utf-8"); assert source.count("browser.new_page()") == 1; results.append("single_page_session"); assert '"polygon_popup_acceptance":False' in source and '"final_ready":False' in source; results.append("truth_boundary"); assert 'page.on("console"' in source and 'page.on("pageerror"' in source; results.append("console_hooks")
    print(json.dumps({"passed":len(results),"total":len(results),"results":[{"test":x,"state":"PASS"} for x in results]},sort_keys=True)); return 0

if __name__=="__main__": raise SystemExit(main())
