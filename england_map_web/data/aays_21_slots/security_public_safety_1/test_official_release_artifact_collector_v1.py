import hashlib
import importlib.util
import json
import tempfile
import unittest
import sys
from pathlib import Path
from unittest.mock import patch

MODULE_PATH = Path(__file__).with_name('official_release_artifact_collector_v1.py')
spec = importlib.util.spec_from_file_location('collector', MODULE_PATH)
collector = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = collector
spec.loader.exec_module(collector)


class CollectorTests(unittest.TestCase):
    def test_host_allowlist(self):
        self.assertTrue(collector.host_allowed('https://www.ons.gov.uk/a'))
        self.assertTrue(collector.host_allowed('https://www.gov.uk/a'))
        self.assertFalse(collector.host_allowed('https://evil.example/a'))

    def test_parse_links_filters_external_and_deduplicates(self):
        html = '''<html><head><title> T </title></head><body>
        <a href="/a.xlsx">Appendix</a><a href="/a.xlsx">Duplicate</a>
        <a href="https://evil.example/x.xlsx">External</a></body></html>'''
        title, links = collector.parse_links('https://www.ons.gov.uk/base', html)
        self.assertEqual(title, 'T')
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0].url, 'https://www.ons.gov.uk/a.xlsx')

    def test_release_pending_marker_wins(self):
        html = '<h1>Released:</h1><p>This release is not yet published</p>'
        self.assertFalse(collector.is_release_published(html))

    def test_release_published_detection(self):
        self.assertTrue(collector.is_release_published('<h2>Publications</h2>'))

    def test_artifact_candidate(self):
        self.assertTrue(collector.artifact_candidate(collector.Link('Appendix tables', 'https://www.ons.gov.uk/a')))
        self.assertTrue(collector.artifact_candidate(collector.Link('file', 'https://www.gov.uk/a.ods')))
        self.assertFalse(collector.artifact_candidate(collector.Link('Contact', 'https://www.ons.gov.uk/contact')))

    def test_inspect_artifact_accepts_raw_spreadsheet(self):
        payload = b'PK\x03\x04xlsx'
        with patch.object(collector, 'fetch', return_value=(200, 'https://www.ons.gov.uk/a.xlsx', {'content-type':'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'}, payload)):
            receipt = collector.inspect_artifact(1, 'ONS', collector.Link('Appendix', 'https://www.ons.gov.uk/a.xlsx'), 10)
        self.assertTrue(receipt.accepted)
        self.assertEqual(receipt.sha256, hashlib.sha256(payload).hexdigest())

    def test_inspect_artifact_rejects_html_masquerade(self):
        payload = b'<!doctype html><title>Error</title>'
        with patch.object(collector, 'fetch', return_value=(200, 'https://www.ons.gov.uk/a', {'content-type':'text/html'}, payload)):
            receipt = collector.inspect_artifact(1, 'ONS', collector.Link('Data', 'https://www.ons.gov.uk/a'), 10)
        self.assertFalse(receipt.accepted)

    def test_collect_pending_has_zero_receipts(self):
        ons = (200, collector.ONS_RELEASE, {'content-type':'text/html; charset=utf-8'}, f'<title>{collector.EXPECTED_TITLE}</title><p>This release is not yet published</p>'.encode())
        ho = (200, collector.HO_ANNOUNCEMENT, {'content-type':'text/html'}, b'<p>Release date: 23 July 2026</p>')
        with patch.object(collector, 'fetch', side_effect=[ons, ho]):
            result = collector.collect(10, 30)
        self.assertFalse(result['release_published'])
        self.assertEqual(result['summary']['artifacts_inspected'], 0)
        self.assertEqual(result['summary']['artifacts_accepted'], 0)
        self.assertFalse(result['summary']['stored_values_modified'])

    def test_main_writes_json(self):
        fake = {'summary': {'artifacts_inspected': 0}, 'final_ready': False}
        with tempfile.TemporaryDirectory() as td, patch.object(collector, 'collect', return_value=fake):
            out = Path(td) / 'out.json'
            rc = collector.main(['--output', str(out)])
            self.assertEqual(rc, 0)
            self.assertEqual(json.loads(out.read_text())['final_ready'], False)


if __name__ == '__main__':
    unittest.main(verbosity=2)
