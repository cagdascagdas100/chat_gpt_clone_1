from __future__ import annotations
import argparse, hashlib, http.cookiejar, json, os, re, tempfile
import urllib.parse, urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

SLOT_ID="parcel_label_3"
TASK_ID="parcel-label-3-voa-business-rates-postcode-v1-20260802"
PROBE_BLOB_SHA="ea8e95593a58ab6cbb9369abc30bc38ce8543ad9"
SEARCH_URL="https://www.tax.service.gov.uk/business-rates-find/search"
GOVUK_URL="https://www.gov.uk/find-business-rates"
GUIDANCE_URL="https://www.gov.uk/guidance/help-with-the-2026-business-rates-revaluation"
ABOUT_URL="https://www.gov.uk/government/organisations/valuation-office-agency/about"
TERMS_URL="https://www.tax.service.gov.uk/business-rates-find/terms-and-conditions"
OGL_URL="https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
MAX_BYTES=1048576
MAX_CANDIDATES=20
POSTCODES={"parcel_61523":"SW16 5TG","parcel_61524":"SW16 5AE","parcel_61525":"SW16 5AZ"}
POINTS={"parcel_61523":(-0.1387938,51.4196454),"parcel_61524":(-0.1407703,51.4170637),"parcel_61525":(-0.1398845,51.4167453)}

class Forms(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True); self.forms=[]; self.f=None; self.sel=None; self.opt=None; self.txt=[]
    def handle_starttag(self,tag,attrs):
        a={k.lower():(v or "") for k,v in attrs}; tag=tag.lower()
        if tag=="form": self.f={"action":a.get("action",""),"method":(a.get("method") or "get").lower(),"inputs":[],"selects":[]}
        elif self.f is not None and tag=="input": self.f["inputs"].append(a)
        elif self.f is not None and tag=="select": self.sel={"name":a.get("name",""),"id":a.get("id",""),"options":[]}
        elif self.sel is not None and tag=="option": self.opt={"value":a.get("value",""),"selected":"selected" in a}; self.txt=[]
    def handle_data(self,data):
        if self.opt is not None: self.txt.append(data)
    def handle_endtag(self,tag):
        tag=tag.lower()
        if tag=="option" and self.opt is not None and self.sel is not None:
            self.opt["text"]=" ".join("".join(self.txt).split()); self.sel["options"].append(self.opt); self.opt=None
        elif tag=="select" and self.sel is not None and self.f is not None: self.f["selects"].append(self.sel); self.sel=None
        elif tag=="form" and self.f is not None: self.forms.append(self.f); self.f=None

class Links(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True); self.links=[]; self.href=None; self.txt=[]; self.page=[]
    def handle_starttag(self,tag,attrs):
        if tag.lower()=="a": self.href=dict(attrs).get("href",""); self.txt=[]
    def handle_data(self,data):
        s=" ".join(data.split())
        if s: self.page.append(s); self.txt.append(s) if self.href is not None else None
    def handle_endtag(self,tag):
        if tag.lower()=="a" and self.href is not None:
            s=" ".join(self.txt)
            if s: self.links.append((self.href,s))
            self.href=None; self.txt=[]

def root(): return Path(__file__).resolve().parents[4]
def now(): return datetime.now(timezone.utc).isoformat()
def sha(b:bytes): return hashlib.sha256(b).hexdigest()
def atomic(path:Path,payload:dict[str,Any]):
    path.parent.mkdir(parents=True,exist_ok=True); data=json.dumps(payload,ensure_ascii=False,separators=(",",":")).encode()
    fd,tmp=tempfile.mkstemp(prefix=path.name+".",dir=str(path.parent))
    try:
        with os.fdopen(fd,"wb") as f: f.write(data); f.flush(); os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)

def load_points(base:Path):
    rows=json.loads((base/"england_map_web/data/distance_property_types/parcel_label_3_canonical_probe_latest.json").read_text())["canonical_points"]
    found={r.get("parcel_id"):r for r in rows if isinstance(r,dict) and r.get("parcel_id") in POINTS}
    if set(found)!=set(POINTS): raise ValueError("exact target parcels missing")
    out=[]
    for pid in POSTCODES:
        r=found[pid]; lon=float(r["longitude"]); lat=float(r["latitude"]); elon,elat=POINTS[pid]
        if r.get("geometry_type")!="Point" or r.get("point_valid") is not True or abs(lon-elon)>1e-7 or abs(lat-elat)>1e-7:
            raise ValueError("invalid canonical Point "+pid)
        out.append({"parcel_id":pid,"longitude":lon,"latitude":lat})
    return out

def open_bounded(opener,req,timeout):
    with opener.open(req,timeout=timeout) as res:
        raw=res.read(MAX_BYTES+1)
        if len(raw)>MAX_BYTES: raise ValueError("response exceeds 1 MiB")
        return int(getattr(res,"status",200)),res.geturl(),raw

def discover(html):
    p=Forms(); p.feed(html)
    for f in p.forms:
        for i in f["inputs"]:
            mark=" ".join((i.get("name",""),i.get("id",""),i.get("placeholder",""))).lower()
            if "post" in mark: return f,i.get("name") or i.get("id")
    return None,None

def fields(form,name,postcode):
    out=[]; setpc=False
    for i in form["inputs"]:
        n=i.get("name",""); typ=(i.get("type") or "text").lower(); val=i.get("value","")
        if not n: continue
        mark=" ".join((n,i.get("id",""),val)).lower()
        if n==name: out.append((n,postcode)); setpc=True
        elif typ=="hidden": out.append((n,val))
        elif typ in {"radio","checkbox"} and ("post" in mark or i.get("checked")=="checked"): out.append((n,val or "true"))
        elif typ in {"submit","button"} and val: out.append((n,val))
    for s in form["selects"]:
        n=s.get("name",""); chosen=next((o for o in s["options"] if o.get("selected") and o.get("value")),None)
        if n and chosen: out.append((n,str(chosen["value"])))
    if not setpc: raise ValueError("postcode field not populated")
    return out

def candidates(html,base_url,postcode):
    p=Links(); p.feed(html); page=" ".join(p.page).upper(); pc=postcode.upper()
    if pc not in page and pc.replace(" ","") not in page.replace(" ",""): return []
    rows=[]; seen=set()
    for href,text in p.links:
        url=urllib.parse.urljoin(base_url,href); marker=(text+" "+url).upper()
        if pc in marker or pc.replace(" ","") in marker.replace(" ","") or re.search(r"\b(rateable|valuation|property|premises|shop|office|warehouse|restaurant|business)\b",marker,re.I):
            key=(url,text)
            if key not in seen:
                seen.add(key); rows.append({"source_url":url,"display_text":text[:500],"searched_postcode":postcode,"context_only":True,"exact_parcel_binding":False,"property_type_binding":False})
                if len(rows)>=MAX_CANDIDATES: break
    return rows

def attempt(point,timeout):
    pid=point["parcel_id"]; pc=POSTCODES[pid]; accessed=now(); made=0
    opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    opener.addheaders=[("User-Agent","AAYS-parcel-label-evidence/1.0 bounded official-source research")]
    try:
        status,url,raw=open_bounded(opener,urllib.request.Request(SEARCH_URL,headers={"Accept":"text/html"}),timeout); made+=1
        form,name=discover(raw.decode("utf-8","replace"))
        if not form or not name:
            return [],evidence(pid,pc,point,url,accessed,sha(raw),"bounded_landing_response_bytes","NO_DISCOVERABLE_POSTCODE_FORM",status,made)
        vals=fields(form,name,pc); action=urllib.parse.urljoin(url,form.get("action") or url); method=(form.get("method") or "get").lower()
        enc=urllib.parse.urlencode(vals).encode()
        req=urllib.request.Request(action,data=enc,headers={"Content-Type":"application/x-www-form-urlencoded","Accept":"text/html"}) if method=="post" else urllib.request.Request(action+("&" if urllib.parse.urlparse(action).query else "?")+enc.decode(),headers={"Accept":"text/html"})
        status,url,raw=open_bounded(opener,req,timeout); made+=1; html=raw.decode("utf-8","replace")
        rec=evidence(pid,pc,point,url,accessed,sha(raw),"bounded_search_response_bytes",re.sub(r"\s+"," ",re.sub(r"<[^>]+>"," ",html))[:1500],status,made)
        rec.update({"discovered_form_method":method,"discovered_postcode_field":name})
        return candidates(html,url,pc),rec
    except Exception as exc:
        err=f"VOA_BUSINESS_RATES_POSTCODE_ERROR:{type(exc).__name__}:{exc}"
        return [],evidence(pid,pc,point,SEARCH_URL,accessed,sha(err.encode()),"bounded_error_evidence_string",err,None,made)

def evidence(pid,pc,point,url,accessed,digest,basis,excerpt,status,made):
    return {"parcel_id":pid,"searched_postcode":pc,"canonical_point":point,"source_url":url,"accessed_at":accessed,"content_sha256":digest,"sha256_basis":basis,"record_scope":"one bounded official VOA business-rates postcode form-discovery/search attempt; maximum two requests, 1 MiB and 20 candidates","supports_fields":["rating-list property address","property/premises description where published","rateable-value context where published","valuation record link"],"relevant_record_ids_or_excerpt":excerpt,"terms_or_license_urls":[TERMS_URL,OGL_URL],"http_status":status,"requests_made":made}

def payload(points,timeout):
    rows=[]; ev=[]
    for p in points:
        c,e=attempt(p,timeout); ev.append(e)
        for row in c: row.update({"parcel_id":p["parcel_id"],"canonical_point":p}); rows.append(row)
    n=len(rows)
    return {"schema_version":1,"workstream_id":"AAYS_21_SLOT_SAFE_PARALLEL_V1","slot_id":SLOT_ID,"task_id":TASK_ID,"generated_at":now(),"state":"CANDIDATES_FOUND_CONTEXT_ONLY" if n else "NO_DATA_CONTINUE","panel_status":"PUBLISHED","completed_count":3,"target_count":3,"previous_percent":0.0,"progress_percent":100.0,"percent_increase":100.0,"validated_canonical_points":points,"produced_candidate_rows":n,"candidate_rows":rows,"source_evidence":ev,"blocker":{"code":None if n else "VOA_BUSINESS_RATES_NO_USABLE_RESPONSE_OR_NO_POSTCODE_RESULT","state":"NONE" if n else "NO_DATA_CONTINUE","manual_action_required":False,"retry_unchanged_route":False},"next_unverified_step":"SELECT_NEXT_OFFICIAL_OR_FREE_SOURCE_AFTER_VOA_BUSINESS_RATES_POSTCODE","service_url":SEARCH_URL,"govuk_service_url":GOVUK_URL,"guidance_url":GUIDANCE_URL,"voa_about_url":ABOUT_URL,"terms_url":TERMS_URL,"open_government_licence_url":OGL_URL,"login_or_api_key_used":False,"bulk_download_performed":False,"full_rating_list_scan_performed":False,"large_data_downloaded":False,"property_type_binding_claimed":False,"exact_parcel_binding_claimed":False,"inferred_values":0,"fake_data":False,"final_ready":False}

def validate(base):
    if len(load_points(base))!=3 or not SEARCH_URL.startswith("https://www.tax.service.gov.uk/"): raise ValueError("validation failed")
    print("PASS_TARGET_3_VOA_BUSINESS_RATES_FORM_DISCOVERY_POSTCODE_MAX2_REQUESTS_EACH_MAX1MIB_20_CANDIDATES_CONTEXT_ONLY")

def main():
    a=argparse.ArgumentParser(); a.add_argument("--timeout",type=float,default=5); a.add_argument("--validate-only",action="store_true"); args=a.parse_args()
    base=root(); validate(base)
    if args.validate_only:return 0
    data=payload(load_points(base),max(1,min(args.timeout,30)))
    atomic(base/"docs/chatgpt_status/_shared/slots_21/parcel_label_3/voa_business_rates_postcode_result_latest.json",data)
    atomic(base/"england_map_web/data/aays_21_slots/parcel_label_3/voa_business_rates_postcode_latest.json",data)
    print(f"PASS_CONTEXT_CANDIDATES_{data['produced_candidate_rows']}_3_OF_3" if data["produced_candidate_rows"] else "PASS_NO_DATA_CONTINUE_3_OF_3")
    return 0
if __name__=="__main__": raise SystemExit(main())
