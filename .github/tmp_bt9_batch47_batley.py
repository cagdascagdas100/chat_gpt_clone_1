import subprocess

SOURCE_COMMIT = "2dd1104bc682198b075fa9283d98f1c2e039102e"
SOURCE_PATH = ".github/tmp_bt9_batch46_ripon_v3.py"

text = subprocess.check_output(
    ["git", "show", f"{SOURCE_COMMIT}:{SOURCE_PATH}"],
    text=True,
)

replacements = {
    'CITY = "Ripon"': 'CITY = "Batley"',
    'GRID = "RIPON_CENTRAL_02"': 'GRID = "BATLEY_CENTRAL_01"',
    'LOCAL_AUTHORITY = "North Yorkshire"': 'LOCAL_AUTHORITY = "Kirklees"',
    'BATCH = 46': 'BATCH = 47',
    'EXPECTED_BEFORE = 2250': 'EXPECTED_BEFORE = 2300',
    'TARGET_AFTER = 2300': 'TARGET_AFTER = 2350',
    'NEXT_TARGET = 2350': 'NEXT_TARGET = 2400',
    'xs = [-1.5650, -1.5350, -1.5050, -1.4750]': 'xs = [-1.6900, -1.6600, -1.6300, -1.6000]',
    'ys = [54.1100, 54.1320, 54.1540, 54.1760]': 'ys = [53.7200, 53.7400, 53.7600, 53.7800]',
}
for old, new in replacements.items():
    if old not in text:
        raise SystemExit("FAIL_CLOSED missing replacement target: " + old)
    text = text.replace(old, new)

text = text.replace("Ripon", "Batley")
text = text.replace("RIPON", "BATLEY")
text = text.replace("batch 46", "batch 47")
text = text.replace("Batch 46", "Batch 47")
text = text.replace("BATCH_046", "BATCH_047")

code = compile(text, SOURCE_PATH + ":batley-batch47", "exec")
exec(code, {"__name__": "__main__", "__file__": SOURCE_PATH})
