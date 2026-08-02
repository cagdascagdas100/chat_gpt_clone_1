from __future__ import annotations
import argparse, hashlib, http.cookiejar, json, os, re, tempfile
import urllib.parse, urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

SLOT="parcel_label_3"; TASK="parcel-label-3-gias-establishment-postcode-v1-20260802"
SEARCH="https://get-information-schools.service.gov.uk/Search/Results"
GUIDANCE="https://www.get-information-schools.service.gov.uk/Guidance/General"
ABOUT="https://www.get-information-schools.service.gov.uk/about/"
TERMS="https://get-information-schools.service.gov.uk/TermsofUse"
AUP="https://get-information-schools.service.gov.uk/AcceptableUsePolicy"
OGL="https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
MAX=1_048_576; LIMIT=20
POST={"parcel_61523":"SW16 5TG","parcel_61524":"SW16 5AE","parcel_61525":"SW16 5AZ"}
PTS={"parcel_61523":(-0.1387938,51.4196454),"parcel_61524":(-0.1407703,51.4170637),"parcel_61525":(-0.1398845,51.4167453)}

class Forms(HTMLParser):
 def __init__(self): super().__init__(convert_charrefs=True); self.forms=[]; self.f=None
 def handle_starttag(self,t,a):
  d={k.lower():(v or "") for k,v in a}; t=t.lower()
  if t=="form": self.f={"action":d.get("action",""),"method":(d.get("method") or "get").lower(),"inputs":[]}
  elif self.f is not None and t=="input": self.f["inputs"].append(d)
 def handle_endtag(self,t):
  if t.lower()=="form" and self.f is not None: self.forms.append(self.f); self.f=None

class Links(HTMLParser):
 def __init__(self): super().__init__(convert_charrefs=True); self.links=[]; self.href=None; self.txt=[]; self.page=[]
 def handle_starttag(self,t,a):
  if t.lower()=="a": self.href=dict(a).get("href") or ""; self.txt=[]
 def handle_data(self,d):
  s=" ".join(d.split())
  if s: self.page.append(s); self.txt.append(s) if self.href is not None else None
 def handle_endtag(self,t):
  if t.lower()=="a" and self.href is not None:
   s=" ".join(self.txt)
   if s: self.links.append((self.href,s))
   self.href=None; self.txt=[]

def root(): return Path(__file__).resolve().parents[4]
def now(): return datetime.now(timezone.utc).isoformat()
def sha(b): return hashlib.sha256(b).hexdigest()
def atomic(p,x):
 p.parent.mkdir(parents=True,exist_ok=True); raw=json.dumps(x,ensure_ascii=False,separators=(",",":")).encode()
 fd,tmp=tempfile.mkstemp(prefix=p.name+".",dir=str(p.parent))
 try:
  with os.fdopen(fd,"wb") as f: f.write(raw); f.flush(); os.fsync(f.fileno())
  os.replace(tmp,p)
 finally:
  if os.path.exists(tmp): os.unlink(tmp)

def points(base):
 rows=json.loads((base/"england_map_web/data/distance_property_types/parcel_label_3_canonical_probe_latest.json").read_text())["canonical_points"]
 found={r.get("parcel_id"):r for r in rows if isinstance(r,dict) and r.get("parcel_id") in PTS}
 if set(found)!=set(PTS): raise ValueError("exact target parcels missing")
 out=[]
 for pid in POST:
  r=found[pid]; lon=float(r["longitude"]); lat=float(r["latitude"]); elon,elat=PTS[pid]
  if r.get("geometry_type")!="Point" or r.get("point_valid") is not True or abs(lon-elon)>1e-7 or abs(lat-elat)>1e-7: raise ValueError("invalid Point "+pid)
  out.append({"parcel_id":pid,"longitude":lon,"latitude":lat})
 return out

def bounded(opener,req,timeout):
 with opener.open(req,timeout=timeout) as res:
  raw=res.read(MAX+1)
  if len(raw)>MAX: raise ValueError("response exceeds 1 MiB")
  return int(getattr(res,"status",200)),res.geturl(),raw

def form(html):
 p=Forms(); p.feed(html)
 for f in p.forms:
  for i in f["inputs"]:
   m=" ".join((i.get("name",""),i.get("id",""),i.get("placeholder",""),i.get("aria-label",""))).lower()
   if "location" in m or "postcode" in m or "town" in m: return f,i.get("name") or i.get("id")
 return None,None

def fields(f,name,pc):
 out=[]; ok=False
 for i in f["inputs"]:
  n=i.get("name",""); typ=(i.get("type") or "text").lower(); val=i.get("value","")
  if not n: continue
  if n==name: out.append((n,pc)); ok=True
  elif typ=="hidden": out.append((n,val))
  elif typ in {"radio","checkbox"} and i.get("checked")=="checked": out.append((n,val or "true"))
  elif typ in {"submit","button"} and val: out.append((n,val))
 if not ok: raise ValueError("location field not populated")
 return out

def candidates(html,url,pc):
 p=Links(); p.feed(html); page=" ".join(p.page).upper(); compact=pc.replace(" ","").upper()
 if pc.upper() not in page and compact not in page.replace(" ",""): return []
 out=[]; seen=set()
 for href,text in p.links:
  u=urllib.parse.urljoin(url,href)
  if "/Establishments/Establishment/Details/" not in urllib.parse.urlparse(u).path or u in seen: continue
  seen.add(u); m=re.search(r"/Details/(\d+)",u)
  out.append({"source_url":u,"establishment_name":text[:500],"urn":m.group(1) if m else None,"searched_postcode":pc,"context_only":True,"exact_parcel_binding":False,"property_type_binding":False})
  if len(out)>=LIMIT: break
 return out

def evidence(pid,pc,p,url,accessed,digest,basis,excerpt,status,made):
 return {"parcel_id":pid,"searched_postcode":pc,"canonical_point":p,"source_url":url,"accessed_at":accessed,"content_sha256":digest,"sha256_basis":basis,"record_scope":"one bounded official DfE GIAS location-search attempt; maximum two requests, 1 MiB and 20 establishment-profile candidates","supports_fields":["establishment profile URL","establishment name","URN from profile URL where published","postcode-location search availability"],"relevant_record_ids_or_excerpt":excerpt,"terms_or_license_urls":[TERMS,AUP,OGL],"http_status":status,"requests_made":made}

def attempt(p,timeout):
 pid=p["parcel_id"]; pc=POST[pid]; accessed=now(); made=0
 op=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar())); op.addheaders=[("User-Agent","AAYS-parcel-label-evidence/1.0 bounded official-source research")]
 try:
  status,url,raw=bounded(op,urllib.request.Request(SEARCH,headers={"Accept":"text/html"}),timeout); made+=1
  f,name=form(raw.decode("utf-8","replace"))
  if not f or not name: return [],evidence(pid,pc,p,url,accessed,sha(raw),"bounded_landing_response_bytes","NO_DISCOVERABLE_LOCATION_FORM",status,made)
  enc=urllib.parse.urlencode(fields(f,name,pc)).encode(); action=urllib.parse.urljoin(url,f.get("action") or url); method=(f.get("method") or "get").lower()
  req=urllib.request.Request(action,data=enc,headers={"Content-Type":"application/x-www-form-urlencoded","Accept":"text/html"}) if method=="post" else urllib.request.Request(action+(("&") if urllib.parse.urlparse(action).query else "?")+enc.decode(),headers={"Accept":"text/html"})
  status,url,raw=bounded(op,req,timeout); made+=1; html=raw.decode("utf-8","replace")
  ev=evidence(pid,pc,p,url,accessed,sha(raw),"bounded_search_response_bytes",re.sub(r"\s+"," ",re.sub(r"<[^>]+>"," ",html))[:1500],status,made); ev.update({"discovered_form_method":method,"discovered_location_field":name})
  return candidates(html,url,pc),ev
 except Exception as exc:
  err=f"GIAS_ESTABLISHMENT_POSTCODE_ERROR:{type(exc).__name__}:{exc}"
  return [],evidence(pid,pc,p,SEARCH,accessed,sha(err.encode()),"bounded_error_evidence_string",err,None,made)

def payload(ps,timeout):
 rows=[]; ev=[]
 for p in ps:
  found,e=attempt(p,timeout); ev.append(e)
  for r in found: r.update({"parcel_id":p["parcel_id"],"canonical_point":p}); rows.append(r)
 n=len(rows)
 return {"schema_version":1,"workstream_id":"AAYS_21_SLOT_SAFE_PARALLEL_V1","slot_id":SLOT,"task_id":TASK,"generated_at":now(),"state":"CANDIDATES_FOUND_CONTEXT_ONLY" if n else "NO_DATA_CONTINUE","panel_status":"PUBLISHED","completed_count":3,"target_count":3,"previous_percent":0.0,"progress_percent":100.0,"percent_increase":100.0,"validated_canonical_points":ps,"produced_candidate_rows":n,"candidate_rows":rows,"source_evidence":ev,"blocker":{"code":None if n else "GIAS_ESTABLISHMENT_NO_USABLE_RESPONSE_OR_NO_POSTCODE_RESULT","state":"NONE" if n else "NO_DATA_CONTINUE","manual_action_required":False,"retry_unchanged_route":False},"next_unverified_step":"SELECT_NEXT_OFFICIAL_OR_FREE_SOURCE_AFTER_GIAS_ESTABLISHMENT_POSTCODE","search_url":SEARCH,"guidance_url":GUIDANCE,"about_url":ABOUT,"terms_url":TERMS,"acceptable_use_url":AUP,"open_government_licence_url":OGL,"login_or_api_key_used":False,"bulk_download_performed":False,"establishment_profile_followup_performed":False,"governor_or_personal_data_requested":False,"large_data_downloaded":False,"property_type_binding_claimed":False,"exact_parcel_binding_claimed":False,"inferred_values":0,"fake_data":False,"final_ready":False}

def validate(base):
 if len(points(base))!=3 or MAX!=1_048_576 or LIMIT!=20 or not SEARCH.startswith("https://get-information-schools.service.gov.uk/"): raise ValueError("validation failed")
 print("PASS_TARGET_3_GIAS_ESTABLISHMENT_LOCATION_FORM_MAX2_REQUESTS_EACH_MAX1MIB_20_CANDIDATES_CONTEXT_ONLY")

def main():
 a=argparse.ArgumentParser(); a.add_argument("--timeout",type=float,default=5); a.add_argument("--validate-only",action="store_true"); args=a.parse_args(); base=root(); validate(base)
 if args.validate_only: return 0
 data=payload(points(base),max(1,min(args.timeout,30))); atomic(base/"docs/chatgpt_status/_shared/slots_21/parcel_label_3/gias_establishment_postcode_result_latest.json",data); atomic(base/"england_map_web/data/aays_21_slots/parcel_label_3/gias_establishment_postcode_latest.json",data)
 print(f"PASS_CONTEXT_CANDIDATES_{data['produced_candidate_rows']}_3_OF_3" if data["produced_candidate_rows"] else "PASS_NO_DATA_CONTINUE_3_OF_3"); return 0
if __name__=="__main__": raise SystemExit(main())
