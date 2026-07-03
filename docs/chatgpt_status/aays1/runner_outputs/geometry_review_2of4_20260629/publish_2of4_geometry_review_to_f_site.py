import json, shutil
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(r'C:\Users\cagda\Documents\GitHub\AAYS')
OUT = ROOT / 'outputs' / 'terrayield_3110_20260629' / 'geometry_review_2of4_20260629'
F_SITE = Path(r'F:\chatgpt\chat_gpt_clone_1_main\england_map_web')
F_DATA = F_SITE / 'data' / 'geometry_review_2of4_20260629'
F_EVIDENCE = F_DATA / 'evidence_sources'

if not OUT.exists():
    raise SystemExit(f'Output folder missing: {OUT}')
if not F_SITE.exists():
    raise SystemExit(f'F site folder missing: {F_SITE}')

F_DATA.mkdir(parents=True, exist_ok=True)
F_EVIDENCE.mkdir(parents=True, exist_ok=True)

published = []
for name in [
    'TerraYield_2OF4_Geometry_Review_Queue_20260629.csv',
    'TerraYield_2OF4_Geometry_Review_Queue_20260629.json',
    'TerraYield_2OF4_Geometry_Review_Updates_Template_20260629.csv',
    'CHATGPT_2OF4_GEOMETRY_REVIEW_MASTER_PROMPT_TR.txt',
    'geometry_review_decision_schema_20260629.json',
    'GEOMETRY_REVIEW_MECHANISM_REPORT_20260629.md',
    'F_DRIVE_COPY_MANIFEST_20260629.json',
]:
    src = OUT / name
    dst = F_DATA / name
    if src.exists():
        shutil.copy2(src, dst)
        published.append({'src': str(src), 'dst': str(dst), 'bytes': dst.stat().st_size})

# Publish review HTML at web root and in data folder.
html_src = OUT / 'TerraYield_2OF4_Geometry_Review_Queue_20260629.html'
html_dst_root = F_SITE / 'geometry_review_2of4_20260629.html'
html_dst_data = F_DATA / 'TerraYield_2OF4_Geometry_Review_Queue_20260629.html'
for dst in [html_dst_root, html_dst_data]:
    shutil.copy2(html_src, dst)
    published.append({'src': str(html_src), 'dst': str(dst), 'bytes': dst.stat().st_size})

# Copy only source files used in the 2/4 / real geometry decision. Do not copy full disks.
source_files = [
    Path(r'C:\Users\cagda\Documents\GitHub\AAYS\outputs\terrayield_3110_20260629\TerraYield_ReadyToSell_3110_FIXED_SOURCE_TABLE_20260629.csv'),
    Path(r'C:\Users\cagda\Documents\GitHub\AAYS\outputs\terrayield_3110_20260629\TerraYield_ReadyToSell_3110_DRAWN_POLYGONS_WITH_EDGE_METADATA_20260629.geojson'),
    Path(r'C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\data\live_feeds\drops\market\repo_master_market_input_force_2026-04-23_sridfix.csv'),
    Path(r'C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\data\FINAL_3110_CURRENT_CONFIDENCE.polygons.geojson'),
    Path(r'D:\sold_buildings\data\nps_polygon.geojson'),
    Path(r'F:\AAYS_DATA\terrayield_land_intelligence\live_feeds_exports_archive\market_listing_parcel_polygons_2026-04-25.geojson'),
    Path(r'F:\chatgpt\chat_gpt_clone_1_main\england_map_web\data\market_listing_real_sale_ready_parcel_geometries_20260629.geojson'),
]
source_copies = []
for src in source_files:
    if not src.exists():
        source_copies.append({'src': str(src), 'dst': '', 'status': 'missing'})
        continue
    # Prefix source drive to avoid basename collisions.
    prefix = src.drive.replace(':','').lower() or 'root'
    dst = F_EVIDENCE / f'{prefix}_{src.name}'
    if (not dst.exists()) or dst.stat().st_size != src.stat().st_size:
        shutil.copy2(src, dst)
        status = 'copied'
    else:
        status = 'already_current'
    source_copies.append({'src': str(src), 'dst': str(dst), 'status': status, 'bytes': dst.stat().st_size})

# Add a non-invasive app link. This does not alter map/layer logic.
link_js = F_SITE / 'aays_geometry_review_2of4_link.js'
link_js.write_text("""(function(){
  const href = './geometry_review_2of4_20260629.html';
  function addLink(){
    if (document.getElementById('aays-geometry-review-2of4-link')) return;
    const a = document.createElement('a');
    a.id = 'aays-geometry-review-2of4-link';
    a.href = href;
    a.target = '_blank';
    a.rel = 'noopener';
    a.textContent = '2/4 Geometri İnceleme';
    a.style.cssText = [
      'position:fixed','left:24px','bottom:24px','z-index:99999','background:#fff7ed','color:#9a3412',
      'border:1px solid #fdba74','border-radius:14px','padding:10px 12px','font:700 13px Segoe UI,Arial,sans-serif',
      'box-shadow:0 8px 24px rgba(15,23,42,.25)','text-decoration:none'
    ].join(';');
    document.body.appendChild(a);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', addLink); else addLink();
})();
""", encoding='utf-8')

index = F_SITE / 'index.html'
index_status = 'not_found'
if index.exists():
    text = index.read_text(encoding='utf-8', errors='ignore')
    tag = '<script src="./aays_geometry_review_2of4_link.js?v=20260629"></script>'
    if 'aays_geometry_review_2of4_link.js' not in text:
        if '</body>' in text:
            text = text.replace('</body>', tag + '\n</body>')
        else:
            text += '\n' + tag + '\n'
        index.write_text(text, encoding='utf-8')
        index_status = 'injected'
    else:
        index_status = 'already_injected'

manifest = {
    'status': 'F_SITE_REVIEW_QUEUE_PUBLISHED',
    'generated_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
    'f_site': str(F_SITE),
    'review_url_local': 'http://127.0.0.1:8010/england_map_web/geometry_review_2of4_20260629.html',
    'published_files': published,
    'source_copies': source_copies,
    'app_link_js': str(link_js),
    'index_injection_status': index_status,
    'safety': {
        'db_write': 'none',
        'ddl': 'none',
        'migration_apply': 'none',
        'prod_deploy': 'none',
        'fake_geometry': 'none'
    }
}
manifest_path = F_DATA / 'F_SITE_PUBLISH_RESULT_20260629.json'
manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({
    'status': manifest['status'],
    'review_url_local': manifest['review_url_local'],
    'source_copy_count': len(source_copies),
    'index_injection_status': index_status,
    'manifest_path': str(manifest_path)
}, ensure_ascii=False, indent=2))
