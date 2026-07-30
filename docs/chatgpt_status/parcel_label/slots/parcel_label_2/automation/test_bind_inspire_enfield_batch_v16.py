from __future__ import annotations

import importlib.util
import pathlib
import shutil
import tempfile
import unittest

ROOT = pathlib.Path(__file__).parent
V16 = ROOT / "bind_inspire_enfield_batch_v16.py"
TRANSPORT = ROOT / "official_hmlr_transport_v2.py"

STUB_V15 = r'''
from __future__ import annotations
import pathlib, tempfile
class B: pass
base=B(); base.REPO=pathlib.Path(tempfile.gettempdir()); base.RESULT=base.REPO/'r.json'; base.RECON=base.REPO/'c.json'; base.WEB=base.REPO/'old.json'; base.DOWNLOAD='https://use-land-property-data.service.gov.uk/datasets/inspire/download'; base.TASK_VERSION='old'; base.main=lambda: 7; base.discover=lambda p,u:'x'
class Streaming:
    def stream_response_to_file(self, response, limit):
        p=pathlib.Path(tempfile.mkstemp(suffix='.gml')[1]); p.write_bytes(response.read()); return p
    def normalise_download_file(self, raw_path, **kwargs):
        return raw_path.read_bytes(), kwargs['final_url']
streaming=Streaming()
_original_write=lambda p,x: None
class Pool:
    def __init__(self): self.cleaned=False
    def cleanup(self): self.cleaned=True
_POOL=Pool()
_PRIMARY_HOST='use-land-property-data.service.gov.uk'
_MAX_INDEX_BYTES=1024
_MAX_DOWNLOAD_BYTES=4096
_MAX_GML_BYTES=4096
_MAX_ZIP_MEMBERS=8
_MAX_ZIP_RATIO=20.0
_DNS_PREFLIGHT=None
'''


class Headers:
    def __init__(self, media="text/html"): self.media=media
    def get_content_type(self): return self.media


class Response:
    def __init__(self, data: bytes, url: str, media="text/html"):
        self.data=data; self.url=url; self.headers=Headers(media); self.pos=0
    def read(self, n=-1):
        if n < 0: n=len(self.data)-self.pos
        out=self.data[self.pos:self.pos+n]; self.pos += len(out); return out
    def geturl(self): return self.url
    def __enter__(self): return self
    def __exit__(self,*args): return False


class Opener:
    def __init__(self, response): self.response=response; self.calls=0
    def open(self, request, timeout): self.calls += 1; return self.response


class WrapperTests(unittest.TestCase):
    def setUp(self):
        self.tmp=pathlib.Path(tempfile.mkdtemp())
        shutil.copy2(V16, self.tmp/V16.name)
        shutil.copy2(TRANSPORT, self.tmp/TRANSPORT.name)
        (self.tmp/"bind_inspire_enfield_batch_v15.py").write_text(STUB_V15)
        spec=importlib.util.spec_from_file_location("v16", self.tmp/V16.name)
        assert spec and spec.loader
        self.m=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.m)
    def tearDown(self): shutil.rmtree(self.tmp, ignore_errors=True)

    def test_version(self): self.assertEqual(self.m.base.TASK_VERSION, "7.5-separate-index-and-binary-redirect-policy-batch")
    def test_wave_path(self): self.assertTrue(str(self.m.EXACT_WEB).endswith("progress_wave24_exact_result_latest.json"))
    def test_index_policy(self): self.assertTrue(self.m._INDEX_REDIRECT_HANDLER.require_primary)
    def test_binary_policy(self): self.assertFalse(self.m._BINARY_REDIRECT_HANDLER.require_primary)
    def test_cookie_jars_separate(self): self.assertIsNot(self.m._INDEX_COOKIE_JAR, self.m._BINARY_COOKIE_JAR)
    def test_openers_separate(self): self.assertIsNot(self.m._INDEX_OPENER, self.m._BINARY_OPENER)

    def test_index_fetch_uses_index_opener(self):
        index=Opener(Response(b"<html>ok</html>", "https://use-land-property-data.service.gov.uk/datasets/inspire/download"))
        binary=Opener(Response(b"<gml/>", "https://inspire.landregistry.gov.uk/x.gml", "application/xml"))
        self.m._INDEX_OPENER=index; self.m._BINARY_OPENER=binary
        data,_=self.m.fetch("https://use-land-property-data.service.gov.uk/datasets/inspire/download",1,1)
        self.assertEqual(data,b"<html>ok</html>"); self.assertEqual(index.calls,1); self.assertEqual(binary.calls,0)

    def test_binary_fetch_uses_binary_opener(self):
        index=Opener(Response(b"<html>ok</html>", "https://use-land-property-data.service.gov.uk/datasets/inspire/download"))
        binary=Opener(Response(b"<FeatureCollection xmlns:gml='http://www.opengis.net/gml'/>", "https://inspire.landregistry.gov.uk/x.gml", "application/xml"))
        self.m._INDEX_OPENER=index; self.m._BINARY_OPENER=binary
        data,_=self.m.fetch("https://use-land-property-data.service.gov.uk/download/x",1,1)
        self.assertIn(b"FeatureCollection",data); self.assertEqual(index.calls,0); self.assertEqual(binary.calls,1)

    def test_index_final_cross_origin_rejected(self):
        self.m._INDEX_OPENER=Opener(Response(b"<html/>","https://inspire.landregistry.gov.uk/index"))
        with self.assertRaisesRegex(RuntimeError,"FETCH_FAILED.*INDEX_REDIRECT_CROSS_ORIGIN"):
            self.m.fetch("https://use-land-property-data.service.gov.uk/datasets/inspire/download",1,1)

    def test_binary_untrusted_final_rejected(self):
        self.m._BINARY_OPENER=Opener(Response(b"<FeatureCollection/>","https://example.com/x.gml","application/xml"))
        with self.assertRaisesRegex(RuntimeError,"FETCH_FAILED.*UNTRUSTED_HOST"):
            self.m.fetch("https://use-land-property-data.service.gov.uk/download/x",1,1)

    def test_write_allowlist(self):
        with self.assertRaisesRegex(RuntimeError,"WRITE_PATH_NOT_ALLOWED"):
            self.m.write(self.tmp/"bad.json",{})

    def test_main_cleanup(self):
        self.assertFalse(self.m._POOL.cleaned)
        self.assertEqual(self.m.main(),7)
        self.assertTrue(self.m._POOL.cleaned)


if __name__ == "__main__":
    unittest.main(verbosity=2)
