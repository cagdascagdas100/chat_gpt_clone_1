from pathlib import Path

p = Path('.github/tmp_bt9_batch46_ripon_v3.py')
text = p.read_text(encoding='utf-8')
replacements = {
    'CITY = "Ripon"': 'CITY = "Dewsbury"',
    'GRID = "RIPON_CENTRAL_02"': 'GRID = "DEWSBURY_CENTRAL_01"',
    'LOCAL_AUTHORITY = "North Yorkshire"': 'LOCAL_AUTHORITY = "Kirklees"',
    'xs = [-1.5650, -1.5350, -1.5050, -1.4750]': 'xs = [-1.6800, -1.6500, -1.6200, -1.5900]',
    'ys = [54.1100, 54.1320, 54.1540, 54.1760]': 'ys = [53.6600, 53.6800, 53.7000, 53.7200]',
    'OpenStreetMap API 0.6 - Ripon batch 46': 'OpenStreetMap API 0.6 - Dewsbury batch 46',
    'appended 50 Ripon OSM API records': 'appended 50 Dewsbury OSM API records',
    'Batch 46 appended 50 new Ripon OSM API evidence-backed building features': 'Batch 46 appended 50 new Dewsbury OSM API evidence-backed building features',
    'BATCH_046_APPENDED_50_RIPON_OSM_FEATURES_CONTINUATION_REQUIRED': 'BATCH_046_APPENDED_50_DEWSBURY_OSM_FEATURES_CONTINUATION_REQUIRED',
}
for old, new in replacements.items():
    if old not in text:
        raise SystemExit('FAIL_CLOSED missing replacement target: ' + old)
    text = text.replace(old, new)
code = compile(text, str(p) + ':dewsbury-v4', 'exec')
exec(code, {'__name__': '__main__', '__file__': str(p)})
