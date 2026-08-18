#!/usr/bin/env python3
import hashlib, urllib.request
from datetime import datetime, timezone
import aays_fg7_regional_331_342_20260819 as m

WM="https://nationalhighways.co.uk/roads-and-travel/road-projects/west-midlands/west-midlands-maintenance-schemes/"
m.SOURCES={"em":WM,"se":WM}
m.FAMILY="National Highways official West Midlands A46 maintenance entries - unused window set 30"
m.BATCHES=[
 (331,"em","national_highways_west_midlands_maintenance:a46_guys_cliffe_sb_20260508","A46 Guys Cliffe southbound Kenilworth to Leek Wootton - 8 May 2026","verified 2026 maintenance window",["Friday 8 May 2026","A46 southbound closed between Kenilworth and Leek Wootton","8pm to 5am"]),
 (332,"em","national_highways_west_midlands_maintenance:a46_guys_cliffe_sb_slips_20260509_11","A46 Guys Cliffe southbound Leek Wootton slips - 9 to 11 May 2026","verified 2026 maintenance window",["Saturday 9 May 2026","Monday 11 May 2026","A46 southbound closed between the exit and entry slip at Leek Wootton"]),
 (333,"em","national_highways_west_midlands_maintenance:a46_guys_cliffe_sb_slips_20260512_14","A46 Guys Cliffe southbound Leek Wootton slips - 12 to 14 May 2026","verified 2026 maintenance window",["Tuesday 12 May 2026","Thursday 14 May 2026","A46 southbound closed between the exit and entry slip at Leek Wootton"]),
 (334,"em","national_highways_west_midlands_maintenance:a46_guys_cliffe_nb_slips_20260511_12","A46 Guys Cliffe northbound Leek Wootton slips - 11 to 12 May 2026","verified 2026 maintenance window",["Monday 11 May 2026","Tuesday 12 May 2026","A46 northbound closed between the exit and entry slip at Leek Wootton"]),
 (335,"em","national_highways_west_midlands_maintenance:a46_guys_cliffe_nb_slips_20260515_18","A46 Guys Cliffe northbound Leek Wootton slips - 15 to 18 May 2026","verified 2026 maintenance window",["Friday 15 May 2026","Monday 18 May 2026","A46 northbound closed between the exit and entry slip at Leek Wootton"]),
 (336,"em","national_highways_west_midlands_maintenance:a46_guys_cliffe_nb_slips_20260518_20","A46 Guys Cliffe northbound Leek Wootton slips - 18 to 20 May 2026","verified 2026 maintenance window",["Monday 18 May 2026","Wednesday 20 May 2026","A46 northbound closed between the exit and entry slip at Leek Wootton"]),
 (337,"em","national_highways_west_midlands_maintenance:a46_tollbar_binley_nb_lane_20260427_20260506","A46 Tollbar End to Binley northbound lane closure - 27 April to 6 May 2026","verified 2026 maintenance window",["Monday 27 April","Wednesday 6 May","A46 northbound Tollbar End roundabout to Binley roundabout","Lane closure on A46 northbound carriageway and exit slip"]),
 (338,"em","national_highways_west_midlands_maintenance:a46_binley_tollbar_sb_lane_20260506_19","A46 Binley to Tollbar End southbound lane closure - 6 to 19 May 2026","verified 2026 maintenance window",["Wednesday 6 to Tuesday 19 May","A46 southbound Binley roundabout to Tollbar End roundabout","Lane closure on A46 southbound carriageway and exit slip"]),
 (339,"em","national_highways_west_midlands_maintenance:a46_tollbar_m6_central_lane2_20260519_20260611","A46 Tollbar End to M6 junction 2 central reservation lane 2 closure - 19 May to 11 June 2026","verified 2026 maintenance window",["Tuesday 19 May to Thursday 11 June","central reservation between Tollbar End and M6 junction 2","A46 north and southbound lane 2 closure"]),
 (340,"em","national_highways_west_midlands_maintenance:a46_tollbar_binley_nb_full_20260611_26","A46 Tollbar End to Binley northbound full closure - 11 to 26 June 2026","verified 2026 maintenance window",["Thursday 11 to Friday 26 June","Total closure of A46 northbound between Tollbar End roundabout and Binley roundabout","Oak Tree Road","Binley Wood exit slip"]),
 (341,"em","national_highways_west_midlands_maintenance:a46_binley_tollbar_sb_full_20260629_20260708","A46 Binley to Tollbar End southbound full closure - 29 June to 8 July 2026","verified 2026 maintenance window",["Monday 29 June to Wednesday 8 July","Total closure of A46 southbound between Binley roundabout and Tollbar End roundabout","Binley Woods entry slip and services"]),
 (342,"em","national_highways_west_midlands_maintenance:a46_tollbar_sb_full_20260708_17","A46 Tollbar End southbound full closure - 8 to 17 July 2026","verified 2026 maintenance window",["Wednesday 8 to Friday 17 July","Total closure A46 southbound at Tollbar End roundabout","Tollbar End entry slip"]),
]

def fetch_source(code):
    req=urllib.request.Request(WM,headers={"User-Agent":"Mozilla/5.0 AAYS-FG7-West-Midlands/2026-08-18","Accept":"text/html,application/xhtml+xml"})
    with urllib.request.urlopen(req,timeout=60) as r:
        raw=r.read(); final=r.geturl(); status=getattr(r,"status",200)
    if status!=200: raise RuntimeError(f"WM_SOURCE_HTTP:{status}")
    if "/west-midlands/" not in final: raise RuntimeError(f"WM_SOURCE_URL:{final}")
    txt=m.norm(raw.decode("utf-8","replace"))
    for b,c,k,n,s,toks in m.BATCHES:
        for tok in toks:
            if m.norm(tok) not in txt:
                raise RuntimeError(f"WM_SOURCE_TOKEN_MISSING:{b}:{tok!r}:BYTES={len(raw)}:FINAL={final}")
    return {"url":WM,"final_url":final,"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw),"accessed_at":datetime.now(timezone.utc).isoformat().replace("+00:00","Z")}

def entry(w,src):
    b,c,k,n,s,t=w
    return {"batch":b,"window_key":k,"project_name":n,"project_stage":s,"source_ref":WM,"source_fetch_ok":True,"source_http_status":200,"source_final_url":src["final_url"],"source_sha256_runtime":src["sha256"],"source_bytes_runtime":src["bytes"],"source_accessed_at":src["accessed_at"],"source_verification":"official_national_highways_west_midlands_runtime_verified_2026-08-18","result":"ZERO_SAFE_CANONICAL_MATCHES","new_unique_evidenced_parcels":0,"reason":"Official National Highways West Midlands A46 maintenance window verified. No jointly readable machine-readable official works/project polygon plus canonical parcel polygon pair is available to prove strict centroid-within-polygon or exact intersection; no inferred polygon, proximity, nearest match, or fake data used.","reason_code":"STRICT_SPATIAL_JOIN_INPUT_PAIR_UNAVAILABLE"}

m.fetch_source=fetch_source
m.entry=entry

if __name__=="__main__":
    m.main()
