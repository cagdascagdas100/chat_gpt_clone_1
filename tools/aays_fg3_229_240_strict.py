from pathlib import Path

base = Path(__file__).with_name('aays_fg3_181_192_strict.py')
code = base.read_text(encoding='utf-8')
repls = [
    ('START=181; END=192', 'START=229; END=240'),
    ('!=180', '!=228'),
    ('batches_181_192_strict_spatial', 'batches_229_240_strict_spatial'),
    ('"181-192"', '"229-240"'),
    ('strict batches 181-192', 'strict batches 229-240'),
]
for old, new in repls:
    if old not in code:
        raise SystemExit(f'EXPECTED_TOKEN_MISSING:{old}')
    code = code.replace(old, new)
exec(compile(code, str(base), 'exec'), {'__name__': '__main__', '__file__': str(base)})
