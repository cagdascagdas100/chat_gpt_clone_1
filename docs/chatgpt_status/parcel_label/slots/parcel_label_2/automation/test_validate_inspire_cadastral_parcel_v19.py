from __future__ import annotations

import hashlib
import importlib.util
import tempfile
from pathlib import Path

SOURCE_ROOT = Path(__file__).parent


def expect(fragment: str, fn) -> None:
    try:
        fn()
    except Exception as exc:
        assert fragment in str(exc), exc
    else:
        raise AssertionError(f"expected {fragment}")


def main() -> int:
    checks = 0
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        for name in ("validate_inspire_cadastral_parcel_v19.py", "stable_xml_source_v1.py"):
            (root / name).write_text((SOURCE_ROOT / name).read_text(encoding="utf-8"), encoding="utf-8")
        (root / "validate_inspire_cadastral_parcel_v18.py").write_text('''from pathlib import Path\nclass Base: pass\nbase=Base()\ndef geometry(x): return {"ok": True}\ndef validate_collection_cardinality(*a, **k): return {"ok": True}\nMUTATE=False\nRAISE=False\ndef parse(path, target_ids):\n    global MUTATE\n    data=Path(path).read_bytes()\n    if MUTATE:\n        Path(path).write_bytes(data+b"x")\n    if RAISE:\n        raise RuntimeError("STUB_PARSE_ERROR")\n    return {x:[{"feature":x}] for x in target_ids}, {"stub_parse":True}\n''', encoding='utf-8')
        spec = importlib.util.spec_from_file_location("validator_v19_test", root / "validate_inspire_cadastral_parcel_v19.py")
        module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(module)

        path = root / "x.gml"
        path.write_bytes(b"<FeatureCollection/>")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        found, summary = module.parse(path, {"1", "2"}, expected_sha256=digest)
        assert set(found) == {"1", "2"}; checks += 1
        assert summary["stub_parse"] is True; checks += 1
        assert summary["xml_parse_bytes_bound_to_download_sha256"] is True; checks += 1
        assert summary["xml_source_toctou_validation_passed"] is True; checks += 1
        assert summary["xml_source_expected_sha256"] == digest; checks += 1
        assert summary["xml_source_observed_sha256"] == digest; checks += 1
        assert module.geometry(None)["ok"] is True; checks += 1
        assert module.validate_collection_cardinality()["ok"] is True; checks += 1
        expect("XML_SOURCE_SHA256_MISMATCH", lambda: module.parse(path, {"1"}, expected_sha256="0" * 64)); checks += 1
        module.previous.MUTATE = True
        expect("XML_SOURCE_", lambda: module.parse(path, {"1"}, expected_sha256=digest)); checks += 1
        module.previous.MUTATE = False
        path.write_bytes(b"<FeatureCollection/>")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        module.previous.RAISE = True
        expect("STUB_PARSE_ERROR", lambda: module.parse(path, {"1"}, expected_sha256=digest)); checks += 1
        module.previous.RAISE = False
        expect("XML_EXPECTED_SHA256_INVALID", lambda: module.parse(path, {"1"}, expected_sha256="bad")); checks += 1
    assert checks == 12, checks
    print("PARCEL_LABEL_2_STABLE_VALIDATOR_TESTS=12/12")
    print("FINAL_READY=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
