#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import tempfile
import urllib.parse
import urllib.request
from datetime import datetime, timezone

INPUT = pathlib.Path("docs/chatgpt_status/_shared/slots_21/parcel_label_3/mdu_status_official_result_latest.json")
MANIFEST = pathlib.Path("docs/chatgpt_status/_shared/slots_21/parcel_label_3/evidence/hmlr_price_paid_exact_address_property_type_source_manifest_20260803.json")
OUTPUTS = [
    pathlib.Path("docs/chatgpt_status/_shared/slots_21/parcel_label_3/hmlr_price_paid_exact_address_property_type_result_latest.json"),
    pathlib.Path("england_map_web/data/aays_21_slots/parcel_label_3/hmlr_price_paid_exact_address_property_type_latest.json"),
]
ENDPOINT = "https://landregistry.data.gov.uk/landregistry/query"
MAX_RESPONSE_BYTES = 4 * 1024 * 1024
MAX_BINDINGS_PER_TARGET = 100
TYPE_LABELS = {
    "detached": "Detached",
    "semi-detached": "Semi-detached",
    "terraced": "Terraced",
    "flat-maisonette": "Flat or maisonette",
    "other": "Other",
}

def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def atomic_write(path: pathlib.Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        handle.write(text)
        temp_path = pathlib.Path(handle.name)
    temp_path.replace(path)

def normalize(value: object) -> str:
    return re.sub(r"[^A-Z0-9]", "", str(value or "").upper())

def safe_url(url: str) -> str:
    parsed = urllib.parse.urlsplit(url)
    if (
        parsed.scheme != "https"
        or (parsed.hostname or "").casefold() != "landregistry.data.gov.uk"
        or parsed.username
        or parsed.password
        or parsed.fragment
    ):
        raise RuntimeError("UNSAFE_OR_UNTRUSTED_URL:" + url)
    return url

def fetch(url: str, timeout: int) -> tuple[bytes, str, int]:
    safe_url(url)
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "AAYS-parcel-label-3/1.0",
            "Accept": "application/sparql-results+json, application/json;q=0.9",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        final_url = response.geturl()
        safe_url(final_url)
        data = bytearray()
        while True:
            chunk = response.read(min(1024 * 1024, MAX_RESPONSE_BYTES - len(data) + 1))
            if not chunk:
                break
            data.extend(chunk)
            if len(data) > MAX_RESPONSE_BYTES:
                raise RuntimeError(f"RESPONSE_TOO_LARGE:{len(data)}:{MAX_RESPONSE_BYTES}")
        return bytes(data), final_url, int(getattr(response, "status", 200))

def load_rows() -> list[dict]:
    payload = json.loads(INPUT.read_text(encoding="utf-8"))
    records = payload.get("records", [])
    if len(records) != 3:
        raise RuntimeError(f"EXPECTED_3_INPUT_ROWS:{len(records)}")
    manifest = load_manifest()
    target_by_uprn = {item["UPRN"]: item for item in manifest["target_exact_addresses"]}
    output: list[dict] = []
    for record in records:
        required = ("parcel_id", "UPRN", "FULLADDRESS", "POSTCODE", "longitude", "latitude")
        if not record.get("exact_uprn_bound") or any(field not in record for field in required):
            raise RuntimeError("INVALID_INPUT_ROW")
        uprn = str(record["UPRN"])
        expected = target_by_uprn.get(uprn)
        if expected is None:
            raise RuntimeError("UPRN_NOT_IN_MANIFEST:" + uprn)
        row = {field: record[field] for field in required}
        row["UPRN"] = uprn
        row["exact_uprn_bound"] = True
        row["expected_paon"] = expected["paon"]
        row["expected_saon"] = expected["saon"]
        row["expected_street"] = expected["street"]
        row["expected_postcode"] = expected["postcode"]
        if normalize(row["POSTCODE"]) != normalize(expected["postcode"]):
            raise RuntimeError("POSTCODE_MANIFEST_MISMATCH:" + uprn)
        output.append(row)
    if len({row["UPRN"] for row in output}) != 3:
        raise RuntimeError("INPUT_UPRNS_NOT_UNIQUE")
    return output

def load_manifest() -> dict:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if payload.get("endpoint_url") != ENDPOINT:
        raise RuntimeError("WRONG_MANIFEST_ENDPOINT")
    targets = payload.get("target_exact_addresses", [])
    if len(targets) != 3:
        raise RuntimeError("SOURCE_MANIFEST_TARGET_COUNT")
    sources = payload.get("sources", [])
    if len(sources) < 5:
        raise RuntimeError("SOURCE_MANIFEST_INCOMPLETE")
    for source in sources:
        excerpt = source.get("retained_excerpt", "")
        if not excerpt or sha256_bytes(excerpt.encode("utf-8")) != source.get("retained_excerpt_sha256"):
            raise RuntimeError("MANIFEST_EXCERPT_SHA_MISMATCH")
    return payload

def sparql_query(row: dict) -> str:
    postcode = str(row["expected_postcode"]).replace("\\", "\\\\").replace('"', '\\"')
    paon = str(row["expected_paon"]).replace("\\", "\\\\").replace('"', '\\"')
    street = str(row["expected_street"]).replace("\\", "\\\\").replace('"', '\\"')
    return f"""PREFIX ppi: <http://landregistry.data.gov.uk/def/ppi/>
PREFIX common: <http://landregistry.data.gov.uk/def/common/>
SELECT ?record ?transactionId ?transactionDate ?propertyType ?paon ?saon ?street ?postcode
WHERE {{
  ?record a ppi:TransactionRecord ;
          ppi:propertyAddress ?address ;
          ppi:transactionId ?transactionId ;
          ppi:transactionDate ?transactionDate ;
          ppi:propertyType ?propertyType .
  ?address common:postcode ?postcode ;
           common:paon ?paon ;
           common:street ?street .
  OPTIONAL {{ ?address common:saon ?saon . }}
  FILTER(UCASE(STR(?postcode)) = "{postcode}")
  FILTER(UCASE(STR(?paon)) = "{paon}")
  FILTER(UCASE(STR(?street)) = "{street}")
  FILTER(!BOUND(?saon) || STRLEN(REPLACE(UCASE(STR(?saon)), "[^A-Z0-9]", "")) = 0)
}}
ORDER BY DESC(?transactionDate)
LIMIT {MAX_BINDINGS_PER_TARGET}"""

def request_url(row: dict) -> tuple[str, str]:
    query = sparql_query(row)
    params = urllib.parse.urlencode({"query": query, "output": "json"})
    return ENDPOINT + "?" + params, query

def binding_value(binding: dict, key: str) -> str:
    item = binding.get(key)
    return str(item.get("value", "")) if isinstance(item, dict) else ""

def property_type_slug(uri: str) -> str | None:
    slug = uri.rstrip("/").rsplit("/", 1)[-1].casefold()
    return slug if slug in TYPE_LABELS else None

def parse_response(body: bytes, row: dict) -> tuple[list[dict], dict]:
    payload = json.loads(body)
    bindings = payload.get("results", {}).get("bindings")
    if not isinstance(bindings, list):
        raise RuntimeError("NOT_SPARQL_RESULTS_JSON")
    exact: list[dict] = []
    rejected = 0
    for binding in bindings:
        if not isinstance(binding, dict):
            rejected += 1
            continue
        paon = binding_value(binding, "paon")
        saon = binding_value(binding, "saon")
        street = binding_value(binding, "street")
        postcode = binding_value(binding, "postcode")
        if (
            normalize(paon) != normalize(row["expected_paon"])
            or normalize(saon) != normalize(row["expected_saon"])
            or normalize(street) != normalize(row["expected_street"])
            or normalize(postcode) != normalize(row["expected_postcode"])
        ):
            rejected += 1
            continue
        uri = binding_value(binding, "propertyType")
        slug = property_type_slug(uri)
        if slug is None:
            rejected += 1
            continue
        record = {
            "record_uri": binding_value(binding, "record"),
            "transaction_id": binding_value(binding, "transactionId"),
            "transaction_date": binding_value(binding, "transactionDate"),
            "property_type_uri": uri,
            "property_type_slug": slug,
            "paon": paon,
            "saon": saon,
            "street": street,
            "postcode": postcode,
        }
        canonical = json.dumps(record, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        record["binding_sha256"] = sha256_bytes(canonical.encode("utf-8"))
        exact.append(record)
    summary = {
        "returned_binding_count": len(bindings),
        "exact_binding_count": len(exact),
        "rejected_binding_count": rejected,
    }
    return exact, summary

def synthetic_body(row: dict, index: int, conflict: bool = False) -> bytes:
    slugs = ["flat-maisonette", "terraced", "terraced"]
    chosen = slugs[index - 1]
    bindings = []
    for transaction_index in (1, 2):
        slug = chosen
        if conflict and index == 2 and transaction_index == 2:
            slug = "semi-detached"
        bindings.append(
            {
                "record": {"type": "uri", "value": f"http://landregistry.data.gov.uk/data/ppi/transaction/SYN-{index}-{transaction_index}/current"},
                "transactionId": {"type": "literal", "value": f"SYN-{index}-{transaction_index}"},
                "transactionDate": {"type": "literal", "value": f"202{transaction_index}-01-0{index}"},
                "propertyType": {"type": "uri", "value": f"http://landregistry.data.gov.uk/def/common/{slug}"},
                "paon": {"type": "literal", "value": row["expected_paon"]},
                "street": {"type": "literal", "value": row["expected_street"]},
                "postcode": {"type": "literal", "value": row["expected_postcode"]},
            }
        )
    return json.dumps({"head": {"vars": []}, "results": {"bindings": bindings}}, separators=(",", ":")).encode("utf-8")

def run(rows: list[dict], timeout: int, synthetic: bool = False, conflict: bool = False) -> tuple[dict, list[dict], int]:
    evidence = {"endpoint_url": ENDPOINT, "accessed_at": now(), "requests": [], "request_count": 0}
    outputs: list[dict] = []
    matched = 0
    for index, row in enumerate(rows, 1):
        url, query = request_url(row)
        evidence["request_count"] += 1
        try:
            if synthetic:
                body = synthetic_body(row, index, conflict=conflict)
                final_url, status = url, 200
            else:
                body, final_url, status = fetch(url, timeout)
            exact, summary = parse_response(body, row)
            type_slugs = sorted({item["property_type_slug"] for item in exact})
            request_evidence = {
                "UPRN": row["UPRN"],
                "endpoint_url": ENDPOINT,
                "request_url": url,
                "final_url": final_url,
                "query_sha256": sha256_bytes(query.encode("utf-8")),
                "http_status": status,
                "bytes": len(body),
                "response_sha256": sha256_bytes(body),
                **summary,
                "exact_property_type_slugs": type_slugs,
                "state": "RESPONSE",
            }
            evidence["requests"].append(request_evidence)
            output = {
                **row,
                "source_url": final_url,
                "candidate_count": len(exact),
                "transaction_count": len(exact),
                "inferred": False,
                "sale_price_retained": False,
            }
            if exact and len(type_slugs) == 1:
                latest = sorted(exact, key=lambda item: item["transaction_date"], reverse=True)[0]
                output.update(
                    {
                        "state": "MATCHED_UNANIMOUS_HMLR_PRICE_PAID_PROPERTY_TYPE",
                        "official_property_type_slug": type_slugs[0],
                        "official_property_type_label": TYPE_LABELS[type_slugs[0]],
                        "property_type_uri": latest["property_type_uri"],
                        "latest_transaction_date": latest["transaction_date"],
                        "exact_binding_sha256": [item["binding_sha256"] for item in exact],
                        "transaction_id_sha256": [
                            sha256_bytes(item["transaction_id"].encode("utf-8")) for item in exact
                        ],
                    }
                )
                matched += 1
            elif exact:
                output.update(
                    {
                        "state": "NO_DATA",
                        "reason": "CONFLICTING_HMLR_PROPERTY_TYPES_FOR_EXACT_ADDRESS",
                        "candidate_property_type_slugs": type_slugs,
                        "exact_binding_sha256": [item["binding_sha256"] for item in exact],
                    }
                )
            else:
                output.update(
                    {
                        "state": "NO_DATA",
                        "reason": "NO_EXACT_HMLR_PRICE_PAID_ADDRESS_BINDING",
                    }
                )
        except Exception as exc:
            error = f"{type(exc).__name__}:{exc}"
            evidence["requests"].append(
                {
                    "UPRN": row["UPRN"],
                    "endpoint_url": ENDPOINT,
                    "request_url": url,
                    "query_sha256": sha256_bytes(query.encode("utf-8")),
                    "state": "ERROR",
                    "error": error,
                }
            )
            output = {
                **row,
                "source_url": ENDPOINT,
                "candidate_count": 0,
                "transaction_count": 0,
                "state": "NO_DATA",
                "reason": error,
                "inferred": False,
                "sale_price_retained": False,
            }
        outputs.append(output)
    return evidence, outputs, matched

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--synthetic-test", action="store_true")
    parser.add_argument("--synthetic-conflict-test", action="store_true")
    args = parser.parse_args()
    if not 1 <= args.timeout <= 300:
        raise RuntimeError("INVALID_TIMEOUT")
    rows = load_rows()
    manifest = load_manifest()
    if args.validate_only:
        print(
            json.dumps(
                {
                    "valid": True,
                    "input_count": 3,
                    "target_uprns": [row["UPRN"] for row in rows],
                    "endpoint_url": ENDPOINT,
                    "resource_class": "network",
                    "request_limit": 3,
                    "max_response_bytes": MAX_RESPONSE_BYTES,
                    "max_bindings_per_target": MAX_BINDINGS_PER_TARGET,
                    "write_paths": [str(path) for path in OUTPUTS],
                },
                sort_keys=True,
            )
        )
        return 0
    synthetic = args.synthetic_test or args.synthetic_conflict_test
    evidence, records, matched = run(rows, args.timeout, synthetic=synthetic, conflict=args.synthetic_conflict_test)
    if args.synthetic_test:
        states = [record["state"] for record in records]
        labels = [record.get("official_property_type_slug") for record in records]
        if matched != 3 or labels != ["flat-maisonette", "terraced", "terraced"]:
            raise RuntimeError(f"SYNTHETIC_UNANIMOUS_FAILED:{matched}:{labels}:{states}")
        print(json.dumps({"valid": True, "matched_rows": matched, "labels": labels, "request_count": evidence["request_count"]}, sort_keys=True))
        return 0
    if args.synthetic_conflict_test:
        states = [record["state"] for record in records]
        if matched != 2 or states[1] != "NO_DATA" or records[1].get("reason") != "CONFLICTING_HMLR_PROPERTY_TYPES_FOR_EXACT_ADDRESS":
            raise RuntimeError(f"SYNTHETIC_CONFLICT_FAILED:{matched}:{states}")
        print(json.dumps({"valid": True, "matched_rows": matched, "conflict_state": states[1], "request_count": evidence["request_count"]}, sort_keys=True))
        return 0
    state = "PUBLISHED" if matched else "NO_DATA_CONTINUE"
    result = {
        "schema_version": 1,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": "parcel_label_3",
        "task_id": "parcel-label-3-hmlr-price-paid-exact-address-property-type-v1-20260803",
        "state": state,
        "panel_status": "PUBLISHED",
        "completed_count": len(records),
        "target_count": 3,
        "previous_percent": 0.0,
        "progress_percent": round(len(records) / 3 * 100, 6),
        "percent_increase": round(len(records) / 3 * 100, 6),
        "matched_unanimous_property_type_rows": matched,
        "evidence_records": len(records),
        "source_evidence": evidence,
        "records": records,
        "sale_prices_retained": False,
        "address_match_policy": "EXACT_PAON_EMPTY_SAON_STREET_POSTCODE",
        "property_type_policy": "UNANIMOUS_ACROSS_ALL_EXACT_TRANSACTIONS",
        "fake_data": False,
        "large_raw_files_committed": False,
        "generated_at": now(),
    }
    text = json.dumps(result, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n"
    for path in OUTPUTS:
        atomic_write(path, text)
    print(
        json.dumps(
            {
                "completed_count": len(records),
                "target_count": 3,
                "matched_unanimous_property_type_rows": matched,
                "state": state,
                "output_sha256": sha256_bytes(text.encode("utf-8")),
            },
            sort_keys=True,
        )
    )
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
