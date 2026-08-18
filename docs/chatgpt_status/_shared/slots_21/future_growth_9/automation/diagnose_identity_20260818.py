#!/usr/bin/env python3
import json
from collections import defaultdict
from pathlib import Path

REPO = Path.cwd() / 'canonical'
ROOT = REPO / 'AAYS/england_map_web/data/future_growth/shards'
BATCH = ROOT / 'future_growth_9_batches'
LATEST = ROOT / 'future_growth_9_latest.geojson'
records=[]
paths=list(BATCH.glob('**/*.geojson'))+[LATEST]
for p in sorted(paths):
    try: obj=json.loads(p.read_text(encoding='utf-8'))
    except Exception as e:
        print(json.dumps({'parse_error':str(p.relative_to(REPO)),'error':repr(e)})); continue
    for i,f in enumerate(obj.get('features',[])):
        pr=f.get('properties') or {}
        records.append({'path':str(p.relative_to(REPO)),'index':i,'feature_id':f.get('id'),'ref':pr.get('source_feature_id'),'entity':pr.get('planning_data_entity'),'slot':pr.get('slot_id')})
by_ref=defaultdict(list); by_ent=defaultdict(list); by_pair=defaultdict(list)
for r in records:
    if r['ref'] not in (None,''): by_ref[str(r['ref'])].append(r)
    if r['entity'] not in (None,''): by_ent[str(r['entity'])].append(r)
    by_pair[(str(r['ref']),str(r['entity']))].append(r)
out={
 'record_count':len(records),
 'unique_refs':len(by_ref),
 'unique_entities':len(by_ent),
 'unique_pairs':len(by_pair),
 'missing_ref':[r for r in records if r['ref'] in (None,'')],
 'missing_entity':[r for r in records if r['entity'] in (None,'')],
 'duplicate_refs':{k:v for k,v in by_ref.items() if len(v)>1},
 'duplicate_entities':{k:v for k,v in by_ent.items() if len(v)>1},
 'duplicate_pairs':{f'{k[0]}|{k[1]}':v for k,v in by_pair.items() if len(v)>1},
}
print('FG9_IDENTITY_DIAGNOSTIC='+json.dumps(out,ensure_ascii=False,sort_keys=True))
