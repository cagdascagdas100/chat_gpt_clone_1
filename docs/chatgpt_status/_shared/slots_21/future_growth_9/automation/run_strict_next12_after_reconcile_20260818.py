#!/usr/bin/env python3
import sys, types
from pathlib import Path

HERE=Path(__file__).resolve().parent
base_src=(HERE/'run_strict_next12_20260818.py').read_text(encoding='utf-8')
needle='if start_window < 91 or before < 91:'
if needle not in base_src: raise RuntimeError('BASE_GUARD_PATTERN_NOT_FOUND')
base_src=base_src.replace(needle,'if start_window < 91 or before < 90:',1)
patched=types.ModuleType('fg9_patched_base'); patched.__file__=str(HERE/'run_strict_next12_20260818.py'); sys.modules[patched.__name__]=patched
exec(compile(base_src,patched.__file__,'exec'),patched.__dict__)

sel_src=(HERE/'run_strict_next12_planning_snapshot_20260818.py').read_text(encoding='utf-8')
sel_src=sel_src.replace('if __name__ == "__main__":\n    try:\n        base.main()\n    except Exception as exc:\n        print("FG9_SNAPSHOT_EXECUTOR_ERROR=" + repr(exc), file=sys.stderr, flush=True)\n        raise\n','')
sel_src=sel_src.replace('if _start_window != 91 or int(cp.get("feature_count_after", -1)) != 91:', 'if _start_window != 91 or int(cp.get("feature_count_after", -1)) != 90:',1)
sel_src=sel_src.replace('expected_window=91/count=91', 'expected_window=91/count=90',1)
selector=types.ModuleType('fg9_selector'); selector.__file__=str(HERE/'run_strict_next12_planning_snapshot_20260818.py'); selector.__name__='fg9_selector'; sys.modules[selector.__name__]=selector
exec(compile(sel_src,selector.__file__,'exec'),selector.__dict__)
selector.base=patched
patched.choose_query_variant=selector.choose_query_variant
patched.api_entities=selector.api_entities

try:
    patched.main()
except Exception as exc:
    print('FG9_POST_RECONCILE_EXECUTOR_ERROR='+repr(exc),file=sys.stderr,flush=True)
    raise
