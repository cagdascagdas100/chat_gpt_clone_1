from pathlib import Path
import subprocess
import sys

TEMPLATE_COMMIT = "2dd1104bc682198b075fa9283d98f1c2e039102e"
TEMPLATE_PATH = ".github/tmp_bt9_batch46_ripon_v3.py"
OUT = Path(".github/tmp_bt9_batch139_horden_20260813.py")

text = subprocess.check_output(["git", "show", f"{TEMPLATE_COMMIT}:{TEMPLATE_PATH}"], text=True)
replacements = [
    ('CITY = "Ripon"', 'CITY = "Horden"'),
    ('GRID = "RIPON_CENTRAL_02"', 'GRID = "HORDEN_COUNTY_DURHAM_01"'),
    ('LOCAL_AUTHORITY = "North Yorkshire"', 'LOCAL_AUTHORITY = "County Durham"'),
    ('BATCH = 46', 'BATCH = 139'),
    ('EXPECTED_BEFORE = 2250', 'EXPECTED_BEFORE = 6900'),
    ('TARGET_AFTER = 2300', 'TARGET_AFTER = 6950'),
    ('NEXT_TARGET = 2350', 'NEXT_TARGET = 7000'),
    ('xs = [-1.5650, -1.5350, -1.5050, -1.4750]', 'xs = [-1.3350, -1.3100, -1.2850, -1.2600, -1.2350]'),
    ('ys = [54.1100, 54.1320, 54.1540, 54.1760]', 'ys = [54.7350, 54.7500, 54.7650, 54.7800, 54.7950]'),
    ('(+evidence batch 46)', '(+evidence batch 139)'),
    ('OpenStreetMap API 0.6 - Ripon batch 46', 'OpenStreetMap API 0.6 - Horden batch 139'),
    ('appended 50 Ripon OSM API records', 'appended 50 Horden OSM API records'),
    ('Batch 46 appended 50 new Ripon OSM API evidence-backed building features', 'Batch 139 appended 50 new Horden OSM API evidence-backed building features'),
    ('BATCH_046_APPENDED_50_RIPON_OSM_FEATURES_CONTINUATION_REQUIRED', 'BATCH_139_APPENDED_50_HORDEN_OSM_FEATURES_CONTINUATION_REQUIRED'),
    ('APPEND_NEW_BATCH_047_AFTER_FEATURE_2300', 'APPEND_NEW_BATCH_140_AFTER_FEATURE_6950'),
    ('for attempt in range(4):', 'for attempt in range(3):'),
]
for old, new in replacements:
    if text.count(old) != 1:
        raise SystemExit(f"FAIL_CLOSED replacement mismatch: {old} count={text.count(old)}")
    text = text.replace(old, new)

patches = [
    ('for v in (ft.get("id"), p.get("parcel_id"), p.get("osm_id")):', 'for v in (ft.get("id"), p.get("parcel_id"), p.get("osm_id"), p.get("source_ref")):'),
    ('"already_processed_id_basis": ["feature.id", "properties.parcel_id", "properties.osm_id"],', '"already_processed_id_basis": ["feature.id", "properties.parcel_id", "properties.osm_id", "properties.source_ref"],'),
    ('"processed_id_basis": ["feature.id", "properties.parcel_id", "properties.osm_id"],', '"processed_id_basis": ["feature.id", "properties.parcel_id", "properties.osm_id", "properties.source_ref"],'),
    ('seen_osm = set()\nfor ft in geo["features"]:', 'seen_osm = set()\nseen_source_ref = set()\nfor ft in geo["features"]:'),
    ('        ("osm_id", str(p.get("osm_id") or ""), seen_osm),\n    ]', '        ("osm_id", str(p.get("osm_id") or ""), seen_osm),\n        ("source_ref", str(p.get("source_ref") or ""), seen_source_ref),\n    ]'),
]
for old, new in patches:
    if text.count(old) != 1:
        raise SystemExit(f"FAIL_CLOSED patch mismatch count={text.count(old)}")
    text = text.replace(old, new)

old = '        "source_url": "https://www.openstreetmap.org/way/" + wid,\n        "source_hash": source_sha,'
new = '        "source_url": "https://www.openstreetmap.org/way/" + wid,\n        "source_ref": "https://www.openstreetmap.org/way/" + wid,\n        "source_hash": source_sha,'
if text.count(old) != 2:
    raise SystemExit(f"FAIL_CLOSED source_ref insertion count={text.count(old)}")
text = text.replace(old, new)

old = '        "evidence_level": "B",\n        "confidence_level_1_to_4": 3,\n        "match_method": method,\n    })'
new = '        "evidence_level": "B",\n        "confidence_score": 0.85,\n        "confidence_level_1_to_4": 3,\n        "match_method": method,\n        "fake_data": False,\n    })'
if text.count(old) != 1:
    raise SystemExit("FAIL_CLOSED confidence/fake_data patch mismatch")
text = text.replace(old, new)

OUT.write_text(text, encoding="utf-8")
subprocess.check_call([sys.executable, str(OUT)])
