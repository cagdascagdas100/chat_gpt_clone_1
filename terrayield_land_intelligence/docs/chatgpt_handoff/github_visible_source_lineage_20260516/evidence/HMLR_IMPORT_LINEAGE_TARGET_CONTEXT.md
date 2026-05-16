# HMLR Import Lineage Target Context

Generated UTC: 2026-05-16T16:57:24.3564325Z

## app\etl\sources\hmlr_inspire.py

FILE_NOT_FOUND

## app\etl\run_hmlr_inspire_low_disk.py

FILE_NOT_FOUND

## app\etl\match\parcel_matcher.py

### line 25 needle=confidence signal=confidence_logic

BEGIN_CONTEXT
      21:     SitesBrownfieldLocalAuthority,
      22:     SitesBrownfieldPlanningData,
      23:     TransactionsPricePaid,
      24: )
>>    25: from app.quality.source_confidence_integration import build_source_confidence_fields
      26: from app.services.scoring import compute_confidence_score, freshness_score, should_require_review, source_reliability_score
      27: 
      28: settings = get_settings()
      29: 
END_CONTEXT

### line 26 needle=confidence signal=confidence_logic

BEGIN_CONTEXT
      22:     SitesBrownfieldPlanningData,
      23:     TransactionsPricePaid,
      24: )
      25: from app.quality.source_confidence_integration import build_source_confidence_fields
>>    26: from app.services.scoring import compute_confidence_score, freshness_score, should_require_review, source_reliability_score
      27: 
      28: settings = get_settings()
      29: 
      30: LONDON_POSTCODE_PREFIXES = {
END_CONTEXT

### line 64 needle=local_authority signal=parcel_identity_mapping

BEGIN_CONTEXT
      60:         'point_attr': 'point_geometry',
      61:         'postcode_attr': 'postcode',
      62:         'name_attrs': ['reference', 'notes'],
      63:     },
>>    64:     'local_authority_brownfield': {
      65:         'model': SitesBrownfieldLocalAuthority,
      66:         'record_id_attr': 'site_id',
      67:         'listing_id_attr': None,
      68:         'polygon_attr': 'site_geometry',
END_CONTEXT

### line 94 needle=source_url signal=source_url_mapping_or_rule

BEGIN_CONTEXT
      90:     },
      91: }
      92: 
      93: 
>>    94: _SOURCE_URL_HINT_ATTRS = (
      95:     "source_url",
      96:     "listing_url",
      97:     "url",
      98:     "canonical_url",
END_CONTEXT

### line 95 needle=source_url signal=source_url_mapping_or_rule

BEGIN_CONTEXT
      91: }
      92: 
      93: 
      94: _SOURCE_URL_HINT_ATTRS = (
>>    95:     "source_url",
      96:     "listing_url",
      97:     "url",
      98:     "canonical_url",
      99:     "verification_source_url",
END_CONTEXT

### line 99 needle=source_url signal=source_url_mapping_or_rule

BEGIN_CONTEXT
      95:     "source_url",
      96:     "listing_url",
      97:     "url",
      98:     "canonical_url",
>>    99:     "verification_source_url",
     100:     "site_plan_url",
     101: )
     102: 
     103: _SPATIAL_MATCH_METHODS = {
END_CONTEXT

### line 120 needle=confidence signal=confidence_logic

BEGIN_CONTEXT
     116:             return value
     117:     return None
     118: 
     119: 
>>   120: def _build_match_source_confidence_fields(record: Any, config: dict[str, Any], candidate: "MatchCandidate") -> dict[str, Any]:
     121:     source_url = _first_populated_attr(record, _SOURCE_URL_HINT_ATTRS)
     122:     record_parcel_hint = _first_populated_attr(record, ("parcel_ref", "inspire_id", "matched_parcel_id"))
     123:     has_geometry = False
     124:     polygon_attr = config.get("polygon_attr")
END_CONTEXT

### line 121 needle=source_url signal=source_url_mapping_or_rule

BEGIN_CONTEXT
     117:     return None
     118: 
     119: 
     120: def _build_match_source_confidence_fields(record: Any, config: dict[str, Any], candidate: "MatchCandidate") -> dict[str, Any]:
>>   121:     source_url = _first_populated_attr(record, _SOURCE_URL_HINT_ATTRS)
     122:     record_parcel_hint = _first_populated_attr(record, ("parcel_ref", "inspire_id", "matched_parcel_id"))
     123:     has_geometry = False
     124:     polygon_attr = config.get("polygon_attr")
     125:     point_attr = config.get("point_attr")
END_CONTEXT

### line 122 needle=inspire_id signal=parcel_identity_mapping

BEGIN_CONTEXT
     118: 
     119: 
     120: def _build_match_source_confidence_fields(record: Any, config: dict[str, Any], candidate: "MatchCandidate") -> dict[str, Any]:
     121:     source_url = _first_populated_attr(record, _SOURCE_URL_HINT_ATTRS)
>>   122:     record_parcel_hint = _first_populated_attr(record, ("parcel_ref", "inspire_id", "matched_parcel_id"))
     123:     has_geometry = False
     124:     polygon_attr = config.get("polygon_attr")
     125:     point_attr = config.get("point_attr")
     126:     if polygon_attr and getattr(record, polygon_attr, None) is not None:
END_CONTEXT

### line 122 needle=parcel_ref signal=parcel_identity_mapping

BEGIN_CONTEXT
     118: 
     119: 
     120: def _build_match_source_confidence_fields(record: Any, config: dict[str, Any], candidate: "MatchCandidate") -> dict[str, Any]:
     121:     source_url = _first_populated_attr(record, _SOURCE_URL_HINT_ATTRS)
>>   122:     record_parcel_hint = _first_populated_attr(record, ("parcel_ref", "inspire_id", "matched_parcel_id"))
     123:     has_geometry = False
     124:     polygon_attr = config.get("polygon_attr")
     125:     point_attr = config.get("point_attr")
     126:     if polygon_attr and getattr(record, polygon_attr, None) is not None:
END_CONTEXT

### line 132 needle=source_url signal=source_url_mapping_or_rule

BEGIN_CONTEXT
     128:     if point_attr and getattr(record, point_attr, None) is not None:
     129:         has_geometry = True
     130: 
     131:     payload = {
>>   132:         "source_url": source_url,
     133:         "matched_parcel_id": candidate.parcel_id,
     134:         "parcel_ref": record_parcel_hint,
     135:         "parcel_specific_spatial_match": (
     136:             candidate.match_method in _SPATIAL_MATCH_METHODS
END_CONTEXT

### line 134 needle=parcel_ref signal=parcel_identity_mapping

BEGIN_CONTEXT
     130: 
     131:     payload = {
     132:         "source_url": source_url,
     133:         "matched_parcel_id": candidate.parcel_id,
>>   134:         "parcel_ref": record_parcel_hint,
     135:         "parcel_specific_spatial_match": (
     136:             candidate.match_method in _SPATIAL_MATCH_METHODS
     137:             or candidate.overlap_ratio is not None
     138:             or candidate.distance_m is not None
END_CONTEXT

### line 143 needle=confidence signal=confidence_logic

BEGIN_CONTEXT
     139:             or has_geometry
     140:         ),
     141:         "ambiguous_match": bool(candidate.requires_review),
     142:     }
>>   143:     return build_source_confidence_fields(payload)
     144: 
     145: 
     146: @dataclass
     147: class MatchCandidate:
END_CONTEXT

### line 159 needle=confidence signal=confidence_logic

BEGIN_CONTEXT
     155:     requires_review: bool = False
     156:     source_scope: str | None = None
     157:     match_tier: str | None = None
     158:     can_publish_history_signal: bool = True
>>   159:     forced_confidence_score: float | None = None
     160: 
     161: 
     162: def _normalize_authority(value: str | None) -> str | None:
     163:     if not value:
END_CONTEXT

### line 197 needle=local_authority signal=parcel_identity_mapping

BEGIN_CONTEXT
     193:     return " ".join(tokens)
     194: 
     195: 
     196: def _covered_authorities(session: Session) -> set[str]:
>>   197:     rows = session.execute(select(ParcelInspire.local_authority).where(ParcelInspire.local_authority.is_not(None)).distinct()).scalars()
     198:     return {normalized for value in rows if (normalized := _normalize_authority(value))}
     199: 
     200: 
     201: def _covered_authority_lookup(session: Session) -> dict[str, str | None]:
END_CONTEXT

### line 202 needle=local_authority signal=parcel_identity_mapping

BEGIN_CONTEXT
     198:     return {normalized for value in rows if (normalized := _normalize_authority(value))}
     199: 
     200: 
     201: def _covered_authority_lookup(session: Session) -> dict[str, str | None]:
>>   202:     rows = session.execute(select(ParcelInspire.local_authority).where(ParcelInspire.local_authority.is_not(None)).distinct()).scalars()
     203:     canonical_to_values: dict[str, set[str]] = {}
     204:     for value in rows:
     205:         canonical = _canonicalize_authority(value)
     206:         if not canonical:
END_CONTEXT

### line 215 needle=local_authority signal=parcel_identity_mapping

BEGIN_CONTEXT
     211:         lookup[canonical] = next(iter(values)) if len(values) == 1 else None
     212:     return lookup
     213: 
     214: 
>>   215: def _resolve_local_authority_filter(record_local_authority: str | None, covered_authorities: set[str], authority_lookup: dict[str, str | None]) -> str | None:
     216:     normalized = _normalize_authority(record_local_authority)
     217:     if normalized and normalized in covered_authorities:
     218:         return record_local_authority
     219:     canonical = _canonicalize_authority(record_local_authority)
END_CONTEXT

### line 216 needle=local_authority signal=parcel_identity_mapping

BEGIN_CONTEXT
     212:     return lookup
     213: 
     214: 
     215: def _resolve_local_authority_filter(record_local_authority: str | None, covered_authorities: set[str], authority_lookup: dict[str, str | None]) -> str | None:
>>   216:     normalized = _normalize_authority(record_local_authority)
     217:     if normalized and normalized in covered_authorities:
     218:         return record_local_authority
     219:     canonical = _canonicalize_authority(record_local_authority)
     220:     if canonical:
END_CONTEXT

### line 218 needle=local_authority signal=parcel_identity_mapping

BEGIN_CONTEXT
     214: 
     215: def _resolve_local_authority_filter(record_local_authority: str | None, covered_authorities: set[str], authority_lookup: dict[str, str | None]) -> str | None:
     216:     normalized = _normalize_authority(record_local_authority)
     217:     if normalized and normalized in covered_authorities:
>>   218:         return record_local_authority
     219:     canonical = _canonicalize_authority(record_local_authority)
     220:     if canonical:
     221:         return authority_lookup.get(canonical)
     222:     return None
END_CONTEXT

### line 219 needle=local_authority signal=parcel_identity_mapping

BEGIN_CONTEXT
     215: def _resolve_local_authority_filter(record_local_authority: str | None, covered_authorities: set[str], authority_lookup: dict[str, str | None]) -> str | None:
     216:     normalized = _normalize_authority(record_local_authority)
     217:     if normalized and normalized in covered_authorities:
     218:         return record_local_authority
>>   219:     canonical = _canonicalize_authority(record_local_authority)
     220:     if canonical:
     221:         return authority_lookup.get(canonical)
     222:     return None
     223: 
END_CONTEXT

### line 322 needle=inspire_id signal=parcel_identity_mapping

BEGIN_CONTEXT
     318:         return None
     319: 
     320:     metadata_jsonb = cast(metadata_col, JSONB)
     321:     matched_inspire = func.nullif(
>>   322:         func.jsonb_extract_path_text(metadata_jsonb, 'match_hints', 'matched_inspire_id'),
     323:         '',
     324:     )
     325:     matched_parcel = func.nullif(
     326:         func.jsonb_extract_path_text(metadata_jsonb, 'match_hints', 'matched_parcel_ref'),
END_CONTEXT

### line 326 needle=parcel_ref signal=parcel_identity_mapping

BEGIN_CONTEXT
     322:         func.jsonb_extract_path_text(metadata_jsonb, 'match_hints', 'matched_inspire_id'),
     323:         '',
     324:     )
     325:     matched_parcel = func.nullif(
>>   326:         func.jsonb_extract_path_text(metadata_jsonb, 'match_hints', 'matched_parcel_ref'),
     327:         '',
     328:     )
     329:     return or_(matched_inspire.is_not(None), matched_parcel.is_not(None))
     330: 
END_CONTEXT

### line 394 needle=source_name signal=source_lineage_field

BEGIN_CONTEXT
     390:     return 0.4
     391: 
     392: 
     393: 
>>   394: def _record_dq_issue(session: Session, *, run_id: str, source_name: str, source_record_id: str, message: str, severity: str = 'warning', rule_code: str = 'unmatched_record', payload: dict[str, Any] | None = None) -> None:
     395:     session.add(
     396:         DQIssue(
     397:             run_id=run_id,
     398:             source_name=source_name,
END_CONTEXT

### line 394 needle=source_record_id signal=source_lineage_field

BEGIN_CONTEXT
     390:     return 0.4
     391: 
     392: 
     393: 
>>   394: def _record_dq_issue(session: Session, *, run_id: str, source_name: str, source_record_id: str, message: str, severity: str = 'warning', rule_code: str = 'unmatched_record', payload: dict[str, Any] | None = None) -> None:
     395:     session.add(
     396:         DQIssue(
     397:             run_id=run_id,
     398:             source_name=source_name,
END_CONTEXT

### line 398 needle=source_name signal=source_lineage_field

BEGIN_CONTEXT
     394: def _record_dq_issue(session: Session, *, run_id: str, source_name: str, source_record_id: str, message: str, severity: str = 'warning', rule_code: str = 'unmatched_record', payload: dict[str, Any] | None = None) -> None:
     395:     session.add(
     396:         DQIssue(
     397:             run_id=run_id,
>>   398:             source_name=source_name,
     399:             severity=severity,
     400:             rule_code=rule_code,
     401:             message=message,
     402:             source_record_id=source_record_id,
END_CONTEXT

### line 402 needle=source_record_id signal=source_lineage_field

BEGIN_CONTEXT
     398:             source_name=source_name,
     399:             severity=severity,
     400:             rule_code=rule_code,
     401:             message=message,
>>   402:             source_record_id=source_record_id,
     403:             payload=payload,
     404:         )
     405:     )
     406: 
END_CONTEXT

### line 409 needle=source_name signal=source_lineage_field

BEGIN_CONTEXT
     405:     )
     406: 
     407: 
     408: 
>>   409: def _manual_override_candidates(session: Session, source_name: str, source_record_id: str) -> list[MatchCandidate]:
     410:     rows = session.execute(
     411:         select(ManualMatchOverride).where(
     412:             ManualMatchOverride.source_name == source_name,
     413:             ManualMatchOverride.source_record_id == source_record_id,
END_CONTEXT

### line 409 needle=source_record_id signal=source_lineage_field

BEGIN_CONTEXT
     405:     )
     406: 
     407: 
     408: 
>>   409: def _manual_override_candidates(session: Session, source_name: str, source_record_id: str) -> list[MatchCandidate]:
     410:     rows = session.execute(
     411:         select(ManualMatchOverride).where(
     412:             ManualMatchOverride.source_name == source_name,
     413:             ManualMatchOverride.source_record_id == source_record_id,
END_CONTEXT

### line 412 needle=source_name signal=source_lineage_field

BEGIN_CONTEXT
     408: 
     409: def _manual_override_candidates(session: Session, source_name: str, source_record_id: str) -> list[MatchCandidate]:
     410:     rows = session.execute(
     411:         select(ManualMatchOverride).where(
>>   412:             ManualMatchOverride.source_name == source_name,
     413:             ManualMatchOverride.source_record_id == source_record_id,
     414:             ManualMatchOverride.override_action == 'force_link',
     415:         )
     416:     ).scalars().all()
END_CONTEXT

### line 413 needle=source_record_id signal=source_lineage_field

BEGIN_CONTEXT
     409: def _manual_override_candidates(session: Session, source_name: str, source_record_id: str) -> list[MatchCandidate]:
     410:     rows = session.execute(
     411:         select(ManualMatchOverride).where(
     412:             ManualMatchOverride.source_name == source_name,
>>   413:             ManualMatchOverride.source_record_id == source_record_id,
     414:             ManualMatchOverride.override_action == 'force_link',
     415:         )
     416:     ).scalars().all()
     417:     return [MatchCandidate(parcel_id=row.parcel_id, match_method='manual_override', match_score=100.0) for row in rows]
END_CONTEXT

### line 428 needle=local_authority signal=parcel_identity_mapping

BEGIN_CONTEXT
     424:     return hints if isinstance(hints, dict) else {}
     425: 
     426: 
     427: 
>>   428: def _hint_candidates(session: Session, record: Any, local_authority: str | None = None) -> list[MatchCandidate]:
     429:     hints = _extract_match_hints(record)
     430:     matched_inspire_id = str(hints.get('matched_inspire_id') or '').strip()
     431:     matched_parcel_ref = str(hints.get('matched_parcel_ref') or '').strip()
     432: 
END_CONTEXT

### line 430 needle=inspire_id signal=parcel_identity_mapping

BEGIN_CONTEXT
     426: 
     427: 
     428: def _hint_candidates(session: Session, record: Any, local_authority: str | None = None) -> list[MatchCandidate]:
     429:     hints = _extract_match_hints(record)
>>   430:     matched_inspire_id = str(hints.get('matched_inspire_id') or '').strip()
     431:     matched_parcel_ref = str(hints.get('matched_parcel_ref') or '').strip()
     432: 
     433:     if matched_inspire_id:
     434:         stmt = select(ParcelInspire.parcel_id).where(ParcelInspire.inspire_id == matched_inspire_id)
END_CONTEXT

### line 431 needle=parcel_ref signal=parcel_identity_mapping

BEGIN_CONTEXT
     427: 
     428: def _hint_candidates(session: Session, record: Any, local_authority: str | None = None) -> list[MatchCandidate]:
     429:     hints = _extract_match_hints(record)
     430:     matched_inspire_id = str(hints.get('matched_inspire_id') or '').strip()
>>   431:     matched_parcel_ref = str(hints.get('matched_parcel_ref') or '').strip()
     432: 
     433:     if matched_inspire_id:
     434:         stmt = select(ParcelInspire.parcel_id).where(ParcelInspire.inspire_id == matched_inspire_id)
     435:         if local_authority:
END_CONTEXT

### line 433 needle=inspire_id signal=parcel_identity_mapping

BEGIN_CONTEXT
     429:     hints = _extract_match_hints(record)
     430:     matched_inspire_id = str(hints.get('matched_inspire_id') or '').strip()
     431:     matched_parcel_ref = str(hints.get('matched_parcel_ref') or '').strip()
     432: 
>>   433:     if matched_inspire_id:
     434:         stmt = select(ParcelInspire.parcel_id).where(ParcelInspire.inspire_id == matched_inspire_id)
     435:         if local_authority:
     436:             stmt = stmt.where(ParcelInspire.local_authority == local_authority)
     437:         parcel_id = session.execute(stmt.limit(1)).scalar_one_or_none()
END_CONTEXT

### line 434 needle=inspire_id signal=parcel_identity_mapping

BEGIN_CONTEXT
     430:     matched_inspire_id = str(hints.get('matched_inspire_id') or '').strip()
     431:     matched_parcel_ref = str(hints.get('matched_parcel_ref') or '').strip()
     432: 
     433:     if matched_inspire_id:
>>   434:         stmt = select(ParcelInspire.parcel_id).where(ParcelInspire.inspire_id == matched_inspire_id)
     435:         if local_authority:
     436:             stmt = stmt.where(ParcelInspire.local_authority == local_authority)
     437:         parcel_id = session.execute(stmt.limit(1)).scalar_one_or_none()
     438:         if parcel_id is not None:
END_CONTEXT

### line 435 needle=local_authority signal=parcel_identity_mapping

BEGIN_CONTEXT
     431:     matched_parcel_ref = str(hints.get('matched_parcel_ref') or '').strip()
     432: 
     433:     if matched_inspire_id:
     434:         stmt = select(ParcelInspire.parcel_id).where(ParcelInspire.inspire_id == matched_inspire_id)
>>   435:         if local_authority:
     436:             stmt = stmt.where(ParcelInspire.local_authority == local_authority)
     437:         parcel_id = session.execute(stmt.limit(1)).scalar_one_or_none()
     438:         if parcel_id is not None:
     439:             return [MatchCandidate(parcel_id=int(parcel_id), match_method='metadata_inspire_exact', match_score=99.8)]
END_CONTEXT

### line 436 needle=local_authority signal=parcel_identity_mapping

BEGIN_CONTEXT
     432: 
     433:     if matched_inspire_id:
     434:         stmt = select(ParcelInspire.parcel_id).where(ParcelInspire.inspire_id == matched_inspire_id)
     435:         if local_authority:
>>   436:             stmt = stmt.where(ParcelInspire.local_authority == local_authority)
     437:         parcel_id = session.execute(stmt.limit(1)).scalar_one_or_none()
     438:         if parcel_id is not None:
     439:             return [MatchCandidate(parcel_id=int(parcel_id), match_method='metadata_inspire_exact', match_score=99.8)]
     440: 
END_CONTEXT

### line 441 needle=parcel_ref signal=parcel_identity_mapping

BEGIN_CONTEXT
     437:         parcel_id = session.execute(stmt.limit(1)).scalar_one_or_none()
     438:         if parcel_id is not None:
     439:             return [MatchCandidate(parcel_id=int(parcel_id), match_method='metadata_inspire_exact', match_score=99.8)]
     440: 
>>   441:     if matched_parcel_ref:
     442:         stmt = select(ParcelInspire.parcel_id).where(ParcelInspire.parcel_ref == matched_parcel_ref)
     443:         if local_authority:
     444:             stmt = stmt.where(ParcelInspire.local_authority == local_authority)
     445:         parcel_id = session.execute(stmt.limit(1)).scalar_one_or_none()
END_CONTEXT

### line 442 needle=parcel_ref signal=parcel_identity_mapping

BEGIN_CONTEXT
     438:         if parcel_id is not None:
     439:             return [MatchCandidate(parcel_id=int(parcel_id), match_method='metadata_inspire_exact', match_score=99.8)]
     440: 
     441:     if matched_parcel_ref:
>>   442:         stmt = select(ParcelInspire.parcel_id).where(ParcelInspire.parcel_ref == matched_parcel_ref)
     443:         if local_authority:
     444:             stmt = stmt.where(ParcelInspire.local_authority == local_authority)
     445:         parcel_id = session.execute(stmt.limit(1)).scalar_one_or_none()
     446:         if parcel_id is not None:
END_CONTEXT

### line 443 needle=local_authority signal=parcel_identity_mapping

BEGIN_CONTEXT
     439:             return [MatchCandidate(parcel_id=int(parcel_id), match_method='metadata_inspire_exact', match_score=99.8)]
     440: 
     441:     if matched_parcel_ref:
     442:         stmt = select(ParcelInspire.parcel_id).where(ParcelInspire.parcel_ref == matched_parcel_ref)
>>   443:         if local_authority:
     444:             stmt = stmt.where(ParcelInspire.local_authority == local_authority)
     445:         parcel_id = session.execute(stmt.limit(1)).scalar_one_or_none()
     446:         if parcel_id is not None:
     447:             return [MatchCandidate(parcel_id=int(parcel_id), match_method='metadata_parcel_ref_exact', match_score=99.6)]
END_CONTEXT

### line 444 needle=local_authority signal=parcel_identity_mapping

BEGIN_CONTEXT
     440: 
     441:     if matched_parcel_ref:
     442:         stmt = select(ParcelInspire.parcel_id).where(ParcelInspire.parcel_ref == matched_parcel_ref)
     443:         if local_authority:
>>   444:             stmt = stmt.where(ParcelInspire.local_authority == local_authority)
     445:         parcel_id = session.execute(stmt.limit(1)).scalar_one_or_none()
     446:         if parcel_id is not None:
     447:             return [MatchCandidate(parcel_id=int(parcel_id), match_method='metadata_parcel_ref_exact', match_score=99.6)]
     448: 
END_CONTEXT

### line 447 needle=parcel_ref signal=parcel_identity_mapping

BEGIN_CONTEXT
     443:         if local_authority:
     444:             stmt = stmt.where(ParcelInspire.local_authority == local_authority)
     445:         parcel_id = session.execute(stmt.limit(1)).scalar_one_or_none()
     446:         if parcel_id is not None:
>>   447:             return [MatchCandidate(parcel_id=int(parcel_id), match_method='metadata_parcel_ref_exact', match_score=99.6)]
     448: 
     449:     return []
     450: 
     451: 
END_CONTEXT

### line 453 needle=local_authority signal=parcel_identity_mapping

BEGIN_CONTEXT
     449:     return []
     450: 
     451: 
     452: 
>>   453: def _polygon_candidates(session: Session, geom_value: Any, local_authority: str | None = None) -> list[MatchCandidate]:
     454:     safe_geom = func.ST_CollectionExtract(func.ST_MakeValid(geom_value), 3)
     455:     overlap_ratio = (
     456:         func.ST_Area(func.ST_Intersection(ParcelInspire.geometry, safe_geom))
     457:         / func.nullif(func.ST_Area(ParcelInspire.geometry), 0)
END_CONTEXT

### line 460 needle=local_authority signal=parcel_identity_mapping

BEGIN_CONTEXT
     456:         func.ST_Area(func.ST_Intersection(ParcelInspire.geometry, safe_geom))
     457:         / func.nullif(func.ST_Area(ParcelInspire.geometry), 0)
     458:     ).label('overlap_ratio')
     459:     stmt = select(ParcelInspire.parcel_id, overlap_ratio).where(func.ST_Intersects(ParcelInspire.geometry, safe_geom))
>>   460:     if local_authority:
     461:         stmt = stmt.where(ParcelInspire.local_authority == local_authority)
     462:     rows = session.execute(stmt.order_by(desc(overlap_ratio)).limit(settings.max_polygon_match_candidates)).all()
     463:     candidates = []
     464:     for parcel_id, overlap in rows:
END_CONTEXT

### line 461 needle=local_authority signal=parcel_identity_mapping

BEGIN_CONTEXT
     457:         / func.nullif(func.ST_Area(ParcelInspire.geometry), 0)
     458:     ).label('overlap_ratio')
     459:     stmt = select(ParcelInspire.parcel_id, overlap_ratio).where(func.ST_Intersects(ParcelInspire.geometry, safe_geom))
     460:     if local_authority:
>>   461:         stmt = stmt.where(ParcelInspire.local_authority == local_authority)
     462:     rows = session.execute(stmt.order_by(desc(overlap_ratio)).limit(settings.max_polygon_match_candidates)).all()
     463:     candidates = []
     464:     for parcel_id, overlap in rows:
     465:         overlap_value = float(overlap or 0.0)
END_CONTEXT

### line 473 needle=local_authority signal=parcel_identity_mapping

BEGIN_CONTEXT
     469:     return candidates
     470: 
     471: 
     472: 
>>   473: def _point_candidates(session: Session, point_value: Any, local_authority: str | None = None) -> list[MatchCandidate]:
     474:     within_expr = func.ST_Within(point_value, ParcelInspire.geometry).label('is_within')
     475:     distance_expr = func.ST_Distance(ParcelInspire.centroid, point_value).label('distance_m')
     476:     knn_distance_expr = ParcelInspire.centroid.op('<->')(point_value)
     477:     stmt = (
END_CONTEXT

### line 481 needle=local_authority signal=parcel_identity_mapping

BEGIN_CONTEXT
     477:     stmt = (
     478:         select(ParcelInspire.parcel_id, within_expr, distance_expr)
     479:         .where(or_(func.ST_Within(point_value, ParcelInspire.geometry), func.ST_DWithin(ParcelInspire.centroid, point_value, settings.point_match_radius_m)))
     480:     )
>>   481:     if local_authority:
     482:         stmt = stmt.where(ParcelInspire.local_authority == local_authority)
     483:     rows = session.execute(stmt.order_by(within_expr.desc(), knn_distance_expr.asc()).limit(3)).all()
     484:     candidates = []
     485:     for parcel_id, is_within, distance_m in rows:
END_CONTEXT

### line 482 needle=local_authority signal=parcel_identity_mapping

BEGIN_CONTEXT
     478:         select(ParcelInspire.parcel_id, within_expr, distance_expr)
     479:         .where(or_(func.ST_Within(point_value, ParcelInspire.geometry), func.ST_DWithin(ParcelInspire.centroid, point_value, settings.point_match_radius_m)))
     480:     )
     481:     if local_authority:
>>   482:         stmt = stmt.where(ParcelInspire.local_authority == local_authority)
     483:     rows = session.execute(stmt.order_by(within_expr.desc(), knn_distance_expr.asc()).limit(3)).all()
     484:     candidates = []
     485:     for parcel_id, is_within, distance_m in rows:
     486:         distance_value = float(distance_m or 0.0)
END_CONTEXT

### line 495 needle=local_authority signal=parcel_identity_mapping

BEGIN_CONTEXT
     491:         return [candidates[0]]
     492:     return []
     493: 
     494: 
>>   495: def _polygon_centroid_candidates(session: Session, geom_value: Any, local_authority: str | None = None) -> list[MatchCandidate]:
     496:     safe_geom = func.ST_CollectionExtract(func.ST_MakeValid(geom_value), 3)
     497:     centroid_value = func.ST_Centroid(safe_geom)
     498:     within_expr = func.ST_Within(centroid_value, ParcelInspire.geometry).label('is_within')
     499:     distance_expr = func.ST_Distance(ParcelInspire.centroid, centroid_value).label('distance_m')
END_CONTEXT

### line 510 needle=local_authority signal=parcel_identity_mapping

BEGIN_CONTEXT
     506:                 func.ST_DWithin(ParcelInspire.centroid, centroid_value, settings.polygon_centroid_match_radius_m),
     507:             )
     508:         )
     509:     )
>>   510:     if local_authority:
     511:         stmt = stmt.where(ParcelInspire.local_authority == local_authority)
     512:     rows = session.execute(stmt.order_by(within_expr.desc(), knn_distance_expr.asc()).limit(3)).all()
     513:     candidates: list[MatchCandidate] = []
     514:     for parcel_id, is_within, distance_m in rows:
END_CONTEXT

### line 511 needle=local_authority signal=parcel_identity_mapping

BEGIN_CONTEXT
     507:             )
     508:         )
     509:     )
     510:     if local_authority:
>>   511:         stmt = stmt.where(ParcelInspire.local_authority == local_authority)
     512:     rows = session.execute(stmt.order_by(within_expr.desc(), knn_distance_expr.asc()).limit(3)).all()
     513:     candidates: list[MatchCandidate] = []
     514:     for parcel_id, is_within, distance_m in rows:
     515:         distance_value = float(distance_m or 0.0)
END_CONTEXT

### line 536 needle=local_authority signal=parcel_identity_mapping

BEGIN_CONTEXT
     532:     return []
     533: 
     534: 
     535: 
>>   536: def _postcode_candidates(session: Session, postcode: str | None, local_authority: str | None) -> list[MatchCandidate]:
     537:     if not postcode:
     538:         return []
     539:     normalized_postcode = str(postcode).replace(' ', '').upper()
     540:     if not normalized_postcode:
END_CONTEXT

### line 546 needle=local_authority signal=parcel_identity_mapping

BEGIN_CONTEXT
     542:     stmt = select(ParcelInspire.parcel_id).where(
     543:         ParcelInspire.postcode.is_not(None),
     544:         _normalized_postcode_expr(ParcelInspire.postcode) == normalized_postcode,
     545:     )
>>   546:     if local_authority:
     547:         stmt = stmt.where(ParcelInspire.local_authority == local_authority)
     548:     parcel_ids = session.execute(stmt.limit(5)).scalars().all()
     549:     return [MatchCandidate(parcel_id=parcel_id, match_method='postcode_assisted', match_score=65.0, postcode_match=True, requires_review=True) for parcel_id in parcel_ids[:1]]
     550: 
END_CONTEXT

### line 547 needle=local_authority signal=parcel_identity_mapping

BEGIN_CONTEXT
     543:         ParcelInspire.postcode.is_not(None),
     544:         _normalized_postcode_expr(ParcelInspire.postcode) == normalized_postcode,
     545:     )
     546:     if local_authority:
>>   547:         stmt = stmt.where(ParcelInspire.local_authority == local_authority)
     548:     parcel_ids = session.execute(stmt.limit(5)).scalars().all()
     549:     return [MatchCandidate(parcel_id=parcel_id, match_method='postcode_assisted', match_score=65.0, postcode_match=True, requires_review=True) for parcel_id in parcel_ids[:1]]
     550: 
     551: 
END_CONTEXT

### line 564 needle=confidence signal=confidence_logic

BEGIN_CONTEXT
     560:     rows = (
     561:         session.execute(
     562:             select(
     563:                 ListingParcelLink.parcel_id.label('parcel_id'),
>>   564:                 ListingParcelLink.confidence_score.label('confidence_score'),
     565:                 ListingParcelLink.match_score.label('match_score'),
     566:             )
     567:             .join(
     568:                 ListingsMarketAdapter,
END_CONTEXT

### line 570 needle=source_name signal=source_lineage_field

BEGIN_CONTEXT
     566:             )
     567:             .join(
     568:                 ListingsMarketAdapter,
     569:                 and_(
>>   570:                     ListingParcelLink.source_name == 'market_listing_adapter',
     571:                     or_(
     572:                         ListingParcelLink.listing_id == ListingsMarketAdapter.listing_id,
     573:                         ListingParcelLink.source_record_id == ListingsMarketAdapter.listing_id,
     574:                     ),
END_CONTEXT

### line 573 needle=source_record_id signal=source_lineage_field

BEGIN_CONTEXT
     569:                 and_(
     570:                     ListingParcelLink.source_name == 'market_listing_adapter',
     571:                     or_(
     572:                         ListingParcelLink.listing_id == ListingsMarketAdapter.listing_id,
>>   573:                         ListingParcelLink.source_record_id == ListingsMarketAdapter.listing_id,
     574:                     ),
     575:                 ),
     576:             )
     577:             .where(
END_CONTEXT

### line 587 needle=confidence signal=confidence_logic

BEGIN_CONTEXT
     583:                     ListingsMarketAdapter.truth_tier != 'demo',
     584:                 ),
     585:             )
     586:             .order_by(
>>   587:                 ListingParcelLink.confidence_score.desc(),
     588:                 ListingParcelLink.match_score.desc(),
     589:                 ListingParcelLink.parcel_id.asc(),
     590:             )
     591:             .limit(10)
END_CONTEXT

### line 609 needle=confidence signal=confidence_logic

BEGIN_CONTEXT
     605:         parcel_id_int = int(parcel_id)
     606:         if parcel_id_int in seen:
     607:             continue
     608:         seen.add(parcel_id_int)
>>   609:         bridge_conf = float(row.get('confidence_score') or 0.0)
     610:         bridge_match = float(row.get('match_score') or 0.0)
     611:         candidates.append(
     612:             MatchCandidate(
     613:                 parcel_id=parcel_id_int,
END_CONTEXT

### line 621 needle=confidence signal=confidence_logic

BEGIN_CONTEXT
     617:                 requires_review=False,
     618:                 source_scope='non_london_scope',
     619:                 match_tier='tier_b',
     620:                 can_publish_history_signal=True,
>>   621:                 forced_confidence_score=0.78,
     622:             )
     623:         )
     624:         if len(candidates) >= 1:
     625:             break
END_CONTEXT

### line 647 needle=confidence signal=confidence_logic

BEGIN_CONTEXT
     643:     rows = (
     644:         session.execute(
     645:             select(
     646:                 ListingParcelLink.parcel_id.label('parcel_id'),
>>   647:                 ListingParcelLink.confidence_score.label('confidence_score'),
     648:                 ListingParcelLink.match_score.label('match_score'),
     649:                 ListingsMarketAdapter.address_text.label('listing_address'),
     650:                 ListingsMarketAdapter.title.label('listing_title'),
     651:                 ListingsMarketAdapter.parcel_name.label('listing_parcel_name'),
END_CONTEXT

### line 656 needle=source_name signal=source_lineage_field

BEGIN_CONTEXT
     652:             )
     653:             .join(
     654:                 ListingsMarketAdapter,
     655:                 and_(
>>   656:                     ListingParcelLink.source_name == 'market_listing_adapter',
     657:                     or_(
     658:                         ListingParcelLink.listing_id == ListingsMarketAdapter.listing_id,
     659:                         ListingParcelLink.source_record_id == ListingsMarketAdapter.listing_id,
     660:                     ),
END_CONTEXT

### line 659 needle=source_record_id signal=source_lineage_field

BEGIN_CONTEXT
     655:                 and_(
     656:                     ListingParcelLink.source_name == 'market_listing_adapter',
     657:                     or_(
     658:                         ListingParcelLink.listing_id == ListingsMarketAdapter.listing_id,
>>   659:                         ListingParcelLink.source_record_id == ListingsMarketAdapter.listing_id,
     660:                     ),
     661:                 ),
     662:             )
     663:             .where(
END_CONTEXT

### line 673 needle=confidence signal=confidence_logic

BEGIN_CONTEXT
     669:                     ListingsMarketAdapter.truth_tier != 'demo',
     670:                 ),
     671:             )
     672:             .order_by(
>>   673:                 ListingParcelLink.confidence_score.desc(),
     674:                 ListingParcelLink.match_score.desc(),
     675:             )
     676:             .limit(30)
     677:         )
END_CONTEXT

### line 701 needle=confidence signal=confidence_logic

BEGIN_CONTEXT
     697:         if parcel_id_raw is None:
     698:             continue
     699:         parcel_id = int(parcel_id_raw)
     700:         item = parcel_scores.setdefault(parcel_id, {'bridge': 0.0, 'address': 0.0})
>>   701:         bridge_conf = float(row.get('confidence_score') or 0.0)
     702:         bridge_match = float(row.get('match_score') or 0.0)
     703:         bridge_score = bridge_conf * 0.65 + bridge_match * 0.35
     704:         if bridge_score > item['bridge']:
     705:             item['bridge'] = bridge_score
END_CONTEXT

### line 738 needle=confidence signal=confidence_logic

BEGIN_CONTEXT
     734:         return None, diagnostics
     735: 
     736:     if unique_parcel_count == 1 and (not ppd_address or top_address_sim >= 0.90):
     737:         tier = 'tier_a' if not ppd_address else 'tier_b'
>>   738:         confidence = 0.90 if tier == 'tier_a' else 0.82
     739:         candidate = MatchCandidate(
     740:             parcel_id=top_parcel_id,
     741:             match_method='market_postcode_bridge' if tier == 'tier_a' else 'market_postcode_address_bridge',
     742:             match_score=88.0 if tier == 'tier_a' else 79.0,
END_CONTEXT

### line 749 needle=confidence signal=confidence_logic

BEGIN_CONTEXT
     745:             requires_review=False,
     746:             source_scope=source_scope,
     747:             match_tier=tier,
     748:             can_publish_history_signal=True,
>>   749:             forced_confidence_score=confidence,
     750:         )
     751:         diagnostics.update({'match_tier': tier, 'reason': 'accepted_unique'})
     752:         return candidate, diagnostics
     753: 
END_CONTEXT

### line 768 needle=confidence signal=confidence_logic

BEGIN_CONTEXT
     764:                 requires_review=False,
     765:                 source_scope=source_scope,
     766:                 match_tier='tier_b',
     767:                 can_publish_history_signal=True,
>>   768:                 forced_confidence_score=0.78,
     769:             )
     770:             diagnostics.update({'match_tier': 'tier_b', 'reason': 'accepted_strong_address'})
     771:             return candidate, diagnostics
     772: 
END_CONTEXT

### line 785 needle=inspire_id signal=parcel_identity_mapping

BEGIN_CONTEXT
     781: def _fuzzy_candidates(session: Session, search_text: str | None) -> list[MatchCandidate]:
     782:     if not search_text:
     783:         return []
     784:     similarity_expr = func.similarity(
>>   785:         func.lower(func.coalesce(ParcelInspire.address_text, ParcelInspire.parcel_ref, ParcelInspire.inspire_id)),
     786:         search_text.lower(),
     787:     ).label('name_similarity')
     788:     rows = session.execute(
     789:         select(ParcelInspire.parcel_id, similarity_expr)
END_CONTEXT

### line 785 needle=parcel_ref signal=parcel_identity_mapping

BEGIN_CONTEXT
     781: def _fuzzy_candidates(session: Session, search_text: str | None) -> list[MatchCandidate]:
     782:     if not search_text:
     783:         return []
     784:     similarity_expr = func.similarity(
>>   785:         func.lower(func.coalesce(ParcelInspire.address_text, ParcelInspire.parcel_ref, ParcelInspire.inspire_id)),
     786:         search_text.lower(),
     787:     ).label('name_similarity')
     788:     rows = session.execute(
     789:         select(ParcelInspire.parcel_id, similarity_expr)
END_CONTEXT

### line 802 needle=source_name signal=source_lineage_field

BEGIN_CONTEXT
     798: 
     799: 
     800: 
     801: def _score_candidate(
>>   802:     source_name: str,
     803:     candidate: MatchCandidate,
     804:     source_updated_at,
     805:     completeness: float,
     806:     *,
END_CONTEXT

### line 804 needle=source_updated_at signal=source_lineage_field

BEGIN_CONTEXT
     800: 
     801: def _score_candidate(
     802:     source_name: str,
     803:     candidate: MatchCandidate,
>>   804:     source_updated_at,
     805:     completeness: float,
     806:     *,
     807:     source_confidence_needs_review: bool = False,
     808: ) -> tuple[float, bool]:
END_CONTEXT

### line 807 needle=confidence signal=confidence_logic

BEGIN_CONTEXT
     803:     candidate: MatchCandidate,
     804:     source_updated_at,
     805:     completeness: float,
     806:     *,
>>   807:     source_confidence_needs_review: bool = False,
     808: ) -> tuple[float, bool]:
     809:     confidence = compute_confidence_score(
     810:         source_reliability=source_reliability_score(source_name),
     811:         freshness=freshness_score(source_updated_at, source_name),
END_CONTEXT

### line 809 needle=confidence signal=confidence_logic

BEGIN_CONTEXT
     805:     completeness: float,
     806:     *,
     807:     source_confidence_needs_review: bool = False,
     808: ) -> tuple[float, bool]:
>>   809:     confidence = compute_confidence_score(
     810:         source_reliability=source_reliability_score(source_name),
     811:         freshness=freshness_score(source_updated_at, source_name),
     812:         geometry_quality=_geometry_quality(candidate.match_method, candidate.overlap_ratio, candidate.distance_m),
     813:         match_quality=candidate.match_score / 100.0,
END_CONTEXT

### line 810 needle=source_name signal=source_lineage_field

BEGIN_CONTEXT
     806:     *,
     807:     source_confidence_needs_review: bool = False,
     808: ) -> tuple[float, bool]:
     809:     confidence = compute_confidence_score(
>>   810:         source_reliability=source_reliability_score(source_name),
     811:         freshness=freshness_score(source_updated_at, source_name),
     812:         geometry_quality=_geometry_quality(candidate.match_method, candidate.overlap_ratio, candidate.distance_m),
     813:         match_quality=candidate.match_score / 100.0,
     814:         completeness=completeness,
END_CONTEXT

### line 811 needle=source_name signal=source_lineage_field

BEGIN_CONTEXT
     807:     source_confidence_needs_review: bool = False,
     808: ) -> tuple[float, bool]:
     809:     confidence = compute_confidence_score(
     810:         source_reliability=source_reliability_score(source_name),
>>   811:         freshness=freshness_score(source_updated_at, source_name),
     812:         geometry_quality=_geometry_quality(candidate.match_method, candidate.overlap_ratio, candidate.distance_m),
     813:         match_quality=candidate.match_score / 100.0,
     814:         completeness=completeness,
     815:     )
END_CONTEXT

### line 811 needle=source_updated_at signal=source_lineage_field

BEGIN_CONTEXT
     807:     source_confidence_needs_review: bool = False,
     808: ) -> tuple[float, bool]:
     809:     confidence = compute_confidence_score(
     810:         source_reliability=source_reliability_score(source_name),
>>   811:         freshness=freshness_score(source_updated_at, source_name),
     812:         geometry_quality=_geometry_quality(candidate.match_method, candidate.overlap_ratio, candidate.distance_m),
     813:         match_quality=candidate.match_score / 100.0,
     814:         completeness=completeness,
     815:     )
END_CONTEXT

### line 817 needle=confidence signal=confidence_logic

BEGIN_CONTEXT
     813:         match_quality=candidate.match_score / 100.0,
     814:         completeness=completeness,
     815:     )
     816:     requires_review = candidate.requires_review or should_require_review(
>>   817:         confidence_score=confidence,
     818:         match_method=candidate.match_method,
     819:         distance_m=candidate.distance_m,
     820:         source_confidence_needs_review=source_confidence_needs_review,
     821:     )
END_CONTEXT

### line 820 needle=confidence signal=confidence_logic

BEGIN_CONTEXT
     816:     requires_review = candidate.requires_review or should_require_review(
     817:         confidence_score=confidence,
     818:         match_method=candidate.match_method,
     819:         distance_m=candidate.distance_m,
>>   820:         source_confidence_needs_review=source_confidence_needs_review,
     821:     )
     822:     return confidence, requires_review
     823: 
     824: 
END_CONTEXT

### line 822 needle=confidence signal=confidence_logic

BEGIN_CONTEXT
     818:         match_method=candidate.match_method,
     819:         distance_m=candidate.distance_m,
     820:         source_confidence_needs_review=source_confidence_needs_review,
     821:     )
>>   822:     return confidence, requires_review
     823: 
     824: 
     825: 
     826: def _match_planning_data_brownfield_records(session: Session, run_id: str) -> int:
END_CONTEXT

### line 829 needle=local_authority signal=parcel_identity_mapping

BEGIN_CONTEXT
     825: 
     826: def _match_planning_data_brownfield_records(session: Session, run_id: str) -> int:
     827:     config = SOURCE_MODEL_CONFIG['planning_data_brownfield']
     828:     # Planning Data brownfield matching already relies on geometry-first candidate SQL.
>>   829:     # Distinct local_authority scans on very large parcel tables can hit statement timeout,
     830:     # so we skip authority pre-filtering for this source and keep matching resilient.
     831:     covered_authorities: set[str] = set()
     832:     authority_lookup: dict[str, str | None] = {}
     833:     session.execute(delete(ListingParcelLink).where(ListingParcelLink.source_name == 'planning_data_brownfield'))
END_CONTEXT

### line 833 needle=source_name signal=source_lineage_field

BEGIN_CONTEXT
     829:     # Distinct local_authority scans on very large parcel tables can hit statement timeout,
     830:     # so we skip authority pre-filtering for this source and keep matching resilient.
     831:     covered_authorities: set[str] = set()
     832:     authority_lookup: dict[str, str | None] = {}
>>   833:     session.execute(delete(ListingParcelLink).where(ListingParcelLink.source_name == 'planning_data_brownfield'))
     834:     session.flush()
     835: 
     836:     candidate_sql = text(
     837:         '''
END_CONTEXT

### line 840 needle=parcels signal=dataset_or_table_mapping

BEGIN_CONTEXT
     836:     candidate_sql = text(
     837:         '''
     838:         WITH parcel_extent AS (
     839:           SELECT ST_SetSRID(ST_Envelope(ST_Extent(geometry)), 27700) AS geom
>>   840:           FROM parcels_inspire
     841:         ),
     842:         source_rows AS (
     843:           SELECT s.site_id, s.point_geometry
     844:           FROM sites_brownfield_planning_data s
END_CONTEXT

### line 840 needle=parcels_inspire signal=dataset_or_table_mapping

BEGIN_CONTEXT
     836:     candidate_sql = text(
     837:         '''
     838:         WITH parcel_extent AS (
     839:           SELECT ST_SetSRID(ST_Envelope(ST_Extent(geometry)), 27700) AS geom
>>   840:           FROM parcels_inspire
     841:         ),
     842:         source_rows AS (
     843:           SELECT s.site_id, s.point_geometry
     844:           FROM sites_brownfield_planning_data s
END_CONTEXT

### line 849 needle=source_record_id signal=source_lineage_field

BEGIN_CONTEXT
     845:           WHERE s.point_geometry IS NOT NULL
     846:             AND ST_Intersects(s.point_geometry, (SELECT geom FROM parcel_extent))
     847:         )
     848:         SELECT
>>   849:           s.site_id AS source_record_id,
     850:           p.parcel_id,
     851:           CASE WHEN ST_Within(s.point_geometry, p.geometry) THEN 'point_within' ELSE 'point_nearest' END AS match_method,
     852:           CASE WHEN ST_Within(s.point_geometry, p.geometry) THEN 88.0
     853:                ELSE GREATEST(55.0, 80.0 - LEAST(ST_Distance(p.centroid, s.point_geometry) / :radius, 1.0) * 25.0)
END_CONTEXT

### line 859 needle=parcels signal=dataset_or_table_mapping

BEGIN_CONTEXT
     855:           ST_Distance(p.centroid, s.point_geometry) AS distance_m
     856:         FROM source_rows s
     857:         JOIN LATERAL (
     858:           SELECT parcel_id, geometry, centroid
>>   859:           FROM parcels_inspire
     860:           WHERE ST_Within(s.point_geometry, geometry)
     861:              OR ST_DWithin(centroid, s.point_geometry, :radius)
     862:           ORDER BY ST_Within(s.point_geometry, geometry) DESC, centroid <-> s.point_geometry
     863:           LIMIT 1
END_CONTEXT

### line 859 needle=parcels_inspire signal=dataset_or_table_mapping

BEGIN_CONTEXT
     855:           ST_Distance(p.centroid, s.point_geometry) AS distance_m
     856:         FROM source_rows s
     857:         JOIN LATERAL (
     858:           SELECT parcel_id, geometry, centroid
>>   859:           FROM parcels_inspire
     860:           WHERE ST_Within(s.point_geometry, geometry)
     861:              OR ST_DWithin(centroid, s.point_geometry, :radius)
     862:           ORDER BY ST_Within(s.point_geometry, geometry) DESC, centroid <-> s.point_geometry
     863:           LIMIT 1
END_CONTEXT

### line 868 needle=source_record_id signal=source_lineage_field

BEGIN_CONTEXT
     864:         ) p ON TRUE
     865:         '''
     866:     )
     867:     candidate_rows = session.execute(candidate_sql, {'radius': settings.point_match_radius_m}).mappings().all()
>>   868:     candidate_map = {str(row['source_record_id']): row for row in candidate_rows}
     869: 
     870:     rows = session.execute(_coverage_filtered_record_stmt(config).execution_options(yield_per=250)).scalars()
     871:     matched_count = 0
     872:     unmatched_issue_count = 0
END_CONTEXT

### line 876 needle=source_record_id signal=source_lineage_field

BEGIN_CONTEXT
     872:     unmatched_issue_count = 0
     873:     suppressed_unmatched_count = 0
     874: 
     875:     for record in rows:
>>   876:         source_record_id = getattr(record, config['record_id_attr'])
     877:         completeness = _completeness_score(record, [config['postcode_attr'], *config['name_attrs']])
     878:         record_local_authority = getattr(record, 'local_authority', None)
     879:         local_authority_filter = _resolve_local_authority_filter(record_local_authority, covered_authorities, authority_lookup)
     880:         candidates = _manual_override_candidates(session, 'planning_data_brownfield', source_record_id)
END_CONTEXT

### line 878 needle=local_authority signal=parcel_identity_mapping

BEGIN_CONTEXT
     874: 
     875:     for record in rows:
     876:         source_record_id = getattr(record, config['record_id_attr'])
     877:         completeness = _completeness_score(record, [config['postcode_attr'], *config['name_attrs']])
>>   878:         record_local_authority = getattr(record, 'local_authority', None)
     879:         local_authority_filter = _resolve_local_authority_filter(record_local_authority, covered_authorities, authority_lookup)
     880:         candidates = _manual_override_candidates(session, 'planning_data_brownfield', source_record_id)
     881:         if not candidates:
     882:             candidates = _hint_candidates(session, record, local_authority_filter)
END_CONTEXT

### line 879 needle=local_authority signal=parcel_identity_mapping

BEGIN_CONTEXT
     875:     for record in rows:
     876:         source_record_id = getattr(record, config['record_id_attr'])
     877:         completeness = _completeness_score(record, [config['postcode_attr'], *config['name_attrs']])
     878:         record_local_authority = getattr(record, 'local_authority', None)
>>   879:         local_authority_filter = _resolve_local_authority_filter(record_local_authority, covered_authorities, authority_lookup)
     880:         candidates = _manual_override_candidates(session, 'planning_data_brownfield', source_record_id)
     881:         if not candidates:
     882:             candidates = _hint_candidates(session, record, local_authority_filter)
     883: 
END_CONTEXT

### line 880 needle=source_record_id signal=source_lineage_field

BEGIN_CONTEXT
     876:         source_record_id = getattr(record, config['record_id_attr'])
     877:         completeness = _completeness_score(record, [config['postcode_attr'], *config['name_attrs']])
     878:         record_local_authority = getattr(record, 'local_authority', None)
     879:         local_authority_filter = _resolve_local_authority_filter(record_local_authority, covered_authorities, authority_lookup)
>>   880:         candidates = _manual_override_candidates(session, 'planning_data_brownfield', source_record_id)
     881:         if not candidates:
     882:             candidates = _hint_candidates(session, record, local_authority_filter)
     883: 
     884:         if not candidates:
END_CONTEXT

### line 882 needle=local_authority signal=parcel_identity_mapping

BEGIN_CONTEXT
     878:         record_local_authority = getattr(record, 'local_authority', None)
     879:         local_authority_filter = _resolve_local_authority_filter(record_local_authority, covered_authorities, authority_lookup)
     880:         candidates = _manual_override_candidates(session, 'planning_data_brownfield', source_record_id)
     881:         if not candidates:
>>   882:             candidates = _hint_candidates(session, record, local_authority_filter)
     883: 
     884:         if not candidates:
     885:             matched_row = candidate_map.get(str(source_record_id))
     886:             if matched_row is not None:
END_CONTEXT

### line 885 needle=source_record_id signal=source_lineage_field

BEGIN_CONTEXT
     881:         if not candidates:
     882:             candidates = _hint_candidates(session, record, local_authority_filter)
     883: 
     884:         if not candidates:
>>   885:             matched_row = candidate_map.get(str(source_record_id))
     886:             if matched_row is not None:
     887:                 candidates = [
     888:                     MatchCandidate(
     889:                         parcel_id=int(matched_row['parcel_id']),
END_CONTEXT

### line 896 needle=bulk signal=load_or_write_path

BEGIN_CONTEXT
     892:                         distance_m=float(matched_row['distance_m']) if matched_row['distance_m'] is not None else None,
     893:                     )
     894:                 ]
     895: 
>>   896:         # Bulk point matching is the fast path for the common case, but some planning-data
     897:         # rows only have polygon geometry or postcode/name fallback signals. Keep the generic
     898:         # matching ladder for those records so coverage grows instead of shrinking.
     899:         if not candidates and config['polygon_attr'] and getattr(record, config['polygon_attr']) is not None:
     900:             candidates = _polygon_candidates(session, getattr(record, config['polygon_attr']), local_authority_filter)
END_CONTEXT

### line 900 needle=local_authority signal=parcel_identity_mapping

BEGIN_CONTEXT
     896:         # Bulk point matching is the fast path for the common case, but some planning-data
     897:         # rows only have polygon geometry or postcode/name fallback signals. Keep the generic
     898:         # matching ladder for those records so coverage grows instead of shrinking.
     899:         if not candidates and config['polygon_attr'] and getattr(record, config['polygon_attr']) is not None:
>>   900:             candidates = _polygon_candidates(session, getattr(record, config['polygon_attr']), local_authority_filter)
     901:         if not candidates and config['polygon_attr'] and getattr(record, config['polygon_attr']) is not None:
     902:             candidates = _polygon_centroid_candidates(session, getattr(record, config['polygon_attr']), local_authority_filter)
     903:         if not candidates and config['point_attr'] and getattr(record, config['point_attr']) is not None:
     904:             candidates = _point_candidates(session, getattr(record, config['point_attr']), local_authority_filter)
END_CONTEXT

### line 902 needle=local_authority signal=parcel_identity_mapping

BEGIN_CONTEXT
     898:         # matching ladder for those records so coverage grows instead of shrinking.
     899:         if not candidates and config['polygon_attr'] and getattr(record, config['polygon_attr']) is not None:
     900:             candidates = _polygon_candidates(session, getattr(record, config['polygon_attr']), local_authority_filter)
     901:         if not candidates and config['polygon_attr'] and getattr(record, config['polygon_attr']) is not None:
>>   902:             candidates = _polygon_centroid_candidates(session, getattr(record, config['polygon_attr']), local_authority_filter)
     903:         if not candidates and config['point_attr'] and getattr(record, config['point_attr']) is not None:
     904:             candidates = _point_candidates(session, getattr(record, config['point_attr']), local_authority_filter)
     905:         if not candidates:
     906:             candidates = _postcode_candidates(session, getattr(record, config['postcode_attr'], None), local_authority_filter)
END_CONTEXT

### line 904 needle=local_authority signal=parcel_identity_mapping

BEGIN_CONTEXT
     900:             candidates = _polygon_candidates(session, getattr(record, config['polygon_attr']), local_authority_filter)
     901:         if not candidates and config['polygon_attr'] and getattr(record, config['polygon_attr']) is not None:
     902:             candidates = _polygon_centroid_candidates(session, getattr(record, config['polygon_attr']), local_authority_filter)
     903:         if not candidates and config['point_attr'] and getattr(record, config['point_attr']) is not None:
>>   904:             candidates = _point_candidates(session, getattr(record, config['point_attr']), local_authority_filter)
     905:         if not candidates:
     906:             candidates = _postcode_candidates(session, getattr(record, config['postcode_attr'], None), local_authority_filter)
     907:         if not candidates:
     908:             search_text = ' '.join(str(getattr(record, field, '') or '') for field in config['name_attrs']).strip()
END_CONTEXT

### line 906 needle=local_authority signal=parcel_identity_mapping

BEGIN_CONTEXT
     902:             candidates = _polygon_centroid_candidates(session, getattr(record, config['polygon_attr']), local_authority_filter)
     903:         if not candidates and config['point_attr'] and getattr(record, config['point_attr']) is not None:
     904:             candidates = _point_candidates(session, getattr(record, config['point_attr']), local_authority_filter)
     905:         if not candidates:
>>   906:             candidates = _postcode_candidates(session, getattr(record, config['postcode_attr'], None), local_authority_filter)
     907:         if not candidates:
     908:             search_text = ' '.join(str(getattr(record, field, '') or '') for field in config['name_attrs']).strip()
     909:             candidates = _fuzzy_candidates(session, search_text)
     910: 
END_CONTEXT

### line 914 needle=confidence signal=confidence_logic

BEGIN_CONTEXT
     910: 
     911:         if not candidates:
     912:             record.match_method = None
     913:             record.match_score = None
>>   914:             record.confidence_score = 0.0
     915:             record.requires_review = True
     916:             if unmatched_issue_count < settings.max_unmatched_dq_issues_per_run:
     917:                 _record_dq_issue(
     918:                     session,
END_CONTEXT

### line 920 needle=source_name signal=source_lineage_field

BEGIN_CONTEXT
     916:             if unmatched_issue_count < settings.max_unmatched_dq_issues_per_run:
     917:                 _record_dq_issue(
     918:                     session,
     919:                     run_id=run_id,
>>   920:                     source_name='planning_data_brownfield',
     921:                     source_record_id=source_record_id,
     922:                     message='No parcel match could be inferred for this source record.',
     923:                     payload={'record_id': source_record_id},
     924:                 )
END_CONTEXT

### line 921 needle=source_record_id signal=source_lineage_field

BEGIN_CONTEXT
     917:                 _record_dq_issue(
     918:                     session,
     919:                     run_id=run_id,
     920:                     source_name='planning_data_brownfield',
>>   921:                     source_record_id=source_record_id,
     922:                     message='No parcel match could be inferred for this source record.',
     923:                     payload={'record_id': source_record_id},
     924:                 )
     925:                 unmatched_issue_count += 1
END_CONTEXT

### line 923 needle=source_record_id signal=source_lineage_field

BEGIN_CONTEXT
     919:                     run_id=run_id,
     920:                     source_name='planning_data_brownfield',
     921:                     source_record_id=source_record_id,
     922:                     message='No parcel match could be inferred for this source record.',
>>   923:                     payload={'record_id': source_record_id},
     924:                 )
     925:                 unmatched_issue_count += 1
     926:             else:
     927:                 suppressed_unmatched_count += 1
END_CONTEXT

### line 931 needle=confidence signal=confidence_logic

BEGIN_CONTEXT
     927:                 suppressed_unmatched_count += 1
     928:             continue
     929: 
     930:         candidate = candidates[0]
>>   931:         source_confidence_fields = _build_match_source_confidence_fields(record, config, candidate)
     932:         confidence, requires_review = _score_candidate(
     933:             'planning_data_brownfield',
     934:             candidate,
     935:             getattr(record, 'source_updated_at', None),
END_CONTEXT

### line 932 needle=confidence signal=confidence_logic

BEGIN_CONTEXT
     928:             continue
     929: 
     930:         candidate = candidates[0]
     931:         source_confidence_fields = _build_match_source_confidence_fields(record, config, candidate)
>>   932:         confidence, requires_review = _score_candidate(
     933:             'planning_data_brownfield',
     934:             candidate,
     935:             getattr(record, 'source_updated_at', None),
     936:             completeness,
END_CONTEXT

### line 935 needle=source_updated_at signal=source_lineage_field

BEGIN_CONTEXT
     931:         source_confidence_fields = _build_match_source_confidence_fields(record, config, candidate)
     932:         confidence, requires_review = _score_candidate(
     933:             'planning_data_brownfield',
     934:             candidate,
>>   935:             getattr(record, 'source_updated_at', None),
     936:             completeness,
     937:             source_confidence_needs_review=bool(source_confidence_fields["source_confidence_needs_review"]),
     938:         )
     939:         requires_review = requires_review or bool(source_confidence_fields["source_confidence_needs_review"])
END_CONTEXT

### line 937 needle=confidence signal=confidence_logic

BEGIN_CONTEXT
     933:             'planning_data_brownfield',
     934:             candidate,
     935:             getattr(record, 'source_updated_at', None),
     936:             completeness,
>>   937:             source_confidence_needs_review=bool(source_confidence_fields["source_confidence_needs_review"]),
     938:         )
     939:         requires_review = requires_review or bool(source_confidence_fields["source_confidence_needs_review"])
     940:         session.add(
     941:             ListingParcelLink(
END_CONTEXT

### line 939 needle=confidence signal=confidence_logic

BEGIN_CONTEXT
     935:             getattr(record, 'source_updated_at', None),
     936:             completeness,
     937:             source_confidence_needs_review=bool(source_confidence_fields["source_confidence_needs_review"]),
     938:         )
>>   939:         requires_review = requires_review or bool(source_confidence_fields["source_confidence_needs_review"])
     940:         session.add(
     941:             ListingParcelLink(
     942:                 parcel_id=candidate.parcel_id,
     943:                 source_name='planning_data_brownfield',
END_CONTEXT

### line 943 needle=source_name signal=source_lineage_field

BEGIN_CONTEXT
     939:         requires_review = requires_review or bool(source_confidence_fields["source_confidence_needs_review"])
     940:         session.add(
     941:             ListingParcelLink(
     942:                 parcel_id=candidate.parcel_id,
>>   943:                 source_name='planning_data_brownfield',
     944:                 source_record_id=source_record_id,
     945:                 listing_id=None,
     946:                 match_method=candidate.match_method,
     947:                 overlap_ratio=candidate.overlap_ratio,
END_CONTEXT

### line 944 needle=source_record_id signal=source_lineage_field

BEGIN_CONTEXT
     940:         session.add(
     941:             ListingParcelLink(
     942:                 parcel_id=candidate.parcel_id,
     943:                 source_name='planning_data_brownfield',
>>   944:                 source_record_id=source_record_id,
     945:                 listing_id=None,
     946:                 match_method=candidate.match_method,
     947:                 overlap_ratio=candidate.overlap_ratio,
     948:                 distance_m=candidate.distance_m,
END_CONTEXT

### line 952 needle=confidence signal=confidence_logic

BEGIN_CONTEXT
     948:                 distance_m=candidate.distance_m,
     949:                 postcode_match=candidate.postcode_match,
     950:                 name_similarity=candidate.name_similarity,
     951:                 match_score=candidate.match_score,
>>   952:                 confidence_score=confidence,
     953:                 requires_review=requires_review,
     954:             )
     955:         )
     956:         matched_count += 1
END_CONTEXT

### line 959 needle=confidence signal=confidence_logic

BEGIN_CONTEXT
     955:         )
     956:         matched_count += 1
     957:         record.match_method = candidate.match_method
     958:         record.match_score = candidate.match_score
>>   959:         record.confidence_score = confidence
     960:         record.requires_review = requires_review
     961:         record.is_stale = freshness_score(getattr(record, 'source_updated_at', None), 'planning_data_brownfield') < 0.5
     962: 
     963:     if suppressed_unmatched_count:
END_CONTEXT

### line 961 needle=source_updated_at signal=source_lineage_field

BEGIN_CONTEXT
     957:         record.match_method = candidate.match_method
     958:         record.match_score = candidate.match_score
     959:         record.confidence_score = confidence
     960:         record.requires_review = requires_review
>>   961:         record.is_stale = freshness_score(getattr(record, 'source_updated_at', None), 'planning_data_brownfield') < 0.5
     962: 
     963:     if suppressed_unmatched_count:
     964:         _record_dq_issue(
     965:             session,
END_CONTEXT

### line 967 needle=source_name signal=source_lineage_field

BEGIN_CONTEXT
     963:     if suppressed_unmatched_count:
     964:         _record_dq_issue(
     965:             session,
     966:             run_id=run_id,
>>   967:             source_name='planning_data_brownfield',
     968:             source_record_id='__summary__',
     969:             message=f'Suppressed {suppressed_unmatched_count} additional unmatched record issues after the per-run cap was reached.',
     970:             rule_code='unmatched_record_summary',
     971:             payload={'suppressed_unmatched_count': suppressed_unmatched_count},
END_CONTEXT

### line 968 needle=source_record_id signal=source_lineage_field

BEGIN_CONTEXT
     964:         _record_dq_issue(
     965:             session,
     966:             run_id=run_id,
     967:             source_name='planning_data_brownfield',
>>   968:             source_record_id='__summary__',
     969:             message=f'Suppressed {suppressed_unmatched_count} additional unmatched record issues after the per-run cap was reached.',
     970:             rule_code='unmatched_record_summary',
     971:             payload={'suppressed_unmatched_count': suppressed_unmatched_count},
     972:         )
END_CONTEXT

### line 977 needle=source_name signal=source_lineage_field

BEGIN_CONTEXT
     973:     session.flush()
     974:     return matched_count
     975: 
     976: 
>>   977: def match_source_records(session: Session, source_name: str, run_id: str) -> int:
     978:     if source_name == 'planning_data_brownfield':
     979:         return _match_planning_data_brownfield_records(session, run_id)
     980: 
     981:     config = SOURCE_MODEL_CONFIG[source_name]
END_CONTEXT

### line 978 needle=source_name signal=source_lineage_field

BEGIN_CONTEXT
     974:     return matched_count
     975: 
     976: 
     977: def match_source_records(session: Session, source_name: str, run_id: str) -> int:
>>   978:     if source_name == 'planning_data_brownfield':
     979:         return _match_planning_data_brownfield_records(session, run_id)
     980: 
     981:     config = SOURCE_MODEL_CONFIG[source_name]
     982:     model = config['model']
END_CONTEXT

### line 981 needle=source_name signal=source_lineage_field

BEGIN_CONTEXT
     977: def match_source_records(session: Session, source_name: str, run_id: str) -> int:
     978:     if source_name == 'planning_data_brownfield':
     979:         return _match_planning_data_brownfield_records(session, run_id)
     980: 
>>   981:     config = SOURCE_MODEL_CONFIG[source_name]
     982:     model = config['model']
     983:     # History transactions (hmlr_price_paid) are high-volume.
     984:     # Distinct authority scans on large parcel tables can hit statement timeout
     985:     # before matching even starts, so skip authority pre-filtering for this source.
END_CONTEXT

### line 983 needle=high signal=confidence_logic

BEGIN_CONTEXT
     979:         return _match_planning_data_brownfield_records(session, run_id)
     980: 
     981:     config = SOURCE_MODEL_CONFIG[source_name]
     982:     model = config['model']
>>   983:     # History transactions (hmlr_price_paid) are high-volume.
     984:     # Distinct authority scans on large parcel tables can hit statement timeout
     985:     # before matching even starts, so skip authority pre-filtering for this source.
     986:     if source_name == 'hmlr_price_paid':
     987:         covered_authorities = set()
END_CONTEXT

### line 986 needle=source_name signal=source_lineage_field

BEGIN_CONTEXT
     982:     model = config['model']
     983:     # History transactions (hmlr_price_paid) are high-volume.
     984:     # Distinct authority scans on large parcel tables can hit statement timeout
     985:     # before matching even starts, so skip authority pre-filtering for this source.
>>   986:     if source_name == 'hmlr_price_paid':
     987:         covered_authorities = set()
     988:         authority_lookup: dict[str, str | None] = {}
     989:     else:
     990:         covered_authorities = _covered_authorities(session)
END_CONTEXT

### line 992 needle=source_name signal=source_lineage_field

BEGIN_CONTEXT
     988:         authority_lookup: dict[str, str | None] = {}
     989:     else:
     990:         covered_authorities = _covered_authorities(session)
     991:         authority_lookup = _covered_authority_lookup(session)
>>   992:     if source_name == 'hmlr_price_paid':
     993:         _ensure_hmlr_link_columns(session)
     994:     session.execute(delete(ListingParcelLink).where(ListingParcelLink.source_name == source_name))
     995:     session.flush()
     996: 
END_CONTEXT

### line 994 needle=source_name signal=source_lineage_field

BEGIN_CONTEXT
     990:         covered_authorities = _covered_authorities(session)
     991:         authority_lookup = _covered_authority_lookup(session)
     992:     if source_name == 'hmlr_price_paid':
     993:         _ensure_hmlr_link_columns(session)
>>   994:     session.execute(delete(ListingParcelLink).where(ListingParcelLink.source_name == source_name))
     995:     session.flush()
     996: 
     997:     london_market_postcodes: set[str] = set()
     998:     if source_name == 'hmlr_price_paid':
END_CONTEXT

### line 998 needle=source_name signal=source_lineage_field

BEGIN_CONTEXT
     994:     session.execute(delete(ListingParcelLink).where(ListingParcelLink.source_name == source_name))
     995:     session.flush()
     996: 
     997:     london_market_postcodes: set[str] = set()
>>   998:     if source_name == 'hmlr_price_paid':
     999:         london_market_postcodes = _london_market_postcodes(session)
    1000:         postcode_column = getattr(model, config['postcode_attr'])
    1001:         market_postcode_exists = exists(
    1002:             select(ListingsMarketAdapter.id).where(
END_CONTEXT

### line 1024 needle=source_record_id signal=source_lineage_field

BEGIN_CONTEXT
    1020:     matched_count = 0
    1021:     unmatched_issue_count = 0
    1022:     suppressed_unmatched_count = 0
    1023:     for record in rows:
>>  1024:         source_record_id = getattr(record, config['record_id_attr'])
    1025:         listing_id = getattr(record, config['listing_id_attr']) if config['listing_id_attr'] else None
    1026:         completeness = _completeness_score(record, [config['postcode_attr'], *config['name_attrs']])
    1027:         record_local_authority = getattr(record, 'local_authority', None)
    1028:         local_authority_filter = _resolve_local_authority_filter(record_local_authority, covered_authorities, authority_lookup)
END_CONTEXT

### line 1027 needle=local_authority signal=parcel_identity_mapping

BEGIN_CONTEXT
    1023:     for record in rows:
    1024:         source_record_id = getattr(record, config['record_id_attr'])
    1025:         listing_id = getattr(record, config['listing_id_attr']) if config['listing_id_attr'] else None
    1026:         completeness = _completeness_score(record, [config['postcode_attr'], *config['name_attrs']])
>>  1027:         record_local_authority = getattr(record, 'local_authority', None)
    1028:         local_authority_filter = _resolve_local_authority_filter(record_local_authority, covered_authorities, authority_lookup)
    1029:         candidates = _manual_override_candidates(session, source_name, source_record_id)
    1030:         if not candidates:
    1031:             candidates = _hint_candidates(session, record, local_authority_filter)
END_CONTEXT

### line 1028 needle=local_authority signal=parcel_identity_mapping

BEGIN_CONTEXT
    1024:         source_record_id = getattr(record, config['record_id_attr'])
    1025:         listing_id = getattr(record, config['listing_id_attr']) if config['listing_id_attr'] else None
    1026:         completeness = _completeness_score(record, [config['postcode_attr'], *config['name_attrs']])
    1027:         record_local_authority = getattr(record, 'local_authority', None)
>>  1028:         local_authority_filter = _resolve_local_authority_filter(record_local_authority, covered_authorities, authority_lookup)
    1029:         candidates = _manual_override_candidates(session, source_name, source_record_id)
    1030:         if not candidates:
    1031:             candidates = _hint_candidates(session, record, local_authority_filter)
    1032: 
END_CONTEXT

### line 1029 needle=source_name signal=source_lineage_field

BEGIN_CONTEXT
    1025:         listing_id = getattr(record, config['listing_id_attr']) if config['listing_id_attr'] else None
    1026:         completeness = _completeness_score(record, [config['postcode_attr'], *config['name_attrs']])
    1027:         record_local_authority = getattr(record, 'local_authority', None)
    1028:         local_authority_filter = _resolve_local_authority_filter(record_local_authority, covered_authorities, authority_lookup)
>>  1029:         candidates = _manual_override_candidates(session, source_name, source_record_id)
    1030:         if not candidates:
    1031:             candidates = _hint_candidates(session, record, local_authority_filter)
    1032: 
    1033:         hmlr_scope: str | None = None
END_CONTEXT

### line 1029 needle=source_record_id signal=source_lineage_field

BEGIN_CONTEXT
    1025:         listing_id = getattr(record, config['listing_id_attr']) if config['listing_id_attr'] else None
    1026:         completeness = _completeness_score(record, [config['postcode_attr'], *config['name_attrs']])
    1027:         record_local_authority = getattr(record, 'local_authority', None)
    1028:         local_authority_filter = _resolve_local_authority_filter(record_local_authority, covered_authorities, authority_lookup)
>>  1029:         candidates = _manual_override_candidates(session, source_name, source_record_id)
    1030:         if not candidates:
    1031:             candidates = _hint_candidates(session, record, local_authority_filter)
    1032: 
    1033:         hmlr_scope: str | None = None
END_CONTEXT

### line 1031 needle=local_authority signal=parcel_identity_mapping

BEGIN_CONTEXT
    1027:         record_local_authority = getattr(record, 'local_authority', None)
    1028:         local_authority_filter = _resolve_local_authority_filter(record_local_authority, covered_authorities, authority_lookup)
    1029:         candidates = _manual_override_candidates(session, source_name, source_record_id)
    1030:         if not candidates:
>>  1031:             candidates = _hint_candidates(session, record, local_authority_filter)
    1032: 
    1033:         hmlr_scope: str | None = None
    1034:         if source_name == 'hmlr_price_paid':
    1035:             normalized_postcode = _normalize_postcode_value(getattr(record, config['postcode_attr'], None))
END_CONTEXT

### line 1034 needle=source_name signal=source_lineage_field

BEGIN_CONTEXT
    1030:         if not candidates:
    1031:             candidates = _hint_candidates(session, record, local_authority_filter)
    1032: 
    1033:         hmlr_scope: str | None = None
>>  1034:         if source_name == 'hmlr_price_paid':
    1035:             normalized_postcode = _normalize_postcode_value(getattr(record, config['postcode_attr'], None))
    1036:             hmlr_scope = _classify_hmlr_source_scope(normalized_postcode, london_market_postcodes)
    1037:             if hmlr_scope in {'london_market_postcode', 'london_prefix_candidate'}:
    1038:                 hmlr_candidate, diagnostics = _hmlr_london_tiered_candidate(
END_CONTEXT

### line 1049 needle=confidence signal=confidence_logic

BEGIN_CONTEXT
    1045:                     candidates = [hmlr_candidate]
    1046:                 else:
    1047:                     record.match_method = diagnostics.get('reason')
    1048:                     record.match_score = None
>>  1049:                     record.confidence_score = 0.0
    1050:                     record.requires_review = True
    1051:                     if unmatched_issue_count < settings.max_unmatched_dq_issues_per_run:
    1052:                         _record_dq_issue(
    1053:                             session,
END_CONTEXT

### line 1055 needle=source_name signal=source_lineage_field

BEGIN_CONTEXT
    1051:                     if unmatched_issue_count < settings.max_unmatched_dq_issues_per_run:
    1052:                         _record_dq_issue(
    1053:                             session,
    1054:                             run_id=run_id,
>>  1055:                             source_name=source_name,
    1056:                             source_record_id=source_record_id,
    1057:                             message='HMLR London candidate matched review/reject thresholds and was not published.',
    1058:                             rule_code=f"hmlr_history_{diagnostics.get('match_tier', 'tier_d')}",
    1059:                             payload=diagnostics,
END_CONTEXT

### line 1056 needle=source_record_id signal=source_lineage_field

BEGIN_CONTEXT
    1052:                         _record_dq_issue(
    1053:                             session,
    1054:                             run_id=run_id,
    1055:                             source_name=source_name,
>>  1056:                             source_record_id=source_record_id,
    1057:                             message='HMLR London candidate matched review/reject thresholds and was not published.',
    1058:                             rule_code=f"hmlr_history_{diagnostics.get('match_tier', 'tier_d')}",
    1059:                             payload=diagnostics,
    1060:                         )
END_CONTEXT

### line 1067 needle=local_authority signal=parcel_identity_mapping

BEGIN_CONTEXT
    1063:                         suppressed_unmatched_count += 1
    1064:                     continue
    1065: 
    1066:         if not candidates and config['polygon_attr'] and getattr(record, config['polygon_attr']) is not None:
>>  1067:             candidates = _polygon_candidates(session, getattr(record, config['polygon_attr']), local_authority_filter)
    1068:         if not candidates and config['polygon_attr'] and getattr(record, config['polygon_attr']) is not None:
    1069:             candidates = _polygon_centroid_candidates(session, getattr(record, config['polygon_attr']), local_authority_filter)
    1070:         if not candidates and config['point_attr'] and getattr(record, config['point_attr']) is not None:
    1071:             candidates = _point_candidates(session, getattr(record, config['point_attr']), local_authority_filter)
END_CONTEXT

### line 1069 needle=local_authority signal=parcel_identity_mapping

BEGIN_CONTEXT
    1065: 
    1066:         if not candidates and config['polygon_attr'] and getattr(record, config['polygon_attr']) is not None:
    1067:             candidates = _polygon_candidates(session, getattr(record, config['polygon_attr']), local_authority_filter)
    1068:         if not candidates and config['polygon_attr'] and getattr(record, config['polygon_attr']) is not None:
>>  1069:             candidates = _polygon_centroid_candidates(session, getattr(record, config['polygon_attr']), local_authority_filter)
    1070:         if not candidates and config['point_attr'] and getattr(record, config['point_attr']) is not None:
    1071:             candidates = _point_candidates(session, getattr(record, config['point_attr']), local_authority_filter)
    1072:         if not candidates:
    1073:             candidates = _postcode_candidates(session, getattr(record, config['postcode_attr'], None), local_authority_filter)
END_CONTEXT

### line 1071 needle=local_authority signal=parcel_identity_mapping

BEGIN_CONTEXT
    1067:             candidates = _polygon_candidates(session, getattr(record, config['polygon_attr']), local_authority_filter)
    1068:         if not candidates and config['polygon_attr'] and getattr(record, config['polygon_attr']) is not None:
    1069:             candidates = _polygon_centroid_candidates(session, getattr(record, config['polygon_attr']), local_authority_filter)
    1070:         if not candidates and config['point_attr'] and getattr(record, config['point_attr']) is not None:
>>  1071:             candidates = _point_candidates(session, getattr(record, config['point_attr']), local_authority_filter)
    1072:         if not candidates:
    1073:             candidates = _postcode_candidates(session, getattr(record, config['postcode_attr'], None), local_authority_filter)
    1074:         if not candidates and source_name == 'hmlr_price_paid':
    1075:             candidates = _market_postcode_bridge_candidates(session, getattr(record, config['postcode_attr'], None))
END_CONTEXT

### line 1073 needle=local_authority signal=parcel_identity_mapping

BEGIN_CONTEXT
    1069:             candidates = _polygon_centroid_candidates(session, getattr(record, config['polygon_attr']), local_authority_filter)
    1070:         if not candidates and config['point_attr'] and getattr(record, config['point_attr']) is not None:
    1071:             candidates = _point_candidates(session, getattr(record, config['point_attr']), local_authority_filter)
    1072:         if not candidates:
>>  1073:             candidates = _postcode_candidates(session, getattr(record, config['postcode_attr'], None), local_authority_filter)
    1074:         if not candidates and source_name == 'hmlr_price_paid':
    1075:             candidates = _market_postcode_bridge_candidates(session, getattr(record, config['postcode_attr'], None))
    1076:         if not candidates and source_name != 'hmlr_price_paid':
    1077:             search_text = ' '.join(str(getattr(record, field, '') or '') for field in config['name_attrs']).strip()
END_CONTEXT

### line 1074 needle=source_name signal=source_lineage_field

BEGIN_CONTEXT
    1070:         if not candidates and config['point_attr'] and getattr(record, config['point_attr']) is not None:
    1071:             candidates = _point_candidates(session, getattr(record, config['point_attr']), local_authority_filter)
    1072:         if not candidates:
    1073:             candidates = _postcode_candidates(session, getattr(record, config['postcode_attr'], None), local_authority_filter)
>>  1074:         if not candidates and source_name == 'hmlr_price_paid':
    1075:             candidates = _market_postcode_bridge_candidates(session, getattr(record, config['postcode_attr'], None))
    1076:         if not candidates and source_name != 'hmlr_price_paid':
    1077:             search_text = ' '.join(str(getattr(record, field, '') or '') for field in config['name_attrs']).strip()
    1078:             candidates = _fuzzy_candidates(session, search_text)
END_CONTEXT

### line 1076 needle=source_name signal=source_lineage_field

BEGIN_CONTEXT
    1072:         if not candidates:
    1073:             candidates = _postcode_candidates(session, getattr(record, config['postcode_attr'], None), local_authority_filter)
    1074:         if not candidates and source_name == 'hmlr_price_paid':
    1075:             candidates = _market_postcode_bridge_candidates(session, getattr(record, config['postcode_attr'], None))
>>  1076:         if not candidates and source_name != 'hmlr_price_paid':
    1077:             search_text = ' '.join(str(getattr(record, field, '') or '') for field in config['name_attrs']).strip()
    1078:             candidates = _fuzzy_candidates(session, search_text)
    1079: 
    1080:         if not candidates:
END_CONTEXT

### line 1083 needle=confidence signal=confidence_logic

BEGIN_CONTEXT
    1079: 
    1080:         if not candidates:
    1081:             record.match_method = None
    1082:             record.match_score = None
>>  1083:             record.confidence_score = 0.0
    1084:             record.requires_review = True
    1085:             if unmatched_issue_count < settings.max_unmatched_dq_issues_per_run:
    1086:                 _record_dq_issue(session, run_id=run_id, source_name=source_name, source_record_id=source_record_id, message='No parcel match could be inferred for this source record.', payload={'record_id': source_record_id})
    1087:                 unmatched_issue_count += 1
END_CONTEXT

### line 1086 needle=source_name signal=source_lineage_field

BEGIN_CONTEXT
    1082:             record.match_score = None
    1083:             record.confidence_score = 0.0
    1084:             record.requires_review = True
    1085:             if unmatched_issue_count < settings.max_unmatched_dq_issues_per_run:
>>  1086:                 _record_dq_issue(session, run_id=run_id, source_name=source_name, source_record_id=source_record_id, message='No parcel match could be inferred for this source record.', payload={'record_id': source_record_id})
    1087:                 unmatched_issue_count += 1
    1088:             else:
    1089:                 suppressed_unmatched_count += 1
    1090:             continue
END_CONTEXT

### line 1086 needle=source_record_id signal=source_lineage_field

BEGIN_CONTEXT
    1082:             record.match_score = None
    1083:             record.confidence_score = 0.0
    1084:             record.requires_review = True
    1085:             if unmatched_issue_count < settings.max_unmatched_dq_issues_per_run:
>>  1086:                 _record_dq_issue(session, run_id=run_id, source_name=source_name, source_record_id=source_record_id, message='No parcel match could be inferred for this source record.', payload={'record_id': source_record_id})
    1087:                 unmatched_issue_count += 1
    1088:             else:
    1089:                 suppressed_unmatched_count += 1
    1090:             continue
END_CONTEXT

### line 1092 needle=source_name signal=source_lineage_field

BEGIN_CONTEXT
    1088:             else:
    1089:                 suppressed_unmatched_count += 1
    1090:             continue
    1091: 
>>  1092:         if source_name == 'hmlr_price_paid' and hmlr_scope in {'london_market_postcode', 'london_prefix_candidate'}:
    1093:             publishable_candidates = [candidate for candidate in candidates if candidate.can_publish_history_signal]
    1094:             if not publishable_candidates:
    1095:                 record.match_method = 'non_publishable_candidate'
    1096:                 record.match_score = None
END_CONTEXT

### line 1097 needle=confidence signal=confidence_logic

BEGIN_CONTEXT
    1093:             publishable_candidates = [candidate for candidate in candidates if candidate.can_publish_history_signal]
    1094:             if not publishable_candidates:
    1095:                 record.match_method = 'non_publishable_candidate'
    1096:                 record.match_score = None
>>  1097:                 record.confidence_score = 0.0
    1098:                 record.requires_review = True
    1099:                 if unmatched_issue_count < settings.max_unmatched_dq_issues_per_run:
    1100:                     _record_dq_issue(
    1101:                         session,
END_CONTEXT

### line 1103 needle=source_name signal=source_lineage_field

BEGIN_CONTEXT
    1099:                 if unmatched_issue_count < settings.max_unmatched_dq_issues_per_run:
    1100:                     _record_dq_issue(
    1101:                         session,
    1102:                         run_id=run_id,
>>  1103:                         source_name=source_name,
    1104:                         source_record_id=source_record_id,
    1105:                         message='HMLR candidate exists but is not publishable under current tier thresholds.',
    1106:                         rule_code='hmlr_history_tier_c',
    1107:                         payload={
END_CONTEXT

### line 1104 needle=source_record_id signal=source_lineage_field

BEGIN_CONTEXT
    1100:                     _record_dq_issue(
    1101:                         session,
    1102:                         run_id=run_id,
    1103:                         source_name=source_name,
>>  1104:                         source_record_id=source_record_id,
    1105:                         message='HMLR candidate exists but is not publishable under current tier thresholds.',
    1106:                         rule_code='hmlr_history_tier_c',
    1107:                         payload={
    1108:                             'source_scope': hmlr_scope or 'unknown',
END_CONTEXT

### line 1124 needle=confidence signal=confidence_logic

BEGIN_CONTEXT
    1120:             for candidate in candidates:
    1121:                 if abs(top - candidate.match_score) <= 5.0:
    1122:                     candidate.requires_review = True
    1123: 
>>  1124:         best_confidence = 0.0
    1125:         best_candidate = candidates[0]
    1126:         for candidate in candidates:
    1127:             source_confidence_fields = _build_match_source_confidence_fields(record, config, candidate)
    1128:             if candidate.forced_confidence_score is not None:
END_CONTEXT

### line 1127 needle=confidence signal=confidence_logic

BEGIN_CONTEXT
    1123: 
    1124:         best_confidence = 0.0
    1125:         best_candidate = candidates[0]
    1126:         for candidate in candidates:
>>  1127:             source_confidence_fields = _build_match_source_confidence_fields(record, config, candidate)
    1128:             if candidate.forced_confidence_score is not None:
    1129:                 confidence = float(candidate.forced_confidence_score)
    1130:                 requires_review = bool(candidate.requires_review) or bool(
    1131:                     source_confidence_fields["source_confidence_needs_review"]
END_CONTEXT

### line 1128 needle=confidence signal=confidence_logic

BEGIN_CONTEXT
    1124:         best_confidence = 0.0
    1125:         best_candidate = candidates[0]
    1126:         for candidate in candidates:
    1127:             source_confidence_fields = _build_match_source_confidence_fields(record, config, candidate)
>>  1128:             if candidate.forced_confidence_score is not None:
    1129:                 confidence = float(candidate.forced_confidence_score)
    1130:                 requires_review = bool(candidate.requires_review) or bool(
    1131:                     source_confidence_fields["source_confidence_needs_review"]
    1132:                 )
END_CONTEXT

### line 1129 needle=confidence signal=confidence_logic

BEGIN_CONTEXT
    1125:         best_candidate = candidates[0]
    1126:         for candidate in candidates:
    1127:             source_confidence_fields = _build_match_source_confidence_fields(record, config, candidate)
    1128:             if candidate.forced_confidence_score is not None:
>>  1129:                 confidence = float(candidate.forced_confidence_score)
    1130:                 requires_review = bool(candidate.requires_review) or bool(
    1131:                     source_confidence_fields["source_confidence_needs_review"]
    1132:                 )
    1133:             else:
END_CONTEXT

### line 1131 needle=confidence signal=confidence_logic

BEGIN_CONTEXT
    1127:             source_confidence_fields = _build_match_source_confidence_fields(record, config, candidate)
    1128:             if candidate.forced_confidence_score is not None:
    1129:                 confidence = float(candidate.forced_confidence_score)
    1130:                 requires_review = bool(candidate.requires_review) or bool(
>>  1131:                     source_confidence_fields["source_confidence_needs_review"]
    1132:                 )
    1133:             else:
    1134:                 confidence, requires_review = _score_candidate(
    1135:                     source_name,
END_CONTEXT

### line 1134 needle=confidence signal=confidence_logic

BEGIN_CONTEXT
    1130:                 requires_review = bool(candidate.requires_review) or bool(
    1131:                     source_confidence_fields["source_confidence_needs_review"]
    1132:                 )
    1133:             else:
>>  1134:                 confidence, requires_review = _score_candidate(
    1135:                     source_name,
    1136:                     candidate,
    1137:                     getattr(record, 'source_updated_at', None),
    1138:                     completeness,
END_CONTEXT

### line 1135 needle=source_name signal=source_lineage_field

BEGIN_CONTEXT
    1131:                     source_confidence_fields["source_confidence_needs_review"]
    1132:                 )
    1133:             else:
    1134:                 confidence, requires_review = _score_candidate(
>>  1135:                     source_name,
    1136:                     candidate,
    1137:                     getattr(record, 'source_updated_at', None),
    1138:                     completeness,
    1139:                     source_confidence_needs_review=bool(source_confidence_fields["source_confidence_needs_review"]),
END_CONTEXT

### line 1137 needle=source_updated_at signal=source_lineage_field

BEGIN_CONTEXT
    1133:             else:
    1134:                 confidence, requires_review = _score_candidate(
    1135:                     source_name,
    1136:                     candidate,
>>  1137:                     getattr(record, 'source_updated_at', None),
    1138:                     completeness,
    1139:                     source_confidence_needs_review=bool(source_confidence_fields["source_confidence_needs_review"]),
    1140:                 )
    1141:                 requires_review = requires_review or bool(source_confidence_fields["source_confidence_needs_review"])
END_CONTEXT

### line 1139 needle=confidence signal=confidence_logic

BEGIN_CONTEXT
    1135:                     source_name,
    1136:                     candidate,
    1137:                     getattr(record, 'source_updated_at', None),
    1138:                     completeness,
>>  1139:                     source_confidence_needs_review=bool(source_confidence_fields["source_confidence_needs_review"]),
    1140:                 )
    1141:                 requires_review = requires_review or bool(source_confidence_fields["source_confidence_needs_review"])
    1142:             session.add(
    1143:                 ListingParcelLink(
END_CONTEXT

### line 1141 needle=confidence signal=confidence_logic

BEGIN_CONTEXT
    1137:                     getattr(record, 'source_updated_at', None),
    1138:                     completeness,
    1139:                     source_confidence_needs_review=bool(source_confidence_fields["source_confidence_needs_review"]),
    1140:                 )
>>  1141:                 requires_review = requires_review or bool(source_confidence_fields["source_confidence_needs_review"])
    1142:             session.add(
    1143:                 ListingParcelLink(
    1144:                     parcel_id=candidate.parcel_id,
    1145:                     source_name=source_name,
END_CONTEXT

### line 1145 needle=source_name signal=source_lineage_field

BEGIN_CONTEXT
    1141:                 requires_review = requires_review or bool(source_confidence_fields["source_confidence_needs_review"])
    1142:             session.add(
    1143:                 ListingParcelLink(
    1144:                     parcel_id=candidate.parcel_id,
>>  1145:                     source_name=source_name,
    1146:                     source_record_id=source_record_id,
    1147:                     listing_id=listing_id,
    1148:                     match_method=candidate.match_method,
    1149:                     overlap_ratio=candidate.overlap_ratio,
END_CONTEXT

### line 1146 needle=source_record_id signal=source_lineage_field

BEGIN_CONTEXT
    1142:             session.add(
    1143:                 ListingParcelLink(
    1144:                     parcel_id=candidate.parcel_id,
    1145:                     source_name=source_name,
>>  1146:                     source_record_id=source_record_id,
    1147:                     listing_id=listing_id,
    1148:                     match_method=candidate.match_method,
    1149:                     overlap_ratio=candidate.overlap_ratio,
    1150:                     distance_m=candidate.distance_m,
END_CONTEXT

### line 1154 needle=confidence signal=confidence_logic

BEGIN_CONTEXT
    1150:                     distance_m=candidate.distance_m,
    1151:                     postcode_match=candidate.postcode_match,
    1152:                     name_similarity=candidate.name_similarity,
    1153:                     match_score=candidate.match_score,
>>  1154:                     confidence_score=confidence,
    1155:                     requires_review=requires_review,
    1156:                     source_scope=candidate.source_scope or hmlr_scope,
    1157:                     match_tier=candidate.match_tier,
    1158:                     can_publish_history_signal=bool(candidate.can_publish_history_signal),
END_CONTEXT

### line 1162 needle=confidence signal=confidence_logic

BEGIN_CONTEXT
    1158:                     can_publish_history_signal=bool(candidate.can_publish_history_signal),
    1159:                 )
    1160:             )
    1161:             matched_count += 1
>>  1162:             if confidence >= best_confidence:
    1163:                 best_confidence = confidence
    1164:                 best_candidate = candidate
    1165:                 record.match_method = candidate.match_method
    1166:                 record.match_score = candidate.match_score
END_CONTEXT

### line 1163 needle=confidence signal=confidence_logic

BEGIN_CONTEXT
    1159:                 )
    1160:             )
    1161:             matched_count += 1
    1162:             if confidence >= best_confidence:
>>  1163:                 best_confidence = confidence
    1164:                 best_candidate = candidate
    1165:                 record.match_method = candidate.match_method
    1166:                 record.match_score = candidate.match_score
    1167:                 record.confidence_score = confidence
END_CONTEXT

### line 1167 needle=confidence signal=confidence_logic

BEGIN_CONTEXT
    1163:                 best_confidence = confidence
    1164:                 best_candidate = candidate
    1165:                 record.match_method = candidate.match_method
    1166:                 record.match_score = candidate.match_score
>>  1167:                 record.confidence_score = confidence
    1168:                 record.requires_review = requires_review
    1169:         record.is_stale = freshness_score(getattr(record, 'source_updated_at', None), source_name) < 0.5
    1170:     if suppressed_unmatched_count:
    1171:         _record_dq_issue(
END_CONTEXT

### line 1169 needle=source_name signal=source_lineage_field

BEGIN_CONTEXT
    1165:                 record.match_method = candidate.match_method
    1166:                 record.match_score = candidate.match_score
    1167:                 record.confidence_score = confidence
    1168:                 record.requires_review = requires_review
>>  1169:         record.is_stale = freshness_score(getattr(record, 'source_updated_at', None), source_name) < 0.5
    1170:     if suppressed_unmatched_count:
    1171:         _record_dq_issue(
    1172:             session,
    1173:             run_id=run_id,
END_CONTEXT

### line 1169 needle=source_updated_at signal=source_lineage_field

BEGIN_CONTEXT
    1165:                 record.match_method = candidate.match_method
    1166:                 record.match_score = candidate.match_score
    1167:                 record.confidence_score = confidence
    1168:                 record.requires_review = requires_review
>>  1169:         record.is_stale = freshness_score(getattr(record, 'source_updated_at', None), source_name) < 0.5
    1170:     if suppressed_unmatched_count:
    1171:         _record_dq_issue(
    1172:             session,
    1173:             run_id=run_id,
END_CONTEXT

### line 1174 needle=source_name signal=source_lineage_field

BEGIN_CONTEXT
    1170:     if suppressed_unmatched_count:
    1171:         _record_dq_issue(
    1172:             session,
    1173:             run_id=run_id,
>>  1174:             source_name=source_name,
    1175:             source_record_id='__summary__',
    1176:             message=f'Suppressed {suppressed_unmatched_count} additional unmatched record issues after the per-run cap was reached.',
    1177:             rule_code='unmatched_record_summary',
    1178:             payload={'suppressed_unmatched_count': suppressed_unmatched_count},
END_CONTEXT

### line 1175 needle=source_record_id signal=source_lineage_field

BEGIN_CONTEXT
    1171:         _record_dq_issue(
    1172:             session,
    1173:             run_id=run_id,
    1174:             source_name=source_name,
>>  1175:             source_record_id='__summary__',
    1176:             message=f'Suppressed {suppressed_unmatched_count} additional unmatched record issues after the per-run cap was reached.',
    1177:             rule_code='unmatched_record_summary',
    1178:             payload={'suppressed_unmatched_count': suppressed_unmatched_count},
    1179:         )
END_CONTEXT

## app\etl\authority_checkpoint.py

FILE_NOT_FOUND

## app\db\models.py

FILE_NOT_FOUND

