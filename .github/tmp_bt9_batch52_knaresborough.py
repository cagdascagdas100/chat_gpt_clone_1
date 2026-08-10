import urllib.request

TEMPLATE_URL = "https://raw.githubusercontent.com/cagdascagdas100/chat_gpt_clone_1/2dd1104bc682198b075fa9283d98f1c2e039102e/.github/tmp_bt9_batch46_ripon_v3.py"
req = urllib.request.Request(TEMPLATE_URL, headers={"User-Agent": "TerraYield-AAYS-building_type_9-batch52-template/1.0"})
with urllib.request.urlopen(req, timeout=60) as response:
    text = response.read().decode("utf-8")

replacements = [
    ('CITY = "Ripon"', 'CITY = "Knaresborough"'),
    ('GRID = "RIPON_CENTRAL_02"', 'GRID = "KNARESBOROUGH_CENTRAL_01"'),
    ('BATCH = 46', 'BATCH = 52'),
    ('EXPECTED_BEFORE = 2250', 'EXPECTED_BEFORE = 2550'),
    ('TARGET_AFTER = 2300', 'TARGET_AFTER = 2600'),
    ('NEXT_TARGET = 2350', 'NEXT_TARGET = 2650'),
    ('xs = [-1.5650, -1.5350, -1.5050, -1.4750]', 'xs = [-1.5200, -1.4900, -1.4600, -1.4300]'),
    ('ys = [54.1100, 54.1320, 54.1540, 54.1760]', 'ys = [53.9800, 54.0050, 54.0300, 54.0550]'),
    ('(+evidence batch 46)', '(+evidence batch 52)'),
    ('OpenStreetMap API 0.6 - Ripon batch 46', 'OpenStreetMap API 0.6 - Knaresborough batch 52'),
    ('appended 50 Ripon OSM API records', 'appended 50 Knaresborough OSM API records'),
    ('Batch 46 appended 50 new Ripon OSM API evidence-backed building features', 'Batch 52 appended 50 new Knaresborough OSM API evidence-backed building features'),
    ('BATCH_046_APPENDED_50_RIPON_OSM_FEATURES_CONTINUATION_REQUIRED', 'BATCH_052_APPENDED_50_KNARESBOROUGH_OSM_FEATURES_CONTINUATION_REQUIRED'),
    ('APPEND_NEW_BATCH_047_AFTER_FEATURE_2300', 'APPEND_NEW_BATCH_053_AFTER_FEATURE_2600'),
]
for old, new in replacements:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"FAIL_CLOSED replacement target count {count} for: {old}")
    text = text.replace(old, new)

if 'CITY = "Ripon"' in text or 'BATCH = 46' in text or 'TARGET_AFTER = 2300' in text:
    raise SystemExit("FAIL_CLOSED stale template literals remain")

code = compile(text, ".github/tmp_bt9_batch52_knaresborough.py:rendered", "exec")
exec(code, {"__name__": "__main__", "__file__": ".github/tmp_bt9_batch52_knaresborough.py"})
