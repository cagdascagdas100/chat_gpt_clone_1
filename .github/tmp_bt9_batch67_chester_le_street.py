import urllib.request

TEMPLATE_URL = "https://raw.githubusercontent.com/cagdascagdas100/chat_gpt_clone_1/2dd1104bc682198b075fa9283d98f1c2e039102e/.github/tmp_bt9_batch46_ripon_v3.py"
req = urllib.request.Request(TEMPLATE_URL, headers={"User-Agent": "TerraYield-AAYS-building_type_9-batch67-template/1.0"})
with urllib.request.urlopen(req, timeout=60) as response:
    text = response.read().decode("utf-8")

replacements = [
    ('CITY = "Ripon"', 'CITY = "Chester-le-Street"'),
    ('GRID = "RIPON_CENTRAL_02"', 'GRID = "CHESTER_LE_STREET_CENTRAL_01"'),
    ('LOCAL_AUTHORITY = "North Yorkshire"', 'LOCAL_AUTHORITY = "County Durham"'),
    ('BATCH = 46', 'BATCH = 67'),
    ('EXPECTED_BEFORE = 2250', 'EXPECTED_BEFORE = 3300'),
    ('TARGET_AFTER = 2300', 'TARGET_AFTER = 3350'),
    ('NEXT_TARGET = 2350', 'NEXT_TARGET = 3400'),
    ('xs = [-1.5650, -1.5350, -1.5050, -1.4750]', 'xs = [-1.6200, -1.5900, -1.5600, -1.5300]'),
    ('ys = [54.1100, 54.1320, 54.1540, 54.1760]', 'ys = [54.8200, 54.8420, 54.8640, 54.8860]'),
    ('(+evidence batch 46)', '(+evidence batch 67)'),
    ('OpenStreetMap API 0.6 - Ripon batch 46', 'OpenStreetMap API 0.6 - Chester-le-Street batch 67'),
    ('appended 50 Ripon OSM API records', 'appended 50 Chester-le-Street OSM API records'),
    ('Batch 46 appended 50 new Ripon OSM API evidence-backed building features', 'Batch 67 appended 50 new Chester-le-Street OSM API evidence-backed building features'),
    ('BATCH_046_APPENDED_50_RIPON_OSM_FEATURES_CONTINUATION_REQUIRED', 'BATCH_067_APPENDED_50_CHESTER_LE_STREET_OSM_FEATURES_CONTINUATION_REQUIRED'),
    ('APPEND_NEW_BATCH_047_AFTER_FEATURE_2300', 'APPEND_NEW_BATCH_068_AFTER_FEATURE_3350'),
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

code = compile(text, ".github/tmp_bt9_batch67_chester_le_street.py:rendered", "exec")
exec(code, {"__name__": "__main__", "__file__": ".github/tmp_bt9_batch67_chester_le_street.py"})
