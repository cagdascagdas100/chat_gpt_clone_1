import importlib.util, json, sys, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
MODULE_PATH = Path(__file__).with_name("official_publication_diff_monitor_v1.py")
spec = importlib.util.spec_from_file_location("diffmon", MODULE_PATH); monitor = importlib.util.module_from_spec(spec); assert spec.loader is not None; sys.modules[spec.name] = monitor; spec.loader.exec_module(monitor)
class Tests(unittest.TestCase):
    def test_https_allowlist(self):
        self.assertTrue(monitor.url_allowed("https://www.ons.gov.uk/x")); self.assertFalse(monitor.url_allowed("http://www.ons.gov.uk/x")); self.assertFalse(monitor.url_allowed("https://evil.example/x"))
    def test_canonical_url(self): self.assertEqual(monitor.canonical_url("https://www.ons.gov.uk/a", "/x?utm_source=a&keep=1#frag"), "https://www.ons.gov.uk/x?keep=1")
    def test_normalize(self):
        got=monitor.normalize_html('<script>x</script><style>y</style><p nonce="abc"> A 1770000000000 </p>'); self.assertNotIn("1770000000000", got); self.assertIn("<epoch>", got)
    def test_ons_pending(self): self.assertFalse(monitor.publication_state("ONS", monitor.EXPECTED_ONS_TITLE, "<p>Released:</p><p>This release is not yet published</p>")[1])
    def test_ons_requires_both(self): self.assertFalse(monitor.publication_state("ONS", monitor.EXPECTED_ONS_TITLE, f"<title>{monitor.EXPECTED_ONS_TITLE}</title><p>Released:</p><h2>Publications</h2>")[1])
    def test_ons_published(self): self.assertTrue(monitor.publication_state("ONS", monitor.EXPECTED_ONS_TITLE, f"<title>{monitor.EXPECTED_ONS_TITLE}</title><p>Released:</p><h2>Publications</h2><h2>Data</h2>")[1])
    def test_ho_announcement(self): self.assertFalse(monitor.publication_state("HOME_OFFICE", monitor.EXPECTED_HO_TITLE, f"<title>{monitor.EXPECTED_HO_TITLE}</title><p>Official statistics announcement</p><p>Published: x</p>")[1])
    def test_ho_published(self): self.assertTrue(monitor.publication_state("HOME_OFFICE", monitor.EXPECTED_HO_TITLE, f"<title>{monitor.EXPECTED_HO_TITLE}</title><p>Published: x</p><h2>Documents</h2>")[1])
    def test_parse_hashes(self):
        page=monitor.parse_page("ONS", monitor.ONS_URL, monitor.ONS_URL, 200, {"content-type":"text/html"}, b'<title>T</title><a href="/x?utm_source=a">X</a><a href="/x">X</a>'); self.assertEqual(len(page.links),1); self.assertEqual(len(page.raw_sha256),64)
    def test_reject_non_html(self):
        with self.assertRaises(ValueError): monitor.parse_page("ONS", monitor.ONS_URL, monitor.ONS_URL, 200, {"content-type":"application/json"}, b"{}")
    def test_transition(self):
        cur=monitor.PageSnapshot("ONS","u","u",200,"text/html",1,"a","b","t","PUBLISHED",True,["https://www.ons.gov.uk/new"]); diff=monitor.compare_page(cur,{"published":False,"normalized_sha256":"a","links":[]}); self.assertTrue(diff["publication_transition"]); self.assertEqual(len(diff["added_links"]),1)
    def test_regression(self):
        cur=monitor.PageSnapshot("ONS","u","u",200,"text/html",1,"a","b","t","UNKNOWN",False,[]); self.assertTrue(monitor.compare_page(cur,{"published":True,"normalized_sha256":"b","links":[]})["publication_regression"])
    def test_previous_schema(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"x"; p.write_text("[]")
            with self.assertRaises(ValueError): monitor.load_previous(p)
    def test_collect_pending(self):
        ons=(200,monitor.ONS_URL,{"content-type":"text/html"},f"<title>{monitor.EXPECTED_ONS_TITLE}</title><p>This release is not yet published</p>".encode()); ho=(200,monitor.HO_URL,{"content-type":"text/html"},f"<title>{monitor.EXPECTED_HO_TITLE}</title><p>Official statistics announcement</p>".encode())
        with patch.object(monitor,"fetch",side_effect=[ons,ho]): result=monitor.collect(10)
        self.assertEqual(result["state"],"NO_PUBLICATION_TRANSITION"); self.assertEqual(result["summary"]["figures_ingested"],0)
    def test_atomic_write(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"x.json"; monitor.atomic_write(p,{"x":1}); self.assertEqual(json.loads(p.read_text()),{"x":1}); self.assertFalse((Path(td)/"x.json.tmp").exists())
if __name__ == "__main__": unittest.main(verbosity=2)
