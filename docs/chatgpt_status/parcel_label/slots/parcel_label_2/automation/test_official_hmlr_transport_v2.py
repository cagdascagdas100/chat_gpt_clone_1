from __future__ import annotations

import importlib.util
import pathlib
import unittest

PATH = pathlib.Path(__file__).with_name("official_hmlr_transport_v2.py")
spec = importlib.util.spec_from_file_location("transport_v2", PATH)
assert spec and spec.loader
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

PRIMARY = "use-land-property-data.service.gov.uk"


class TransportV2Tests(unittest.TestCase):
    def assertRejects(self, code: str, fn, *args, **kwargs):
        with self.assertRaisesRegex(RuntimeError, code):
            fn(*args, **kwargs)

    def test_primary_url(self):
        url = f"https://{PRIMARY}/datasets/inspire/download"
        self.assertEqual(m.validate_official_hmlr_url(url, primary_host=PRIMARY, require_primary=True), url)

    def test_binary_landregistry_root(self):
        self.assertTrue(m.validate_official_hmlr_url("https://landregistry.gov.uk/file.gml", primary_host=PRIMARY))

    def test_binary_landregistry_subdomain(self):
        self.assertTrue(m.validate_official_hmlr_url("https://inspire.landregistry.gov.uk/file.gml", primary_host=PRIMARY))

    def test_require_primary_rejects_landregistry(self):
        self.assertRejects("INDEX_REDIRECT_CROSS_ORIGIN", m.validate_official_hmlr_url, "https://inspire.landregistry.gov.uk/file.gml", primary_host=PRIMARY, require_primary=True)

    def test_untrusted_host(self):
        self.assertRejects("UNTRUSTED_HOST", m.validate_official_hmlr_url, "https://example.com/file.gml", primary_host=PRIMARY)

    def test_suffix_confusion(self):
        self.assertRejects("UNTRUSTED_HOST", m.validate_official_hmlr_url, "https://landregistry.gov.uk.example.com/file.gml", primary_host=PRIMARY)

    def test_http(self):
        self.assertRejects("NOT_HTTPS", m.validate_official_hmlr_url, f"http://{PRIMARY}/file.gml", primary_host=PRIMARY)

    def test_port(self):
        self.assertRejects("PORT_NOT_443", m.validate_official_hmlr_url, f"https://{PRIMARY}:444/file.gml", primary_host=PRIMARY)

    def test_userinfo(self):
        self.assertRejects("USERINFO", m.validate_official_hmlr_url, f"https://u:p@{PRIMARY}/file.gml", primary_host=PRIMARY)

    def test_fragment(self):
        self.assertRejects("FRAGMENT", m.validate_official_hmlr_url, f"https://{PRIMARY}/file.gml#x", primary_host=PRIMARY)

    def test_control(self):
        self.assertRejects("CONTROL_CHARACTER", m.validate_official_hmlr_url, f"https://{PRIMARY}/file\ngml", primary_host=PRIMARY)

    def test_trailing_dot(self):
        self.assertRejects("TRAILING_DOT", m.validate_official_hmlr_url, f"https://{PRIMARY}./file.gml", primary_host=PRIMARY)

    def test_ipv4(self):
        self.assertRejects("IP_LITERAL", m.validate_official_hmlr_url, "https://127.0.0.1/file.gml", primary_host=PRIMARY)

    def test_ipv6(self):
        self.assertRejects("IP_LITERAL", m.validate_official_hmlr_url, "https://[::1]/file.gml", primary_host=PRIMARY)

    def test_relative_index_redirect_primary(self):
        got = m.validate_redirect_target(f"https://{PRIMARY}/datasets/inspire/download", "/datasets/inspire/download?x=1", primary_host=PRIMARY, require_primary=True)
        self.assertEqual(got, f"https://{PRIMARY}/datasets/inspire/download?x=1")

    def test_protocol_relative_index_cross_origin_rejected(self):
        self.assertRejects("INDEX_REDIRECT_CROSS_ORIGIN", m.validate_redirect_target, f"https://{PRIMARY}/datasets/inspire/download", "//inspire.landregistry.gov.uk/file.gml", primary_host=PRIMARY, require_primary=True)

    def test_protocol_relative_binary_landregistry_allowed(self):
        got = m.validate_redirect_target(f"https://{PRIMARY}/download/1", "//inspire.landregistry.gov.uk/file.gml", primary_host=PRIMARY, require_primary=False)
        self.assertEqual(got, "https://inspire.landregistry.gov.uk/file.gml")

    def test_binary_http_redirect_rejected(self):
        self.assertRejects("NOT_HTTPS", m.validate_redirect_target, f"https://{PRIMARY}/download/1", "http://inspire.landregistry.gov.uk/file.gml", primary_host=PRIMARY, require_primary=False)

    def test_index_handler_policy(self):
        handler = m.TrustedHMLRRedirectHandler(PRIMARY, require_primary=True)
        self.assertTrue(handler.require_primary)
        self.assertEqual(handler.max_redirections, 5)
        self.assertEqual(handler.max_repeats, 2)

    def test_binary_handler_policy(self):
        self.assertFalse(m.TrustedHMLRRedirectHandler(PRIMARY, require_primary=False).require_primary)

    def test_build_openers_are_separate(self):
        first, first_jar, first_handler = m.build_trusted_opener(PRIMARY, require_primary=True)
        second, second_jar, second_handler = m.build_trusted_opener(PRIMARY, require_primary=False)
        self.assertIsNot(first, second)
        self.assertIsNot(first_jar, second_jar)
        self.assertTrue(first_handler.require_primary)
        self.assertFalse(second_handler.require_primary)


if __name__ == "__main__":
    unittest.main(verbosity=2)
