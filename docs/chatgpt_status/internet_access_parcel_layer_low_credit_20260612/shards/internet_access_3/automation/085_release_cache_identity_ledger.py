#!/usr/bin/env python3
"""Bind resumable release cache files to immutable package identities.

Runs before hydration. Existing final/partial bytes are preserved only when an adjacent
identity ledger matches the current official package specification. Unknown or stale
bytes are moved into a quarantine directory and never counted as resumable cache.
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, os, re, shutil, tempfile
from pathlib import Path
from typing import Any

SLOT_ID = "internet_access_3"
AUTOMATION = Path(__file__).resolve().parent
DEFAULT_OS = "docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/runner_outputs/041_os_opendata_download_resolution_latest.json"
DEFAULT_ONS = "docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/runner_outputs/015_ons_uprn_arcgis_release_discovery_latest.json"
DEFAULT_RUNNER = "docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/runner_outputs/055_release_cache_identity_ledger_latest.json"
DEFAULT_WEB = "england_map_web/data/aays_21_slots/internet_access_3/release_cache_identity_ledger_latest.json"


def args() -> argparse.Namespace:
    p=argparse.ArgumentParser();p.add_argument("--repo-root",type=Path);p.add_argument("--os-resolution",default=DEFAULT_OS);p.add_argument("--ons-discovery",default=DEFAULT_ONS)
    p.add_argument("--cache-dir",type=Path,default=Path(tempfile.gettempdir())/"aays_internet_access_3_release_cache")
    p.add_argument("--runner-output",default=DEFAULT_RUNNER);p.add_argument("--web-output",default=DEFAULT_WEB);return p.parse_args()


def root(explicit: Path|None) -> Path:
    if explicit:return explicit.expanduser().resolve()
    for p in [Path.cwd(),*Path(__file__).resolve().parents]:
        if (p/"docs").exists() and (p/"england_map_web").exists():return p
    raise FileNotFoundError("repo root")


def load(path: Path) -> Any:
    with path.open("r",encoding="utf-8-sig") as h:return json.load(h)


def write(path: Path,payload: Any) -> None:
    path.parent.mkdir(parents=True,exist_ok=True);fd,tmp=tempfile.mkstemp(prefix=path.name+".",suffix=".tmp",dir=path.parent)
    try:
        with os.fdopen(fd,"w",encoding="utf-8") as h:json.dump(payload,h,ensure_ascii=False,separators=(",",":"));h.write("\n")
        os.replace(tmp,path)
    except Exception:
        try:os.unlink(tmp)
        except FileNotFoundError:pass
        raise


def import_hydrator():
    path=AUTOMATION/"071_full_release_hydration_manifest.py";spec=importlib.util.spec_from_file_location("rev15_hydrator",path)
    if not spec or not spec.loader:raise ImportError(path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod


def safe(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+","_",value).strip("._")[:180] or "package"


def canonical_identity(spec: dict[str,Any]) -> dict[str,Any]:
    keys=("package_id","authority","product_id","title","download_url","expected_size","expected_md5","release_label","arcgis_item_id")
    return {k:spec.get(k) for k in keys}


def identity_sha(identity: dict[str,Any]) -> str:
    return hashlib.sha256(json.dumps(identity,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()


def package_paths(cache: Path,spec: dict[str,Any]) -> tuple[Path,Path,Path]:
    ext=".zip" if str(spec["package_id"]).startswith("os_") else ".download"
    base=cache/(safe(f"{spec['package_id']}_{spec.get('release_label') or ''}")+ext)
    return base,base.with_suffix(base.suffix+".part"),base.with_suffix(base.suffix+".identity.json")


def quarantine(path: Path,qdir: Path,reason: str,identity_prefix: str) -> Path|None:
    if not path.exists():return None
    qdir.mkdir(parents=True,exist_ok=True)
    target=qdir/(path.name+f".{reason}.{identity_prefix}")
    counter=1
    while target.exists():target=qdir/(path.name+f".{reason}.{identity_prefix}.{counter}");counter+=1
    shutil.move(str(path),str(target));return target


def main() -> int:
    o=args();r=root(o.repo_root);cache=o.cache_dir.expanduser().resolve();cache.mkdir(parents=True,exist_ok=True)
    packages=import_hydrator().build_packages(load(r/o.os_resolution),load(r/o.ons_discovery));rows=[];blockers=[];qdir=cache/"quarantine"
    for spec in packages:
        final,partial,ledger=package_paths(cache,spec);identity=canonical_identity(spec);digest=identity_sha(identity);existing=None
        if ledger.exists():
            try:existing=load(ledger)
            except Exception as exc:blockers.append(f"{spec['package_id'].upper()}_LEDGER_PARSE_ERROR:{type(exc).__name__}")
        ledger_match=isinstance(existing,dict) and existing.get("identity_sha256")==digest and existing.get("identity")==identity
        quarantined=[]
        has_bytes=final.exists() or partial.exists()
        if has_bytes and not ledger_match:
            for p in (final,partial,ledger):
                moved=quarantine(p,qdir,"STALE_OR_UNBOUND",digest[:12])
                if moved:quarantined.append(str(moved))
        elif ledger.exists() and not ledger_match:
            moved=quarantine(ledger,qdir,"STALE_LEDGER",digest[:12])
            if moved:quarantined.append(str(moved))
        payload={"schema_version":1,"slot_id":SLOT_ID,"package_id":spec["package_id"],"identity":identity,"identity_sha256":digest,
                 "final_path":str(final),"partial_path":str(partial),"created_or_refreshed_at":__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),
                 "allows_resume_only_when_identity_matches":True,"parcel_relation_promoted":False}
        write(ledger,payload)
        rows.append({"package_id":spec["package_id"],"identity_sha256":digest,"ledger_path":str(ledger),"ledger_match_before":ledger_match,
                     "final_bytes":final.stat().st_size if final.exists() else 0,"partial_bytes":partial.stat().st_size if partial.exists() else 0,
                     "quarantined":quarantined,"cache_state":"BOUND_CACHE_PRESENT" if final.exists() or partial.exists() else "BOUND_EMPTY_CACHE"})
    passed=len(packages)==4 and not blockers
    now=__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()
    summary={"schema_version":1,"task_id":"aays1-internet-access-3-release-cache-identity-ledger-20260722","slot_id":SLOT_ID,
             "state":"runtime_validation_passed" if passed else "blocked","updated_at":now,"packages_expected":4,"packages_bound":len(rows),"packages":rows,
             "quarantined_files":sum(len(x["quarantined"]) for x in rows),"bound_cache_bytes":sum(x["final_bytes"]+x["partial_bytes"] for x in rows),
             "source_checks_executed":4,"validation":{"passed":passed,"blockers":blockers},"parcel_relations_promoted":0,"confidence_uplifts":0,
             "actual_business_data_rows_written":0,"final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False}
    write(r/o.runner_output,summary);write(r/o.web_output,summary);print(json.dumps(summary,ensure_ascii=False,indent=2));return 0 if passed else 2

if __name__=="__main__":
    try:raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"slot_id":SLOT_ID,"state":"exception","error_type":type(exc).__name__,"error":str(exc),"final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False},ensure_ascii=False),file=__import__('sys').stderr);raise
