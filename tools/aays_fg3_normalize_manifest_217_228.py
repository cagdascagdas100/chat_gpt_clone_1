from pathlib import Path

base = Path(__file__).with_name('aays_fg3_normalize_manifest_193_204.py')
code = base.read_text(encoding='utf-8')
repls = [
    ('==204', '==228'),
    ("{'first':193,'last':204}", "{'first':217,'last':228}"),
    ('range(193,205)', 'range(217,229)'),
    ("'bounded_batches_completed':204", "'bounded_batches_completed':228"),
    ("'request_batch_start':193", "'request_batch_start':217"),
    ("'request_batch_end':204", "'request_batch_end':228"),
    ("'request_batch_range':'193-204'", "'request_batch_range':'217-228'"),
    ("'bounded_batches_total':204", "'bounded_batches_total':228"),
    ("'cursor':204", "'cursor':228"),
    ("'processed_window_count':204", "'processed_window_count':228"),
    ('batches 193-204', 'batches 217-228'),
]
for old, new in repls:
    if old not in code:
        raise SystemExit(f'EXPECTED_TOKEN_MISSING:{old}')
    code = code.replace(old, new)
exec(compile(code, str(base), 'exec'), {'__name__': '__main__', '__file__': str(base)})
