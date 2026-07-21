#!/usr/bin/env python3
"""Fail-closed validator for Planning Data coordinate-query outputs."""
from __future__ import annotations
import argparse,json,math
from pathlib import Path
from shapely import wkt
from shapely.geometry import Point
ALLOWED={"brownfield-land","conservation-area","listed-building","green-belt","flood-risk-zone","article-4-direction-area","tree-preservation-zone"}
class ContractError(RuntimeError): pass
def validate(manifest_path:Path,response_dir:Path)->dict:
 m=json.loads(manifest_path.read_text(encoding="utf-8")); out=[]; total_entities=0
 rows=m.get("rows",[])
 if len(rows)!=19 or len({x.get("row_no") for x in rows})!=19: raise ContractError("manifest must contain 19 unique rows")
 for row in rows:
  rn=row["row_no"]; p=Point(float(row["longitude"]),float(row["latitude"])); path=response_dir/f"row_{rn:05d}.json"
  if not path.exists(): raise ContractError(f"row {rn}: response missing")
  payload=json.loads(path.read_text(encoding="utf-8")); entities=payload.get("entities")
  if not isinstance(entities,list): raise ContractError(f"row {rn}: entities must be list")
  if len(entities)>100: raise ContractError(f"row {rn}: limit exceeded")
  ids=set(); checked=[]
  for e in entities:
   eid=e.get("entity"); ds=e.get("dataset")
   if not isinstance(eid,int) or eid in ids: raise ContractError(f"row {rn}: duplicate/invalid entity")
   ids.add(eid)
   if ds not in ALLOWED: raise ContractError(f"row {rn}: unexpected dataset {ds}")
   if e.get("end-date") not in (None,""): raise ContractError(f"row {rn}: historical entity returned under current contract")
   geom=e.get("geometry")
   if not isinstance(geom,str) or not geom.strip(): raise ContractError(f"row {rn}: geometry missing")
   try: shape=wkt.loads(geom)
   except Exception as exc: raise ContractError(f"row {rn}: invalid WKT") from exc
   if not shape.covers(p): raise ContractError(f"row {rn}: geometry does not cover query point")
   checked.append({'entity':eid,'dataset':ds,'reference':e.get('reference'),'point_covered':True,'promotion_eligible':False,'score':None})
  total_entities+=len(checked)
  out.append({'row_no':rn,'entities':checked,'entity_count':len(checked),'zero_result_semantics':'NO_DATA_COVERAGE_NOT_PROOF' if not checked else None,'promotion_eligible':False,'score':None})
 return {'schema_version':1,'slot_id':'future_growth_1','result':'PASS','rows_validated':19,'entities_validated':total_entities,'rows':out,'polygon_relation_claimed':False,'scores_emitted':0,'final_ready':False}
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('manifest',type=Path); ap.add_argument('response_dir',type=Path); ap.add_argument('output',type=Path); a=ap.parse_args()
 try:r=validate(a.manifest,a.response_dir)
 except ContractError as e: print(json.dumps({'result':'BLOCKED','error':str(e)})); return 2
 a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(r,indent=2)+'\n'); print(json.dumps({'result':'PASS','rows':19,'entities':r['entities_validated']})); return 0
if __name__=='__main__': raise SystemExit(main())
