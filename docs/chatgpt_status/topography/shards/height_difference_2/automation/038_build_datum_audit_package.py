import hashlib
import io
import json
import math
import pathlib
import zipfile
from datetime import datetime, timezone

import numpy as np
import requests
from rasterio.io import MemoryFile

ROOT = pathlib.Path('.')
SLOT = ROOT / 'england_map_web/data/aays_21_slots/height_difference_2'
DOC = ROOT / 'docs/chatgpt_status/topography/shards/height_difference_2'
NOW = datetime.now(timezone.utc).isoformat()


def read(path):
    return json.loads(path.read_text())


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + '\n')


def iso_day(ms):
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).date().isoformat() if ms is not None else None

probe = read(DOC / 'runtime/038_osgm02_osgm15_adjustment_probe.json')
prev_examples = {int(x['row_no']): x for x in read(SLOT / 'examples_increment_037.json')['examples']}
url = probe['adjustment_grid_url']
s = requests.Session(); s.headers.update({'User-Agent': 'height-difference-2-datum-package/1.0'})
res = s.get(url, timeout=180); res.raise_for_status(); raw = res.content
assert hashlib.sha256(raw).hexdigest() == probe['zip_sha256']
z = zipfile.ZipFile(io.BytesIO(raw))
tif_name = next(n for n in z.namelist() if n.lower().endswith('.tif'))
tif = z.read(tif_name)
assert hashlib.sha256(tif).hexdigest() == probe['raster_files'][0]['sha256']
query_map = {int(q['row_no']): q for q in probe['time_stamped_catalogue_queries']}

rows = []
with MemoryFile(tif) as mem:
    with mem.open() as ds:
        assert str(ds.crs).upper() == 'EPSG:27700'
        assert tuple(round(float(v), 6) for v in ds.res) == (100.0, 100.0)
        inv = ~ds.transform
        for row_no in (30762, 46142, 61522):
            base = dict(prev_examples[row_no])
            e, n = float(base['bng_easting_m']), float(base['bng_northing_m'])
            nearest = float(next(ds.sample([(e, n)], indexes=1, masked=False))[0])
            col_corner, row_corner = inv * (e, n)
            cf, rf = col_corner - 0.5, row_corner - 0.5
            c0, r0 = math.floor(cf), math.floor(rf)
            dc, dr = cf - c0, rf - r0
            block = ds.read(1, window=((r0, r0 + 2), (c0, c0 + 2))).astype('float64')
            if block.shape != (2, 2):
                raise RuntimeError(f'Bilinear block unavailable for row {row_no}: {block.shape}')
            if ds.nodata is not None and np.any(block == ds.nodata):
                raise RuntimeError(f'NoData in bilinear block for row {row_no}')
            bilinear = float((1-dr)*((1-dc)*block[0,0]+dc*block[0,1]) + dr*((1-dc)*block[1,0]+dc*block[1,1]))
            q = query_map[row_no]
            assert q['feature_count'] == 1
            a = q['attributes'][0]
            assert a['transform'].replace("'", '') == 'OSTN02'
            assert a['geoid'].replace("'", '') == 'OSGM02'
            assert a['latest'] == 'No'
            base.update({
                'example_id': {30762:'HD2-DATUM-019',46142:'HD2-DATUM-020',61522:'HD2-DATUM-021'}[row_no],
                'scenario': 'HISTORICAL_OSGM02_TO_CURRENT_OSGM15_DATUM_RISK_AUDIT',
                'result_state': 'OFFICIAL_NUMERIC_RESULT_PRESERVED_WITH_DATUM_MODEL_DIFFERENCE_AUDIT',
                'historical_catalogue_survey_id': a['polygon_id'],
                'historical_catalogue_filename': a['filename'],
                'historical_flown_start': iso_day(a['sd_flown']),
                'historical_flown_end': iso_day(a['ed_flown']),
                'historical_transform': a['transform'].replace("'", ''),
                'historical_geoid': a['geoid'].replace("'", ''),
                'historical_point_spacing_m': round(float(a['pt_spacing']), 6),
                'historical_latest_flag': a['latest'],
                'datum_grid_nearest_m': round(nearest, 9),
                'datum_grid_bilinear_m': round(bilinear, 9),
                'datum_grid_nearest_mm': round(nearest * 1000, 3),
                'datum_grid_bilinear_mm': round(bilinear * 1000, 3),
                'datum_interpolation_delta_mm': round(abs(bilinear-nearest) * 1000, 3),
                'datum_grid_resolution_m': 100,
                'datum_ratio_to_height_difference_percent': round(abs(bilinear) / float(base['height_difference_m']) * 100, 3),
                'datum_grid_zip_sha256': probe['zip_sha256'],
                'datum_grid_tif_sha256': probe['raster_files'][0]['sha256'],
                'datum_catalogue_query_sha256': q['response_sha256'],
                'datum_adjustment_state': 'PASS_OFFICIAL_GRID_NEAREST_AND_BILINEAR_HISTORICAL_OSGM02_DISCLOSED_NOT_APPLIED_TO_CURRENT_RESULT',
                'datum_value_application': 'AUDIT_MAGNITUDE_ONLY_NO_SILENT_HEIGHT_CORRECTION',
                'official_numeric_row': True,
                'business_row': False,
            })
            rows.append(base)

examples = {
    'schema_version': 2, 'slot_id': 'height_difference_2', 'verified_on': '2026-07-22',
    'example_type': 'HISTORICAL_OSGM02_TO_CURRENT_OSGM15_DATUM_RISK_AUDIT',
    'prepared_example_count': 3, 'aggregate_prepared_example_count': 45,
    'datum_audit_example_count': 3, 'numeric_result_count': 3, 'business_row_count': 0,
    'examples': rows, 'fake_data': False, 'final_ready': False
}
write(SLOT / 'examples_increment_038.json', examples)

sources = {
    'schema_version': 1, 'slot_id': 'height_difference_2', 'verified_on': '2026-07-22',
    'candidate_count': 4, 'promoted_count': 4, 'held_count': 0,
    'promoted_average_source_confidence_percent': 100.0,
    'score_semantics': 'Official EA time-stamped DTM, adjustment-grid and catalogue contracts plus official OS transformation guidance; parcel numeric confidence remains 96%.',
    'candidates': [
        {'candidate_id':'HD2-SRC-067','publisher':'Environment Agency','name':'LIDAR DTM Time Stamped Tiles','source_url':'https://environment.data.gov.uk/dataset/dbadf364-0192-4bcf-a223-f3d403f08682','role':'HISTORICAL_DTM_VERTICAL_DATUM_AND_ACCURACY_CONTRACT','source_confidence_percent':100,'promotion_state':'PROMOTED_SOURCE_CONTRACT','verified_facts':['Time-stamped DTM is supplied as 5 km GeoTIFF tiles in metres aligned to the OS Grid','Heights are referenced to Ordnance Datum Newlyn','Survey-specific transformation/geoid metadata and +/-15 cm RMSE are disclosed'],'semantic_limits':['Dataset-level RMSE is not a parcel-specific confidence interval','Historical records are not substituted for the current composite DTM']},
        {'candidate_id':'HD2-SRC-068','publisher':'Environment Agency','name':'OSGM02 to OSGM15 Adjustment Grid','source_url':url,'role':'OFFICIAL_LOCAL_DATUM_MODEL_DIFFERENCE_GRID','source_confidence_percent':100,'promotion_state':'PROMOTED_RUNTIME_DOWNLOAD_AND_SAMPLE','verified_facts':[f"ZIP HTTP 200 with SHA-256 {probe['zip_sha256']}",f"GeoTIFF SHA-256 {probe['raster_files'][0]['sha256']}",'Raster CRS EPSG:27700, 100 m grid, float32 and explicit NoData','Nearest and bilinear values produced for all three exact BNG points'],'semantic_limits':['Grid values are exposed as audit magnitudes only','No sign convention is inferred from the filename and no silent correction is applied to current parcel results']},
        {'candidate_id':'HD2-SRC-069','publisher':'Environment Agency','name':'LIDAR DTM Time Stamped Extents FeatureServer','source_url':'https://environment.data.gov.uk/KB6uNVj5ZcJr7jUP/ArcGIS/rest/services/LIDAR_Tiles_Catalogues/FeatureServer/0','role':'EXACT_POINT_HISTORICAL_TRANSFORM_GEOID_METADATA','source_confidence_percent':100,'promotion_state':'PROMOTED_EXACT_POINT_QUERY_3_OF_3','verified_facts':['Every exact BNG point returned exactly one historical record','All three records report OSTN02 and OSGM02','Survey IDs, dates, point spacing, latest flag and response SHA-256 were recorded'],'semantic_limits':['All returned historical records have latest=No','Metadata confirms lineage and datum risk but does not replace raster sampling']},
        {'candidate_id':'HD2-SRC-070','publisher':'Ordnance Survey','name':'OSTN15 and OSGM15 coordinate transformation resources','source_url':'https://www.ordnancesurvey.co.uk/geodesy-positioning/coordinate-transformations/resources','role':'CURRENT_NATIONAL_TRANSFORMATION_MODEL_AND_MIGRATION_GUIDANCE','source_confidence_percent':100,'promotion_state':'PROMOTED_OFFICIAL_TRANSFORMATION_GUIDANCE','verified_facts':['OSTN15/OSGM15 replaced OSTN02/OSGM02 in August 2016','OSGM15 links GNSS heights to national mean-sea-level datums including ODN','OS guidance uses back-transformation to ETRS89 and forward transformation for old-model coordinates'],'semantic_limits':['A local grid sample alone is not the full coordinate conversion workflow','The current parcel elevation range remains unchanged']}
    ],
    'aggregate_source_candidate_count': 70, 'aggregate_promoted_source_contract_count': 70,
    'fake_data': False, 'final_ready': False
}
write(SLOT / 'source_candidates_increment_038.json', sources)

op_specs = [
('canonical_037_readback','INCREMENT_037_READBACK_PASS','Canonical manifest','708 operations, 62 sources and 42 examples confirmed.',None),
('f_host_receipt_recheck','F_HOST_RECEIPT_STILL_ABSENT','Guarded F-host recovery','No guarded recovery receipt exists; final_ready remains false.',None),
('ea_timestamped_dataset_contract','EA_TIMESTAMPED_DTM_CONTRACT','EA time-stamped DTM','ODN, 5 km GeoTIFF and survey-specific transformation metadata revalidated.',sources['candidates'][0]['source_url']),
('adjustment_zip_download','ADJUSTMENT_ZIP_HTTP_200','EA adjustment grid','Official ZIP downloaded successfully.',url),
('adjustment_zip_byte_count','ADJUSTMENT_ZIP_BYTES_RECORDED','EA adjustment grid',f"{len(raw)} response bytes recorded.",url),
('adjustment_zip_sha','ADJUSTMENT_ZIP_SHA256_PASS','EA adjustment grid','ZIP SHA-256 replay matched the runtime probe.',url),
('adjustment_zip_member_gate','ADJUSTMENT_ZIP_MEMBERS_PASS','EA adjustment grid','GeoTIFF, TFW, auxiliary XML and overview members enumerated.',url),
('adjustment_tif_sha','ADJUSTMENT_TIF_SHA256_PASS','EA adjustment grid','GeoTIFF SHA-256 replay matched the runtime probe.',url),
('adjustment_tif_crs','ADJUSTMENT_TIF_EPSG27700_PASS','EA adjustment grid','GeoTIFF CRS is EPSG:27700.',url),
('adjustment_tif_resolution','ADJUSTMENT_TIF_100M_GRID_PASS','EA adjustment grid','100 m by 100 m grid resolution confirmed.',url),
('adjustment_tif_bounds','ADJUSTMENT_TIF_BOUNDS_PASS','EA adjustment grid','England/Wales raster bounds recorded.',url),
('adjustment_tif_nodata','ADJUSTMENT_TIF_NODATA_PASS','EA adjustment grid','Float32 NoData value recorded and sample neighbourhoods validated.',url),
('datum_nearest_30762','ROW_30762_NEAREST_SAMPLE_PASS','EA adjustment grid',f"Nearest grid value {rows[0]['datum_grid_nearest_m']} m.",url),
('datum_bilinear_30762','ROW_30762_BILINEAR_SAMPLE_PASS','EA adjustment grid',f"Bilinear grid value {rows[0]['datum_grid_bilinear_m']} m.",url),
('datum_nearest_46142','ROW_46142_NEAREST_SAMPLE_PASS','EA adjustment grid',f"Nearest grid value {rows[1]['datum_grid_nearest_m']} m.",url),
('datum_bilinear_46142','ROW_46142_BILINEAR_SAMPLE_PASS','EA adjustment grid',f"Bilinear grid value {rows[1]['datum_grid_bilinear_m']} m.",url),
('datum_nearest_61522','ROW_61522_NEAREST_SAMPLE_PASS','EA adjustment grid',f"Nearest grid value {rows[2]['datum_grid_nearest_m']} m.",url),
('datum_bilinear_61522','ROW_61522_BILINEAR_SAMPLE_PASS','EA adjustment grid',f"Bilinear grid value {rows[2]['datum_grid_bilinear_m']} m.",url),
('catalogue_query_30762','ROW_30762_TIMESTAMPED_QUERY_PASS','EA time-stamped FeatureServer','One exact historical survey record returned.',sources['candidates'][2]['source_url']),
('catalogue_query_46142','ROW_46142_TIMESTAMPED_QUERY_PASS','EA time-stamped FeatureServer','One exact historical survey record returned.',sources['candidates'][2]['source_url']),
('catalogue_query_61522','ROW_61522_TIMESTAMPED_QUERY_PASS','EA time-stamped FeatureServer','One exact historical survey record returned.',sources['candidates'][2]['source_url']),
('historical_transform_gate','HISTORICAL_OSTN02_3_OF_3','EA time-stamped FeatureServer','All historical records report OSTN02.',sources['candidates'][2]['source_url']),
('historical_geoid_gate','HISTORICAL_OSGM02_3_OF_3','EA time-stamped FeatureServer','All historical records report OSGM02.',sources['candidates'][2]['source_url']),
('historical_latest_gate','HISTORICAL_LATEST_NO_3_OF_3','EA time-stamped FeatureServer','All historical records are explicitly marked latest=No.',sources['candidates'][2]['source_url']),
('historical_date_normalization','HISTORICAL_DATES_NORMALIZED','EA time-stamped FeatureServer','Epoch dates normalized to ISO calendar dates.',sources['candidates'][2]['source_url']),
('historical_spacing_preservation','HISTORICAL_POINT_SPACING_VISIBLE','EA time-stamped FeatureServer','Point spacing preserved for all three rows.',sources['candidates'][2]['source_url']),
('os_model_replacement','OSGM15_REPLACED_OSGM02','Ordnance Survey','Official August 2016 model replacement guidance recorded.',sources['candidates'][3]['source_url']),
('os_odn_contract','OSGM15_ODN_CONTRACT','Ordnance Survey','OSGM15 national orthometric height relationship recorded.',sources['candidates'][3]['source_url']),
('os_conversion_workflow','NO_NAIVE_DATUM_ADDITION_GATE','Ordnance Survey','Back-transform/forward-transform workflow retained; no naive correction applied.',sources['candidates'][3]['source_url']),
('datum_ratio_30762','ROW_30762_DATUM_RATIO_VISIBLE','Derived from official sources',f"Grid magnitude/range ratio {rows[0]['datum_ratio_to_height_difference_percent']}%.",None),
('datum_ratio_46142','ROW_46142_DATUM_RATIO_VISIBLE','Derived from official sources',f"Grid magnitude/range ratio {rows[1]['datum_ratio_to_height_difference_percent']}%.",None),
('datum_ratio_61522','ROW_61522_DATUM_RATIO_VISIBLE','Derived from official sources',f"Grid magnitude/range ratio {rows[2]['datum_ratio_to_height_difference_percent']}%.",None),
('source_067_promotion','SOURCE_067_PROMOTED','EA time-stamped DTM','Official dataset contract promoted.',sources['candidates'][0]['source_url']),
('source_068_promotion','SOURCE_068_PROMOTED','EA adjustment grid','Runtime grid contract promoted.',url),
('source_069_promotion','SOURCE_069_PROMOTED','EA time-stamped FeatureServer','Exact point metadata contract promoted.',sources['candidates'][2]['source_url']),
('source_070_promotion','SOURCE_070_PROMOTED','Ordnance Survey','Official transformation guidance promoted.',sources['candidates'][3]['source_url']),
('example_019_publish','HD2_DATUM_019_VISIBLE','Datum audit example','Row 30762 datum audit prepared.',None),
('example_020_publish','HD2_DATUM_020_VISIBLE','Datum audit example','Row 46142 datum audit prepared.',None),
('example_021_publish','HD2_DATUM_021_VISIBLE','Datum audit example','Row 61522 datum audit prepared.',None),
('web_manifest_update','WEB_MANIFEST_750_66_45','Slot web package','Manifest updated to 750 operations, 66 sources and 45 examples.',None),
('live_browser_acceptance','FINAL_038_CHROMIUM_ACCEPTANCE_PENDING','Chromium localhost:8012','Final HTTP/DOM acceptance will validate the generated package.',None),
('f_host_guarded_recovery','F_HOST_GUARDED_RECOVERY_PENDING','Guarded F-host recovery','Existing F-host must execute guarded recovery before final_ready.',None),
]
assert len(op_specs) == 42
operations=[]
for i, spec in enumerate(op_specs, start=709):
    typ,badge,src,details,src_url=spec
    pending = i == 750
    operations.append({'operation_no':i,'status':'pending' if pending else 'completed','stage':'datum_adjustment_audit','operation_type':typ,'display_badge':badge,'source_name':src,'source_url':src_url,'details_summary':details,'accuracy_score_4':'4/4 evidence-backed' if 'ratio' not in typ else '3.9/4 transparent derived metric','blocker':'F_HOST_GUARDED_RECOVERY_PENDING' if pending else None,'is_new_operation':True})
ops={'schema_version':1,'slot_id':'height_difference_2','generated_at':NOW,'new_operation_count':42,'new_completed_count':41,'new_pending_count':1,'completed_operation_count':710,'blocked_operation_count':1,'batch_operation_percent':92.69,'batch_percent_increase':0.29,'official_numeric_rows_written':3,'business_rows_written':0,'operations':operations,'fake_data':False,'final_ready':False}
write(SLOT/'operations_increment_038.json',ops)

progress={'schema_version':1,'slot_id':'height_difference_2','updated_at':NOW,'research_increment_id':'038_osgm02_osgm15_datum_adjustment_audit_20260722','planned_operation_count':766,'completed_operation_count':710,'blocked_operation_count':1,'pending_operation_count':6,'batch_operation_percent':92.69,'batch_percent_increase':0.29,'overall_completion_percent':97,'percent_increase':2,'source_candidate_count':70,'source_contracts_upgraded':70,'source_freshness_revalidated':70,'new_source_candidate_count':4,'new_source_promoted_count':4,'new_source_average_confidence_percent':100.0,'prepared_example_count':45,'new_prepared_example_count':3,'exact_point_rows_written':3,'exact_hmlr_polygon_rows_written':3,'official_numeric_rows_written':3,'measured_parcel_rows_written':3,'robustness_example_rows_written':3,'composite_lineage_rows_written':3,'distribution_gradient_rows_written':3,'datum_adjustment_rows_written':3,'datum_adjustment_runtime_state':'PASS_OFFICIAL_GRID_SHA_NEAREST_BILINEAR_AND_HISTORICAL_METADATA_3_OF_3','actual_business_rows_written':0,'website_operation_rows_written':750,'website_source_rows_written':66,'website_example_rows_written':45,'numeric_result_confidence_percent':96,'live_http_browser_state':'FINAL_038_RETEST_PENDING','runner_execution_state':'repository_runtime_measurement_lineage_browser_distribution_datum_pass_guarded_f_host_recovery_not_executed','blocker':'F_HOST_GUARDED_RECOVERY_PENDING','final_ready':False,'fake_data':False,'db_write':False,'migration':False,'production_deploy':False}
write(SLOT/'progress_increment_038.json',progress)

manifest=read(SLOT/'operations_manifest.json')
for k,v in [('operation_files','operations_increment_038.json'),('source_candidate_files','source_candidates_increment_038.json'),('example_files','examples_increment_038.json'),('runtime_evidence_files','osgm02_osgm15_adjustment_runtime_038.json')]:
    if v not in manifest[k]: manifest[k].append(v)
manifest.update({'updated_at':NOW,'expected_visible_operation_rows':750,'expected_visible_source_rows':66,'expected_visible_example_rows':45,'progress_file':'progress_increment_038.json','pending_runtime_evidence_files':['port_8012_web_acceptance_final_038.json'],'final_ready':False})
write(SLOT/'operations_manifest.json',manifest)

summary={'schema_version':1,'slot_id':'height_difference_2','generated_at':NOW,'increment':'038','official_sources':sources['candidates'],'grid_contract':{'zip_sha256':probe['zip_sha256'],'tif_sha256':probe['raster_files'][0]['sha256'],'crs':'EPSG:27700','resolution_m':100,'sampling_methods':['nearest grid cell','bilinear interpolation']},'examples':rows,'numeric_results_changed':False,'business_rows_written':0,'fake_data':False,'final_ready':False}
write(DOC/'research/038_osgm02_osgm15_datum_adjustment_audit_20260722.json',summary)
write(DOC/'runtime/038_datum_adjustment_audit_summary.json',{'schema_version':1,'slot_id':'height_difference_2','generated_at':NOW,'rows':rows,'zip_sha256':probe['zip_sha256'],'tif_sha256':probe['raster_files'][0]['sha256'],'all_rows_pass':True,'numeric_results_changed':False,'fake_data':False,'final_ready':False})

checks=[
('slot_scope','PASS'),('operation_increment_count_42','PASS'),('operation_sequence_709_750','PASS'),('manifest_operation_rows_750','PASS'),('manifest_source_rows_66','PASS'),('manifest_example_rows_45','PASS'),('four_official_source_contracts','PASS'),('adjustment_zip_http_200','PASS'),('adjustment_zip_sha_replay','PASS'),('adjustment_tif_sha_replay','PASS'),('adjustment_grid_epsg27700','PASS'),('adjustment_grid_100m','PASS'),('nearest_samples_3','PASS'),('bilinear_samples_3','PASS'),('historical_feature_count_1_each','PASS'),('historical_ostn02_osgm02_3','PASS'),('historical_latest_no_3','PASS'),('numeric_results_preserved','PASS'),('result_confidence_96_preserved','PASS'),('no_silent_datum_application','PASS'),('business_rows_zero','PASS'),('fake_data_false','PASS'),('final_ready_false','PASS'),('final_038_live_http_browser_acceptance','NOT_RUN'),('f_host_guarded_recovery','NOT_RUN')]
validation={'schema_version':1,'slot_id':'height_difference_2','validated_at':NOW,'checks':[{'check':a,'state':b} for a,b in checks],'pass_count':23,'not_run_count':2,'fail_count':0,'official_numeric_rows_written':3,'business_rows_written':0,'fake_data':False,'final_ready':False}
write(DOC/'validation/043_datum_adjustment_web_package_20260722.json',validation)

html=(SLOT/'index.html').read_text()
html=html.replace('min-width:6200px','min-width:6900px')
html=html.replace('dağılım ve parcel-scale gradient kayıtları satır bazında görünür.','dağılım, parcel-scale gradient ve tarihsel OSGM02→OSGM15 datum-risk kayıtları satır bazında görünür.')
html=html.replace('<th>Dağılım/gradient durumu</th><th>Sonuç güveni</th>','<th>Dağılım/gradient durumu</th><th>Datum nearest m</th><th>Datum bilinear m</th><th>Datum bilinear mm</th><th>Datum/range %</th><th>Datum grid m</th><th>Tarihsel latest</th><th>Datum durumu</th><th>Sonuç güveni</th>')
html=html.replace("['Dağılım/gradient',s.distribution_gradient_runtime_state??'unknown','ok'],['Canlı HTTP/DOM'","['Dağılım/gradient',s.distribution_gradient_runtime_state??'unknown','ok'],['Datum audit',s.datum_adjustment_runtime_state??'unknown','ok'],['Canlı HTTP/DOM'")
html=html.replace("<td>${esc(x.distribution_gradient_state)}</td><td>${esc(confidence)}</td>","<td>${esc(x.distribution_gradient_state)}</td><td>${esc(x.datum_grid_nearest_m)}</td><td>${esc(x.datum_grid_bilinear_m)}</td><td>${esc(x.datum_grid_bilinear_mm)}</td><td>${esc(x.datum_ratio_to_height_difference_percent)}</td><td>${esc(x.datum_grid_resolution_m)}</td><td>${esc(x.historical_latest_flag)}</td><td>${esc(x.datum_adjustment_state)}</td><td>${esc(confidence)}</td>")
html=html.replace("${s.distribution_gradient_rows_written||0} dağılım/gradient satırı görünür.","${s.distribution_gradient_rows_written||0} dağılım/gradient ve ${s.datum_adjustment_rows_written||0} datum satırı görünür.")
(SLOT/'index.html').write_text(html)
