#!/usr/bin/env python3
import hashlib,html,re,urllib.request
from datetime import datetime, timezone
import aays_fg7_yne_319_330_20260818 as m
m.BATCHES=[
(319,"national_highways_yorkshire_ne_maintenance:a1_berwick_lighting_20260511_20261031","A1 Berwick upon Tweed lighting renewal - 11 May to end of October 2026","current/forward 2026 maintenance window",["A1 Berwick upon Tweed lighting renewal","end of October 2026"]),
(320,"national_highways_yorkshire_ne_maintenance:a1m_lumley_thicks_20260724_20270531","A1(M) Lumley Thicks/Chester-le-Street bridge works - 24 July 2026 to Spring 2027","current/forward bridge works",["Lumley Thicks/Chester-le-Street bridge works","24 July 2026","Spring 2027"]),
(321,"national_highways_yorkshire_ne_maintenance:a19_redhill_bridge_20260505_20261130","A19 southbound Redhill bridge repairs - 5 May to November 2026","current 2026 bridge works",["A19 southbound Redhill bridge repairs","November 2026"]),
(322,"national_highways_yorkshire_ne_maintenance:a628_woodhead_cascade_20260629_20261231","A628 Woodhead Cascade repairs - 29 June to December 2026","current/forward 2026 maintenance window",["A628 Woodhead Cascade repairs","29 June","December 2026"]),
(323,"national_highways_yorkshire_ne_maintenance:a66_elton_yarm_20260801_20270531","A66 Elton to Yarm barriers and streetlights - August 2026 to Spring 2027","current/forward 2026-27 maintenance window",["A66 Elton to Yarm","August 2026 to Spring 2027"]),
(324,"national_highways_yorkshire_ne_maintenance:m1_tinsley_a631_nb_20260914","M1 junction 34 Tinsley Viaduct A631 northbound closure - 14 September 2026","forward 2026 maintenance window",["14 September","A631 northbound lower deck"]),
(325,"national_highways_yorkshire_ne_maintenance:m18_greenland_lane_ongoing_2029","M18 Greenland Lane bridge closure - ongoing 2029","ongoing bridge closure",["M18 Greenland Lane bridge closure","ongoing 2029"]),
(326,"national_highways_yorkshire_ne_maintenance:m62_howden_north_cave_eb_20260810_20260827","M62 Howden to North Cave eastbound lane closures - 10 to 27 August 2026","current 2026 maintenance window",["10 - 27 August","M62 eastbound between junctions 37 and 38"]),
(327,"national_highways_yorkshire_ne_maintenance:m62_j36_airmyn_surveys_20260810_20260818","M62 junction 36 Goole/Airmyn surveys - 10 to 18 August 2026","current/recent 2026 survey window",["10 to 18 August","M62 lanes 2 and 3 closed east and westbound"]),
(328,"national_highways_yorkshire_ne_maintenance:m62_j36_rawcliffe_bridge_20261005_20261009","A614 Rawcliffe Road bridge deck surveys at M62 junction 36 - 5 to 9 October 2026","forward 2026 survey window",["5 to 9 October","A614 Rawcliffe Road bridge deck"]),
(329,"national_highways_yorkshire_ne_maintenance:m62_m621_j27_eb_slips_20260820_20260826","M62/M621 junction 27 eastbound slip closures - 20 to 26 August 2026","forward 2026 maintenance window",["20-26 August","M62 J27 eastbound exit and eastbound entry slip roads"]),
(330,"national_highways_yorkshire_ne_maintenance:m62_m18_links_sb_20260825_20260908","M62 to M18 southbound links and M18 southbound J7-J6 - 25 August to 8 September 2026","forward 2026 maintenance window",["25 August to 8 September","M18 southbound from junctions 7 to 6"])]
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
