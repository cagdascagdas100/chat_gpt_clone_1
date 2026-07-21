from __future__ import annotations

import importlib.util
from pathlib import Path


BASE_WORKER = Path(__file__).with_name("ready_to_sell_3_wave3456789101112131415161718_live_hash_worker.py")
WAVE_19 = "england_map_web/data/aays_21_slots/ready_to_sell_3/research_preload_wave_19_20260721.json"
WAVE_20 = "england_map_web/data/aays_21_slots/ready_to_sell_3/research_preload_wave_20_20260721.json"


def load_base_worker():
    spec = importlib.util.spec_from_file_location("ready_to_sell_3_wave3456789101112131415161718_base", BASE_WORKER)
    if spec is None or spec.loader is None:
        raise RuntimeError("BASE_WORKER_IMPORT_SPEC_UNAVAILABLE")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    base_module = module.load_base_worker()
    base_module.WAVES = tuple(base_module.WAVES) + (WAVE_19, WAVE_20)
    return base_module


if __name__ == "__main__":
    raise SystemExit(load_base_worker().main())
