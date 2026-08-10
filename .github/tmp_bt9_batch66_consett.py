import urllib.request

TEMPLATE_URL = "https://raw.githubusercontent.com/cagdascagdas100/chat_gpt_clone_1/2dd1104bc682198b075fa9283d98f1c2e039102e/.github/tmp_bt9_batch46_ripon_v3.py"
req = urllib.request.Request(TEMPLATE_URL, headers={"User-Agent": "TerraYield-AAYS-building_type_9-batch66-template/1.0"})
with urllib.request.urlopen(req, timeout=60) as response:
    text = response.read().decode("utf-8")

replacements = [
    ('CITY = "Ripon"', 'CITY = "Consett"'),
    ('GRID = "RIPON_CENTRAL_02"', 'GRID = "CONSETT_CENTRAL_01"'),
    ('LOCAL_AUTHORITY = "North Yorkshire"', 'LOCAL_AUTHORITY = "County Durham"'),
    ('BATCH = 46', 'BATCH = 66'),
    ('EXPECTED_BEFORE = 2250', 'EXPECTED_BEFORE = 3250'),
    ('TARGET_AFTER = 2300', 'TARGET_AFTER = 3300'),
    ('NEXT_TARGET = 2350', 'NEXT_TARGET = 3350'),
    ('xs = [-1.5650, -1.5350, -1.5050, -1.4750]', 'xs = [-1.8800, -1.8500, -1.8200, -1.7900]'),
    ('ys = [54.1100, 54.1320, 54.1540, 54.1760]', 'ys = [54.8200, 54.8420, 54.8640, 54.8860]'),
    ('(+evidence batch 46)', '(+evidence batch 66)'),
    ('OpenStreetMap API 0.6 - Ripon batch 46', 'OpenStreetMap API 0.6 - Consett batch 66'),
    ('appended 50 Ripon OSM API records', 'appended 50 Consett OSM API records'),
    ('Batch 46 appended 50 new Ripon OSM API evidence-backed building features', 'Batch 66 appended 50 new Consett OSM API evidence-backed building features'),
    ('BATCH_046_APPENDED_50_RIPON_OSM_FEATURES_CONTINUATION_REQUIRED', 'BATCH_066_APPENDED_50_CONSETT_OSM_FEATURES_CONTINUATION_REQUIRED'),
    ('APPEND_NEW_BATCH_047_AFTER_FEATURE_2300', 'APPEND_NEW_BATCH_067_AFTER_FEATURE_3300'),
]
for old, new in replacements:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"FAIL_CLOSED replacement target count {count} for: {old}")
    text = text.replace(old, new)

stale_literals = [
    'CITY = "Ripon"',
    'GRID = "RIPON_CENTRAL_02"',
    'LOCAL_AUTHORITY = "North Yorkshire"',
    'BATCH = 46',
    'EXPECTED_BEFORE = 2250',
    'TARGET_AFTER = 2300',
]
for literal in stale_literals:
    if literal in text:
        raise SystemExit(f"FAIL_CLOSED stale template literal remains: {literal}")

code = compile(text, ".github/tmp_bt9_batch66_consett.py:rendered", "exec")
exec(code, {"__name__": "__main__", "__file__": ".github/tmp_bt9_batch66_consett.py"})
