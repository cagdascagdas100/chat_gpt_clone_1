from __future__ import annotations

import binascii
import importlib.util
import stat
import tempfile
import zipfile
from pathlib import Path

HERE = Path(__file__).parent
spec = importlib.util.spec_from_file_location("zipv2", HERE / "secure_zip_payload_v2.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
base_spec = importlib.util.spec_from_file_location("streamv1", HERE / "stream_inspire_payload_v1.py")
base = importlib.util.module_from_spec(base_spec)
base_spec.loader.exec_module(base)
checks = 0


def ok(value):
    global checks
    assert value
    checks += 1


def expect(fragment, fn):
    global checks
    try:
        fn()
    except RuntimeError as exc:
        assert fragment in str(exc), exc
    else:
        raise AssertionError(fragment)
    checks += 1


def info(name="data.gml"):
    z = zipfile.ZipInfo(name)
    z.compress_type = zipfile.ZIP_DEFLATED
    z.file_size = 100
    z.compress_size = 50
    z.CRC = 1
    z.header_offset = 1
    return z


ok(zipfile.ZIP_DEFLATED in mod._allowed_compression_methods())
expect("NAME_EMPTY", lambda: mod._normalise_name(""))
expect("CONTROL_CHARACTER", lambda: mod._normalise_name("x\n.gml"))
expect("PATH_UNSAFE", lambda: mod._normalise_name("../x.gml"))
expect("NAME_LIMIT", lambda: mod._normalise_name("a" * 1025 + ".gml"))
ok(mod._normalise_name("folder\\x.gml") == "folder/x.gml")

z = info(); z.flag_bits = 1
expect("ENCRYPTED", lambda: mod.validate_archive_members([z], archive_size=1000, max_zip_members=10, max_gml_bytes=1000, max_zip_ratio=250))
z = info(); z.compress_type = 99
expect("UNSUPPORTED", lambda: mod.validate_archive_members([z], archive_size=1000, max_zip_members=10, max_gml_bytes=1000, max_zip_ratio=250))
z = info(); z.reserved = 1
expect("RESERVED", lambda: mod.validate_archive_members([z], archive_size=1000, max_zip_members=10, max_gml_bytes=1000, max_zip_ratio=250))
z = info(); z.volume = 1
expect("MULTIDISK", lambda: mod.validate_archive_members([z], archive_size=1000, max_zip_members=10, max_gml_bytes=1000, max_zip_ratio=250))
z = info(); z.header_offset = 1000
expect("HEADER_OFFSET", lambda: mod.validate_archive_members([z], archive_size=1000, max_zip_members=10, max_gml_bytes=1000, max_zip_ratio=250))
z = info(); z.create_system = 3; z.external_attr = (stat.S_IFLNK | 0o777) << 16
expect("NOT_REGULAR", lambda: mod.validate_archive_members([z], archive_size=1000, max_zip_members=10, max_gml_bytes=1000, max_zip_ratio=250))
z1, z2 = info("A.gml"), info("a.GML")
expect("DUPLICATE", lambda: mod.validate_archive_members([z1, z2], archive_size=1000, max_zip_members=10, max_gml_bytes=1000, max_zip_ratio=250))
expect("MEMBER_COUNT", lambda: mod.validate_archive_members([info(str(i) + ".txt") for i in range(3)], archive_size=1000, max_zip_members=2, max_gml_bytes=1000, max_zip_ratio=250))
expect("GML_MEMBER_COUNT:0", lambda: mod.validate_archive_members([info("x.txt")], archive_size=1000, max_zip_members=10, max_gml_bytes=1000, max_zip_ratio=250))
z = info(); z.file_size = 0; z.compress_size = 1
expect("MEMBER_EMPTY", lambda: mod.validate_archive_members([z], archive_size=1000, max_zip_members=10, max_gml_bytes=1000, max_zip_ratio=250))
z = info(); z.file_size = 2000; z.compress_size = 100
expect("SIZE_LIMIT", lambda: mod.validate_archive_members([z], archive_size=1000, max_zip_members=10, max_gml_bytes=1000, max_zip_ratio=250))
z = info(); z.file_size = 1000; z.compress_size = 1
expect("RATIO_EXCEEDED", lambda: mod.validate_archive_members([z], archive_size=1000, max_zip_members=10, max_gml_bytes=2000, max_zip_ratio=250))


class Pool:
    def __init__(self):
        self.items = []

    def map_file(self, path, digest):
        data = Path(path).read_bytes()
        self.items.append((Path(path), digest, data))
        return data


pool = Pool()
with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as handle:
    zip_path = Path(handle.name)
try:
    payload = b"<gml:FeatureCollection xmlns:gml='http://www.opengis.net/gml'><PREDEFINED/></gml:FeatureCollection>"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("folder/data.gml", payload)
    fallback_called = []
    result, url = mod.normalise_download_file(
        zip_path,
        final_url="https://example.test/file.zip",
        media_type="application/zip",
        pool=pool,
        base=base,
        fallback=lambda *args, **kwargs: fallback_called.append(1),
    )
    ok(result == payload)
    ok(url.endswith("#folder/data.gml"))
    ok(not fallback_called)
    ok(pool.items[0][1] == __import__("hashlib").sha256(payload).hexdigest())
    for path, _, _ in pool.items:
        path.unlink(missing_ok=True)
finally:
    zip_path.unlink(missing_ok=True)

with tempfile.NamedTemporaryFile(suffix=".gml", delete=False) as handle:
    handle.write(b'<gml:FeatureCollection xmlns:gml="http://www.opengis.net/gml"/>')
    direct = Path(handle.name)
try:
    calls = []
    output = mod.normalise_download_file(
        direct,
        final_url="https://example.test/x.gml",
        media_type="application/gml+xml",
        pool=pool,
        base=base,
        fallback=lambda *args, **kwargs: (calls.append(kwargs) or (b"direct", "url")),
    )
    ok(output == (b"direct", "url"))
    ok(len(calls) == 1)
finally:
    direct.unlink(missing_ok=True)


class Source:
    def __init__(self, parts):
        self.parts = list(parts)

    def read(self, _):
        return self.parts.pop(0) if self.parts else b""


class Destination:
    def __init__(self):
        self.data = b""

    def write(self, data):
        self.data += data

    def flush(self):
        pass


z = info(); z.file_size = 3; z.CRC = binascii.crc32(b"abc") & 0xFFFFFFFF
ok(mod._copy_verified_member(Source([b"abc"]), Destination(), info=z, base=base, limit=10)[0] == __import__("hashlib").sha256(b"abc").hexdigest())
z = info(); z.file_size = 4; z.CRC = binascii.crc32(b"abc") & 0xFFFFFFFF
expect("SIZE_MISMATCH", lambda: mod._copy_verified_member(Source([b"abc"]), Destination(), info=z, base=base, limit=10))
z = info(); z.file_size = 3; z.CRC = 0
expect("CRC_MISMATCH", lambda: mod._copy_verified_member(Source([b"abc"]), Destination(), info=z, base=base, limit=10))

print(f"PARCEL_LABEL_2_SECURE_ZIP_TESTS={checks}/{checks}")
print("FINAL_READY=false")
