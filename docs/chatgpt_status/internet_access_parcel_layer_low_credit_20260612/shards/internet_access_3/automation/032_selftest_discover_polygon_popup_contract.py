#!/usr/bin/env python3
from __future__ import annotations
import importlib.util
from pathlib import Path
from typing import Any, Callable
ROOT=Path(__file__).parent

def load()->Any:
    spec=importlib.util.spec_from_file_location("d031",ROOT/"031_discover_polygon_popup_contract.py")
    assert spec and spec.loader
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod

def expect(value: bool, name: str, out: list[str])->None:
    assert value,name;out.append(name)

def main()->int:
    m=load(); out=[]
    leaf_html='<script src="app.js"></script>'
    leaf_js='L.map( map ); L.geoJSON(data).bindPopup(x); Internet Availability internet_availability parcel_id row_no internet.geojson'
    r=m.discover_from_files({'england_map_web/index.html':leaf_html,'england_map_web/app.js':leaf_js})
    expect(r['state'].startswith('PASS_'),'unique_leaflet',out);expect(r['selected']['engine']=='leaflet','leaflet_engine',out)
    map_js='new maplibregl.Map({}); queryRenderedFeatures(); querySourceFeatures(); maplibregl-popup-content Internet Availability parcel_id row_no program_layer_matrix/internet'
    r=m.discover_from_files({'england_map_web/map.html':'<script src="map.js"></script>','england_map_web/map.js':map_js})
    expect(r['state'].startswith('PASS_'),'unique_maplibre',out);expect(r['selected']['engine']=='maplibre','maplibre_engine',out)
    r=m.discover_from_files({'england_map_web/sub/index.html':'<script src="../app.js?v=1"></script>','england_map_web/app.js':leaf_js})
    expect(r['selected']['included_paths'][-1]=='england_map_web/app.js','parent_script_resolution',out)
    r=m.discover_from_files({'england_map_web/index.html':'<script src="https://x/app.js"></script>'+leaf_js})
    expect(len(r['selected']['included_paths'])==1,'external_script_ignored',out)
    r=m.discover_from_files({'england_map_web/index.html':'Internet Availability parcel_id row_no'})
    expect(r['state'].startswith('WAITING_'),'no_engine_waits',out)
    r=m.discover_from_files({'england_map_web/index.html':'L.map( x ); bindPopup(x); parcel_id row_no'})
    expect(r['state'].startswith('WAITING_'),'no_internet_waits',out)
    r=m.discover_from_files({'england_map_web/index.html':'L.map( x ); bindPopup(x); Internet Availability'})
    expect(r['state'].startswith('WAITING_'),'no_identity_waits',out)
    r=m.discover_from_files({'england_map_web/a.html':leaf_js,'england_map_web/b.html':leaf_js})
    expect('ambiguous' in r['reason'],'tie_ambiguous',out)
    stronger=leaf_js+' openPopup leaflet-popup-content hmlr_inspire_id'
    r=m.discover_from_files({'england_map_web/a.html':leaf_js,'england_map_web/b.html':stronger})
    expect(r['selected']['html_path'].endswith('b.html'),'highest_score_wins',out)
    r=m.discover_from_files({'england_map_web/app.js':leaf_js})
    expect(r['state'].startswith('WAITING_'),'orphan_js_not_entry',out)
    expect(m._safe_relative(Path('england_map_web').as_posix() if False else __import__('pathlib').PurePosixPath('england_map_web'), '../../x.js') is None,'traversal_rejected',out)
    expect(m._safe_relative(__import__('pathlib').PurePosixPath('england_map_web/sub'),'./a.js')=='england_map_web/sub/a.js','dot_resolution',out)
    expect(m._safe_relative(__import__('pathlib').PurePosixPath('england_map_web'),'data:text/js,x') is None,'data_url_rejected',out)
    expect(m._safe_relative(__import__('pathlib').PurePosixPath('england_map_web'),'//cdn/x.js') is None,'protocol_relative_rejected',out)
    r=m.discover_from_files({'england_map_web/index.htm':leaf_js})
    expect(r['selected']['html_path'].endswith('.htm'),'htm_entry',out)
    expect(len(r['selected']['bundle_sha256'])==64,'bundle_sha',out)
    expect(r['selected']['popup_evidence'] is True,'popup_evidence',out)
    expect(r['selected']['identity_evidence'] is True,'identity_evidence',out)
    print(f"PASS {len(out)}/{len(out)}");return 0
if __name__=='__main__':raise SystemExit(main())
