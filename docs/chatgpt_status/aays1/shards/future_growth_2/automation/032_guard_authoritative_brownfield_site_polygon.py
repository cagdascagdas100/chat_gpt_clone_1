#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,re
from pathlib import Path
POLYGON=re.compile(r'^\s*(MULTIPOLYGON|POLYGON)\s*\(',re.I)
def validate_candidate(c):
 s=c.get('authoritative_brownfield_site')
 if not s:return False
 cid=str(c.get('candidate_id') or '')
 if s.get('dataset')!='brownfield-site':raise ValueError(f'{cid}: wrong support dataset')
 if str(s.get('quality') or '').lower()!='authoritative':raise ValueError(f'{cid}: support must be authoritative')
 if str(s.get('reference') or '')!=str(c.get('source_reference') or ''):raise ValueError(f'{cid}: reference mismatch')
 if s.get('end_date') not in (None,''):raise ValueError(f'{cid}: ended support polygon forbidden')
 if not POLYGON.match(str(s.get('geometry_wkt') or '')):raise ValueError(f'{cid}: polygon geometry required')
 if c.get('canonical_row_no') is not None or c.get('canonical_parcel_id') is not None:raise ValueError(f'{cid}: polygon support is not parcel proof')
 if c.get('future_growth_score') is not None or c.get('future_growth_confidence') not in (0,None):raise ValueError(f'{cid}: polygon support cannot authorize score')
 return True
def validate(payload):
 if payload.get('slot_id')!='future_growth_2':raise ValueError('wrong slot_id')
 ids=[c['candidate_id'] for c in payload.get('candidates',[]) if validate_candidate(c)]
 return {'schema_version':1,'slot_id':'future_growth_2','executed':True,'authoritative_reference_polygons':ids,'count':len(ids),'canonical_parcel_matches':0,'future_growth_scores_produced':0,'actual_business_data_rows_written':0,'all_passed':True,'final_ready':False,'fake_data':False,'db_write':False,'migration':False,'production_deploy':False}
def main():
 p=argparse.ArgumentParser();p.add_argument('--wave',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();o=validate(json.loads(a.wave.read_text()));a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(o,indent=2)+'\n');print(json.dumps(o));return 0
if __name__=='__main__':raise SystemExit(main())
