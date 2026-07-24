#!/usr/bin/env python3
"""Exact-feature polygon popup acceptance for a validated internet_access_3 runtime sample.

No nearest feature, manual coordinate, synthetic parcel or score fallback is permitted.
The browser step supports Leaflet and MapLibre-style global map objects and fails closed.
"""
from __future__ import annotations
import argparse, hashlib, json, os, re, tempfile
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

SLOT_ID="internet_access_3"; ROW_START=61523; ROW_END=92283; EXPECTED_ROWS=30761
PASS_DISCOVERY="PASS_UNIQUE_MAIN_MAP_POPUP_CONTRACT_DISCOVERED"
PASS_RUNTIME="REAL_RUNTIME_BUNDLE_VALIDATED_REVIEW_ONLY"
NO_DATA_STATUSES={"IDENTITY_CONFLICT_NO_DATA","POSTCODE_NOT_FOUND_IN_CURRENT_R2_NO_DATA","NO_VERIFIED_POSTCODE_NO_DATA"}

class GateError(RuntimeError): pass

def require(value: bool, message: str)->None:
    if not value: raise GateError(message)

def load_json(path: Path)->dict[str,Any]:
    require(path.is_file() and path.stat().st_size>0,f"missing {path}")
    value=json.loads(path.read_text(encoding='utf-8'));require(isinstance(value,dict),'object required');return value

def validate_runtime(value: dict[str,Any])->dict[str,Any]:
    require(value.get('slot_id')==SLOT_ID,'wrong slot')
    require(value.get('status')==PASS_RUNTIME,'runtime not validated')
    require(value.get('real_runtime_rows_validated')==EXPECTED_ROWS,'runtime row count')
    part=value.get('row_partition') or {};require((part.get('start'),part.get('end'),part.get('rows'))==(ROW_START,ROW_END,EXPECTED_ROWS),'partition mismatch')
    samples=value.get('samples');require(isinstance(samples,list) and 1<=len(samples)<=8,'real samples required')
    clean=[]
    for sample in samples:
        require(isinstance(sample,dict),'sample object')
        row=int(sample.get('canonical_row_no'));parcel=str(sample.get('canonical_program_parcel_id') or '')
        require(ROW_START<=row<=ROW_END and parcel==f'parcel_{row}','sample identity')
        require(sample.get('business_row_written') is False,'business write forbidden')
        require(sample.get('internet_availability_quality_percent') is None,'parcel score forbidden')
        clean.append(sample)
    clean.sort(key=lambda s:(s.get('status')!='CURRENT_R2_POSTCODE_PROXY_READY_FOR_REVIEW',int(s['canonical_row_no'])))
    return clean[0]

def validate_discovery(value: dict[str,Any])->dict[str,Any]:
    require(value.get('slot_id')==SLOT_ID,'discovery slot')
    require(value.get('state')==PASS_DISCOVERY,'discovery not unique')
    selected=value.get('selected');require(isinstance(selected,dict),'selected bundle')
    html=str(selected.get('html_path') or '')
    require(html.startswith('england_map_web/') and html.endswith(('.html','.htm')),'tracked map HTML required')
    require(selected.get('engine') in {'leaflet','maplibre','leaflet_or_maplibre'},'unsupported engine')
    require(selected.get('popup_evidence') is True and selected.get('internet_evidence') is True and selected.get('identity_evidence') is True,'evidence missing')
    require(value.get('nearest_feature_fallback_allowed') is False,'nearest fallback forbidden')
    require(value.get('manual_coordinate_fallback_allowed') is False,'manual coordinate forbidden')
    return selected

def popup_requirements(sample: dict[str,Any])->dict[str,Any]:
    status=str(sample.get('status') or '')
    parcel=str(sample['canonical_program_parcel_id']);row=str(sample['canonical_row_no'])
    postcode=str(sample.get('postcode') or '').strip()
    if status=='CURRENT_R2_POSTCODE_PROXY_READY_FOR_REVIEW':
        require(bool(postcode),'proxy sample requires postcode')
        semantic=[postcode,'postcode','broadband','internet','availability','fibre']
    elif status in NO_DATA_STATUSES:
        semantic=['no_data','no data','veri yok','postcode bulunamadı','kimlik çakışması','internet']
    else: raise GateError('unsupported runtime status')
    return {'parcel':parcel,'row':row,'status':status,'postcode':postcode or None,'semantic_any':semantic}

def validate_popup_text(text: str, requirements: dict[str,Any])->dict[str,bool]:
    norm=' '.join(text.casefold().split())
    parcel=requirements['parcel'].casefold();row=requirements['row'].casefold();status=requirements['status'].casefold()
    identity=(parcel in norm) or bool(re.search(rf'(?<!\d){re.escape(row)}(?!\d)',norm))
    status_exact=status in norm
    semantic=any(token.casefold() in norm for token in requirements['semantic_any'])
    postcode=True
    if requirements['postcode']:
        postcode=requirements['postcode'].casefold() in norm
    return {'identity_exact':identity,'status_exact':status_exact,'internet_semantics':semantic,'postcode_exact_when_required':postcode,'pass':identity and semantic and postcode}

BROWSER_JS=r"""
async ({parcelId,rowNo}) => {
 const exact=p=>p&&(String(p.parcel_id??p.program_parcel_id??p.canonical_program_parcel_id??'')===parcelId||Number(p.row_no??p.canonical_row_no)===rowNo);
 const values=[]; for(const name of Object.getOwnPropertyNames(window)){try{values.push([name,window[name]])}catch(e){}}
 const leaf=[];
 const walk=(layer,owner)=>{try{if(layer&&layer.feature&&exact(layer.feature.properties||{}))leaf.push({layer,owner,properties:layer.feature.properties||{}});if(layer&&typeof layer.eachLayer==='function')layer.eachLayer(ch=>walk(ch,owner||layer));}catch(e){}};
 for(const [name,v] of values){try{if(v&&typeof v.eachLayer==='function'&&typeof v.getCenter==='function')v.eachLayer(l=>walk(l,v));}catch(e){}}
 if(leaf.length===1){const hit=leaf[0];if(typeof hit.layer.openPopup==='function')hit.layer.openPopup();else if(typeof hit.layer.fire==='function')hit.layer.fire('click');else if(hit.owner&&typeof hit.owner.fire==='function')hit.owner.fire('click',{layer:hit.layer});return {engine:'leaflet',matchCount:1,properties:hit.properties};}
 const maps=[]; for(const [name,v] of values){try{if(v&&typeof v.getStyle==='function'&&typeof v.querySourceFeatures==='function'&&typeof v.project==='function')maps.push([name,v]);}catch(e){}}
 const found=[];
 const coords=g=>{const out=[];const walkc=x=>{if(Array.isArray(x)&&x.length>=2&&typeof x[0]==='number'&&typeof x[1]==='number')out.push(x);else if(Array.isArray(x))x.forEach(walkc)};if(g)walkc(g.coordinates);return out};
 for(const [name,map] of maps){const style=map.getStyle()||{};for(const sid of Object.keys(style.sources||{})){let feats=[];try{feats=map.querySourceFeatures(sid)||[]}catch(e){}for(const f of feats){if(exact(f.properties||{})){const cs=coords(f.geometry);if(cs.length)found.push({name,map,sid,feature:f,center:[cs.reduce((a,c)=>a+c[0],0)/cs.length,cs.reduce((a,c)=>a+c[1],0)/cs.length]});}}}}
 if(found.length===1){const h=found[0];h.map.jumpTo({center:h.center,zoom:Math.max(Number(h.map.getZoom?.()||0),16)});await new Promise(r=>setTimeout(r,500));const point=h.map.project(h.center);let rendered=[];try{rendered=h.map.queryRenderedFeatures(point)||[]}catch(e){}const exactRendered=rendered.filter(f=>exact(f.properties||{}));const feature=exactRendered[0]||h.feature;try{h.map.fire('click',{point,lngLat:h.map.unproject(point),features:[feature]})}catch(e){}return {engine:'maplibre',matchCount:1,properties:feature.properties||{}};}
 return {engine:null,matchCount:leaf.length+found.length};
}
"""

def atomic(path:Path,value:dict[str,Any])->None:
    path.parent.mkdir(parents=True,exist_ok=True);fd,tmp=tempfile.mkstemp(prefix=path.name+'.',suffix='.tmp',dir=str(path.parent))
    try:
        with os.fdopen(fd,'w',encoding='utf-8',newline='\n') as h:json.dump(value,h,ensure_ascii=False,indent=2);h.write('\n');h.flush();os.fsync(h.fileno())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)

def main()->int:
    ap=argparse.ArgumentParser();ap.add_argument('--runtime-results',type=Path,required=True);ap.add_argument('--discovery',type=Path,required=True);ap.add_argument('--base-url',default='http://127.0.0.1:8012/');ap.add_argument('--output',type=Path,required=True);ap.add_argument('--timeout-ms',type=int,default=30000);a=ap.parse_args()
    runtime=load_json(a.runtime_results);sample=validate_runtime(runtime);selected=validate_discovery(load_json(a.discovery));requirements=popup_requirements(sample)
    url=urljoin(a.base_url.rstrip('/')+'/',selected['html_path'])
    receipt={'schema_version':1,'slot_id':SLOT_ID,'status':'FAILED','map_url':url,'selected_html_path':selected['html_path'],'declared_engine':selected['engine'],'sample':sample,'requirements':requirements,'nearest_feature_fallback_used':False,'manual_coordinate_fallback_used':False,'exact_feature_match_count':0,'polygon_popup_acceptance':False,'actual_business_data_rows_written':0,'fake_data':False,'db_write':False,'migration':False,'production_deploy':False,'final_ready':False}
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser=p.chromium.launch(headless=True);page=browser.new_page();errors=[]
            page.on('console',lambda msg: errors.append(f'console:{msg.type}:{msg.text}') if msg.type=='error' else None);page.on('pageerror',lambda err:errors.append(f'page:{err}'))
            response=page.goto(url,wait_until='networkidle',timeout=a.timeout_ms);require(response is not None and response.ok,'map HTTP not OK')
            result=page.evaluate(BROWSER_JS,{'parcelId':requirements['parcel'],'rowNo':int(requirements['row'])});receipt['engine_detected']=result.get('engine');receipt['exact_feature_match_count']=result.get('matchCount',0);require(receipt['exact_feature_match_count']==1,'exact feature count must be one')
            selector='.leaflet-popup-content,.maplibregl-popup-content,[data-popup-content],[role="dialog"]';page.wait_for_selector(selector,state='visible',timeout=a.timeout_ms);popup=page.locator(selector).filter(visible=True).first.inner_text();checks=validate_popup_text(popup,requirements);require(checks['pass'],'popup text contract failed');require(not errors,'browser errors')
            receipt.update({'status':'PASS_EXACT_POLYGON_POPUP_ACCEPTANCE','popup_selector':selector,'popup_text_sha256':hashlib.sha256(popup.encode('utf-8')).hexdigest(),'checks':checks,'browser_errors':errors,'polygon_popup_acceptance':True});browser.close()
    except Exception as exc:
        receipt['error']=str(exc);atomic(a.output,receipt);print(json.dumps({'status':receipt['status'],'error':receipt['error']},sort_keys=True));return 2
    atomic(a.output,receipt);print(json.dumps({'status':receipt['status'],'map_url':url,'parcel':requirements['parcel']},sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
