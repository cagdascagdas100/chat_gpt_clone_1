from __future__ import annotations

import builtins
import sys
from pathlib import Path

builtins.null = None
sys.path.insert(0, str(Path(__file__).resolve().parent))

from ready_to_sell_3_multi_work_worker import main

if __name__ == "__main__":
    raise SystemExit(main())
