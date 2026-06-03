# PASS/FAIL Control List

PASS only if:

- All generated files are under `security_accuracy_expansion/`.
- `git diff --name-only -- england_map_web` is empty.
- Active overlay/data/score files are not changed.
- Existing live blocker is documented if baseline fails.

FAIL and stop if:

- Any generated file targets `england_map_web/`.
- Any active GeoJSON/JSON, overlay JS, or `index.html` is modified.
- A run manifest allows live outputs in this phase.