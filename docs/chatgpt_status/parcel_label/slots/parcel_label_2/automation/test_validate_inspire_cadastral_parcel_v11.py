from __future__ import annotations

import importlib.util
import tempfile
from pathlib import Path

HERE = Path(__file__).parent
legacy_spec = importlib.util.spec_from_file_location("v10tests", HERE / "test_validate_inspire_cadastral_parcel_v10.py")
legacy = importlib.util.module_from_spec(legacy_spec)
legacy_spec.loader.exec_module(legacy)

spec = importlib.util.spec_from_file_location("v11", HERE / "validate_inspire_cadastral_parcel_v11.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
checks = 0


def ok(value):
    global checks
    assert value
    checks += 1


ok(legacy.checks == 7)
TARGET = legacy.TARGET
xml = legacy.xml
with tempfile.NamedTemporaryFile(suffix=".gml", delete=False) as handle:
    handle.write(xml)
    path = Path(handle.name)
try:
    found, summary = mod.parse(path, {TARGET, "46037757"})
finally:
    path.unlink(missing_ok=True)
ok(len(found[TARGET]) == 1)
ok(summary["xml_security_preflight_passed"])
ok(summary["xml_structure_preflight_passed"])
ok(summary["xml_structure_root_count"] == 1)
ok(summary["xml_structure_element_count"] > 5)
ok(summary["xml_structure_max_depth"] >= 3)
ok(mod.geometry is mod.previous.geometry)
ok(mod.validate_collection_cardinality is mod.previous.validate_collection_cardinality)

print(f"PARCEL_LABEL_2_XML_STRUCTURE_VALIDATOR_TESTS={checks}/{checks}")
print("FINAL_READY=false")
