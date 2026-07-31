from __future__ import annotations

import importlib.util
import tempfile
from pathlib import Path

HERE = Path(__file__).parent
spec = importlib.util.spec_from_file_location("validator_v10", HERE / "validate_inspire_cadastral_parcel_v10.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

legacy_spec = importlib.util.spec_from_file_location("validator_v9_tests", HERE / "test_validate_inspire_cadastral_parcel_v9.py")
legacy = importlib.util.module_from_spec(legacy_spec)
legacy_spec.loader.exec_module(legacy)

TARGET = legacy.TARGET
checks = 0


def ok(value):
    global checks
    assert value
    checks += 1


def run(payload: bytes):
    handle = tempfile.NamedTemporaryFile(suffix=".gml", delete=False)
    handle.write(payload)
    handle.close()
    path = Path(handle.name)
    try:
        return module.parse(path, {TARGET, "46037757"})
    finally:
        path.unlink(missing_ok=True)


assert legacy.main() == 0
xml = legacy.wfs([legacy.cp()], "numberReturned='1' numberMatched='1'").encode()
found, summary = run(xml)
ok(bool(found[TARGET]))
ok(summary["xml_security_preflight_passed"] is True)
ok(summary["xml_security_encoding"] == "UTF-8")
ok(tuple(int(x) for x in summary["xml_security_expat_version"].split(".")) >= (2, 6, 0))
ok(module.geometry is module.previous.geometry)
ok(module.validate_collection_cardinality is module.previous.validate_collection_cardinality)

bad = b"<!DOCTYPE root [<!ENTITY x 'boom'>]>" + xml
try:
    run(bad)
except RuntimeError as exc:
    ok("XML_DOCTYPE_DECLARATION_FORBIDDEN" in str(exc))
else:
    raise AssertionError("expected doctype rejection")

print(f"PARCEL_LABEL_2_XML_SECURITY_VALIDATOR_TESTS={checks}/{checks}")
print("FINAL_READY=false")
