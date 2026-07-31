from __future__ import annotations

import hashlib
import importlib.util
import os
import tempfile
from pathlib import Path

HERE = Path(__file__).parent
spec = importlib.util.spec_from_file_location("stable_v2", HERE / "stable_xml_source_v2.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
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

with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    source = root / "source.gml"
    payload = b"<root><x>safe</x></root>"
    source.write_bytes(payload)
    digest = hashlib.sha256(payload).hexdigest()

    (data, evidence) = mod.guarded_descriptor_call(
        source,
        expected_sha256=digest,
        operation=lambda path: Path(path).read_bytes(),
    )
    ok(data == payload)
    ok(evidence["xml_descriptor_pinning_validation_passed"] is True)
    ok(evidence["xml_parser_source_bound_to_open_descriptor"] is True)
    ok(evidence["xml_source_observed_sha256"] == digest)
    ok(evidence["xml_parser_source_mode"] in {"PROC_DESCRIPTOR_PATH", "PRIVATE_SECURE_COPY"})

    (private_data, private_evidence) = mod.guarded_descriptor_call(
        source,
        expected_sha256=digest.upper(),
        operation=lambda path: Path(path).read_bytes(),
        force_private_copy=True,
    )
    ok(private_data == payload)
    ok(private_evidence["xml_parser_source_mode"] == "PRIVATE_SECURE_COPY")

    expect("XML_SOURCE_SHA256_MISMATCH", lambda: mod.guarded_descriptor_call(
        source, expected_sha256="0" * 64, operation=lambda path: None
    ))
    expect("XML_EXPECTED_SHA256_INVALID", lambda: mod.guarded_descriptor_call(
        source, expected_sha256="x", operation=lambda path: None
    ))
    expect("chunk_size", lambda: mod.guarded_descriptor_call(
        source, expected_sha256=digest, operation=lambda path: None, chunk_size=0
    ))

    empty = root / "empty.gml"; empty.write_bytes(b"")
    expect("XML_SOURCE_EMPTY", lambda: mod.guarded_descriptor_call(
        empty, expected_sha256=hashlib.sha256(b"").hexdigest(), operation=lambda path: None
    ))

    hard = root / "hard.gml"; os.link(source, hard)
    expect("XML_SOURCE_LINK_COUNT_NOT_ONE", lambda: mod.guarded_descriptor_call(
        source, expected_sha256=digest, operation=lambda path: None
    ))
    hard.unlink()

    if hasattr(os, "symlink"):
        symlink = root / "link.gml"; symlink.symlink_to(source)
        expect("XML_SOURCE_DESCRIPTOR_OPEN_FAILED", lambda: mod.guarded_descriptor_call(
            symlink, expected_sha256=digest, operation=lambda path: None
        ))

    def mutate_inode(stable_path):
        with source.open("ab") as handle:
            handle.write(b"x")
        return Path(stable_path).read_bytes()
    expect("XML_SOURCE_DESCRIPTOR_METADATA_CHANGED_DURING_PARSE", lambda: mod.guarded_descriptor_call(
        source, expected_sha256=digest, operation=mutate_inode
    ))
    source.write_bytes(payload)

    def swap_path(stable_path):
        backup = root / "backup.gml"
        source.rename(backup)
        source.write_bytes(b"evil")
        observed = Path(stable_path).read_bytes()
        source.unlink()
        backup.rename(source)
        assert observed == payload
        return observed
    swapped_data, swapped_evidence = mod.guarded_descriptor_call(
        source, expected_sha256=digest, operation=swap_path
    )
    ok(swapped_data == payload)
    ok(swapped_evidence["xml_parser_source_bound_to_open_descriptor"] is True)

    ok(mod._normalise_expected(digest.upper()) == digest)
    fd = mod._open_source(source)
    try:
        ok(mod._hash_descriptor(fd, chunk_size=3) == digest)
        ok(os.fstat(fd).st_size == len(payload))
    finally:
        os.close(fd)

print(f"PARCEL_LABEL_2_DESCRIPTOR_PINNING_TESTS={checks}/{checks}")
