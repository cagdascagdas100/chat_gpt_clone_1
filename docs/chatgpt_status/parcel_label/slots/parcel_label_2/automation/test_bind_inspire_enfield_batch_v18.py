from __future__ import annotations

import importlib.util
import io
import tempfile
import textwrap
import unittest
from email.message import Message
from pathlib import Path

HERE = Path(__file__).resolve().parent


class FakeResponse:
    def __init__(self, body: bytes, *, url: str, status=200, headers=None):
        self._stream = io.BytesIO(body)
        self._url = url
        self.status = status
        self.headers = headers if headers is not None else Message()

    def read(self, size=-1):
        return self._stream.read(size)

    def geturl(self):
        return self._url

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class FakeOpener:
    def __init__(self, response):
        self.response = response
        self.requests = []

    def open(self, request, timeout=None):
        self.requests.append((request, timeout))
        return self.response


class WrapperTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        for name in ("official_hmlr_response_v1.py", "bind_inspire_enfield_batch_v18.py"):
            (root / name).write_text((HERE / name).read_text(encoding="utf-8"), encoding="utf-8")
        fake = '''
from pathlib import Path
import tempfile
class Pool:
    def __init__(self): self.cleaned=0; self.hashes={}
    def cleanup(self): self.cleaned += 1
class Base:
    def __init__(self):
        self.REPO=Path(__file__).parent; self.RESULT=self.REPO/'result.json'; self.RECON=self.REPO/'recon.json'; self.WEB=self.REPO/'old.json'; self.TASK_VERSION='old'; self.main_result=9
    def main(self): return self.main_result
base=Base(); _POOL=Pool(); _PRIMARY_HOST='use-land-property-data.service.gov.uk'; _MAX_INDEX_BYTES=64; _MAX_DOWNLOAD_BYTES=128; _MAX_GML_BYTES=128; _MAX_ZIP_MEMBERS=8; _MAX_ZIP_RATIO=20.0; _DNS_PREFLIGHT=lambda: None
class Streaming:
    @staticmethod
    def stream_response_to_file(response, limit):
        h=tempfile.NamedTemporaryFile(delete=False); h.write(response.read()); h.close(); return Path(h.name)
    @staticmethod
    def normalise_download_file(path, **kwargs): return path.read_bytes(), kwargs['final_url']
streaming=Streaming()
class Policy:
    @staticmethod
    def validate_official_hmlr_url(url, **kwargs): return url
transport=Policy()
class Opener: pass
_INDEX_OPENER=Opener(); _BINARY_OPENER=Opener()
def _original_write(path,payload): path.parent.mkdir(parents=True,exist_ok=True); path.write_text(str(payload),encoding='utf-8')
'''
        (root / "bind_inspire_enfield_batch_v17.py").write_text(
            textwrap.dedent(fake), encoding="utf-8"
        )
        spec = importlib.util.spec_from_file_location(
            "wrapper_v18", root / "bind_inspire_enfield_batch_v18.py"
        )
        assert spec and spec.loader
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)
        self.root = root

    def tearDown(self):
        self.temp.cleanup()

    def _headers(self, **items):
        message = Message()
        for key, value in items.items():
            message[key.replace("_", "-")] = value
        return message

    def test_task_version_and_exact_output(self):
        self.assertEqual(
            self.module.base.TASK_VERSION,
            "7.7-http-response-integrity-and-complete-body-batch",
        )
        self.assertTrue(
            str(self.module.EXACT_WEB).endswith(
                "progress_wave26_exact_result_latest.json"
            )
        )

    def test_fetch_replaces_base_fetch(self):
        self.assertIs(self.module.base.fetch, self.module.fetch)

    def test_index_uses_index_opener_and_identity_encoding(self):
        response = FakeResponse(
            b"<html>ok</html>",
            url="https://use-land-property-data.service.gov.uk/datasets/inspire/download",
            headers=self._headers(Content_Length="15", Content_Type="text/html"),
        )
        opener = FakeOpener(response)
        self.module._INDEX_OPENER = opener
        payload, url = self.module.fetch(response.geturl(), 5, 1)
        self.assertEqual(payload, b"<html>ok</html>")
        self.assertEqual(len(opener.requests), 1)
        self.assertEqual(opener.requests[0][0].get_header("Accept-encoding"), "identity")

    def test_binary_uses_binary_opener_and_complete_length(self):
        body = b"<FeatureCollection xmlns:gml='http://www.opengis.net/gml'/>"
        response = FakeResponse(
            body,
            url="https://inspire.landregistry.gov.uk/enfield.gml",
            headers=self._headers(
                Content_Length=str(len(body)), Content_Type="application/gml+xml"
            ),
        )
        opener = FakeOpener(response)
        self.module._BINARY_OPENER = opener
        payload, url = self.module.fetch(response.geturl(), 5, 1)
        self.assertEqual(payload, body)
        self.assertEqual(url, response.geturl())
        self.assertEqual(len(opener.requests), 1)

    def test_partial_status_rejected(self):
        response = FakeResponse(
            b"abc",
            url="https://inspire.landregistry.gov.uk/enfield.gml",
            status=206,
            headers=self._headers(Content_Length="3"),
        )
        self.module._BINARY_OPENER = FakeOpener(response)
        with self.assertRaisesRegex(RuntimeError, "STATUS_NOT_200:206"):
            self.module.fetch(response.geturl(), 5, 1)

    def test_truncated_binary_rejected(self):
        response = FakeResponse(
            b"abc",
            url="https://inspire.landregistry.gov.uk/enfield.gml",
            headers=self._headers(Content_Length="4"),
        )
        self.module._BINARY_OPENER = FakeOpener(response)
        with self.assertRaisesRegex(RuntimeError, "BODY_LENGTH_MISMATCH:3:4"):
            self.module.fetch(response.geturl(), 5, 1)

    def test_compressed_response_rejected(self):
        response = FakeResponse(
            b"abc",
            url="https://inspire.landregistry.gov.uk/enfield.gml",
            headers=self._headers(Content_Encoding="gzip"),
        )
        self.module._BINARY_OPENER = FakeOpener(response)
        with self.assertRaisesRegex(RuntimeError, "CONTENT_ENCODING_UNSUPPORTED"):
            self.module.fetch(response.geturl(), 5, 1)

    def test_content_range_rejected(self):
        response = FakeResponse(
            b"abc",
            url="https://inspire.landregistry.gov.uk/enfield.gml",
            headers=self._headers(Content_Range="bytes 0-2/10"),
        )
        self.module._BINARY_OPENER = FakeOpener(response)
        with self.assertRaisesRegex(RuntimeError, "CONTENT_RANGE_FORBIDDEN"):
            self.module.fetch(response.geturl(), 5, 1)

    def test_index_wrong_media_rejected(self):
        response = FakeResponse(
            b"abc",
            url="https://use-land-property-data.service.gov.uk/datasets/inspire/download",
            headers=self._headers(
                Content_Length="3", Content_Type="application/octet-stream"
            ),
        )
        self.module._INDEX_OPENER = FakeOpener(response)
        with self.assertRaisesRegex(RuntimeError, "DOWNLOAD_INDEX_UNEXPECTED_MEDIA_TYPE"):
            self.module.fetch(response.geturl(), 5, 1)

    def test_write_allows_exact_paths(self):
        for path in (self.module.base.RESULT, self.module.base.RECON, self.module.EXACT_WEB):
            self.module.write(path, {"ok": True})
            self.assertTrue(path.exists())

    def test_write_rejects_old_web(self):
        with self.assertRaisesRegex(RuntimeError, "WRITE_PATH_NOT_ALLOWED"):
            self.module.write(self.root / "old.json", {})

    def test_main_cleans_pool_success(self):
        self.assertEqual(self.module.main(), 9)
        self.assertEqual(self.module._POOL.cleaned, 1)

    def test_main_cleans_pool_error(self):
        def fail():
            raise ValueError("boom")

        self.module.base.main = fail
        with self.assertRaisesRegex(ValueError, "boom"):
            self.module.main()
        self.assertEqual(self.module._POOL.cleaned, 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
