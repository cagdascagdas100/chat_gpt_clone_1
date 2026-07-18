from __future__ import annotations

import argparse
import importlib.util
import json
import time
from pathlib import Path

from PIL import ImageGrab


def load_panel(path: Path):
    spec = importlib.util.spec_from_file_location("aays_portable_panel_test_target", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"PANEL_IMPORT_FAILED:{path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--panel", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--screenshot", type=Path, required=True)
    args = parser.parse_args()

    module = load_panel(args.panel.resolve())
    app = module.AaysPanel()
    app.geometry("1200x800+20+20")
    app.update_idletasks()
    app.refresh_status()
    app.update_idletasks()
    app.update()
    app.attributes("-topmost", True)
    app.lift()
    app.focus_force()
    app.update()

    canvas = app.scroll_canvas
    scrollregion = canvas.bbox("all") or (0, 0, 0, 0)
    viewport_height = canvas.winfo_height()
    content_height = int(scrollregion[3] - scrollregion[1])
    before = canvas.yview()
    canvas.yview_moveto(1.0)
    app.update_idletasks()
    app.update()
    after = canvas.yview()

    slot_texts = {slot_id: variable.get() for slot_id, variable in app.slot_vars.items()}
    test_lines = {
        "continue": app.continue_test_var.get(),
        "layers": app.layer_test_var.get(),
        "ai": app.ai_test_var.get(),
        "browser": app.browser_test_var.get(),
        "blockers": app.test_blocker_var.get(),
    }
    checks = {
        "scroll_canvas_exists": canvas is not None,
        "vertical_scroll_required": content_height > viewport_height,
        "scroll_reaches_bottom": bool(after and after[1] >= 0.99 and after != before),
        "all_21_slot_variables_present": len(slot_texts) == 21,
        "all_slot_ids_visible_in_text": all(slot_id in text for slot_id, text in slot_texts.items()),
        "all_slot_partitions_visible": all("aralık" in text for text in slot_texts.values()),
        "continue_test_visible": "21/21" in test_lines["continue"],
        "layer_test_visible": "Katman bütünlüğü: PASS" in test_lines["layers"],
        "ai_test_visible": "fotoğraf decode 1562/1562" in test_lines["ai"],
        "browser_test_visible": "kontrol 14/14" in test_lines["browser"],
        "real_blockers_visible": "AI_VISUAL_COMPARISON_ROWS_ZERO" in test_lines["blockers"],
    }

    app.update_idletasks()
    x = app.winfo_rootx()
    y = app.winfo_rooty()
    width = app.winfo_width()
    height = app.winfo_height()
    args.screenshot.parent.mkdir(parents=True, exist_ok=True)
    time.sleep(0.5)
    app.lift()
    app.update()
    ImageGrab.grab(bbox=(x, y, x + width, y + height), all_screens=True).save(args.screenshot)

    report = {
        "status": "PASS" if all(checks.values()) else "BLOCKED",
        "checks": checks,
        "viewport_height": viewport_height,
        "content_height": content_height,
        "scroll_before": before,
        "scroll_after": after,
        "slot_count": len(slot_texts),
        "slot_texts": slot_texts,
        "test_lines": test_lines,
        "screenshot": str(args.screenshot),
        "final_ready": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    app.destroy()
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
