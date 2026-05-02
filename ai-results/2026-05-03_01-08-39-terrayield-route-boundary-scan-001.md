# ChatGPT Runner Result

## Task
Scan current sales history route boundaries after aborted patch

## Task ID
terrayield-route-boundary-scan-001

## Progress
97%

## Time
05/03/2026 01:08:42

## Working Directory
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence

## Exit Code
0

## Command
Write-Output 'TASK: guncel route sinirlari tarama'; Write-Output 'PROGRESS: 97%'; Write-Output 'ESTIMATED_WAIT: 2-3 dakika'; Write-Output 'START_TIME:'; Get-Date; $file='app\api\routes\aays_sales_history_layers.py'; Write-Output ('FILE_EXISTS=' + (Test-Path $file)); if (Test-Path $file) { $lines=Get-Content $file; Write-Output ('LINE_COUNT=' + $lines.Count); Write-Output '--- ROUTER DECORATORS ---'; Select-String -Path $file -Pattern '@router\.get|@router\.post|def status|def external_evidence|def parcels|def combined|fast_static_status_v1|fast_non_spatial_status_v1' -CaseSensitive:$false | ForEach-Object { $_.LineNumber.ToString() + ': ' + $_.Line }; Write-Output '--- FIRST 260 LINES ---'; for ($i=0; $i -lt [Math]::Min(260,$lines.Count); $i++) { Write-Output ((($i+1).ToString()) + ': ' + $lines[$i]) }; Write-Output '--- PY_COMPILE ---'; python -m py_compile $file 2>&1 }; Write-Output 'END_TIME:'; Get-Date; Write-Output 'ROUTE_BOUNDARY_SCAN_DONE'

## Output
TASK: guncel route sinirlari tarama
PROGRESS: 97%
ESTIMATED_WAIT: 2-3 dakika
START_TIME:

3 Mayıs 2026 Pazar 01:08:40
FILE_EXISTS=True
LINE_COUNT=633
--- ROUTER DECORATORS ---
126: @router.get("/map/sales-history/status")
127: def status():
288: @router.get("/map/sales-history/external-evidence")
289: def external_evidence(limit: int = 5000, offset: int = 0):
377: @router.get("/map/sales-history/parcels")
459: @router.get("/map/sales-history/combined")
460: def combined(limit: int = 10000, offset: int = 0):
572: @router.get("/map/sales-history/l4-reviewed-package/status")
589: @router.get("/map/sales-history/l4-reviewed-package")
--- FIRST 260 LINES ---
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
181:       GROUP BY b.region
182:     ),
183:     map_listing_counts AS (
184:       SELECT
185:         b.region,
186:         (
187:           -- homes_england_landhub
188:           (
189:             SELECT count(*)
190:             FROM public.listings_landhub h
191:             WHERE h.geometry IS NOT NULL
192:               AND ST_Intersects(
193:                 CASE
194:                   WHEN ST_SRID(h.geometry) = 4326 THEN h.geometry
195:                   WHEN ST_SRID(h.geometry) = 0 THEN ST_SetSRID(h.geometry, 4326)
196:                   ELSE ST_Transform(h.geometry, 4326)
197:                 END,
198:                 b.bbox
199:               )
200:           )
201:           +
202:           -- government_property_finder (exclude demo default)
203:           (
204:             SELECT count(*)
205:             FROM public.listings_government_property_finder g
206:             WHERE
207:               COALESCE(g.is_demo, false) IS false
208:               AND (g.truth_tier IS NULL OR g.truth_tier <> 'demo')
209:               AND COALESCE(g.site_geometry, g.point_geometry) IS NOT NULL
210:               AND ST_Intersects(
211:                 CASE
212:                   WHEN ST_SRID(COALESCE(g.site_geometry, g.point_geometry)) = 4326 THEN COALESCE(g.site_geometry, g.point_geometry)
213:                   WHEN ST_SRID(COALESCE(g.site_geometry, g.point_geometry)) = 0 THEN ST_SetSRID(COALESCE(g.site_geometry, g.point_geometry), 4326)
214:                   ELSE ST_Transform(COALESCE(g.site_geometry, g.point_geometry), 4326)
215:                 END,
216:                 b.bbox
217:               )
218:           )
219:           +
220:           -- market_listing_adapter (exclude demo default)
221:           (
222:             SELECT count(*)
223:             FROM public.listings_market_adapter m
224:             WHERE
225:               COALESCE(m.is_demo, false) IS false
226:               AND (m.truth_tier IS NULL OR m.truth_tier <> 'demo')
227:               AND COALESCE(m.site_geometry, m.point_geometry) IS NOT NULL
228:               AND ST_Intersects(
229:                 CASE
230:                   WHEN ST_SRID(COALESCE(m.site_geometry, m.point_geometry)) = 4326 THEN COALESCE(m.site_geometry, m.point_geometry)
231:                   WHEN ST_SRID(COALESCE(m.site_geometry, m.point_geometry)) = 0 THEN ST_SetSRID(COALESCE(m.site_geometry, m.point_geometry), 4326)
232:                   ELSE ST_Transform(COALESCE(m.site_geometry, m.point_geometry), 4326)
233:                 END,
234:                 b.bbox
235:               )
236:           )
237:         )::bigint AS listings_count
238:       FROM map_bbox b
239:     )
240:     SELECT jsonb_build_object(
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
251:       ),
252:       'external_evidence_rows', (SELECT count(*) FROM public.parcel_external_market_evidence_summary WHERE parcel_id IS NOT NULL),
253:       'external_joinable_rows', (
254:         SELECT count(*)
255:         FROM public.parcel_external_market_evidence_summary e
256:         JOIN public.parcels_inspire p ON p.parcel_id = e.parcel_id
257:       ),
258:       'listings_market_adapter_rows', (SELECT count(*) FROM public.listings_market_adapter),
259:       'market_listing_link_rows', (
260:         SELECT count(*)
--- PY_COMPILE ---
END_TIME:
3 Mayıs 2026 Pazar 01:08:42
ROUTE_BOUNDARY_SCAN_DONE



