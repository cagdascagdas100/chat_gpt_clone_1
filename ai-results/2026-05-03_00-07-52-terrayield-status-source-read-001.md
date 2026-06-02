# ChatGPT Runner Result

## Task
Read sales history status route source

## Task ID
terrayield-status-source-read-001

## Progress
88%

## Time
05/03/2026 00:07:54

## Working Directory
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence

## Exit Code
0

## Command
Write-Output 'TASK: sales-history/status kaynak kodu okuma'; Write-Output 'PROGRESS: 88%'; Write-Output 'ESTIMATED_WAIT: 2-3 dakika'; Write-Output 'START_TIME:'; Get-Date; $file='app\api\routes\aays_sales_history_layers.py'; Write-Output ('FILE_EXISTS=' + (Test-Path $file)); Write-Output '--- LINES 1-180 ---'; if (Test-Path $file) { $lines=Get-Content $file; for ($i=0; $i -lt [Math]::Min(180,$lines.Count); $i++) { Write-Output ((($i+1).ToString()) + ': ' + $lines[$i]) } }; Write-Output '--- FUNCTION AND SQL KEYWORDS ---'; if (Test-Path $file) { Select-String -Path $file -Pattern 'def status|count\(|COUNT\(|select\(|session|execute|sales_history|official|external|parcel|status\)' -CaseSensitive:$false | Select-Object -First 160 | ForEach-Object { $_.LineNumber.ToString() + ': ' + $_.Line } }; Write-Output 'END_TIME:'; Get-Date; Write-Output 'STATUS_SOURCE_READ_DONE'

## Output
TASK: sales-history/status kaynak kodu okuma
PROGRESS: 88%
ESTIMATED_WAIT: 2-3 dakika
START_TIME:

3 Mayıs 2026 Pazar 00:07:53
FILE_EXISTS=True
--- LINES 1-180 ---
1: from __future__ import annotations
2: 
3: import json
4: import os
5: import re
6: from functools import lru_cache
7: from typing import Any
8: 
9: from fastapi import APIRouter, HTTPException
10: from sqlalchemy import create_engine, text
11: 
12: router = APIRouter(tags=["aays-sales-history"])
13: 
14: CANDIDATE_URLS = json.loads(r'''["postgresql://postgres:postgres@db:5432/terrayield_land","postgresql://postgres:postgres@db:5432/postgres","postgresql://postgres:postgres@localhost:55460/terrayield_land","postgresql://postgres:postgres@localhost:55460/postgres","postgresql://postgres:postgres@127.0.0.1:55460/terrayield_land","postgresql://postgres:postgres@127.0.0.1:55460/postgres"]''')
15: 
16: 
17: def _raw_database_url():
18:     return (
19:         os.getenv("DATABASE_URL")
20:         or os.getenv("SQLALCHEMY_DATABASE_URI")
21:         or os.getenv("POSTGRES_URL")
22:         or os.getenv("DB_URL")
23:     )
24: 
25: 
26: def _normalize_url(url: str) -> str:
27:     if url.startswith("postgres://"):
28:         return "postgresql://" + url[len("postgres://"):]
29:     return url
30: 
31: 
32: def _driver_variants(url: str):
33:     url = _normalize_url(url)
34:     if "+asyncpg" in url:
35:         return []
36:     if url.startswith("postgresql://"):
37:         tail = url[len("postgresql://"):]
38:         return [
39:             "postgresql+psycopg://" + tail,
40:             "postgresql+psycopg2://" + tail,
41:             url,
42:         ]
43:     return [url]
44: 
45: 
46: def _candidate_urls():
47:     urls = []
48:     for base in CANDIDATE_URLS:
49:         for url in _driver_variants(base):
50:             if url and url not in urls:
51:                 urls.append(url)
52: 
53:     raw = _raw_database_url()
54:     if raw:
55:         for url in _driver_variants(raw):
56:             if url and url not in urls:
57:                 urls.append(url)
58: 
59:     return urls
60: 
61: 
62: def _mask_url(url: str) -> str:
63:     return re.sub(r"://([^:]+):([^@]+)@", r"://\1:***@", url)
64: 
65: 
66: @lru_cache(maxsize=1)
67: def _working_url():
68:     last_error = None
69: 
70:     for url in _candidate_urls():
71:         try:
72:             engine = create_engine(url, pool_pre_ping=True)
73:             with engine.connect() as conn:
74:                 row = conn.execute(text("""
75:                     SELECT
76:                       current_database() AS db,
77:                       to_regclass('public.parcels_inspire') IS NOT NULL AS has_parcels,
78:                       to_regclass('public.parcel_external_market_evidence_summary') IS NOT NULL AS has_external
79:                 """)).mappings().first()
80: 
81:             engine.dispose()
82: 
83:             if row and row["has_parcels"] and row["has_external"]:
84:                 return url
85: 
86:             last_error = RuntimeError(
87:                 f"DB connected but required tables missing: url={_mask_url(url)} row={dict(row or {})}"
88:             )
89:         except Exception as exc:
90:             last_error = exc
91: 
92:     raise RuntimeError(f"No working AAYS database URL. Last error: {last_error}")
93: 
94: 
95: @lru_cache(maxsize=1)
96: def _engine():
97:     return create_engine(_working_url(), pool_pre_ping=True)
98: 
99: 
100: def _limit_offset(limit: int, offset: int):
101:     try:
102:         limit_i = int(limit)
103:     except Exception:
104:         limit_i = 5000
105:     try:
106:         offset_i = int(offset)
107:     except Exception:
108:         offset_i = 0
109:     return max(1, min(limit_i, 10000)), max(0, offset_i)
110: 
111: 
112: def _fetch(sql: str) -> Any:
113:     try:
114:         with _engine().connect() as conn:
115:             raw = conn.execute(text(sql)).scalar()
116:     except Exception as exc:
117:         raise HTTPException(status_code=500, detail=f"AAYS sales query failed: {exc}") from exc
118: 
119:     if not raw:
120:         return {"type": "FeatureCollection", "features": []}
121:     if isinstance(raw, (dict, list)):
122:         return raw
123:     return json.loads(raw)
124: 
125: 
126: @router.get("/map/sales-history/status")
127: def status():
128:     sql = """
129:     WITH bounds AS (
130:       SELECT
131:         ST_MakeEnvelope(-0.65,51.25,0.35,51.75,4326) AS london_bbox,
132:         ST_MakeEnvelope(-8.7,49.8,2.1,61.1,4326) AS england_bbox
133:     ),
134:     map_bbox AS (
135:       SELECT
136:         'london'::text AS region,
137:         london_bbox AS bbox
138:       FROM bounds
139:       UNION ALL
140:       SELECT
141:         'england'::text AS region,
142:         england_bbox AS bbox
143:       FROM bounds
144:     ),
145:     map_parcel_counts AS (
146:       SELECT
147:         b.region,
148:         count(*) FILTER (
149:           WHERE
150:             (
151:               COALESCE(ps.visible_sale_count, 0) > 0
152:               OR EXISTS (
153:                 SELECT 1
154:                 FROM public.parcel_external_market_evidence_summary eme
155:                 WHERE eme.parcel_id = p.parcel_id
156:               )
157:             )
158:         ) AS sale_ready_count,
159:         count(*) FILTER (
160:           WHERE
161:             (
162:               COALESCE(ps.history_transaction_count, 0) > 0
163:               OR EXISTS (
164:                 SELECT 1
165:                 FROM public.parcel_sales_history_summary sh
166:                 WHERE sh.parcel_id = p.parcel_id
167:               )
168:             )
169:         ) AS history_signal_count
170:       FROM map_bbox b
171:       JOIN public.parcels_inspire p
172:         ON ST_Intersects(
173:           CASE
174:             WHEN ST_SRID(p.geometry) = 4326 THEN p.geometry
175:             WHEN ST_SRID(p.geometry) = 0 THEN ST_SetSRID(p.geometry, 4326)
176:             ELSE ST_Transform(p.geometry, 4326)
177:           END,
178:           b.bbox
179:         )
180:       LEFT JOIN public.parcel_signal_summary ps ON ps.parcel_id = p.parcel_id
--- FUNCTION AND SQL KEYWORDS ---
74:                 row = conn.execute(text("""
77:                       to_regclass('public.parcels_inspire') IS NOT NULL AS has_parcels,
78:                       to_regclass('public.parcel_external_market_evidence_summary') IS NOT NULL AS has_external
83:             if row and row["has_parcels"] and row["has_external"]:
115:             raw = conn.execute(text(sql)).scalar()
127: def status():
145:     map_parcel_counts AS (
148:         count(*) FILTER (
154:                 FROM public.parcel_external_market_evidence_summary eme
155:                 WHERE eme.parcel_id = p.parcel_id
159:         count(*) FILTER (
165:                 FROM public.parcel_sales_history_summary sh
166:                 WHERE sh.parcel_id = p.parcel_id
171:       JOIN public.parcels_inspire p
180:       LEFT JOIN public.parcel_signal_summary ps ON ps.parcel_id = p.parcel_id
189:             SELECT count(*)
204:             SELECT count(*)
222:             SELECT count(*)
241:       'parcels_inspire_rows', (SELECT count(*) FROM public.parcels_inspire),
242:       'parcels_with_geometry', (SELECT count(*) FROM public.parcels_inspire WHERE geometry IS NOT NULL),
243:       'srid', (SELECT COALESCE(NULLIF(Find_SRID('public','parcels_inspire','geometry'),0),27700)),
244:       'parcel_sales_history_rows', (SELECT count(*) FROM public.parcel_sales_history),
245:       'parcel_sales_history_summary_rows', (SELECT count(*) FROM public.parcel_sales_history_summary),
246:       'legacy_external_evidence_rows', (SELECT count(*) FROM public.parcel_external_market_evidence_summary WHERE parcel_id IS NOT NULL),
247:       'legacy_external_joinable_rows', (
248:         SELECT count(*)
249:         FROM public.parcel_external_market_evidence_summary e
250:         JOIN public.parcels_inspire p ON p.parcel_id = e.parcel_id
252:       'external_evidence_rows', (SELECT count(*) FROM public.parcel_external_market_evidence_summary WHERE parcel_id IS NOT NULL),
253:       'external_joinable_rows', (
254:         SELECT count(*)
255:         FROM public.parcel_external_market_evidence_summary e
256:         JOIN public.parcels_inspire p ON p.parcel_id = e.parcel_id
258:       'listings_market_adapter_rows', (SELECT count(*) FROM public.listings_market_adapter),
260:         SELECT count(*)
261:         FROM public.listing_parcel_link
265:         SELECT count(DISTINCT COALESCE(NULLIF(listing_id, ''), source_record_id))
266:         FROM public.listing_parcel_link
270:         SELECT count(*)
271:         FROM public.parcel_signal_summary
275:       'map_sale_ready_london_count', (SELECT COALESCE(sale_ready_count, 0) FROM map_parcel_counts WHERE region = 'london'),
276:       'map_history_signal_london_count', (SELECT COALESCE(history_signal_count, 0) FROM map_parcel_counts WHERE region = 'london'),
278:       'map_sale_ready_england_count', (SELECT COALESCE(sale_ready_count, 0) FROM map_parcel_counts WHERE region = 'england'),
279:       'map_history_signal_england_count', (SELECT COALESCE(history_signal_count, 0) FROM map_parcel_counts WHERE region = 'england')
288: @router.get("/map/sales-history/external-evidence")
289: def external_evidence(limit: int = 5000, offset: int = 0):
294:         p.parcel_id,
295:         to_jsonb(p)->>'parcel_ref' AS parcel_ref,
299:         CASE WHEN (to_jsonb(e)->>'external_market_evidence_count') ~ '^-?[0-9]+$'
300:           THEN (to_jsonb(e)->>'external_market_evidence_count')::integer END AS external_market_evidence_count,
301:         CASE WHEN (to_jsonb(e)->>'external_market_l2_count') ~ '^-?[0-9]+$'
302:           THEN (to_jsonb(e)->>'external_market_l2_count')::integer END AS external_market_l2_count,
303:         CASE WHEN (to_jsonb(e)->>'external_market_l3_count') ~ '^-?[0-9]+$'
304:           THEN (to_jsonb(e)->>'external_market_l3_count')::integer END AS external_market_l3_count,
305:         CASE WHEN (to_jsonb(e)->>'external_market_polygon_match_count') ~ '^-?[0-9]+$'
306:           THEN (to_jsonb(e)->>'external_market_polygon_match_count')::integer END AS external_market_polygon_match_count,
308:         CASE WHEN (to_jsonb(e)->>'external_market_best_overlap_ratio') ~ '^-?[0-9]+([.][0-9]+)?$'
309:           THEN (to_jsonb(e)->>'external_market_best_overlap_ratio')::numeric END AS external_market_best_overlap_ratio,
310:         CASE WHEN (to_jsonb(e)->>'external_market_avg_overlap_ratio') ~ '^-?[0-9]+([.][0-9]+)?$'
311:           THEN (to_jsonb(e)->>'external_market_avg_overlap_ratio')::numeric END AS external_market_avg_overlap_ratio,
312:         CASE WHEN (to_jsonb(e)->>'external_market_best_confidence_score') ~ '^-?[0-9]+([.][0-9]+)?$'
313:           THEN (to_jsonb(e)->>'external_market_best_confidence_score')::numeric END AS external_market_best_confidence_score,
315:         CASE WHEN to_jsonb(e) ? 'external_market_evidence_samples'
316:           THEN to_jsonb(e)->'external_market_evidence_samples'
318:         END AS external_market_evidence_samples,
324:         END AS parcel_area_m2,
332:       FROM public.parcel_external_market_evidence_summary e
333:       JOIN public.parcels_inspire p ON p.parcel_id = e.parcel_id
334:       WHERE e.parcel_id IS NOT NULL
336:         CASE WHEN (to_jsonb(e)->>'external_market_best_confidence_score') ~ '^-?[0-9]+([.][0-9]+)?$'
337:           THEN (to_jsonb(e)->>'external_market_best_confidence_score')::numeric END DESC NULLS LAST,
338:         p.parcel_id ASC
347:           'parcel_id', parcel_id,
348:           'parcel_ref', parcel_ref,
351:           'parcel_area_m2', parcel_area_m2,
352:           'sales_history_available', false,
353:           'external_market_evidence_available', true,
354:           'external_market_evidence_count', external_market_evidence_count,
355:           'external_market_l2_count', external_market_l2_count,
356:           'external_market_l3_count', external_market_l3_count,
357:           'external_market_polygon_match_count', external_market_polygon_match_count,
358:           'external_market_best_overlap_ratio', external_market_best_overlap_ratio,
359:           'external_market_avg_overlap_ratio', external_market_avg_overlap_ratio,
360:           'external_market_best_confidence_score', external_market_best_confidence_score,
361:           'external_market_evidence_samples', coalesce(external_market_evidence_samples, '[]'::jsonb),
362:           'layer_kind', 'EXTERNAL_EVIDENCE',
377: @router.get("/map/sales-history/parcels")
383:         p.parcel_id,
384:         to_jsonb(p)->>'parcel_ref' AS parcel_ref,
388:         CASE WHEN (to_jsonb(h)->>'sales_history_count') ~ '^-?[0-9]+$'
389:           THEN (to_jsonb(h)->>'sales_history_count')::integer END AS sales_history_count,
398:         to_jsonb(h)->>'best_sales_history_confidence_score' AS best_sales_history_confidence_score,
400:         CASE WHEN to_jsonb(h) ? 'sales_history_records'
401:           THEN to_jsonb(h)->'sales_history_records'
403:         END AS sales_history_records,
409:         END AS parcel_area_m2,
417:       FROM public.parcel_sales_history_summary h
418:       JOIN public.parcels_inspire p ON p.parcel_id = h.parcel_id
419:       ORDER BY p.parcel_id ASC
428:           'parcel_id', parcel_id,
429:           'parcel_ref', parcel_ref,
432:           'parcel_area_m2', parcel_area_m2,
433:           'sales_history_available', true,
434:           'sales_history_count', sales_history_count,
441:           'sales_history_confidence_score', best_sales_history_confidence_score,
442:           'sales_history_records', coalesce(sales_history_records, '[]'::jsonb),
443:           'external_market_evidence_available', false,
463:     WITH external_features AS (
473:           'parcel_id', p.parcel_id,
474:           'parcel_ref', to_jsonb(p)->>'parcel_ref',
477:           'sales_history_available', false,
478:           'external_market_evidence_available', true,
479:           'external_market_evidence_count', to_jsonb(e)->>'external_market_evidence_count',
480:           'external_market_l2_count', to_jsonb(e)->>'external_market_l2_count',
481:           'external_market_l3_count', to_jsonb(e)->>'external_market_l3_count',
482:           'external_market_best_confidence_score', to_jsonb(e)->>'external_market_best_confidence_score',
483:           'layer_kind', 'EXTERNAL_EVIDENCE',
487:       FROM public.parcel_external_market_evidence_summary e
488:       JOIN public.parcels_inspire p ON p.parcel_id = e.parcel_id
489:       WHERE e.parcel_id IS NOT NULL
501:           'parcel_id', p.parcel_id,
502:           'parcel_ref', to_jsonb(p)->>'parcel_ref',
505:           'sales_history_available', true,
506:           'external_market_evidence_available', false,
507:           'sales_history_count', to_jsonb(h)->>'sales_history_count',
514:           'sales_history_confidence_score', to_jsonb(h)->>'best_sales_history_confidence_score',
515:           'sales_history_records',
516:             CASE WHEN to_jsonb(h) ? 'sales_history_records' THEN to_jsonb(h)->'sales_history_records' ELSE '[]'::jsonb END,
521:       FROM public.parcel_sales_history_summary h
522:       JOIN public.parcels_inspire p ON p.parcel_id = h.parcel_id
525:       SELECT feature FROM external_features
END_TIME:
3 Mayıs 2026 Pazar 00:07:54
STATUS_SOURCE_READ_DONE



