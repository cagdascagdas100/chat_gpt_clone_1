#!/usr/bin/env python3
"""Wave322 fail-closed official gas/CO2 alternative-source granularity discovery."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from typing import Any

SOURCE_IDS = {
    "canonical_wave321","desnz_postcode_gas_notes","desnz_postcode_electricity_notes",
    "desnz_need_anonymised_2026","need_csv_preview_schema","need_property_access_guidance",
    "desnz_tre_access","ons_property_access","epc_service","local_authority_ghg",
}
CANDIDATES = {
    "postcode_gas","postcode_electricity","need_public_anonymised",
    "need_identifiable","epc","local_authority_ghg",
}
def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
def load(path: Path) -> dict[str, Any]:
    value=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value,dict): raise ValueError("fixture object required")
    return value
def validate(value: dict[str, Any]):
    if (value.get("slot_id"),value.get("wave")) != ("gas_emissions_2",322):
        raise ValueError("slot/wave mismatch")
    ctx=value.get("canonical_context"); candidates=value.get("candidate_assessment"); manifest=value.get("source_evidence_manifest")
    if not isinstance(ctx,dict) or not isinstance(candidates,dict) or not isinstance(manifest,list):
        raise ValueError("sections missing")
    if ctx.get("wave321_remote_readback") != "PASS":
        raise ValueError("Wave321 readback missing")
    if ctx.get("slot_partition") != {"start":30762,"end":61522,"count":30761}:
        raise ValueError("partition mismatch")
    if set(candidates) != CANDIDATES:
        raise ValueError("candidate set mismatch")
    if any(x.get("parcel_bindable") is not False for x in candidates.values()):
        raise ValueError("candidate unexpectedly parcel-bindable")
    by={}
    for item in manifest:
        sid=item.get("source_id"); excerpt=item.get("relevant_excerpt")
        if not isinstance(sid,str) or not isinstance(excerpt,str) or not excerpt:
            raise ValueError("source identity/excerpt missing")
        if item.get("excerpt_sha256") != digest(excerpt):
            raise ValueError(f"{sid}: excerpt sha mismatch")
        for key in ("publisher","source_url","accessed_at","hash_scope","supports_fields","license_or_terms_url"):
            if not item.get(key): raise ValueError(f"{sid}: {key} missing")
        by[sid]=item
    if set(by) != SOURCE_IDS: raise ValueError("source set mismatch")
    return [by[k] for k in sorted(by)],ctx,candidates
def build(value: dict[str, Any]) -> dict[str, Any]:
    manifest,ctx,candidates=validate(value)
    return {
        "schema_version":1,
        "slot_id":"gas_emissions_2",
        "wave":322,
        "state":"NO_DATA_CONTINUE",
        "decision":"OFFICIAL_ALTERNATIVE_SOURCE_GRANULARITY_NO_DATA_CONTINUE",
        "decision_reason":"Official alternatives were measured by granularity and access. DESNZ postcode gas and electricity are privacy-suppressed postcode aggregates; local-authority greenhouse-gas data is area-level; the public NEED sample is anonymised and its visible schema has no UPRN/address/postcode/property identifier; identifiable NEED requires accredited Trusted Research Environment access; EPC bulk data requires authorised access. No deterministic canonical parcel binding can be promoted.",
        "canonical_context":ctx,
        "candidate_assessment":candidates,
        "source_count":len(manifest),
        "source_evidence_manifest":manifest,
        "resolved_blockers":["OFFICIAL_ALTERNATIVE_SOURCE_SET_UNCHECKED","NEED_ANONYMISED_SAMPLE_SCHEMA_UNVERIFIED"],
        "remaining_blocker":"POSTCODE_GAS_AND_ELECTRICITY_ARE_AGGREGATED_AND_DISCLOSURE_SUPPRESSED;NEED_ANONYMISED_SAMPLE_HAS_NO_VISIBLE_ADDRESS_UPRN_POSTCODE_OR_PROPERTY_IDENTIFIER;IDENTIFIABLE_PROPERTY_LEVEL_NEED_REQUIRES_ACCREDITED_TRE_ACCESS;LOCAL_AUTHORITY_GHG_IS_NOT_PARCEL_LEVEL;EPC_BULK_REQUIRES_AUTHORISED_ACCESS;CANONICAL_PARCEL_TO_UPRN_OR_ADDRESS_BINDING_ABSENT;PARCEL_BINDING_REMAINS_NO_DATA_CONTINUE",
        "first_unverified_step":"NON_PERSONAL_BUILDING_LEVEL_MODEL_OR_OPEN_ESTIMATE_DISCOVERY_OR_NO_DATA_CONTINUE",
        "business_rows_produced":0,"parcel_rows_bound":0,
        "completed_count":0,"target_count":30761,
        "previous_percent":0.0,"current_percent":0.0,"percent_increase":0.0,
        "fake_data":False,"final_ready":False,
    }
def self_test():
    excerpt="x"
    manifest=[{"source_id":sid,"publisher":"x","source_url":"https://example.invalid","accessed_at":"x","hash_scope":"x","relevant_excerpt":excerpt,"excerpt_sha256":digest(excerpt),"supports_fields":["x"],"license_or_terms_url":"https://example.invalid"} for sid in SOURCE_IDS]
    candidates={name:{"parcel_bindable":False} for name in CANDIDATES}
    fixture={"slot_id":"gas_emissions_2","wave":322,"canonical_context":{"wave321_remote_readback":"PASS","slot_partition":{"start":30762,"end":61522,"count":30761}},"candidate_assessment":candidates,"source_evidence_manifest":manifest}
    out=build(fixture)
    assert out["source_count"]==10 and out["parcel_rows_bound"]==0
    print("SELF_TEST_PASS")
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--fixture",type=Path); parser.add_argument("--output",type=Path); parser.add_argument("--self-test",action="store_true")
    args=parser.parse_args()
    if args.self_test: self_test(); return 0
    if args.fixture is None or args.output is None: parser.error("--fixture and --output required")
    out=build(load(args.fixture))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(out,ensure_ascii=False,sort_keys=True,separators=(",",":")),encoding="utf-8")
    print("DECISION="+out["decision"]); print("BUSINESS_ROWS_PRODUCED=0"); print("PARCEL_ROWS_BOUND=0")
    return 0
if __name__=="__main__": raise SystemExit(main())
