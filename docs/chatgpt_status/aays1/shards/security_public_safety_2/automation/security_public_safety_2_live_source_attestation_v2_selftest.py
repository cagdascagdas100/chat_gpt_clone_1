from __future__ import annotations
import copy, hashlib, importlib.util, json, calendar, tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path

HERE=Path(__file__).resolve().parent
def load(name, filename):
    spec=importlib.util.spec_from_file_location(name,HERE/filename)
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module
att=load("attestation","security_public_safety_2_live_source_attestation_v2.py")
repo=Path(tempfile.mkdtemp())
cache=repo/att.CACHE_REL; cache.mkdir(parents=True)
iod=cache/"File_7_IoD2025_All_Ranks_Scores_Deciles_Population_Denominators_v2.csv"
mps=cache/"MPS_LSOA_Level_Crime_latest.csv"
iod.write_text("LSOA Code (2021),Crime Score,Crime Rank (where 1 is most deprived),Crime Decile (where 1 is most deprived 10% of LSOAs)\nE01000001,0.2,10,1\n",encoding="utf-8")
months=[]
for year,start,end in ((2024,7,12),(2025,1,12),(2026,1,6)):
    for month in range(start,end+1): months.append(f"{calendar.month_abbr[month]} {year}")
mps.write_text("LSOA Code (2021),"+",".join(months)+"\nE01000001,"+",".join(["1"]*len(months))+"\n",encoding="utf-8")
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
now=datetime.now(timezone.utc)
prov={"pass":True,"generated_at":(now-timedelta(seconds=10)).isoformat().replace("+00:00","Z"),"contract":{"pass":True},"sources":{
"police_latest":{"parsed":{"latest_date":"2026-05-01"}},
"iod25_page":{"parsed":{"v2_required":True,"files_1_9_corrected":True}},
"mps_page":{"parsed":{"latest_period":"Jul 2024 – Jun 2026","connect_caveat":True}}}}
mps_url="https://data.london.gov.uk/download/MPS%20LSOA%20Level%20Crime.csv"
boot={"pass":True,"generated_at":(now-timedelta(seconds=5)).isoformat().replace("+00:00","Z"),"contract":{"pass":True},"sources":{
"iod25_file7_v2":{"pass":True,"method":"download","path":str(iod),"url":att.IOD25_FILE_URL,"validation":{"sha256":sha(iod),"headers":["LSOA Code (2021)","Crime Score"]},"http":{"sha256":sha(iod),"http_status":200,"final_url":att.IOD25_FILE_URL}},
"mps_lsoa":{"pass":True,"method":"download","path":str(mps),"url":mps_url,"validation":{"sha256":sha(mps),"headers":["LSOA Code (2021)"]+months},"http":{"sha256":sha(mps),"http_status":200,"final_url":mps_url}}},
"mps_discovery":{"pass":True,"selected_url":mps_url}}
cases=[]
def add(name,value):cases.append({"name":name,"pass":bool(value)})
valid=att.validate(repo,prov,boot,now=now)
for name,value in valid["checks"].items(): add("valid_"+name,value)
tests=[
("cached_iod_rejected",("boot","iod25_file7_v2","method","cached_path")),
("cached_mps_rejected",("boot","mps_lsoa","method","cached_path")),
("iod_http_status_rejected",("boot","iod25_file7_v2","http_status",500)),
("mps_http_status_rejected",("boot","mps_lsoa","http_status",500)),
("iod_http_sha_rejected",("boot","iod25_file7_v2","http_sha","0"*64)),
("mps_http_sha_rejected",("boot","mps_lsoa","http_sha","0"*64)),
("mps_selected_url_rejected",("boot","mps_lsoa","selected","https://example.invalid/a.csv")),
("mps_http_url_rejected",("boot","mps_lsoa","url","http://data.london.gov.uk/a.csv")),
("iod_wrong_url_rejected",("boot","iod25_file7_v2","url","https://assets.publishing.service.gov.uk/wrong.csv")),
("police_bad_date_rejected",("prov","police","date","2026-05-02")),
("iod_v2_missing_rejected",("prov","iod","v2",False)),
("iod_correction_missing_rejected",("prov","iod","corrected",False)),
("mps_connect_missing_rejected",("prov","mps","connect",False)),
("mps_period_mismatch_rejected",("prov","mps","period","Jun 2024 – May 2026")),
]
for name,spec in tests:
    p=copy.deepcopy(prov); b=copy.deepcopy(boot)
    kind,source,field,value=spec
    if kind=="boot":
        s=b["sources"][source]
        if field=="method":s["method"]=value
        elif field=="http_status":s["http"]["http_status"]=value
        elif field=="http_sha":s["http"]["sha256"]=value
        elif field=="selected":b["mps_discovery"]["selected_url"]=value
        elif field=="url":
            s["url"]=value
            if source=="mps_lsoa":b["mps_discovery"]["selected_url"]=value
    else:
        if source=="police":p["sources"]["police_latest"]["parsed"]["latest_date"]=value
        elif source=="iod":
            key="v2_required" if field=="v2" else "files_1_9_corrected";p["sources"]["iod25_page"]["parsed"][key]=value
        elif source=="mps":
            key="connect_caveat" if field=="connect" else "latest_period";p["sources"]["mps_page"]["parsed"][key]=value
    add(name,not att.validate(repo,p,b,now=now)["pass"])
stale=copy.deepcopy(boot);stale["generated_at"]=(now-timedelta(seconds=att.MAX_AGE_SECONDS+1)).isoformat().replace("+00:00","Z")
add("stale_bootstrap_rejected",not att.validate(repo,prov,stale,now=now)["pass"])
before=copy.deepcopy(boot);before["generated_at"]=(now-timedelta(seconds=20)).isoformat().replace("+00:00","Z")
add("bootstrap_before_provenance_rejected",not att.validate(repo,prov,before,now=now)["pass"])
payload={"schema_version":1,"slot_id":att.SLOT_ID,"test_type":"LIVE_SOURCE_ATTESTATION_V2_SELFTEST","cases":cases,"passed":sum(x["pass"] for x in cases),"total":len(cases),"pass":all(x["pass"] for x in cases),"actual_business_rows_written":0,"fake_data":False,"final_ready":False}
out=HERE.parent/"validation/security_public_safety_2_live_source_attestation_v2_selftest_latest.json";out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps({"passed":payload["passed"],"total":payload["total"],"pass":payload["pass"]}))
raise SystemExit(0 if payload["pass"] else 1)
