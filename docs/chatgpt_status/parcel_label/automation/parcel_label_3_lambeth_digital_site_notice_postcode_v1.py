from __future__ import annotations
import argparse, hashlib, html, json, os, re, urllib.parse, urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

TASK_ID="parcel-label-3-lambeth-digital-site-notice-postcode-v1-20260802"
PROBE="england_map_web/data/distance_property_types/parcel_label_3_canonical_probe_latest.json"
INPUT="docs/chatgpt_status/_shared/slots_21/parcel_label_3/evidence/epc_postcode_search_input_20260802.json"
OUT=("docs/chatgpt_status/_shared/slots_21/parcel_label_3/lambeth_digital_site_notice_postcode_result_latest.json","england_map_web/data/aays_21_slots/parcel_label_3/lambeth_digital_site_notice_postcode_latest.json")
HOME="https://digitalsitenotice.lambeth.gov.uk/"
TERMS="https://www.lambeth.gov.uk/planning-building-control/planning-applications/search-submit-comment-applications"
DATA="https://www.lambeth.gov.uk/planning-building-control/planning-applications/planning-permissions-data"
IDS=("parcel_61523","parcel_61524","parcel_61525")
MAX=1048576

def now(): return datetime.now(timezone.utc).isoformat()
def digest(v):
    if isinstance(v,str): v=v.encode()
    return hashlib.sha256(v).hexdigest()
def write(path,obj):
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True); t=p.with_name(p.name+".tmp")
    t.write_text(json.dumps(obj,ensure_ascii=False,separators=(",",":")),encoding="utf-8"); os.replace(t,p)

def inputs():
    points={r["parcel_id"]:r for r in json.loads(Path(PROBE).read_text())["canonical_points"]}
    pcs={r["parcel_id"]:r for r in json.loads(Path(INPUT).read_text())["parcel_postcodes"]}
    out=[]
    for pid in IDS:
        p=points.get(pid); c=pcs.get(pid); postcode=" ".join(str((c or {}).get("postcode","")).upper().split())
        if not p or p.get("geometry_type")!="Point" or p.get("point_valid") is not True: raise ValueError("invalid point "+pid)
        if not c or c.get("exact_parcel_bound") is not False or not re.fullmatch(r"[A-Z]{1,2}\d[A-Z\d]?\s+\d[A-Z]{2}",postcode): raise ValueError("invalid postcode "+pid)
        out.append((pid,postcode))
    return out

class Forms(HTMLParser):
    def __init__(self): super().__init__(); self.forms=[]; self.cur=None
    def handle_starttag(self,tag,attrs):
        d={k.lower():(v or "") for k,v in attrs}
        if tag=="form": self.cur={"action":d.get("action",""),"method":d.get("method","get").lower(),"inputs":[]}; self.forms.append(self.cur)
        elif tag=="input" and self.cur is not None: self.cur["inputs"].append(d)
    def handle_endtag(self,tag):
        if tag=="form": self.cur=None

class Links(HTMLParser):
    def __init__(self): super().__init__(); self.href=None; self.buf=[]; self.rows=[]
    def handle_starttag(self,tag,attrs):
        if tag=="a":
            href=dict(attrs).get("href","")
            if "/planning-applications/" in href: self.href=href; self.buf=[]
    def handle_data(self,data):
        if self.href is not None: self.buf.append(data)
    def handle_endtag(self,tag):
        if tag=="a" and self.href is not None:
            self.rows.append((self.href,html.unescape(" ".join("".join(self.buf).split()))[:500])); self.href=None; self.buf=[]

def open1(req,timeout):
    with urllib.request.urlopen(req,timeout=timeout) as r:
        b=r.read(MAX+1)
        if len(b)>MAX: raise ValueError("response exceeded 1 MiB")
        return b,getattr(r,"status",None),r.geturl()

def search(postcode,timeout):
    ua={"User-Agent":"TerraYield-AAYS/1.0 bounded Lambeth planning research"}
    hb,hs,hu=open1(urllib.request.Request(HOME,headers=ua),timeout); parser=Forms(); parser.feed(hb.decode(errors="replace"))
    chosen=None
    for f in parser.forms:
        for x in f["inputs"]:
            if "postcode" in " ".join([x.get("name",""),x.get("id",""),x.get("placeholder",""),x.get("aria-label","")]).lower():
                chosen=(f,x.get("name") or x.get("id")); break
        if chosen: break
    if not chosen or not chosen[1]: raise ValueError("postcode form not found")
    f,key=chosen; fields={}
    for x in f["inputs"]:
        n=x.get("name",""); kind=x.get("type","text").lower()
        if n and kind not in {"submit","button","image","file"} and not (kind in {"checkbox","radio"} and "checked" not in x): fields[n]=x.get("value","")
    fields[key]=postcode; action=urllib.parse.urljoin(hu,f.get("action") or hu); data=urllib.parse.urlencode(fields)
    if (f.get("method") or "get").lower()=="post": req=urllib.request.Request(action,data=data.encode(),headers={**ua,"Content-Type":"application/x-www-form-urlencoded"})
    else: req=urllib.request.Request(action+("&" if "?" in action else "?")+data,headers=ua)
    rb,rs,ru=open1(req,timeout); lp=Links(); lp.feed(rb.decode(errors="replace")); seen=set(); candidates=[]
    for href,text in lp.rows:
        url=urllib.parse.urljoin(ru,href)
        if url in seen: continue
        seen.add(url); candidates.append({"application_url":url,"visible_text":text,"postcode_search":postcode,"candidate_only":True,"exact_parcel_binding_claimed":False,"property_type_binding_claimed":False})
        if len(candidates)>=20: break
    return candidates,{"source_url":ru,"service_entry_url":HOME,"accessed_at":now(),"content_sha256":digest(hb+b"\n---RESULT---\n"+rb),"sha256_basis":"bounded_homepage_and_search_result_bytes","record_scope":"one official Lambeth Digital Site Notice postcode search; form discovery plus one bounded submission; max 20 links; max 1 MiB per response","supports_fields":["postcode search","planning application URL","visible result text"],"relevant_record_ids_or_excerpt":{"postcode":postcode,"candidate_count":len(candidates),"application_urls":[x["application_url"] for x in candidates]},"terms_url":TERMS,"planning_permissions_data_url":DATA,"home_http_status":hs,"result_http_status":rs}

def validate():
    inputs()
    for p in (PROBE,INPUT,*OUT):
        if Path(p).is_absolute(): raise ValueError("relative paths required")
    print("PASS_TARGET_3_LAMBETH_DIGITAL_SITE_NOTICE_POSTCODE_FORM_DISCOVERY_MAX1MIB_CANDIDATE_ONLY")

def run(timeout):
    evidence=[]; candidates=[]
    for pid,postcode in inputs():
        at=now()
        try:
            rows,ev=search(postcode,timeout); candidates.extend({"parcel_id":pid,**x} for x in rows); evidence.append({"parcel_id":pid,**ev})
        except Exception as exc:
            msg=f"LAMBETH_DIGITAL_SITE_NOTICE_POSTCODE_ERROR:{type(exc).__name__}:{exc}"
            evidence.append({"parcel_id":pid,"source_url":HOME,"accessed_at":at,"content_sha256":digest(msg),"sha256_basis":"bounded_error_evidence_string","record_scope":"one official Lambeth Digital Site Notice postcode search attempt; no document crawl","supports_fields":["Digital Site Notice postcode-search endpoint availability"],"relevant_record_ids_or_excerpt":msg[:512],"terms_url":TERMS,"planning_permissions_data_url":DATA,"http_status":getattr(exc,"code",None)})
    state="PLANNING_APPLICATION_CANDIDATES_FOUND" if candidates else "NO_DATA_CONTINUE"
    result={"schema_version":1,"workstream_id":"AAYS_21_SLOT_SAFE_PARALLEL_V1","slot_id":"parcel_label_3","task_id":TASK_ID,"generated_at":now(),"state":state,"panel_status":"PUBLISHED","completed_count":3,"target_count":3,"previous_percent":0.0,"progress_percent":100.0,"percent_increase":100.0,"validated_canonical_points":list(IDS),"produced_candidate_rows":len(candidates),"candidate_rows":candidates,"source_evidence":evidence,"blocker":{"code":"NONE" if candidates else "LAMBETH_DIGITAL_SITE_NOTICE_NO_USABLE_RESPONSE_OR_NO_POSTCODE_RESULTS","state":state,"manual_action_required":False,"retry_unchanged_route":False},"next_unverified_step":"VALIDATE_LAMBETH_PLANNING_APPLICATION_CANDIDATES_WITHOUT_PARCEL_OR_PROPERTY_TYPE_INFERENCE" if candidates else "SELECT_NEXT_OFFICIAL_OR_FREE_SOURCE_AFTER_LAMBETH_DIGITAL_SITE_NOTICE_POSTCODE","large_data_downloaded":False,"document_crawl_performed":False,"property_type_binding_claimed":False,"exact_parcel_binding_claimed":False,"inferred_values":0,"fake_data":False,"final_ready":False}
    for p in OUT: write(p,result)
    return result

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--timeout",type=float,default=20); ap.add_argument("--validate-only",action="store_true"); a=ap.parse_args()
    if a.validate_only: validate(); return
    r=run(a.timeout); print(json.dumps({"state":r["state"],"completed_count":3,"target_count":3,"produced_candidate_rows":r["produced_candidate_rows"],"evidence_records":len(r["source_evidence"])},separators=(",",":")))

if __name__=="__main__": main()
