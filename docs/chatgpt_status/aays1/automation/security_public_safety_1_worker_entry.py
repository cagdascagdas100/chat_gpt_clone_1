from __future__ import annotations

from pathlib import Path

TEMPLATE = Path(__file__).with_name('security_public_safety_1_acceptance_worker.py')
source = TEMPLATE.read_text(encoding='utf-8')
needle = '”; ”.join'
replacement = '"; ".join'
if source.count(needle) != 1:
    raise RuntimeError(f'EXPECTED_SINGLE_TEMPLATE_PATCH_NOT_FOUND:{source.count(needle)}')
patched = source.replace(needle, replacement)
compiled = compile(patched, str(TEMPLATE), 'exec')
namespace = {
    '__name__': '__main__',
    '__file__': str(TEMPLATE),
    '__package__': None,
}
exec(compiled, namespace)
