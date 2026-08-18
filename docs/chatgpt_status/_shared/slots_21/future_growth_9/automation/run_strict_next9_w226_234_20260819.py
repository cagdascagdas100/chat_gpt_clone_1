#!/usr/bin/env python3
import sys, types
from pathlib import Path

HERE=Path(__file__).resolve().parent
base_src=(HERE/'run_strict_next12_20260818.py').read_text(encoding='utf-8')
base_src=base_src.replace('future_growth_9_bounded12_', 'future_growth_9_bounded9_recovery_', 1)
base_src=base_src.replace('windows = list(range(start_window, start_window + 12))', 'windows = list(range(start_window, start_window + 9))', 1)
base_src=base_src.replace('"bounded_batches_requested": 12', '"bounded_batches_requested": 9', 1)
base_src=base_src.replace('"bounded_batches_completed": 12', '"bounded_batches_completed": 9', 1)
base_src=base_src.replace('TWELVE_NEW_BOUNDED_BATCHES_MIRRORED_AND_READBACK_VERIFIED', 'NINE_RECOVERY_BATCHES_MIRRORED_AND_READBACK_VERIFIED')
patched=types.ModuleType('fg9_base_w226_recovery9'); patched.__file__=str(HERE/'run_strict_next12_20260818.py'); sys.modules[patched.__name__]=patched
exec(compile(base_src,patched.__file__,'exec'),patched.__dict__)

sel_src=(HERE/'run_strict_next12_planning_snapshot_20260818.py').read_text(encoding='utf-8')
sel_src=sel_src.replace('if __name__ == "__main__":\n    try:\n        base.main()\n    except Exception as exc:\n        print("FG9_SNAPSHOT_EXECUTOR_ERROR=" + repr(exc), file=sys.stderr, flush=True)\n        raise\n','')
sel_src=sel_src.replace('if _start_window != 91 or int(cp.get("feature_count_after", -1)) != 91:', 'if _start_window != 226 or int(cp.get("feature_count_after", -1)) != 225:',1)
sel_src=sel_src.replace('expected_window=91/count=91', 'expected_window=226/count=225',1)
selector=types.ModuleType('fg9_selector_w226_recovery9'); selector.__file__=str(HERE/'run_strict_next12_planning_snapshot_20260818.py'); selector.__name__='fg9_selector_w226_recovery9'; sys.modules[selector.__name__]=selector
exec(compile(sel_src,selector.__file__,'exec'),selector.__dict__)
selector.base=patched
patched.choose_query_variant=selector.choose_query_variant
patched.api_entities=selector.api_entities

try:
    patched.main()
except Exception as exc:
    print('FG9_W226_234_RECOVERY9_EXECUTOR_ERROR='+repr(exc),file=sys.stderr,flush=True)
    raise
