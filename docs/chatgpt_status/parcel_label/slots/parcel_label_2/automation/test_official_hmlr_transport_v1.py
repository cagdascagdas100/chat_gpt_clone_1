from __future__ import annotations

import urllib.request

import official_hmlr_transport_v1 as module

PRIMARY = "use-land-property-data.service.gov.uk"


def expect_error(fragment: str, fn) -> None:
    try:
        fn()
    except RuntimeError as exc:
        assert fragment in str(exc), exc
    else:
        raise AssertionError(fragment)


def redirect(handler, source: str, target: str):
    request = urllib.request.Request(source)
    return handler.redirect_request(request, None, 302, "Found", {}, target)


def main() -> int:
    checks = 0
    assert module.validate_official_hmlr_url(f"https://{PRIMARY}/datasets/inspire/download", primary_host=PRIMARY)
    checks += 1
    assert module.validate_official_hmlr_url("https://inspire.landregistry.gov.uk/file.gml", primary_host=PRIMARY)
    checks += 1
    assert module.validate_official_hmlr_url("https://cdn.inspire.landregistry.gov.uk/file.gml", primary_host=PRIMARY)
    checks += 1
    assert module.validate_official_hmlr_url("https://landregistry.gov.uk/file.gml", primary_host=PRIMARY)
    checks += 1
    assert module.validate_official_hmlr_url(f"https://{PRIMARY}/index", primary_host=PRIMARY, require_primary=True)
    checks += 1
    expect_error("UNTRUSTED_HOST", lambda: module.validate_official_hmlr_url("https://evil.example/file.gml", primary_host=PRIMARY)); checks += 1
    expect_error("UNTRUSTED_HOST", lambda: module.validate_official_hmlr_url("https://landregistry.gov.uk.evil.example/file.gml", primary_host=PRIMARY)); checks += 1
    expect_error("INDEX_REDIRECT_CROSS_ORIGIN", lambda: module.validate_official_hmlr_url("https://inspire.landregistry.gov.uk/index", primary_host=PRIMARY, require_primary=True)); checks += 1
    expect_error("IP_LITERAL_FORBIDDEN", lambda: module.validate_official_hmlr_url("https://127.0.0.1/file.gml", primary_host=PRIMARY)); checks += 1
    expect_error("PORT_NOT_443", lambda: module.validate_official_hmlr_url(f"https://{PRIMARY}:8443/file.gml", primary_host=PRIMARY)); checks += 1
    expect_error("PORT_INVALID", lambda: module.validate_official_hmlr_url(f"https://{PRIMARY}:bad/file.gml", primary_host=PRIMARY)); checks += 1
    expect_error("NOT_HTTPS", lambda: module.validate_official_hmlr_url(f"http://{PRIMARY}/file.gml", primary_host=PRIMARY)); checks += 1
    expect_error("CONTAINS_USERINFO", lambda: module.validate_official_hmlr_url(f"https://u:p@{PRIMARY}/file.gml", primary_host=PRIMARY)); checks += 1
    expect_error("CONTAINS_FRAGMENT", lambda: module.validate_official_hmlr_url(f"https://{PRIMARY}/file.gml#x", primary_host=PRIMARY)); checks += 1
    expect_error("CONTROL_CHARACTER", lambda: module.validate_official_hmlr_url(f"https://{PRIMARY}/file\ngml", primary_host=PRIMARY)); checks += 1
    expect_error("HOST_TRAILING_DOT", lambda: module.validate_official_hmlr_url(f"https://{PRIMARY}./file.gml", primary_host=PRIMARY)); checks += 1
    handler = module.TrustedHMLRRedirectHandler(PRIMARY)
    request = redirect(handler, f"https://{PRIMARY}/start", "/next")
    assert request.full_url == f"https://{PRIMARY}/next"; checks += 1
    request = redirect(handler, f"https://{PRIMARY}/start", "https://inspire.landregistry.gov.uk/file.gml")
    assert request.full_url == "https://inspire.landregistry.gov.uk/file.gml"; checks += 1
    expect_error("UNTRUSTED_HOST", lambda: redirect(handler, f"https://{PRIMARY}/start", "https://evil.example/file.gml")); checks += 1
    expect_error("NOT_HTTPS", lambda: redirect(handler, f"https://{PRIMARY}/start", "http://inspire.landregistry.gov.uk/file.gml")); checks += 1
    expect_error("PORT_NOT_443", lambda: redirect(handler, f"https://{PRIMARY}/start", "https://inspire.landregistry.gov.uk:444/file.gml")); checks += 1
    print(f"PARCEL_LABEL_2_TRUSTED_HMLR_TRANSPORT_TESTS={checks}/{checks}")
    print("FINAL_READY=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
