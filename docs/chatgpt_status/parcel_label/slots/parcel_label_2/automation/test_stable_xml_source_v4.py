from __future__ import annotations

import hashlib
import importlib.util
import os
import stat
import tempfile
from pathlib import Path

HERE = Path(__file__).parent
spec = importlib.util.spec_from_file_location("stable_v4", HERE / "stable_xml_source_v4.py")
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
checks = 0

def ok(value):
    global checks
    assert value
    checks += 1

def expect(fragment, fn):
    global checks
    try:
        fn()
    except Exception as exc:
        assert fragment in str(exc), exc
        checks += 1
    else:
        raise AssertionError(fragment)

payload = b"<FeatureCollection><x>123</x></FeatureCollection>"
digest = hashlib.sha256(payload).hexdigest()
with tempfile.NamedTemporaryFile(suffix=".gml", delete=False) as h:
    h.write(payload); path = Path(h.name)
try:
    result, evidence = mod.guarded_immutable_snapshot_call(
        path, expected_sha256=digest, expected_size_bytes=len(payload), max_bytes=1024,
        chunk_size=7, operation=lambda p: Path(p).read_bytes(),
    )
    ok(result == payload)
    ok(evidence["xml_immutable_snapshot_validation_passed"])
    ok(evidence["xml_exact_size_validation_passed"])
    ok(evidence["xml_bounded_read_validation_passed"])
    ok(evidence["xml_source_expected_size_bytes"] == len(payload))
    ok(evidence["xml_source_observed_size_bytes"] == len(payload))
    ok(evidence["xml_snapshot_observed_size_bytes"] == len(payload))
    ok(evidence["xml_source_max_bytes"] == 1024)
    ok(evidence["xml_parser_uses_private_snapshot"])
    ok(evidence["xml_parser_uses_original_descriptor"] is False)
    ok(evidence["xml_parser_source_mode"] in {"UNLINKED_PRIVATE_DESCRIPTOR", "PRIVATE_READ_ONLY_PATH"})

    result, evidence = mod.guarded_immutable_snapshot_call(
        path, expected_sha256=digest, expected_size_bytes=len(payload), max_bytes=1024,
        force_linked_snapshot=True, operation=lambda p: (Path(p).read_bytes(), stat.S_IMODE(os.stat(p).st_mode)),
    )
    ok(result[0] == payload)
    ok(result[1] == 0o400)
    ok(evidence["xml_parser_source_mode"] == "PRIVATE_READ_ONLY_PATH")
    ok(evidence["xml_snapshot_unlinked_before_parse"] is False)

    expect("SHA256_MISMATCH", lambda: mod.guarded_immutable_snapshot_call(
        path, expected_sha256="0"*64, expected_size_bytes=len(payload), operation=lambda p: None))
    expect("EXPECTED_SHA256_INVALID", lambda: mod.guarded_immutable_snapshot_call(
        path, expected_sha256="bad", expected_size_bytes=len(payload), operation=lambda p: None))
    expect("expected_size_bytes must be a positive integer", lambda: mod.guarded_immutable_snapshot_call(
        path, expected_sha256=digest, expected_size_bytes=0, operation=lambda p: None))
    expect("expected_size_bytes must be a positive integer", lambda: mod.guarded_immutable_snapshot_call(
        path, expected_sha256=digest, expected_size_bytes=True, operation=lambda p: None))
    expect("chunk_size must be a positive integer", lambda: mod.guarded_immutable_snapshot_call(
        path, expected_sha256=digest, expected_size_bytes=len(payload), chunk_size=0, operation=lambda p: None))
    expect("max_bytes must be a positive integer", lambda: mod.guarded_immutable_snapshot_call(
        path, expected_sha256=digest, expected_size_bytes=len(payload), max_bytes=-1, operation=lambda p: None))
    expect("EXPECTED_SIZE_LIMIT_EXCEEDED", lambda: mod.guarded_immutable_snapshot_call(
        path, expected_sha256=digest, expected_size_bytes=len(payload), max_bytes=len(payload)-1, operation=lambda p: None))
    expect("SIZE_MISMATCH", lambda: mod.guarded_immutable_snapshot_call(
        path, expected_sha256=digest, expected_size_bytes=len(payload)+1, max_bytes=1024, operation=lambda p: None))

    def mutate_original(_snapshot):
        path.write_bytes(payload + b"x")
        return b"parsed"
    expect("SOURCE_DESCRIPTOR_METADATA_CHANGED_DURING_PARSE", lambda: mod.guarded_immutable_snapshot_call(
        path, expected_sha256=digest, expected_size_bytes=len(payload), max_bytes=1024,
        force_linked_snapshot=True, operation=mutate_original))
    path.write_bytes(payload)

    def mutate_snapshot(snapshot):
        os.chmod(snapshot, 0o600)
        Path(snapshot).write_bytes(payload + b"x")
        return b"parsed"
    expect("SNAPSHOT_DESCRIPTOR_METADATA_CHANGED_DURING_PARSE", lambda: mod.guarded_immutable_snapshot_call(
        path, expected_sha256=digest, expected_size_bytes=len(payload), max_bytes=1024,
        force_linked_snapshot=True, operation=mutate_snapshot))

    empty = path.with_name(path.name + ".empty"); empty.write_bytes(b"")
    expect("XML_SOURCE_EMPTY", lambda: mod.guarded_immutable_snapshot_call(
        empty, expected_sha256=hashlib.sha256(b"").hexdigest(), expected_size_bytes=1, operation=lambda p: None))
    empty.unlink()

    link = path.with_name(path.name + ".link")
    try:
        link.symlink_to(path)
        expect("DESCRIPTOR_OPEN_FAILED", lambda: mod.guarded_immutable_snapshot_call(
            link, expected_sha256=digest, expected_size_bytes=len(payload), operation=lambda p: None))
    finally:
        link.unlink(missing_ok=True)

    ok(mod._normalise_expected(digest.upper()) == digest)
    ok(mod._positive("x", 1) == 1)
    ok(mod._DEFAULT_MAX_BYTES == 256 * 1024 * 1024)
    print(f"PARCEL_LABEL_2_BOUNDED_SNAPSHOT_HELPER_TESTS={checks}/{checks}")
finally:
    path.unlink(missing_ok=True)
