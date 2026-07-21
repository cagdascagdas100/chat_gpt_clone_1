from __future__ import annotations

import runpy
from pathlib import Path


if __name__ == "__main__":
    worker = Path(__file__).with_name("ready_to_sell_3_wave345678910111213141516171819202122232425262728293031323334_live_hash_worker.py")
    runpy.run_path(str(worker), run_name="__main__")
