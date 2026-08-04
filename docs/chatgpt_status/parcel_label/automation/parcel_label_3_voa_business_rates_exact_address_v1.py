#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, html, http.cookiejar, json, pathlib, re, tempfile
import urllib.parse, urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from typing import Any

INPUT=pathlib.Path("docs/chatgpt_status/_shared/slots_21/parcel_label_3/mdu_status_official_result_latest.json")
MANIFEST=pathlib.Path("docs/chatgpt_status/_shared/slots_21/parcel_label_3/evidence/voa_business_rates_exact_address_source_manifest_20260804.json")
OUTPUTS=[pathlib.Path("docs/chatgpt_status/_shared/slots_21/parcel_label_3/voa_business_rates_exact_address_result_latest.json"),pathlib.Path("england_map_web/data/aays_21_slots/parcel_label_3/voa_business_rates_exact_address_latest.json")]
SEARCH_URL="https://www.tax.service.gov.uk/business-rates-find/search"
ALLOWED_HOST="www.tax.service.gov.uk"; MAX_RESPONSE_BYTES=8*1024*1024; MAX_REQUESTS=6
MONEY_RE=re.compile(r"£\s*([0-9][0-9,]*)")

def now(): return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")
def sha(data:bytes): return hashlib.sha256(data).hexdigest()
def norm(v:str): return re.sub(r"[^A-Z0-9]","",html.unescape(v).upper())
def cjson(v): return json.dumps(v,ensure_ascii=False,separators=(",",":"),sort_keys=True)
def safe(url):
    p=urllib.parse.urlsplit(url)
    if p.scheme!="https" or (p.hostname or "").casefold()!=ALLOWED_HOST or p.username or p.password or p.fragment: raise RuntimeError(f"UNSAFE_URL:{url}")
    return url
def atomic(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile("w",encoding="utf-8",dir=path.parent,delete=False) as h: h.write(text); t=pathlib.Path(h.name)
    t.replace(path)

class FormParser(HTMLParser):
    def __init__(self): super().__init__(convert_charrefs=True); self.forms=[]; self.cur=None
    def handle_starttag(self,tag,attrs):
        v={k.casefold():(x or "") for k,x in attrs}; low=tag.casefold()
        if low=="form": self.cur={"action":v.get("action",""),"method":v.get("method","get").casefold(),"inputs":[]}
        elif self.cur is not None and low in {"input","button","select"}: self.cur["inputs"].append({"tag":low,**v})
    def handle_endtag(self,tag):
        if tag.casefold()=="form" and self.cur is not None: self.forms.append(self.cur); self.cur=None

class RowParser(HTMLParser):
    def __init__(self): super().__init__(convert_charrefs=True); self.rows=[]; self.inrow=False; self.depth=0; self.parts=[]; self.cells=[]
    def handle_starttag(self,tag,attrs):
        low=tag.casefold()
        if low in {"tr","li"} and not self.inrow: self.inrow=True; self.cells=[]
        elif self.inrow and low in {"td","th","p","span","a","div"}: self.depth+=1; self.parts=[] if self.depth==1 else self.parts
        elif self.depth and low=="br": self.parts.append(" ")
    def handle_data(self,data):
        if self.depth: self.parts.append(data)
    def handle_endtag(self,tag):
        low=tag.casefold()
        if self.inrow and low in {"td","th","p","span","a","div"} and self.depth:
            self.depth-=1
            if self.depth==0:
                text=" ".join(" ".join(self.parts).split())
                if text: self.cells.append(text)
                self.parts=[]
        elif self.inrow and low in {"tr","li"}:
            if self.cells: self.rows.append(self.cells)
            self.inrow=False; self.depth=0; self.parts=[]; self.cells=[]

def load_rows():
    m=json.loads(MANIFEST.read_text()); p=json.loads(INPUT.read_text()); targets=set(m["target_uprns"])
    if m.get("search_url")!=SEARCH_URL or len(m.get("sources",[]))<4: raise RuntimeError("BAD_MANIFEST")
    for s in m["sources"]:
        if sha(s["retained_excerpt"].encode())!=s["retained_excerpt_sha256"]: raise RuntimeError("MANIFEST_SHA")
    recs=p.get("records",[])
    if len(recs)!=3: raise RuntimeError("EXPECTED_3")
    out=[]
    for r in recs:
        req=("parcel_id","UPRN","FULLADDRESS","POSTCODE","longitude","latitude")
        if not r.get("exact_uprn_bound") or any(k not in r for k in req): raise RuntimeError("BAD_INPUT")
        x={k:r[k] for k in req}; x["UPRN"]=str(x["UPRN"]); x["exact_uprn_bound"]=True; x["POSTCODE"]=" ".join(str(x["POSTCODE"]).upper().split()); x["_norm"]=norm(str(x["FULLADDRESS"]))
        if x["UPRN"] not in targets: raise RuntimeError("UPRN_NOT_TARGET")
        out.append(x)
    return out

def read_response(resp):
    b=bytearray()
    while True:
        chunk=resp.read(min(1024*1024,MAX_RESPONSE_BYTES-len(b)+1))
        if not chunk: break
        b.extend(chunk)
        if len(b)>MAX_RESPONSE_BYTES: raise RuntimeError("RESPONSE_TOO_LARGE")
    return bytes(b)

def choose_form(body):
    p=FormParser(); p.feed(body.decode(errors="replace")); ranked=[]
    for f in p.forms:
        names=" ".join(i.get("name","") for i in f["inputs"]).casefold()
        ranked.append(((5 if "postcode" in names else 0)+(2 if "search" in names else 0),f))
    if not ranked or max(x[0] for x in ranked)<=0: raise RuntimeError("POSTCODE_FORM_NOT_FOUND")
    return sorted(ranked,key=lambda x:x[0],reverse=True)[0][1]

def form_data(form,postcode):
    d={}; pc=[]
    for i in form["inputs"]:
        name=i.get("name",""); typ=i.get("type","").casefold(); val=i.get("value","")
        if not name: continue
        if typ=="hidden": d[name]=val
        if "postcode" in name.casefold(): pc.append(name)
        if typ=="radio" and "postcode" in (name+" "+val).casefold(): d[name]=val
        if typ=="submit" and name: d.setdefault(name,val)
    if not pc: raise RuntimeError("POSTCODE_FIELD_NOT_FOUND")
    for n in pc: d[n]=postcode
    return d

def search(postcode,timeout):
    jar=http.cookiejar.CookieJar(); op=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    req=urllib.request.Request(SEARCH_URL,headers={"User-Agent":"AAYS-parcel-label-3/1.0","Accept":"text/html"})
    with op.open(req,timeout=timeout) as r: geturl=safe(r.geturl()); getbody=read_response(r); getstatus=int(getattr(r,"status",200))
    form=choose_form(getbody); action=safe(urllib.parse.urljoin(geturl,form.get("action") or geturl)); data=form_data(form,postcode); method=(form.get("method") or "get").casefold()
    if method=="get": req=urllib.request.Request(action+"?"+urllib.parse.urlencode(data),headers={"User-Agent":"AAYS-parcel-label-3/1.0","Accept":"text/html"})
    else: req=urllib.request.Request(action,data=urllib.parse.urlencode(data).encode(),method="POST",headers={"User-Agent":"AAYS-parcel-label-3/1.0","Accept":"text/html","Content-Type":"application/x-www-form-urlencoded","Referer":geturl})
    with op.open(req,timeout=timeout) as r: final=safe(r.geturl()); body=read_response(r); status=int(getattr(r,"status",200))
    return body,{"postcode":postcode,"get_url":geturl,"get_status":getstatus,"get_sha256":sha(getbody),"form_method":method,"form_action":action,"submitted_fields":sorted(data),"cookie_count":len(jar),"result_url":final,"result_status":status,"result_sha256":sha(body),"state":"RESPONSE"}

def candidates(body,row):
    p=RowParser(); p.feed(body.decode(errors="replace")); out=[]
    for idx,cells in enumerate(p.rows,1):
        joined=" | ".join(cells)
        if row["_norm"] not in norm(joined): continue
        out.append({"row_index":idx,"official_row_text":joined,"official_row_sha256":sha(joined.encode()),"rateable_value_texts":["£"+x for x in sorted(set(MONEY_RE.findall(joined)))]})
    return out

def synthetic_html(row,rv,duplicate=False):
    rows=[f"<tr><td>{html.escape(str(row['FULLADDRESS']))}</td><td>Shop and premises</td><td>£{rv:,}</td></tr>"]
    if duplicate: rows.append(f"<tr><td>{html.escape(str(row['FULLADDRESS']))}</td><td>Office</td><td>£{rv+1000:,}</td></tr>")
    return ("<html><table>"+"".join(rows)+"</table></html>").encode()

def run(rows,timeout,synthetic=False,ambiguous=False):
    ev={"accessed_at":now(),"search_url":SEARCH_URL,"request_count":0,"requests":[]}; records=[]; matched=0
    for i,row in enumerate(rows):
        try:
            if synthetic: body=synthetic_html(row,12000+i*1000,ambiguous and i==1); e={"postcode":row["POSTCODE"],"result_url":SEARCH_URL,"result_status":200,"result_sha256":sha(body),"state":"SYNTHETIC_RESPONSE"}
            else: ev["request_count"]+=2; body,e=search(row["POSTCODE"],timeout)
            cs=candidates(body,row); ev["requests"].append({**e,"UPRN":row["UPRN"],"exact_address_candidate_count":len(cs)})
            o={**{k:v for k,v in row.items() if k!="_norm"},"source_url":e.get("result_url",SEARCH_URL),"candidate_count":len(cs),"inferred":False}
            if len(cs)==1: o.update({"state":"MATCHED_UNIQUE_VOA_NON_DOMESTIC_RATING_LIST_EXACT_ADDRESS","official_non_domestic_rating_list_presence":True,**cs[0]}); matched+=1
            elif len(cs)>1: o.update({"state":"NO_DATA","reason":"AMBIGUOUS_MULTIPLE_EXACT_ADDRESS_RATING_LIST_ROWS","candidate_row_sha256":[c["official_row_sha256"] for c in cs]})
            else: o.update({"state":"NO_DATA","reason":"NO_EXACT_ADDRESS_NON_DOMESTIC_RATING_LIST_ROW"})
        except Exception as exc:
            error=f"{type(exc).__name__}:{exc}"; ev["requests"].append({"UPRN":row["UPRN"],"postcode":row["POSTCODE"],"state":"ERROR","error":error})
            o={**{k:v for k,v in row.items() if k!="_norm"},"source_url":SEARCH_URL,"candidate_count":0,"state":"NO_DATA","reason":error,"inferred":False}
        records.append(o)
    return ev,records,matched

def main():
    p=argparse.ArgumentParser(); p.add_argument("--timeout",type=int,default=20); p.add_argument("--validate-only",action="store_true"); p.add_argument("--synthetic-test",action="store_true"); p.add_argument("--synthetic-ambiguous-test",action="store_true"); a=p.parse_args()
    if not 1<=a.timeout<=300: raise RuntimeError("INVALID_TIMEOUT")
    rows=load_rows()
    if a.validate_only:
        print(json.dumps({"valid":True,"input_count":3,"target_uprns":[r["UPRN"] for r in rows],"resource_class":"network","request_limit":MAX_REQUESTS,"max_response_bytes":MAX_RESPONSE_BYTES,"write_paths":[str(x) for x in OUTPUTS]},sort_keys=True)); return 0
    syn=a.synthetic_test or a.synthetic_ambiguous_test; ev,recs,matched=run(rows,a.timeout,syn,a.synthetic_ambiguous_test)
    if a.synthetic_test:
        if matched!=3: raise RuntimeError("SYNTHETIC_UNIQUE_FAILED")
        print(json.dumps({"valid":True,"matched_rows":matched},sort_keys=True)); return 0
    if a.synthetic_ambiguous_test:
        if matched!=2 or recs[1].get("reason")!="AMBIGUOUS_MULTIPLE_EXACT_ADDRESS_RATING_LIST_ROWS": raise RuntimeError("SYNTHETIC_AMBIGUOUS_FAILED")
        print(json.dumps({"valid":True,"matched_rows":matched,"ambiguous_state":recs[1]["state"]},sort_keys=True)); return 0
    state="PUBLISHED" if matched else "NO_DATA_CONTINUE"
    result={"schema_version":1,"workstream_id":"AAYS_21_SLOT_SAFE_PARALLEL_V1","slot_id":"parcel_label_3","task_id":"parcel-label-3-voa-business-rates-exact-address-v1-20260804","state":state,"panel_status":"PUBLISHED","completed_count":len(recs),"target_count":3,"previous_percent":0.0,"progress_percent":round(len(recs)/3*100,6),"percent_increase":round(len(recs)/3*100,6),"matched_unique_exact_address_rows":matched,"evidence_records":len(recs),"source_evidence":ev,"records":recs,"restricted_licence_scope":"NDR_PURPOSE_ONLY","bulk_data_retained":False,"fake_data":False,"generated_at":now()}
    text=cjson(result)+"\n"
    for x in OUTPUTS: atomic(x,text)
    print(json.dumps({"completed_count":len(recs),"target_count":3,"matched_unique_exact_address_rows":matched,"state":state,"output_sha256":sha(text.encode())},sort_keys=True)); return 0
if __name__=="__main__": raise SystemExit(main())
