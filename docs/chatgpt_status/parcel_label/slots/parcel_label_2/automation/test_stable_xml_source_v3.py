from __future__ import annotations

import hashlib
import os
import stat
import tempfile
from pathlib import Path

import stable_xml_source_v3 as module

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


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    data = b"<root><x>safe</x></root>"
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        source = root / "source.gml"
        source.write_bytes(data)
        expected = digest(data)

        seen = {}
        def read_proc(path: Path):
            seen["path"] = path
            seen["exists"] = path.exists()
            return path.read_bytes()
        result, evidence = module.guarded_immutable_snapshot_call(source, expected_sha256=expected, operation=read_proc)
        ok(result == data)
        ok(evidence["xml_parser_uses_private_snapshot"] is True)
        ok(evidence["xml_parser_uses_original_descriptor"] is False)
        ok(evidence["xml_snapshot_observed_sha256"] == expected)
        if evidence["xml_parser_source_mode"] == "UNLINKED_PRIVATE_DESCRIPTOR":
            ok(evidence["xml_snapshot_unlinked_before_parse"] is True)
        else:
            ok(evidence["xml_parser_source_mode"] == "PRIVATE_READ_ONLY_PATH")

        linked_seen = {}
        def read_linked(path: Path):
            linked_seen["mode"] = stat.S_IMODE(os.lstat(path).st_mode)
            linked_seen["parent_mode"] = stat.S_IMODE(os.lstat(path.parent).st_mode)
            return path.read_bytes()
        result, evidence = module.guarded_immutable_snapshot_call(
            source, expected_sha256=expected, operation=read_linked, force_linked_snapshot=True
        )
        ok(result == data)
        ok(evidence["xml_parser_source_mode"] == "PRIVATE_READ_ONLY_PATH")
        ok(linked_seen["mode"] == 0o400)
        ok(linked_seen["parent_mode"] == 0o700)

        expect("XML_EXPECTED_SHA256_INVALID", lambda: module.guarded_immutable_snapshot_call(source, expected_sha256="x", operation=lambda p: None))
        expect("chunk_size must be a positive integer", lambda: module.guarded_immutable_snapshot_call(source, expected_sha256=expected, operation=lambda p: None, chunk_size=0))
        expect("XML_SOURCE_SHA256_MISMATCH", lambda: module.guarded_immutable_snapshot_call(source, expected_sha256="0"*64, operation=lambda p: None))

        empty = root / "empty.gml"; empty.write_bytes(b"")
        expect("XML_SOURCE_EMPTY", lambda: module.guarded_immutable_snapshot_call(empty, expected_sha256=digest(b""), operation=lambda p: None))

        directory = root / "dir"; directory.mkdir()
        expect("XML_SOURCE_NOT_REGULAR_FILE", lambda: module.guarded_immutable_snapshot_call(directory, expected_sha256=expected, operation=lambda p: None))

        link = root / "link.gml"; link.symlink_to(source)
        expect("XML_SOURCE_DESCRIPTOR_OPEN_FAILED", lambda: module.guarded_immutable_snapshot_call(link, expected_sha256=expected, operation=lambda p: None))

        hard = root / "hard.gml"; os.link(source, hard)
        expect("XML_SOURCE_LINK_COUNT_NOT_ONE", lambda: module.guarded_immutable_snapshot_call(source, expected_sha256=expected, operation=lambda p: None))
        hard.unlink()

        captured = {}
        def mutate_original(path: Path):
            captured["bytes"] = path.read_bytes()
            source.write_bytes(b"<root>changed</root>")
            return "done"
        expect("XML_SOURCE_DESCRIPTOR_METADATA_CHANGED_DURING_PARSE", lambda: module.guarded_immutable_snapshot_call(source, expected_sha256=expected, operation=mutate_original))
        ok(captured["bytes"] == data)
        source.write_bytes(data)

        captured = {}
        def replace_original(path: Path):
            captured["bytes"] = path.read_bytes()
            replacement = root / "replacement.gml"
            replacement.write_bytes(data)
            os.replace(replacement, source)
            return "done"
        expect("XML_SOURCE_DESCRIPTOR_METADATA_CHANGED_DURING_PARSE", lambda: module.guarded_immutable_snapshot_call(source, expected_sha256=expected, operation=replace_original))
        ok(captured["bytes"] == data)

        source.write_bytes(data)
        def mutate_snapshot(path: Path):
            os.chmod(path, 0o600)
            path.write_bytes(b"<root>snapshot changed</root>")
            return None
        expect("XML_SNAPSHOT_DESCRIPTOR_METADATA_CHANGED_DURING_PARSE", lambda: module.guarded_immutable_snapshot_call(source, expected_sha256=expected, operation=mutate_snapshot, force_linked_snapshot=True))

        source.write_bytes(data)
        def delete_snapshot(path: Path):
            path.unlink()
            return None
        expect("XML_SNAPSHOT_DESCRIPTOR_METADATA_CHANGED_DURING_PARSE", lambda: module.guarded_immutable_snapshot_call(source, expected_sha256=expected, operation=delete_snapshot, force_linked_snapshot=True))

        source.write_bytes(data)
        operation_error = RuntimeError("OPERATION_FAILED")
        expect("OPERATION_FAILED", lambda: module.guarded_immutable_snapshot_call(source, expected_sha256=expected, operation=lambda p: (_ for _ in ()).throw(operation_error)))

    print(f"PARCEL_LABEL_2_IMMUTABLE_SNAPSHOT_HELPER_TESTS={checks}/{checks}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
