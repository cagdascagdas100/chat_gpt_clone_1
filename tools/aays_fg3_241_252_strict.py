from pathlib import Path

base = Path(__file__).with_name('aays_fg3_181_192_strict.py')
code = base.read_text(encoding='utf-8')
repls = [
    ('START=181; END=192', 'START=241; END=252'),
    ('!=180', '!=240'),
    ('batches_181_192_strict_spatial', 'batches_241_252_strict_spatial'),
    ('"181-192"', '"241-252"'),
    ('strict batches 181-192', 'strict batches 241-252'),
]
for old, new in repls:
    if old not in code:
        raise SystemExit(f'EXPECTED_TOKEN_MISSING:{old}')
    code = code.replace(old, new)
exec(compile(code, str(base), 'exec'), {'__name__': '__main__', '__file__': str(base)})
