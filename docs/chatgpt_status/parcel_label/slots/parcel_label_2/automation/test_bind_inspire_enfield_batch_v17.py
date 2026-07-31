from __future__ import annotations

import importlib.util
import tempfile
import textwrap
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent


class WrapperTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        for name in ("official_hmlr_transport_v3.py", "bind_inspire_enfield_batch_v17.py"):
            (root / name).write_text((HERE / name).read_text(encoding="utf-8"), encoding="utf-8")
        fake = '''
from pathlib import Path
import http.cookiejar
import urllib.request
class Pool:
    def __init__(self): self.cleaned = 0
    def cleanup(self): self.cleaned += 1
class Base:
    def __init__(self):
        self.REPO = Path(__file__).parent
        self.RESULT = self.REPO / "result.json"
        self.RECON = self.REPO / "recon.json"
        self.WEB = self.REPO / "old.json"
        self.TASK_VERSION = "old"
        self.fetch = None
        self.write = None
        self.main_result = 7
    def main(self): return self.main_result
base = Base()
_POOL = Pool()
_INDEX_COOKIE_JAR = http.cookiejar.CookieJar()
_BINARY_COOKIE_JAR = http.cookiejar.CookieJar()
class Redirect(urllib.request.HTTPRedirectHandler): pass
_INDEX_REDIRECT_HANDLER = Redirect()
_BINARY_REDIRECT_HANDLER = Redirect()
_INDEX_OPENER = object()
_BINARY_OPENER = object()
def fetch(*args): return args
base.fetch = fetch
def _original_write(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(str(payload), encoding="utf-8")
'''
        (root / "bind_inspire_enfield_batch_v16.py").write_text(textwrap.dedent(fake), encoding="utf-8")
        spec = importlib.util.spec_from_file_location("wrapper_v17", root / "bind_inspire_enfield_batch_v17.py")
        assert spec and spec.loader
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)
        self.root = root

    def tearDown(self):
        self.temp.cleanup()

    def test_task_version(self):
        self.assertEqual(self.module.base.TASK_VERSION, "7.6-public-dns-pinning-and-no-proxy-batch")

    def test_exact_output_is_wave25(self):
        self.assertTrue(str(self.module.EXACT_WEB).endswith("progress_wave25_exact_result_latest.json"))

    def test_base_fetch_preserved(self):
        self.assertIs(self.module.base.fetch, self.module.previous.fetch)

    def test_index_and_binary_openers_are_separate(self):
        self.assertIsNot(self.module._INDEX_OPENER, self.module._BINARY_OPENER)

    def test_cookie_jars_preserved_and_separate(self):
        self.assertIs(self.module._INDEX_COOKIE_JAR, self.module.previous._INDEX_COOKIE_JAR)
        self.assertIs(self.module._BINARY_COOKIE_JAR, self.module.previous._BINARY_COOKIE_JAR)
        self.assertIsNot(self.module._INDEX_COOKIE_JAR, self.module._BINARY_COOKIE_JAR)

    def test_previous_openers_rebound(self):
        self.assertIs(self.module.previous._INDEX_OPENER, self.module._INDEX_OPENER)
        self.assertIs(self.module.previous._BINARY_OPENER, self.module._BINARY_OPENER)

    def test_proxy_handlers_are_empty(self):
        self.assertEqual(self.module._INDEX_PROXY_HANDLER.proxies, {})
        self.assertEqual(self.module._BINARY_PROXY_HANDLER.proxies, {})

    def test_https_handlers_use_public_dns(self):
        self.assertIsInstance(self.module._INDEX_HTTPS_HANDLER, self.module.transport.PublicDNSHTTPSHandler)
        self.assertIsInstance(self.module._BINARY_HTTPS_HANDLER, self.module.transport.PublicDNSHTTPSHandler)

    def test_write_allows_three_exact_paths(self):
        for path in (self.module.base.RESULT, self.module.base.RECON, self.module.EXACT_WEB):
            self.module.write(path, {"ok": True})
            self.assertTrue(path.exists())

    def test_write_rejects_old_web_path(self):
        with self.assertRaisesRegex(RuntimeError, "WRITE_PATH_NOT_ALLOWED"):
            self.module.write(self.root / "old.json", {})

    def test_main_returns_base_result_and_cleans_pool(self):
        self.assertEqual(self.module.main(), 7)
        self.assertEqual(self.module._POOL.cleaned, 1)

    def test_main_cleans_pool_on_error(self):
        def fail():
            raise ValueError("boom")
        self.module.base.main = fail
        with self.assertRaisesRegex(ValueError, "boom"):
            self.module.main()
        self.assertEqual(self.module._POOL.cleaned, 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
