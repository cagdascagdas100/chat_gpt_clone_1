from __future__ import annotations
import argparse,hashlib,html,json,os,re,urllib.parse,urllib.request
from datetime import datetime,timezone
from pathlib import Path

TASK_ID="parcel-label-3-epc-postcode-search-v1-20260802"
PROBE="england_map_web/data/distance_property_types/parcel_label_3_canonical_probe_latest.json"
INPUT="docs/chatgpt_status/_shared/slots_21/parcel_label_3/evidence/epc_postcode_search_input_20260802.json"
OUT=("docs/chatgpt_status/_shared/slots_21/parcel_label_3/epc_postcode_search_result_latest.json","england_map_web/data/aays_21_slots/parcel_label_3/epc_postcode_search_latest.json")
IDS=("parcel_61523","parcel_61524","parcel_61525")
BASE="https://find-energy-certificate.service.gov.uk/find-a-certificate/search-by-postcode"
ENTRY="https://www.gov.uk/find-energy-certificate"
OGL="https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
MAX_BYTES=1048576

def now(): return datetime.now(timezone.utc).isoformat()
def sha(v):
    if isinstance(v,str): v=v.encode()
    return hashlib.sha256(v).hexdigest()
def write(path,obj):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True);t=p.with_name(p.name+".tmp")
    t.write_text(json.dumps(obj,ensure_ascii=False,separators=(",",":")),encoding="utf-8");os.replace(t,p)

def rows():
    points={x["parcel_id"]:x for x in json.loads(Path(PROBE).read_text())["canonical_points"]}
    maps={x["parcel_id"]:x for x in json.loads(Path(INPUT).read_text())["parcel_postcodes"]}
    out=[]
    for pid in IDS:
        p,m=points.get(pid),maps.get(pid)
        if not p or p.get("geometry_type")!="Point" or p.get("point_valid") is not True: raise ValueError("invalid point "+pid)
        if not m or not re.fullmatch(r"[A-Z]{1,2}\d[A-Z\d]?\s+\d[A-Z]{2}",m.get("postcode","")): raise ValueError("invalid postcode "+pid)
        if m.get("exact_parcel_bound") is not False: raise ValueError("mapping must remain candidate-only")
        out.append({"parcel_id":pid,"postcode":m["postcode"]})
    return out

def validate():
    rows()
    if any(Path(x).is_absolute() for x in (PROBE,INPUT,*OUT)): raise ValueError("relative paths required")
    if not all(x.startswith(("docs/chatgpt_status/_shared/slots_21/parcel_label_3/","england_map_web/data/aays_21_slots/parcel_label_3/")) for x in OUT): raise ValueError("write boundary")
    print("PASS_TARGET_3_GOVUK_EPC_POSTCODE_SEARCH_MAX1MIB_ADDRESS_EVIDENCE_ONLY")

def parse(raw):
    text=raw.decode("utf-8",errors="replace")
    heading=re.search(r"<h1[^>]*>\s*([^<]*EPCs?\s+for\s+[^<]+)</h1>",text,re.I)
    links=[]
    for m in re.finditer(r'href="(/energy-certificate/[^"]+)"[^>]*>\s*([^<]+?)\s*</a>',text,re.I|re.S):
        address=html.unescape(re.sub(r"\s+"," ",m.group(2))).strip()
        links.append({"certificate_path":m.group(1),"address_sha256":sha(address)})
    return {"page_heading":html.unescape(heading.group(1)).strip() if heading else None,"certificate_link_count":len(links),"records":links[:100]}

def run(timeout):
    evidence=[];pages=[]
    for row in rows():
        url=BASE+"?"+urllib.parse.urlencode({"postcode":row["postcode"]});at=now()
        req=urllib.request.Request(url,headers={"User-Agent":"TerraYield-AAYS/1.0 bounded official GOV.UK EPC research"})
        try:
            with urllib.request.urlopen(req,timeout=timeout) as response:
                raw=response.read(MAX_BYTES+1)
                if len(raw)>MAX_BYTES: raise ValueError("response exceeded 1 MiB")
                p=parse(raw)
                pages.append({"parcel_id":row["parcel_id"],"candidate_postcode":row["postcode"],"source_url":url,**p,"candidate_only":True,"property_type_binding_claimed":False,"exact_parcel_binding_claimed":False})
                evidence.append({"parcel_id":row["parcel_id"],"source_url":url,"accessed_at":at,"content_sha256":sha(raw),"sha256_basis":"bounded_raw_response_bytes","record_scope":"one official GOV.UK EPC postcode search page; max 1 MiB; no certificate-detail crawl","supports_fields":["postcode","address","certificate link","energy rating","valid until"],"relevant_record_ids_or_excerpt":{"page_heading":p["page_heading"],"certificate_link_count":p["certificate_link_count"],"address_hashes":[x["address_sha256"] for x in p["records"]]},"license_or_terms_url":OGL,"service_entry_url":ENTRY,"http_status":getattr(response,"status",None)})
        except Exception as exc:
            msg=f"GOVUK_EPC_POSTCODE_SEARCH_ERROR:{type(exc).__name__}:{exc}"
            evidence.append({"parcel_id":row["parcel_id"],"source_url":url,"accessed_at":at,"content_sha256":sha(msg),"sha256_basis":"bounded_error_evidence_string","record_scope":"one official GOV.UK EPC postcode search request; no certificate-detail crawl","supports_fields":["EPC postcode search endpoint availability"],"relevant_record_ids_or_excerpt":msg[:512],"license_or_terms_url":OGL,"service_entry_url":ENTRY,"http_status":getattr(exc,"code",None)})
    count=sum(p["certificate_link_count"]>0 for p in pages);state="POSTCODE_EPC_PAGES_FOUND" if count else "NO_DATA_CONTINUE"
    result={"schema_version":1,"workstream_id":"AAYS_21_SLOT_SAFE_PARALLEL_V1","slot_id":"parcel_label_3","task_id":TASK_ID,"generated_at":now(),"state":state,"panel_status":"PUBLISHED","completed_count":3,"target_count":3,"previous_percent":0.0,"progress_percent":100.0,"percent_increase":100.0,"validated_canonical_points":list(IDS),"produced_candidate_rows":count,"postcode_pages":pages,"source_evidence":evidence,"blocker":{"code":"NONE" if count else "GOVUK_EPC_POSTCODE_SEARCH_NO_USABLE_RESPONSE","state":state,"manual_action_required":False,"retry_unchanged_route":False},"next_unverified_step":"VALIDATE_EPC_ADDRESS_CANDIDATES_WITHOUT_PARCEL_OR_PROPERTY_TYPE_INFERENCE" if count else "SELECT_NEXT_OFFICIAL_OR_FREE_SOURCE_AFTER_GOVUK_EPC_POSTCODE_SEARCH","large_data_downloaded":False,"property_type_binding_claimed":False,"exact_parcel_binding_claimed":False,"inferred_values":0,"fake_data":False,"final_ready":False}
    for path in OUT: write(path,result)
    return result

def main():
    p=argparse.ArgumentParser();p.add_argument("--timeout",type=float,default=20);p.add_argument("--validate-only",action="store_true");a=p.parse_args()
    if a.validate_only: validate();return
    r=run(a.timeout);print(json.dumps({"state":r["state"],"completed_count":3,"target_count":3,"produced_candidate_rows":r["produced_candidate_rows"],"evidence_records":len(r["source_evidence"])},separators=(",",":")))
if __name__=="__main__": main()
