#!/usr/bin/env python3
import hashlib,html,re,urllib.request
from datetime import datetime, timezone
import aays_fg7_yne_319_330_20260818 as m
m.BATCHES[6]=(325,"national_highways_yorkshire_ne_maintenance:a1m_j43_j44_m1_20260620_20260627","M1/A1(M) junction 43-44 widening closures - 20 and 27 June 2026","official 2026 maintenance window",["20 and 27 June","Selby Fork","Bramham"])
m.BATCHES[7]=(326,"national_highways_yorkshire_ne_maintenance:a1m_j43_j44_m1_20260706_20260731","M1/A1(M) junction 43-44 widening closures - 6 to 31 July 2026","recent 2026 maintenance window",["6-31 July 2026","J42","J44"])
def norm(s):
    s=html.unescape(s).replace("–","-").replace("—","-").replace("‑","-")
    s=re.sub(r"<[^>]+>"," ",s)
    return re.sub(r"\s+"," ",s).strip().lower()
def source_verify():
    req=urllib.request.Request(m.SOURCE,headers={"User-Agent":"Mozilla/5.0 AAYS-FG7/2026-08-18"})
    with urllib.request.urlopen(req,timeout=60) as r:
        raw=r.read(); final=r.geturl(); status=getattr(r,"status",200)
    low=norm(raw.decode("utf-8","replace"))
    assert status==200 and "yorkshire-and-north-east-maintenance-schemes" in final
    for b,k,n,s,toks in m.BATCHES:
        for tok in toks: assert norm(tok) in low,(b,tok)
    return hashlib.sha256(raw).hexdigest(),len(raw),datetime.now(timezone.utc).isoformat().replace("+00:00","Z")
m.source_verify=source_verify
if __name__=="__main__":
    m.main()
