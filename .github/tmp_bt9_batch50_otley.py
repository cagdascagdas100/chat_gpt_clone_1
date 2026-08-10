import urllib.request

TEMPLATE_URL = "https://raw.githubusercontent.com/cagdascagdas100/chat_gpt_clone_1/2dd1104bc682198b075fa9283d98f1c2e039102e/.github/tmp_bt9_batch46_ripon_v3.py"
req = urllib.request.Request(TEMPLATE_URL, headers={"User-Agent": "TerraYield-AAYS-building_type_9-batch50-template/1.0"})
with urllib.request.urlopen(req, timeout=60) as response:
    text = response.read().decode("utf-8")

replacements = [
    ('CITY = "Ripon"', 'CITY = "Otley"'),
    ('GRID = "RIPON_CENTRAL_02"', 'GRID = "OTLEY_CENTRAL_01"'),
    ('LOCAL_AUTHORITY = "North Yorkshire"', 'LOCAL_AUTHORITY = "Leeds"'),
    ('BATCH = 46', 'BATCH = 50'),
    ('EXPECTED_BEFORE = 2250', 'EXPECTED_BEFORE = 2450'),
    ('TARGET_AFTER = 2300', 'TARGET_AFTER = 2500'),
    ('NEXT_TARGET = 2350', 'NEXT_TARGET = 2550'),
    ('xs = [-1.5650, -1.5350, -1.5050, -1.4750]', 'xs = [-1.7500, -1.7100, -1.6700, -1.6300]'),
    ('ys = [54.1100, 54.1320, 54.1540, 54.1760]', 'ys = [53.8700, 53.8950, 53.9200, 53.9450]'),
    ('(+evidence batch 46)', '(+evidence batch 50)'),
    ('OpenStreetMap API 0.6 - Ripon batch 46', 'OpenStreetMap API 0.6 - Otley batch 50'),
    ('appended 50 Ripon OSM API records', 'appended 50 Otley OSM API records'),
    ('Batch 46 appended 50 new Ripon OSM API evidence-backed building features', 'Batch 50 appended 50 new Otley OSM API evidence-backed building features'),
    ('BATCH_046_APPENDED_50_RIPON_OSM_FEATURES_CONTINUATION_REQUIRED', 'BATCH_050_APPENDED_50_OTLEY_OSM_FEATURES_CONTINUATION_REQUIRED'),
    ('APPEND_NEW_BATCH_047_AFTER_FEATURE_2300', 'APPEND_NEW_BATCH_051_AFTER_FEATURE_2500'),
]
for old, new in replacements:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"FAIL_CLOSED replacement target count {count} for: {old}")
    text = text.replace(old, new)

if 'CITY = "Ripon"' in text or 'BATCH = 46' in text or 'TARGET_AFTER = 2300' in text:
    raise SystemExit("FAIL_CLOSED stale template literals remain")

code = compile(text, ".github/tmp_bt9_batch50_otley.py:rendered", "exec")
exec(code, {"__name__": "__main__", "__file__": ".github/tmp_bt9_batch50_otley.py"})
