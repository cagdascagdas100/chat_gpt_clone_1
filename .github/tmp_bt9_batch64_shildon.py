import urllib.request

TEMPLATE_URL = "https://raw.githubusercontent.com/cagdascagdas100/chat_gpt_clone_1/2dd1104bc682198b075fa9283d98f1c2e039102e/.github/tmp_bt9_batch46_ripon_v3.py"
req = urllib.request.Request(TEMPLATE_URL, headers={"User-Agent": "TerraYield-AAYS-building_type_9-batch64-template/1.0"})
with urllib.request.urlopen(req, timeout=60) as response:
    text = response.read().decode("utf-8")

replacements = [
    ('CITY = "Ripon"', 'CITY = "Shildon"'),
    ('GRID = "RIPON_CENTRAL_02"', 'GRID = "SHILDON_CENTRAL_01"'),
    ('LOCAL_AUTHORITY = "North Yorkshire"', 'LOCAL_AUTHORITY = "County Durham"'),
    ('BATCH = 46', 'BATCH = 64'),
    ('EXPECTED_BEFORE = 2250', 'EXPECTED_BEFORE = 3150'),
    ('TARGET_AFTER = 2300', 'TARGET_AFTER = 3200'),
    ('NEXT_TARGET = 2350', 'NEXT_TARGET = 3250'),
    ('xs = [-1.5650, -1.5350, -1.5050, -1.4750]', 'xs = [-1.6900, -1.6600, -1.6300, -1.6000]'),
    ('ys = [54.1100, 54.1320, 54.1540, 54.1760]', 'ys = [54.6000, 54.6220, 54.6440, 54.6660]'),
    ('(+evidence batch 46)', '(+evidence batch 64)'),
    ('OpenStreetMap API 0.6 - Ripon batch 46', 'OpenStreetMap API 0.6 - Shildon batch 64'),
    ('appended 50 Ripon OSM API records', 'appended 50 Shildon OSM API records'),
    ('Batch 46 appended 50 new Ripon OSM API evidence-backed building features', 'Batch 64 appended 50 new Shildon OSM API evidence-backed building features'),
    ('BATCH_046_APPENDED_50_RIPON_OSM_FEATURES_CONTINUATION_REQUIRED', 'BATCH_064_APPENDED_50_SHILDON_OSM_FEATURES_CONTINUATION_REQUIRED'),
    ('APPEND_NEW_BATCH_047_AFTER_FEATURE_2300', 'APPEND_NEW_BATCH_065_AFTER_FEATURE_3200'),
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

code = compile(text, ".github/tmp_bt9_batch64_shildon.py:rendered", "exec")
exec(code, {"__name__": "__main__", "__file__": ".github/tmp_bt9_batch64_shildon.py"})
