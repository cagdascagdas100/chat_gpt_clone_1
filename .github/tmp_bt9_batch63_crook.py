import urllib.request

TEMPLATE_URL = "https://raw.githubusercontent.com/cagdascagdas100/chat_gpt_clone_1/2dd1104bc682198b075fa9283d98f1c2e039102e/.github/tmp_bt9_batch46_ripon_v3.py"
req = urllib.request.Request(TEMPLATE_URL, headers={"User-Agent": "TerraYield-AAYS-building_type_9-batch63-template/1.0"})
with urllib.request.urlopen(req, timeout=60) as response:
    text = response.read().decode("utf-8")

replacements = [
    ('CITY = "Ripon"', 'CITY = "Crook"'),
    ('GRID = "RIPON_CENTRAL_02"', 'GRID = "CROOK_CENTRAL_01"'),
    ('LOCAL_AUTHORITY = "North Yorkshire"', 'LOCAL_AUTHORITY = "County Durham"'),
    ('BATCH = 46', 'BATCH = 63'),
    ('EXPECTED_BEFORE = 2250', 'EXPECTED_BEFORE = 3100'),
    ('TARGET_AFTER = 2300', 'TARGET_AFTER = 3150'),
    ('NEXT_TARGET = 2350', 'NEXT_TARGET = 3200'),
    ('xs = [-1.5650, -1.5350, -1.5050, -1.4750]', 'xs = [-1.7900, -1.7600, -1.7300, -1.7000]'),
    ('ys = [54.1100, 54.1320, 54.1540, 54.1760]', 'ys = [54.6850, 54.7050, 54.7250, 54.7450]'),
    ('(+evidence batch 46)', '(+evidence batch 63)'),
    ('OpenStreetMap API 0.6 - Ripon batch 46', 'OpenStreetMap API 0.6 - Crook batch 63'),
    ('appended 50 Ripon OSM API records', 'appended 50 Crook OSM API records'),
    ('Batch 46 appended 50 new Ripon OSM API evidence-backed building features', 'Batch 63 appended 50 new Crook OSM API evidence-backed building features'),
    ('BATCH_046_APPENDED_50_RIPON_OSM_FEATURES_CONTINUATION_REQUIRED', 'BATCH_063_APPENDED_50_CROOK_OSM_FEATURES_CONTINUATION_REQUIRED'),
    ('APPEND_NEW_BATCH_047_AFTER_FEATURE_2300', 'APPEND_NEW_BATCH_064_AFTER_FEATURE_3150'),
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

code = compile(text, ".github/tmp_bt9_batch63_crook.py:rendered", "exec")
exec(code, {"__name__": "__main__", "__file__": ".github/tmp_bt9_batch63_crook.py"})
