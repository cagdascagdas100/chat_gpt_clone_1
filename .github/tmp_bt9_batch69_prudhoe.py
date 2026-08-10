import urllib.request

TEMPLATE_URL = "https://raw.githubusercontent.com/cagdascagdas100/chat_gpt_clone_1/2dd1104bc682198b075fa9283d98f1c2e039102e/.github/tmp_bt9_batch46_ripon_v3.py"
req = urllib.request.Request(TEMPLATE_URL, headers={"User-Agent": "TerraYield-AAYS-building_type_9-batch69-template/1.0"})
with urllib.request.urlopen(req, timeout=60) as response:
    text = response.read().decode("utf-8")

replacements = [
    ('CITY = "Ripon"', 'CITY = "Prudhoe"'),
    ('GRID = "RIPON_CENTRAL_02"', 'GRID = "PRUDHOE_CENTRAL_01"'),
    ('LOCAL_AUTHORITY = "North Yorkshire"', 'LOCAL_AUTHORITY = "Northumberland"'),
    ('BATCH = 46', 'BATCH = 69'),
    ('EXPECTED_BEFORE = 2250', 'EXPECTED_BEFORE = 3400'),
    ('TARGET_AFTER = 2300', 'TARGET_AFTER = 3450'),
    ('NEXT_TARGET = 2350', 'NEXT_TARGET = 3500'),
    ('xs = [-1.5650, -1.5350, -1.5050, -1.4750]', 'xs = [-1.8900, -1.8650, -1.8400, -1.8150]'),
    ('ys = [54.1100, 54.1320, 54.1540, 54.1760]', 'ys = [54.9350, 54.9520, 54.9690, 54.9860]'),
    ('(+evidence batch 46)', '(+evidence batch 69)'),
    ('OpenStreetMap API 0.6 - Ripon batch 46', 'OpenStreetMap API 0.6 - Prudhoe batch 69'),
    ('appended 50 Ripon OSM API records', 'appended 50 Prudhoe OSM API records'),
    ('Batch 46 appended 50 new Ripon OSM API evidence-backed building features', 'Batch 69 appended 50 new Prudhoe OSM API evidence-backed building features'),
    ('BATCH_046_APPENDED_50_RIPON_OSM_FEATURES_CONTINUATION_REQUIRED', 'BATCH_069_APPENDED_50_PRUDHOE_OSM_FEATURES_CONTINUATION_REQUIRED'),
    ('APPEND_NEW_BATCH_047_AFTER_FEATURE_2300', 'APPEND_NEW_BATCH_070_AFTER_FEATURE_3450'),
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

code = compile(text, ".github/tmp_bt9_batch69_prudhoe.py:rendered", "exec")
exec(code, {"__name__": "__main__", "__file__": ".github/tmp_bt9_batch69_prudhoe.py"})
