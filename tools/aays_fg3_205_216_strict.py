from pathlib import Path

base = Path(__file__).with_name('aays_fg3_181_192_strict.py')
code = base.read_text(encoding='utf-8')
repls = [
    ('START=181; END=192', 'START=205; END=216'),
    ('!=180', '!=204'),
    ('batches_181_192_strict_spatial', 'batches_205_216_strict_spatial'),
    ('"181-192"', '"205-216"'),
    ('strict batches 181-192', 'strict batches 205-216'),
]
for old, new in repls:
    if old not in code:
        raise SystemExit(f'EXPECTED_TOKEN_MISSING:{old}')
    code = code.replace(old, new)
exec(compile(code, str(base), 'exec'), {'__name__': '__main__', '__file__': str(base)})
