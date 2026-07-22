#!/usr/bin/env python3
"""Fail-closed runtime preflight for four official UPRN release downloads.

Validates package identity, response metadata, remaining download bytes, disk headroom,
and SQLite staging reserve before the full hydration worker is allowed to run.
"""
from __future__ import annotations
import argparse, importlib.util, json, os, re, shutil, tempfile, urllib.error, urllib.request
from pathlib import Path
from typing import Any

SLOT_ID = "internet_access_3"
AUTOMATION = Path(__file__).resolve().parent
DEFAULT_OS = "docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/runner_outputs/041_os_opendata_download_resolution_latest.json"
DEFAULT_ONS = "docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/runner_outputs/015_ons_uprn_arcgis_release_discovery_latest.json"
DEFAULT_RUNNER = "docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/runner_outputs/052_runtime_resource_download_preflight_latest.json"
DEFAULT_WEB = "england_map_web/data/aays_21_slots/internet_access_3/runtime_resource_download_preflight_latest.json"

def args():
    p=argparse.ArgumentParser()
    p.add_argument("--repo-root",type=Path)
    p.add_argument("--os-resolution",default=DEFAULT_OS)
    p.add_argument("--ons-discovery",default=DEFAULT_ONS)
    p.add_argument("--cache-dir",type=Path,default=Path(tempfile.gettempdir())/"aays_internet_access_3_release_cache")
    p.add_argument("--database",type=Path,default=Path(tempfile.gettempdir())/"aays_internet_access_3_uprn_join.sqlite")
    p.add_argument("--timeout",type=int,default=90)
    p.add_argument("--database-reserve-bytes",type=int,default=40*1024**3)
    p.add_argument("--minimum-free-after-bytes",type=int,default=8*1024**3)
    p.add_argument("--download-safety-factor",type=float,default=1.15)
    p.add_argument("--runner-output",default=DEFAULT_RUNNER)
    p.add_argument("--web-output",default=DEFAULT_WEB)
    return p.parse_args()

def root(explicit):
    if explicit:return explicit.expanduser().resolve()
    for p in [Path.cwd(),*Path(__file__).resolve().parents]:
        if (p/"docs").exists() and (p/"england_map_web").exists():return p
    raise FileNotFoundError("repo root")

def load(path):
    with path.open("r",encoding="utf-8-sig") as h:return json.load(h)

def write(path,payload):
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix=path.name+".",suffix=".tmp",dir=path.parent)
    try:
        with os.fdopen(fd,"w",encoding="utf-8") as h:
            json.dump(payload,h,ensure_ascii=False,separators=(",",":"));h.write("\n")
        os.replace(tmp,path)
    except Exception:
        try:os.unlink(tmp)
        except FileNotFoundError:pass
        raise

def import_hydrator():
    path=AUTOMATION/"071_full_release_hydration_manifest.py"
    spec=importlib.util.spec_from_file_location("rev15_hydrator",path)
    if not spec or not spec.loader:raise ImportError(path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod

def content_range_total(value):
    m=re.search(r"/(\d+)$",str(value or ""))
    return int(m.group(1)) if m else 0

def response_probe(url,timeout):
    headers={"User-Agent":"TerraYield-AAYS-internet-access-3/16","Accept":"*/*"}
    request=urllib.request.Request(url,headers=headers,method="HEAD")
    try:
        response=urllib.request.urlopen(request,timeout=timeout)
    except urllib.error.HTTPError as exc:
        if exc.code not in {400,403,405,501}:raise
        headers["Range"]="bytes=0-0"
        response=urllib.request.urlopen(urllib.request.Request(url,headers=headers),timeout=timeout)
    with response:
        status=int(getattr(response,"status",response.getcode()))
        total=content_range_total(response.headers.get("Content-Range"))
        length=total or int(response.headers.get("Content-Length") or 0)
        return {
            "status":status,
            "final_url":response.geturl(),
            "content_length":length,
            "content_type":str(response.headers.get("Content-Type") or "").split(";")[0].lower(),
            "content_disposition":response.headers.get("Content-Disposition"),
            "accept_ranges":response.headers.get("Accept-Ranges"),
            "etag":response.headers.get("ETag"),
            "last_modified":response.headers.get("Last-Modified"),
        }

def media_type_allowed(package_id,content_type,disposition,final_url):
    text=" ".join([content_type or "",disposition or "",final_url or ""]).lower()
    if package_id in {"nsul","onsud"} and ("json" in text or "html" in text):
        return False
    return any(token in text for token in ("zip","csv","octet-stream","download","attachment")) or package_id.startswith("os_")

def existing_bytes(cache_dir,package_id,release_label):
    safe=re.sub(r"[^A-Za-z0-9._-]+","_",f"{package_id}_{release_label}").strip("._")[:180]
    total=0
    for ext in (".zip",".download",".zip.part",".download.part"):
        p=cache_dir/(safe+ext)
        if p.exists():total=max(total,p.stat().st_size)
    return total

def compute_budget(packages,probes,cache_dir,database_reserve,minimum_free_after,safety_factor):
    remaining=0
    rows=[]
    for spec,probe in zip(packages,probes):
        expected=max(int(spec.get("expected_size") or 0),int(probe.get("content_length") or 0))
        present=existing_bytes(cache_dir,str(spec["package_id"]),str(spec.get("release_label") or ""))
        left=max(0,expected-present)
        remaining+=left
        rows.append({"package_id":spec["package_id"],"expected_runtime_bytes":expected,"cached_or_partial_bytes":present,"remaining_bytes":left})
    guarded=int(remaining*max(1.0,safety_factor))
    required=guarded+max(0,database_reserve)+max(0,minimum_free_after)
    return rows,remaining,required

def main():
    o=args();r=root(o.repo_root);cache=o.cache_dir.expanduser().resolve();cache.mkdir(parents=True,exist_ok=True)
    hydrator=import_hydrator()
    os_resolution=load(r/o.os_resolution);ons_discovery=load(r/o.ons_discovery)
    packages=hydrator.build_packages(os_resolution,ons_discovery)
    blockers=[];probes=[]
    for spec in packages:
        url=str(spec.get("download_url") or "")
        if not url.startswith("https://"):blockers.append(spec["package_id"].upper()+"_NON_HTTPS_URL")
        try:probe=response_probe(url,o.timeout)
        except Exception as exc:
            probe={"status":0,"error_type":type(exc).__name__,"error":str(exc),"content_length":0,"content_type":"","final_url":url}
            blockers.append(spec["package_id"].upper()+"_PROBE_ERROR:"+type(exc).__name__)
        probes.append(probe)
        if int(probe.get("status") or 0) not in {200,206}:blockers.append(spec["package_id"].upper()+"_HTTP_STATUS")
        if not media_type_allowed(str(spec["package_id"]),str(probe.get("content_type") or ""),str(probe.get("content_disposition") or ""),str(probe.get("final_url") or "")):
            blockers.append(spec["package_id"].upper()+"_UNSAFE_MEDIA_TYPE")
        expected=int(spec.get("expected_size") or 0);reported=int(probe.get("content_length") or 0)
        if expected>0 and reported>0 and expected!=reported:blockers.append(spec["package_id"].upper()+f"_SIZE_METADATA_MISMATCH:{expected}!={reported}")
    rows,remaining,required=compute_budget(packages,probes,cache,o.database_reserve_bytes,o.minimum_free_after_bytes,o.download_safety_factor)
    usage=shutil.disk_usage(cache)
    if usage.free<required:blockers.append(f"INSUFFICIENT_DISK_HEADROOM:{usage.free}<{required}")
    database=o.database.expanduser().resolve()
    if database.exists() and not database.is_file():blockers.append("DATABASE_PATH_NOT_FILE")
    passed=not blockers
    now=__import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()
    summary={"schema_version":1,"task_id":"aays1-internet-access-3-runtime-resource-download-preflight-20260722","slot_id":SLOT_ID,
      "state":"runtime_validation_passed" if passed else "blocked","updated_at":now,"packages_expected":4,"packages":[{**s,"probe":p,**b} for s,p,b in zip(packages,probes,rows)],
      "budget":{"remaining_download_bytes":remaining,"database_reserve_bytes":o.database_reserve_bytes,"minimum_free_after_bytes":o.minimum_free_after_bytes,
      "download_safety_factor":o.download_safety_factor,"required_free_bytes":required,"disk_total_bytes":usage.total,"disk_free_bytes":usage.free,"database_path":str(database)},
      "source_checks_executed":4,"validation":{"passed":passed,"blockers":blockers},"parcel_relations_promoted":0,"confidence_uplifts":0,
      "actual_business_data_rows_written":0,"final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False}
    write(r/o.runner_output,summary);write(r/o.web_output,summary);print(json.dumps(summary,ensure_ascii=False,indent=2));return 0 if passed else 2

if __name__=="__main__":
    try:raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"slot_id":SLOT_ID,"state":"exception","error_type":type(exc).__name__,"error":str(exc),"final_ready":False,
        "fake_data":False,"db_write":False,"migration":False,"production_deploy":False},ensure_ascii=False,indent=2),file=__import__("sys").stderr);raise
