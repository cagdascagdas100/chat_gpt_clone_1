from __future__ import annotations

import importlib.util
from pathlib import Path


BASE_WORKER = Path(__file__).with_name("ready_to_sell_3_wave3456_live_hash_worker.py")
WAVE_7 = "england_map_web/data/aays_21_slots/ready_to_sell_3/research_preload_wave_7_20260721.json"


def load_base_worker():
    spec = importlib.util.spec_from_file_location("ready_to_sell_3_wave3456_base", BASE_WORKER)
    if spec is None or spec.loader is None:
        raise RuntimeError("BASE_WORKER_IMPORT_SPEC_UNAVAILABLE")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.WAVES = tuple(module.WAVES) + (WAVE_7,)
    return module


if __name__ == "__main__":
    raise SystemExit(load_base_worker().main())
