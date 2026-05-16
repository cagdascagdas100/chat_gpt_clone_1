# Actual Import / Model Path Discovery

Generated UTC: 2026-05-16T17:02:42.1849245Z

## app\etl\match\parcel_matcher.py

score=17
hits=ParcelInspire|parcels_inspire|source_url|source_name|source_record_id|inspire_id|parcel_ref|source_updated_at

### line 20 needle=ParcelInspire
BEGIN_CONTEXT
      17:     ListingsLandHub,
      18:     ListingsMarketAdapter,
      19:     ManualMatchOverride,
>>    20:     ParcelInspire,
      21:     SitesBrownfieldLocalAuthority,
      22:     SitesBrownfieldPlanningData,
      23:     TransactionsPricePaid,
END_CONTEXT

### line 840 needle=parcels_inspire
BEGIN_CONTEXT
     837:         '''
     838:         WITH parcel_extent AS (
     839:           SELECT ST_SetSRID(ST_Envelope(ST_Extent(geometry)), 27700) AS geom
>>   840:           FROM parcels_inspire
     841:         ),
     842:         source_rows AS (
     843:           SELECT s.site_id, s.point_geometry
END_CONTEXT

### line 94 needle=source_url
BEGIN_CONTEXT
      91: }
      92: 
      93: 
>>    94: _SOURCE_URL_HINT_ATTRS = (
      95:     "source_url",
      96:     "listing_url",
      97:     "url",
END_CONTEXT

### line 394 needle=source_name
BEGIN_CONTEXT
     391: 
     392: 
     393: 
>>   394: def _record_dq_issue(session: Session, *, run_id: str, source_name: str, source_record_id: str, message: str, severity: str = 'warning', rule_code: str = 'unmatched_record', payload: dict[str, Any] | None = None) -> None:
     395:     session.add(
     396:         DQIssue(
     397:             run_id=run_id,
END_CONTEXT

### line 394 needle=source_record_id
BEGIN_CONTEXT
     391: 
     392: 
     393: 
>>   394: def _record_dq_issue(session: Session, *, run_id: str, source_name: str, source_record_id: str, message: str, severity: str = 'warning', rule_code: str = 'unmatched_record', payload: dict[str, Any] | None = None) -> None:
     395:     session.add(
     396:         DQIssue(
     397:             run_id=run_id,
END_CONTEXT

### line 122 needle=inspire_id
BEGIN_CONTEXT
     119: 
     120: def _build_match_source_confidence_fields(record: Any, config: dict[str, Any], candidate: "MatchCandidate") -> dict[str, Any]:
     121:     source_url = _first_populated_attr(record, _SOURCE_URL_HINT_ATTRS)
>>   122:     record_parcel_hint = _first_populated_attr(record, ("parcel_ref", "inspire_id", "matched_parcel_id"))
     123:     has_geometry = False
     124:     polygon_attr = config.get("polygon_attr")
     125:     point_attr = config.get("point_attr")
END_CONTEXT

### line 122 needle=parcel_ref
BEGIN_CONTEXT
     119: 
     120: def _build_match_source_confidence_fields(record: Any, config: dict[str, Any], candidate: "MatchCandidate") -> dict[str, Any]:
     121:     source_url = _first_populated_attr(record, _SOURCE_URL_HINT_ATTRS)
>>   122:     record_parcel_hint = _first_populated_attr(record, ("parcel_ref", "inspire_id", "matched_parcel_id"))
     123:     has_geometry = False
     124:     polygon_attr = config.get("polygon_attr")
     125:     point_attr = config.get("point_attr")
END_CONTEXT

### line 804 needle=source_updated_at
BEGIN_CONTEXT
     801: def _score_candidate(
     802:     source_name: str,
     803:     candidate: MatchCandidate,
>>   804:     source_updated_at,
     805:     completeness: float,
     806:     *,
     807:     source_confidence_needs_review: bool = False,
END_CONTEXT

## app\services\source_service.py

score=11
hits=source_url|source_name|hmlr_inspire|inspire_id|parcel_ref|source_updated_at

### line 24 needle=source_url
BEGIN_CONTEXT
      21:         notes["manifest_status"] = manifest_status
      22: 
      23:     source_confidence_record = {
>>    24:         "source_url": notes.get("source_url")
      25:         or notes.get("listing_url")
      26:         or notes.get("canonical_url")
      27:         or notes.get("provider_url"),
END_CONTEXT

### line 17 needle=source_name
BEGIN_CONTEXT
      14:     return [SourceDescriptor(**payload) for payload in SOURCE_CATALOG.values()]
      15: 
      16: 
>>    17: def _build_source_status_notes(source_name: str, metadata_json: dict[str, Any] | None, settings) -> dict[str, Any]:
      18:     notes = dict(metadata_json or {})
      19:     manifest_status = inspect_configured_manifest_status(source_name, settings)
      20:     if manifest_status:
END_CONTEXT

### line 51 needle=hmlr_inspire
BEGIN_CONTEXT
      48:         'government_property_finder': settings.government_property_stale_after_days,
      49:         'planning_data_brownfield': settings.planning_data_stale_after_days,
      50:         'local_authority_brownfield': settings.local_brownfield_stale_after_days,
>>    51:         'hmlr_inspire': settings.inspire_stale_after_days,
      52:         'hmlr_price_paid': settings.price_paid_stale_after_days,
      53:         'market_listing_adapter': settings.market_stale_after_days,
      54:     }
END_CONTEXT

### line 28 needle=inspire_id
BEGIN_CONTEXT
      25:         or notes.get("listing_url")
      26:         or notes.get("canonical_url")
      27:         or notes.get("provider_url"),
>>    28:         "parcel_ref": notes.get("parcel_ref") or notes.get("inspire_id"),
      29:         "parcel_specific_spatial_match": bool(
      30:             notes.get("has_parcel_match")
      31:             or notes.get("has_geometry")
END_CONTEXT

### line 28 needle=parcel_ref
BEGIN_CONTEXT
      25:         or notes.get("listing_url")
      26:         or notes.get("canonical_url")
      27:         or notes.get("provider_url"),
>>    28:         "parcel_ref": notes.get("parcel_ref") or notes.get("inspire_id"),
      29:         "parcel_specific_spatial_match": bool(
      30:             notes.get("has_parcel_match")
      31:             or notes.get("has_geometry")
END_CONTEXT

### line 64 needle=source_updated_at
BEGIN_CONTEXT
      61:     for name in SOURCE_CATALOG:
      62:         latest = latest_by_source.get(name)
      63:         last_snapshot_at = getattr(latest, 'fetched_at', None)
>>    64:         last_source_updated_at = getattr(latest, 'source_updated_at', None)
      65:         row_count = getattr(latest, 'row_count', 0) or 0
      66:         stale_days = threshold_map.get(name, STALE_THRESHOLDS.get(name, 30))
      67:         is_stale = True
END_CONTEXT

## tests\test_parcel_matcher_source_confidence.py

score=11
hits=source_url|parcel_ref

### line 6 needle=source_url
BEGIN_CONTEXT
       3: from app.etl.match.parcel_matcher import MatchCandidate, _build_match_source_confidence_fields
       4: 
       5: 
>>     6: def test_parcel_matcher_source_confidence_requires_review_without_source_url() -> None:
       7:     record = SimpleNamespace(parcel_ref="abc-123", site_geometry=None, point_geometry=None)
       8:     config = {"polygon_attr": "site_geometry", "point_attr": "point_geometry"}
       9:     candidate = MatchCandidate(parcel_id=101, match_method="fuzzy_address", match_score=70.0)
END_CONTEXT

### line 7 needle=parcel_ref
BEGIN_CONTEXT
       4: 
       5: 
       6: def test_parcel_matcher_source_confidence_requires_review_without_source_url() -> None:
>>     7:     record = SimpleNamespace(parcel_ref="abc-123", site_geometry=None, point_geometry=None)
       8:     config = {"polygon_attr": "site_geometry", "point_attr": "point_geometry"}
       9:     candidate = MatchCandidate(parcel_id=101, match_method="fuzzy_address", match_score=70.0)
      10: 
END_CONTEXT

## app\quality\source_confidence_integration.py

score=7
hits=source_url|parcel_ref

### line 16 needle=source_url
BEGIN_CONTEXT
      13:     HIGH,
      14:     decide_confidence,
      15:     normalize_parcel_key,
>>    16:     normalize_source_url,
      17:     should_route_to_review,
      18: )
      19: 
END_CONTEXT

### line 29 needle=parcel_ref
BEGIN_CONTEXT
      26: _PARCEL_KEYS = (
      27:     "parcel_id",
      28:     "matched_parcel_id",
>>    29:     "parcel_ref",
      30:     "uprn",
      31:     "cadastre_id",
      32: )
END_CONTEXT

## tests\test_source_confidence_integration.py

score=7
hits=source_url|parcel_ref

### line 12 needle=source_url
BEGIN_CONTEXT
       9: 
      10: def test_integration_fields_do_not_mutate_input_record():
      11:     record = {
>>    12:         "source_url": "https://example.test/source",
      13:         "parcel_id": "abc-123",
      14:         "geometry": {"type": "Point", "coordinates": [0, 0]},
      15:     }
END_CONTEXT

### line 74 needle=parcel_ref
BEGIN_CONTEXT
      71: def test_verified_source_and_parcel_match_has_no_review_payload():
      72:     record = {
      73:         "source_url": "https://example.test/source",
>>    74:         "parcel_ref": " abC-123_def ",
      75:         "geometry": {"type": "Point", "coordinates": [0, 0]},
      76:     }
      77: 
END_CONTEXT

## tests\test_source_manifest_status.py

score=7
hits=source_url|source_name

### line 93 needle=source_url
BEGIN_CONTEXT
      90:     assert notes["source_confidence"]["needs_review"] is True
      91:     assert notes["source_confidence"]["review_route"] == "source_confidence_review"
      92:     assert notes["source_confidence"]["origin"] == "source_status"
>>    93:     assert "missing_source_url" in notes["source_confidence"]["reasons"]
      94: 
      95: 
      96: def test_summarize_facilities_manifest_entries_counts_download_mode_as_live_ready() -> None:
END_CONTEXT

### line 41 needle=source_name
BEGIN_CONTEXT
      38:         ],
      39:         manifest_path=manifest_path,
      40:         container_key="providers",
>>    41:         source_name="market_listing_adapter",
      42:     )
      43: 
      44:     assert status["manifest_entries"] == 2
END_CONTEXT

## app\quality\source_confidence_rules.py

score=6
hits=source_url

### line 27 needle=source_url
BEGIN_CONTEXT
      24:     reasons: tuple[str, ...]
      25: 
      26: 
>>    27: def normalize_source_url(value: Any) -> str | None:
      28:     if value is None:
      29:         return None
      30:     text = str(value).strip()
END_CONTEXT

## scripts\contractor_match_to_parcels.py

score=6
hits=source_url|source_name

### line 203 needle=source_url
BEGIN_CONTEXT
     200:           reason text,
     201:           matched_at timestamptz,
     202:           evidence_source_name text,
>>   203:           evidence_source_url text,
     204:           evidence_record_id text,
     205:           loaded_at timestamptz not null default now(),
     206:           primary key(parcel_id, contractor_id, match_method)
END_CONTEXT

### line 50 needle=source_name
BEGIN_CONTEXT
      47: 
      48: def status(storage_root: Path, status_type: str, reason: str, details: Optional[Dict[str, Any]] = None) -> Path:
      49:     path = storage_root / "raw" / "status" / f"{status_type}_parcel_match.json"
>>    50:     write_json(path, {"status": status_type, "source_name": "contractor parcel matcher", "reason": reason, "details": details or {}, "fetched_at": utc_now(), "license_name": None})
      51:     return path
      52: 
      53: 
END_CONTEXT

## tests\test_source_confidence_rules.py

score=6
hits=source_url

### line 11 needle=source_url
BEGIN_CONTEXT
       8: )
       9: 
      10: 
>>    11: def test_missing_source_url_cannot_be_high_confidence():
      12:     decision = decide_confidence({
      13:         "source_url": "",
      14:         "parcel_id": "abc-123",
END_CONTEXT

## scripts\contractor_load_to_postgres.py

score=3
hits=source_url|source_name|source_record_id

### line 84 needle=source_url
BEGIN_CONTEXT
      81:       activity_density_label text,
      82:       do_not_contact boolean,
      83:       contact_status text,
>>    84:       company_source_url text,
      85:       last_company_fetch_at text,
      86:       company_license_name text,
      87:       scored_at timestamptz,
END_CONTEXT

### line 36 needle=source_name
BEGIN_CONTEXT
      33: 
      34: def status(storage_root: Path, status_type: str, reason: str, details: Optional[Dict[str, Any]] = None) -> Path:
      35:     path = storage_root / "raw" / "status" / f"{status_type}_postgres.json"
>>    36:     write_json(path, {"status": status_type, "source_name": "PostgreSQL loader", "reason": reason, "details": details or {}, "fetched_at": utc_now(), "license_name": None})
      37:     return path
      38: 
      39: 
END_CONTEXT

### line 97 needle=source_record_id
BEGIN_CONTEXT
      94:       contractor_id text references contractor_company(contractor_id) on delete set null,
      95:       source_name text,
      96:       source_url text,
>>    97:       source_record_id text,
      98:       ocid text,
      99:       release_id text,
     100:       release_date text,
END_CONTEXT

## app\services\scoring.py

score=2
hits=source_name|hmlr_inspire

### line 19 needle=source_name
BEGIN_CONTEXT
      16: }
      17: 
      18: 
>>    19: def source_reliability_score(source_name: str) -> float:
      20:     return SOURCE_RELIABILITY.get(source_name, 0.6)
      21: 
      22: 
END_CONTEXT

### line 11 needle=hmlr_inspire
BEGIN_CONTEXT
       8: SOURCE_RELIABILITY = {
       9:     'homes_england_landhub': 0.95,
      10:     'government_property_finder': 0.93,
>>    11:     'hmlr_inspire': 0.95,
      12:     'local_authority_brownfield': 0.9,
      13:     'planning_data_brownfield': 0.8,
      14:     'hmlr_price_paid': 0.7,
END_CONTEXT

## FG_STAGE2_CONNECTOR_SPEC.md

score=2
hits=source_url|source_name

### line 7 needle=source_url
BEGIN_CONTEXT
       4: - layer_name: Future Urban Growth & Value Shift Layer
       5: - calculation_version: future_growth_v1
       6: - disclaimer_required: "Kesin fiyat tahmini değildir"
>>     7: - confidence_guard: source_url olmayan kayıt high confidence olamaz
       8: - evidence_guard: popup evidence sadece ilgili parsel ile spatial olarak eşleşmiş kayıtları gösterebilir
       9: 
      10: ## Normalized Target Shape
END_CONTEXT

### line 34 needle=source_name
BEGIN_CONTEXT
      31: 
      32: ## Connector Spec - hmlr_price_paid
      33: - source_key: hmlr_price_paid
>>    34: - source_name: HM Land Registry Price Paid Data
      35: - source_url: https://www.gov.uk/government/statistical-data-sets/price-paid-data-downloads
      36: - mode: fixture
      37: - purpose: market_momentum
END_CONTEXT

## tests\test_sale_land_verification_route.py

score=2
hits=source_url|parcel_ref

### line 6 needle=source_url
BEGIN_CONTEXT
       3: 
       4: def test_classify_sale_land_record_includes_source_confidence_metadata() -> None:
       5:     payload = {
>>     6:         "source_url": "",
       7:         "parcel_ref": "abc-123",
       8:         "geometry": {"type": "Point", "coordinates": [0, 0]},
       9:     }
END_CONTEXT

### line 7 needle=parcel_ref
BEGIN_CONTEXT
       4: def test_classify_sale_land_record_includes_source_confidence_metadata() -> None:
       5:     payload = {
       6:         "source_url": "",
>>     7:         "parcel_ref": "abc-123",
       8:         "geometry": {"type": "Point", "coordinates": [0, 0]},
       9:     }
      10: 
END_CONTEXT

## FG_STAGE0_SCOPE.md

score=1
hits=source_url

### line 19 needle=source_url
BEGIN_CONTEXT
      16: - [x] "Kesin fiyat tahmini değildir" metni zorunlu
      17: - [x] calculation_version = future_growth_v1 korunacak
      18: - [x] Kaynaksız high confidence yasak
>>    19: - [x] source_url olmayan kayıt high confidence olamaz
      20: - [x] Evidence sadece ilgili parsel için gösterilecek
      21: - [x] Parsel popup içinde başka parsellerin evidence verisi gösterilmeyecek
      22: - [x] Eksik veri sistemi bozmayacak, confidence düşecek
END_CONTEXT

## FG_STAGE3_SPATIAL_EVIDENCE_RULES.yaml

score=1
hits=source_url

### line 15 needle=source_url
BEGIN_CONTEXT
      12:     parcel_specific: true
      13:     popup_eligible: true
      14:     weight_hint: 1.00
>>    15:     confidence_cap: high_if_source_url_present
      16:     warning_rule: none
      17: 
      18:   - relation_type: WITHIN_250M
END_CONTEXT

