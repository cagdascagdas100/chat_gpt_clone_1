from __future__ import annotations

import hashlib
import importlib.util
import os
import stat
import tempfile
from types import SimpleNamespace
from unittest.mock import patch
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("stable_xml_source_v1.py")
spec = importlib.util.spec_from_file_location("stable_xml_source_v1", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


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
        source = root / "source.gml"
        source.write_bytes(b"<FeatureCollection><x>1</x></FeatureCollection>")
        digest = hashlib.sha256(source.read_bytes()).hexdigest()

        snap = module.capture(source); checks += 1
        assert snap.sha256 == digest and snap.size == source.stat().st_size
        assert module.normalise_sha256(digest.upper()) == digest; checks += 1
        expect("XML_EXPECTED_SHA256_INVALID", lambda: module.normalise_sha256("x")); checks += 1
        expect("positive integer", lambda: module.capture(source, chunk_size=0)); checks += 1

        result, evidence = module.guarded_call(source, expected_sha256=digest, operation=lambda: 7)
        assert result == 7 and evidence["xml_source_stability_validation_passed"] is True; checks += 1
        assert evidence["xml_source_expected_sha256"] == digest; checks += 1
        assert evidence["xml_source_observed_sha256"] == digest; checks += 1
        assert evidence["xml_source_digest_stable"] is True; checks += 1

        expect("XML_SOURCE_SHA256_MISMATCH", lambda: module.guarded_call(source, expected_sha256="0" * 64, operation=lambda: None)); checks += 1

        empty = root / "empty.gml"; empty.write_bytes(b"")
        expect("XML_SOURCE_EMPTY", lambda: module.capture(empty)); checks += 1
        directory_path = root / "folder"; directory_path.mkdir()
        expect("XML_SOURCE_NOT_REGULAR_FILE", lambda: module.capture(directory_path)); checks += 1

        fake_symlink = SimpleNamespace(st_mode=stat.S_IFLNK | 0o777)
        with patch.object(module.os, "lstat", return_value=fake_symlink):
            expect("XML_SOURCE_SYMLINK_FORBIDDEN", lambda: module.capture(source)); checks += 1

        fake_hardlink = SimpleNamespace(st_mode=stat.S_IFREG | 0o600, st_size=1, st_nlink=2)
        with patch.object(module.os, "lstat", return_value=fake_hardlink):
            expect("XML_SOURCE_LINK_COUNT_NOT_ONE", lambda: module.capture(source)); checks += 1

        source.write_bytes(b"<FeatureCollection><x>1</x></FeatureCollection>")
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        def append_mutation():
            source.write_bytes(source.read_bytes() + b"x")
            return 1
        expect("XML_SOURCE_METADATA_CHANGED", lambda: module.guarded_call(source, expected_sha256=digest, operation=append_mutation)); checks += 1

        source.write_bytes(b"<FeatureCollection><x>1</x></FeatureCollection>")
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        def same_size_mutation():
            data = bytearray(source.read_bytes()); data[-2] = ord("y"); source.write_bytes(data)
        expect("XML_SOURCE_", lambda: module.guarded_call(source, expected_sha256=digest, operation=same_size_mutation)); checks += 1

        source.write_bytes(b"<FeatureCollection><x>1</x></FeatureCollection>")
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        def replace_same_bytes():
            replacement = root / "replacement.gml"; replacement.write_bytes(source.read_bytes()); replacement.replace(source)
        expect("XML_SOURCE_METADATA_CHANGED", lambda: module.guarded_call(source, expected_sha256=digest, operation=replace_same_bytes)); checks += 1

        source.write_bytes(b"<FeatureCollection><x>1</x></FeatureCollection>")
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        def error_no_mutation():
            raise ValueError("original")
        expect("original", lambda: module.guarded_call(source, expected_sha256=digest, operation=error_no_mutation)); checks += 1

        source.write_bytes(b"<FeatureCollection><x>1</x></FeatureCollection>")
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        def error_with_mutation():
            source.write_bytes(b"changed")
            raise ValueError("original")
        expect("XML_SOURCE_", lambda: module.guarded_call(source, expected_sha256=digest, operation=error_with_mutation)); checks += 1

        missing = root / "missing.gml"
        expect("XML_SOURCE_LSTAT_FAILED", lambda: module.capture(missing)); checks += 1

        source.write_bytes(b"a" * 10000)
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        snap = module.capture(source, chunk_size=17)
        assert snap.sha256 == digest; checks += 1

        source.write_bytes(b"stable")
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        _, evidence = module.guarded_call(source, expected_sha256=digest, operation=lambda: source.read_bytes())
        assert evidence["xml_source_size_bytes"] == 6; checks += 1

    assert checks == 21, checks
    print("PARCEL_LABEL_2_XML_SOURCE_STABILITY_TESTS=21/21")
    print("FINAL_READY=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
