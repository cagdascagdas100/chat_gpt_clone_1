import urllib.request

TEMPLATE_URL = "https://raw.githubusercontent.com/cagdascagdas100/chat_gpt_clone_1/2dd1104bc682198b075fa9283d98f1c2e039102e/.github/tmp_bt9_batch46_ripon_v3.py"
req = urllib.request.Request(TEMPLATE_URL, headers={"User-Agent": "TerraYield-AAYS-building_type_9-batch51-template/1.0"})
with urllib.request.urlopen(req, timeout=60) as response:
    text = response.read().decode("utf-8")

replacements = [
    ('CITY = "Ripon"', 'CITY = "Malton"'),
    ('GRID = "RIPON_CENTRAL_02"', 'GRID = "MALTON_CENTRAL_01"'),
    ('BATCH = 46', 'BATCH = 51'),
    ('EXPECTED_BEFORE = 2250', 'EXPECTED_BEFORE = 2500'),
    ('TARGET_AFTER = 2300', 'TARGET_AFTER = 2550'),
    ('NEXT_TARGET = 2350', 'NEXT_TARGET = 2600'),
    ('xs = [-1.5650, -1.5350, -1.5050, -1.4750]', 'xs = [-0.8500, -0.8100, -0.7700, -0.7300]'),
    ('ys = [54.1100, 54.1320, 54.1540, 54.1760]', 'ys = [54.1050, 54.1300, 54.1550, 54.1800]'),
    ('(+evidence batch 46)', '(+evidence batch 51)'),
    ('OpenStreetMap API 0.6 - Ripon batch 46', 'OpenStreetMap API 0.6 - Malton batch 51'),
    ('appended 50 Ripon OSM API records', 'appended 50 Malton OSM API records'),
    ('Batch 46 appended 50 new Ripon OSM API evidence-backed building features', 'Batch 51 appended 50 new Malton OSM API evidence-backed building features'),
    ('BATCH_046_APPENDED_50_RIPON_OSM_FEATURES_CONTINUATION_REQUIRED', 'BATCH_051_APPENDED_50_MALTON_OSM_FEATURES_CONTINUATION_REQUIRED'),
    ('APPEND_NEW_BATCH_047_AFTER_FEATURE_2300', 'APPEND_NEW_BATCH_052_AFTER_FEATURE_2550'),
]
for old, new in replacements:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"FAIL_CLOSED replacement target count {count} for: {old}")
    text = text.replace(old, new)

if 'CITY = "Ripon"' in text or 'BATCH = 46' in text or 'TARGET_AFTER = 2300' in text:
    raise SystemExit("FAIL_CLOSED stale template literals remain")

code = compile(text, ".github/tmp_bt9_batch51_malton.py:rendered", "exec")
exec(code, {"__name__": "__main__", "__file__": ".github/tmp_bt9_batch51_malton.py"})
