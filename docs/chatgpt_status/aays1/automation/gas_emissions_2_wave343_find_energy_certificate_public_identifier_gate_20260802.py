#!/usr/bin/env python3
"""Wave343: bounded public Find an Energy Certificate identifier-access gate."""
from __future__ import annotations
import argparse, hashlib, json, os, re, tempfile, urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

URLS = [
    "https://www.gov.uk/find-energy-certificate",
    "https://find-energy-certificate.service.gov.uk/find-a-certificate/type-of-property",
]
MAX_BYTES_PER_URL = 750_000
MAX_TOTAL_BYTES = 1_500_000

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")

def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=path.parent) as tmp:
        json.dump(payload,tmp,ensure_ascii=False,sort_keys=True,separators=(",",":"))
        tmp.write("\n")
        name=tmp.name
    os.replace(name,path)

def bounded_fetch(url: str, timeout: int, remaining: int) -> dict[str, Any]:
    limit=max(0,min(MAX_BYTES_PER_URL,remaining))
    req=urllib.request.Request(url,headers={"Accept":"text/html, text/plain, */*","User-Agent":"AAYS-wave343/1.0"},method="GET")
    try:
        with urllib.request.urlopen(req,timeout=timeout) as response:
            data=response.read(limit+1)
            truncated=len(data)>limit
            data=data[:limit]
            return {
                "source_url":url,"final_url":response.geturl(),"http_status":response.status,
                "content_type":response.headers.get("Content-Type"),"bytes_read":len(data),
                "content_sha256":sha256_bytes(data),"truncated":truncated,
                "body_text":data.decode("utf-8",errors="replace"),
                "network_or_validation_error":None,
            }
    except Exception as exc:
        return {
            "source_url":url,"final_url":None,"http_status":getattr(exc,"code",None),
            "content_type":None,"bytes_read":0,"content_sha256":sha256_bytes(b""),
            "truncated":False,"body_text":"",
            "network_or_validation_error":f"{type(exc).__name__}:{exc}",
        }

def markers(text: str) -> dict[str,bool]:
    lower=re.sub(r"\s+"," ",text.lower())
    return {
        "postcode": "postcode" in lower,
        "street_name_and_town": ("street name" in lower and "town" in lower) or ("street and post town" in lower),
        "certificate_number": "certificate number" in lower or "unique reference number" in lower,
        "domestic_property": "a domestic property" in lower or "domestic property" in lower,
        "non_domestic_property": "a non-domestic property" in lower or "non-domestic property" in lower,
        "uprn": bool(re.search(r"\buprn\b",lower)),
        "hmlr_inspire_id": "inspire id" in lower or "land registry-inspire id" in lower,
        "sign_in": "sign in" in lower or "log in" in lower,
    }

def self_test() -> None:
    sample="You can search by postcode, street name and town, or certificate number. A domestic property. A non-domestic property."
    m=markers(sample)
    assert m["postcode"] and m["street_name_and_town"] and m["certificate_number"]
    assert m["domestic_property"] and m["non_domestic_property"]
    assert not m["uprn"] and not m["hmlr_inspire_id"]
    print("SELF_TEST_PASS")

def main() -> None:
    p=argparse.ArgumentParser()
    p.add_argument("--fixture",type=Path)
    p.add_argument("--output",type=Path)
    p.add_argument("--timeout",type=int,default=30)
    p.add_argument("--self-test",action="store_true")
    a=p.parse_args()
    if a.self_test:
        self_test(); return
    if not a.fixture or not a.output:
        p.error("--fixture and --output are required unless --self-test is used")
    fixture_bytes=a.fixture.read_bytes()
    fixture=json.loads(fixture_bytes)
    manifest=fixture.get("source_evidence_manifest",[])
    if len(manifest)!=4:
        raise SystemExit("fixture must contain exactly 4 official evidence records")

    probes=[]; total=0
    for url in URLS:
        probe=bounded_fetch(url,a.timeout,MAX_TOTAL_BYTES-total)
        total+=probe["bytes_read"]
        body=probe.pop("body_text")
        probe["markers"]=markers(body)
        probes.append(probe)

    combined={key:any(p["markers"][key] for p in probes) for key in probes[0]["markers"]}
    identifier_contract = combined["postcode"] and combined["street_name_and_town"] and combined["certificate_number"]
    property_route = combined["domestic_property"] and combined["non_domestic_property"]
    validated = identifier_contract and property_route
    state="PUBLISHED" if validated else "NO_DATA_CONTINUE"
    decision="PUBLIC_REGISTER_IDENTIFIER_CONTRACT_VALIDATED" if validated else "PUBLIC_REGISTER_IDENTIFIER_CONTRACT_NOT_LIVE_ACQUIRED"
    blocker=(
        "THREE_CANONICAL_SAMPLE_ADDRESSES_OR_POSTCODES_NOT_ACQUIRED;"
        "THREE_EXACT_UPRNS_NOT_ACQUIRED;"
        "PUBLIC_REGISTER_DOES_NOT_EVIDENCE_UPRN_OR_HMLR_INSPIRE_ID_SEARCH;"
        "EXACT_OPEN_PARCEL_BINDING_REMAINS_NO_DATA_CONTINUE"
        if validated else
        "PUBLIC_FIND_ENERGY_CERTIFICATE_PAGES_NOT_LIVE_ACQUIRED;"
        "PUBLIC_REGISTER_IDENTIFIER_CONTRACT_NOT_LIVE_VALIDATED;"
        "THREE_EXACT_UPRNS_NOT_ACQUIRED;"
        "EXACT_OPEN_PARCEL_BINDING_REMAINS_NO_DATA_CONTINUE"
    )
    next_step=(
        "ASSESS_CANONICAL_SAMPLE_ADDRESS_OR_POSTCODE_SOURCE_FOR_PUBLIC_EPC_REGISTER_LOOKUP_OR_NO_DATA_CONTINUE"
        if validated else
        "ASSESS_FIND_ENERGY_CERTIFICATE_PUBLIC_ROUTE_METADATA_OR_NO_DATA_CONTINUE"
    )
    network_errors=[f"{p['source_url']}:{p['network_or_validation_error']}" for p in probes if p["network_or_validation_error"]]
    payload={
        "schema_version":1,"architecture_version":3,"workstream_id":"AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id":"gas_emissions_2","wave":343,"accessed_at":utc_now(),"state":state,
        "decision":decision,"blocker":blocker,"first_unverified_step":next_step,
        "fake_data":False,"final_ready":False,"canonical_sample_rows_in_scope":3,
        "hmlr_inspire_ids_in_scope":["46058185","46037757","45981756"],
        "business_rows_produced":0,"parcel_rows_bound":0,"completed_count":0,"target_count":30761,
        "previous_percent":0.0,"current_percent":0.0,"percent_increase":0.0,
        "fixture_sha256":sha256_bytes(fixture_bytes),
        "official_source_evidence_count":len(manifest),"source_evidence_manifest":manifest,
        "probe_count":len(probes),"total_bytes_read":total,"max_total_bytes":MAX_TOTAL_BYTES,
        "identifier_contract_validated":identifier_contract,"property_route_validated":property_route,
        "public_identifiers_validated":[k for k in ["postcode","street_name_and_town","certificate_number"] if combined[k]],
        "uprn_search_evidenced":combined["uprn"],"hmlr_inspire_id_search_evidenced":combined["hmlr_inspire_id"],
        "sign_in_marker_observed":combined["sign_in"],"probes":probes,
        "network_or_validation_errors":network_errors,
        "form_submitted":False,"personal_data_submitted":False,"certificate_downloaded":False,
    }
    atomic_json(a.output,payload)

if __name__=="__main__":
    main()
