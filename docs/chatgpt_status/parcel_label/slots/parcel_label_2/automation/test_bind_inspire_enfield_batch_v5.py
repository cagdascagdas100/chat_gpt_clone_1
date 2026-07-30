from __future__ import annotations

import importlib.util
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("bind_inspire_enfield_batch_v5.py")
spec = importlib.util.spec_from_file_location("parcel_label_2_v5", MODULE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("PARCEL_LABEL_2_V5_IMPORT_FAILED")
worker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(worker)

BASE_URL = "https://use-land-property-data.service.gov.uk/datasets/inspire/download"


def expect_error(fragment: str, html: str) -> None:
    try:
        worker.discover(html.encode(), BASE_URL)
    except RuntimeError as exc:
        assert fragment in str(exc), (fragment, exc)
    else:
        raise AssertionError(f"EXPECTED_ERROR_NOT_RAISED:{fragment}")


def main() -> int:
    adjacent = """
    <table>
      <tr><td>London Borough of Ealing</td><td><a href='/files/ealing.gml'>Download .gml</a></td></tr>
      <tr><td>London Borough of Enfield</td><td><a href='/files/enfield.gml'>Download .gml</a></td></tr>
      <tr><td>London Borough of Hackney</td><td><a href='/files/hackney.gml'>Download .gml</a></td></tr>
    </table>
    """
    assert worker.discover(adjacent.encode(), BASE_URL) == "https://use-land-property-data.service.gov.uk/files/enfield.gml"

    whitespace = """
    <table><tr><td> London   Borough\n of Enfield </td><td><a href='current/enfield'>Download .gml</a></td></tr></table>
    """
    assert worker.discover(whitespace.encode(), BASE_URL).endswith("/datasets/inspire/current/enfield")

    ignored = """
    <table><tr><td>London Borough of Enfield</td><td><a href='#l'>Anchor</a><a href='mailto:x@example.test'>Mail</a><a href='/only.gml'>Download</a></td></tr></table>
    """
    assert worker.discover(ignored.encode(), BASE_URL).endswith("/only.gml")

    expect_error("AUTHORITY_ROW_MATCH_COUNT:0", "<table><tr><td>London Borough of Hackney</td><td><a href='/x.gml'>Download</a></td></tr></table>")
    expect_error("AUTHORITY_ROW_MATCH_COUNT:2", adjacent.replace("London Borough of Hackney", "London Borough of Enfield"))
    expect_error("AUTHORITY_ROW_DOWNLOAD_LINK_COUNT:2", "<table><tr><td>London Borough of Enfield</td><td><a href='/a.gml'>A</a><a href='/b.gml'>B</a></td></tr></table>")
    expect_error("AUTHORITY_ROW_DOWNLOAD_LINK_COUNT:0", "<table><tr><td>London Borough of Enfield</td><td>No link</td></tr></table>")

    print("PARCEL_LABEL_2_V5_DISCOVERY_TESTS=7/7")
    print("FINAL_READY=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
