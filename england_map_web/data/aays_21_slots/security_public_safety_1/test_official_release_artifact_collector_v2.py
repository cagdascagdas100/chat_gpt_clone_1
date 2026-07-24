import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

MODULE_PATH = Path(__file__).with_name('official_release_artifact_collector_v2.py')
spec = importlib.util.spec_from_file_location('collector_v2', MODULE_PATH)
collector = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = collector
spec.loader.exec_module(collector)


class CollectorV2Tests(unittest.TestCase):
    def test_host_allowlist_requires_https(self):
        self.assertTrue(collector.host_allowed('https://www.ons.gov.uk/a'))
        self.assertTrue(collector.host_allowed('https://www.gov.uk/a'))
        self.assertFalse(collector.host_allowed('http://www.ons.gov.uk/a'))
        self.assertFalse(collector.host_allowed('https://evil.example/a'))

    def test_canonicalize_removes_fragment_and_tracking(self):
        value = collector.canonicalize_url('https://WWW.ONS.GOV.UK/a?x=1&utm_source=z#part')
        self.assertEqual(value, 'https://www.ons.gov.uk/a?x=1')

    def test_parse_page_filters_external_and_deduplicates(self):
        html = '''<html><head><title> T </title></head><body>
        <a href="/a.xlsx#x">Appendix</a><a href="/a.xlsx?utm_source=t">Duplicate</a>
        <a href="https://evil.example/x.xlsx">External</a></body></html>'''
        title, text, links = collector.parse_page('https://www.ons.gov.uk/base', html)
        self.assertEqual(title, 'T')
        self.assertIn('Appendix', text)
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0].url, 'https://www.ons.gov.uk/a.xlsx')

    def test_ons_pending_marker_wins(self):
        text = f'{collector.EXPECTED_ONS_TITLE} Released: 23 July 2026 Publications Data This release is not yet published'
        self.assertFalse(collector.ons_release_published('', text))

    def test_ons_published_requires_title_release_and_products(self):
        text = f'{collector.EXPECTED_ONS_TITLE} Released: 23 July 2026 Publications Data'
        self.assertTrue(collector.ons_release_published('', text))
        self.assertFalse(collector.ons_release_published('', f'{collector.EXPECTED_ONS_TITLE} Release date: 23 July 2026'))

    def test_home_office_announcement_is_not_published_product(self):
        text = f'Official statistics announcement {collector.EXPECTED_HO_TITLE} Published 10 February 2026 Release date 23 July 2026'
        self.assertFalse(collector.home_office_release_published(collector.HO_ANNOUNCEMENT, '', text))

    def test_home_office_publication_detection(self):
        url = 'https://www.gov.uk/government/statistics/crime-outcomes-in-england-and-wales-2025-to-2026'
        text = f'{collector.EXPECTED_HO_TITLE} Published 23 July 2026 Documents'
        self.assertTrue(collector.home_office_release_published(url, '', text))

    def test_classification_and_prerelease_exclusion(self):
        self.assertEqual(collector.classify_link(collector.Link('Appendix tables', 'https://www.ons.gov.uk/a.xlsx')), 'ONS_APPENDIX')
        self.assertEqual(collector.classify_link(collector.Link('Pre-release access list', 'https://www.gov.uk/a')), 'EXCLUDED_PRERELEASE')
        self.assertFalse(collector.artifact_candidate(collector.Link('Contact', 'https://www.ons.gov.uk/contact')))

    def test_validate_xlsx_magic(self):
        ok, reason = collector.validate_download('.xlsx', 'application/octet-stream', b'PK\x03\x04xlsx')
        self.assertTrue(ok)
        self.assertEqual(reason, 'PASS_ZIP_CONTAINER')

    def test_validate_xlsx_rejects_wrong_magic(self):
        ok, reason = collector.validate_download('.xlsx', 'application/octet-stream', b'not-a-zip')
        self.assertFalse(ok)
        self.assertEqual(reason, 'REJECT_BAD_ZIP_MAGIC')

    def test_validate_csv_rejects_html(self):
        ok, reason = collector.validate_download('.csv', 'text/csv', b'<!doctype html><title>Error</title>')
        self.assertFalse(ok)
        self.assertEqual(reason, 'REJECT_HTML_MASQUERADE')

    def test_inspect_accepts_official_ons_html_product(self):
        html = f'<html><title>{collector.EXPECTED_ONS_TITLE}</title><h1>{collector.EXPECTED_ONS_TITLE}</h1></html>'.encode()
        link = collector.Link('Crime in England and Wales', 'https://www.ons.gov.uk/publication')
        with patch.object(collector, 'fetch_with_retry', return_value=(200, link.url, {'content-type':'text/html; charset=utf-8'}, html)):
            receipt = collector.inspect_artifact(1, 'ONS', link, 10)
        self.assertTrue(receipt.accepted)
        self.assertEqual(receipt.sha256, hashlib.sha256(html).hexdigest())

    def test_inspect_rejects_html_error_page(self):
        html = b'<!doctype html><html><title>Page not found</title><p>Page not found</p></html>'
        link = collector.Link('Crime in England and Wales', 'https://www.ons.gov.uk/missing')
        with patch.object(collector, 'fetch_with_retry', return_value=(200, link.url, {'content-type':'text/html'}, html)):
            receipt = collector.inspect_artifact(1, 'ONS', link, 10)
        self.assertFalse(receipt.accepted)
        self.assertEqual(receipt.reason, 'REJECT_HTML_ERROR_PAGE')

    def test_collect_pending_has_zero_receipts(self):
        ons = (200, collector.ONS_RELEASE, {'content-type':'text/html; charset=utf-8'}, f'<title>{collector.EXPECTED_ONS_TITLE}</title><p>This release is not yet published</p>'.encode())
        ho = (200, collector.HO_ANNOUNCEMENT, {'content-type':'text/html'}, f'<title>{collector.EXPECTED_HO_TITLE}</title><p>Official statistics announcement</p>'.encode())
        with patch.object(collector, 'fetch_with_retry', side_effect=[ons, ho]):
            result = collector.collect(10, 30)
        self.assertFalse(result['release_published'])
        self.assertEqual(result['summary']['artifacts_inspected'], 0)
        self.assertEqual(result['summary']['artifacts_accepted'], 0)

    def test_collect_source_isolation(self):
        ons_html = f'''<title>{collector.EXPECTED_ONS_TITLE}</title><p>Released: 23 July 2026</p><h2>Publications</h2><h2>Data</h2><a href="/a.xlsx">Appendix</a>'''.encode()
        ho_html = f'<title>{collector.EXPECTED_HO_TITLE}</title><p>Official statistics announcement</p><a href="/b.ods">Crime outcomes data tables</a>'.encode()
        ons = (200, collector.ONS_RELEASE, {'content-type':'text/html'}, ons_html)
        ho = (200, collector.HO_ANNOUNCEMENT, {'content-type':'text/html'}, ho_html)
        receipt = collector.ArtifactReceipt(1, 'ONS', 'ONS_APPENDIX', 'Appendix', 'https://www.ons.gov.uk/a.xlsx', 'https://www.ons.gov.uk/a.xlsx', True, 200, 'application/octet-stream', 5, 'x', '.xlsx', True, 'PASS_ZIP_CONTAINER')
        with patch.object(collector, 'fetch_with_retry', side_effect=[ons, ho]), patch.object(collector, 'inspect_artifact', return_value=receipt) as inspect:
            result = collector.collect(10, 30)
        self.assertTrue(result['release_published'])
        self.assertEqual(result['published_by_source'], {'ONS': True, 'HOME_OFFICE': False})
        self.assertEqual(inspect.call_count, 1)
        self.assertEqual(result['artifact_receipts'][0]['source'], 'ONS')

    def test_main_writes_json_atomically(self):
        fake = {'summary': {'artifacts_inspected': 0}, 'final_ready': False}
        with tempfile.TemporaryDirectory() as td, patch.object(collector, 'collect', return_value=fake):
            out = Path(td) / 'out.json'
            rc = collector.main(['--output', str(out)])
            self.assertEqual(rc, 0)
            self.assertFalse(json.loads(out.read_text())['final_ready'])
            self.assertEqual(list(Path(td).glob('*.tmp')), [])


if __name__ == '__main__':
    unittest.main(verbosity=2)
