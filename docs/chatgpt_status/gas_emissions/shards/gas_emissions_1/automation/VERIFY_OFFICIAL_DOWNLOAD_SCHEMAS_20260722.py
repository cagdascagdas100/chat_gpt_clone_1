from __future__ import annotations
import hashlib, html, json, os, re, tempfile, urllib.parse, urllib.request, zipfile
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

SLOT="gas_emissions_1"
PART={"start":1,"end":30761,"count":30761,"canonical_count":92283}
SOURCES=[
 ("naei_point_sources_2023","xlsx","https://naei.energysecurity.gov.uk/sites/default/files/2025-09/NAEIPointsSources_2023.xlsx"),
 ("uk_prtr_2024","xml","https://assets.publishing.service.gov.uk/media/6a3d096c4c7605ab56723a63/uk_prtr_dataset_2024.xml"),
 ("ea_pollution_inventory_2024","zip","https://environment.data.gov.uk/api/file/download?fileDataSetId=4faa4a52-7df2-4047-bc3f-877dd04222d8&fileName=2024+Pollution+Inventory+Dataset.zip"),
 ("hmlr_inspire_20260705","gml_listing","https://use-land-property-data.service.gov.uk/datasets/inspire/download"),
 ("naei_gridded_emissions_2023","grid_listing","https://naei.energysecurity.gov.uk/data/maps/download-gridded-emissions"),
]
def now(): return datetime.now(timezone.utc).isoformat().replace("+00:00","Z")
def lname(tag): return tag.rsplit("}",1)[-1]
def get(url,timeout=240):
 r=urllib.request.Request(url,headers={"User-Agent":"AAYS-TerraYield-schema-audit/1.0","Accept":"*/*"})
 with urllib.request.urlopen(r,timeout=timeout) as x:
  b=x.read()
  return b,{"http_status":int(getattr(x,"status",200)),"final_url":x.geturl(),"content_type":x.headers.get("Content-Type")}
def xml_tags(data):
 with tempfile.NamedTemporaryFile(suffix=".xml",delete=False) as f: f.write(data); p=Path(f.name)
 try:
  tags={}; root=None
  for ev,e in ET.iterparse(p,events=("start","end")):
   n=lname(e.tag)
   if root is None and ev=="start": root=n
   if ev=="end": tags[n]=tags.get(n,0)+1; e.clear()
  low=" ".join(tags).lower()
  return {"root_tag":root,"distinct_tag_count":len(tags),"top_tags":sorted(tags.items(),key=lambda x:(-x[1],x[0]))[:100],
          "facility_hint":"facility" in low,"release_hint":("pollutant" in low or "release" in low),
          "location_hint":any(x in low for x in ("coordinate","latitude","longitude","geographical")),
          "schema_verified":bool(root and "facility" in low and ("pollutant" in low or "release" in low) and any(x in low for x in ("coordinate","latitude","longitude","geographical")))}
 finally: p.unlink(missing_ok=True)
def inspect_xlsx(data):
 with tempfile.NamedTemporaryFile(suffix=".xlsx",delete=False) as f: f.write(data); p=Path(f.name)
 try:
  with zipfile.ZipFile(p) as z:
   names=z.namelist(); sheets=[x for x in names if x.startswith("xl/worksheets/sheet") and x.endswith(".xml")]
   first=[]
   if sheets:
    root=ET.fromstring(z.read(sheets[0]))
    for row in root.iter():
     if lname(row.tag)=="row":
      vals=[]
      for c in row:
       if lname(c.tag)=="c":
        v=next((q for q in c if lname(q.tag)=="v"),None); vals.append("" if v is None else (v.text or ""))
      first.append(vals)
      if len(first)>=5: break
   return {"workbook_present":"xl/workbook.xml" in names,"worksheet_count":len(sheets),"first_rows":first,
           "schema_verified":bool("xl/workbook.xml" in names and sheets and first)}
 finally: p.unlink(missing_ok=True)
def inspect_zip(data):
 with tempfile.NamedTemporaryFile(suffix=".zip",delete=False) as f: f.write(data); p=Path(f.name)
 try:
  with zipfile.ZipFile(p) as z:
   names=z.namelist(); members=[x for x in names if x.lower().endswith((".csv",".xlsx",".xls",".shp",".gml",".geojson",".gpkg",".dbf"))]
   return {"zip_member_count":len(names),"members":names[:200],"schema_members":members[:100],"schema_verified":bool(members)}
 finally: p.unlink(missing_ok=True)
def main():
 root=Path.cwd(); task=os.environ.get("AAYS_TASK_ID","")
 if os.environ.get("AAYS_SLOT_ID","")!=SLOT or not task: raise RuntimeError("GAS_EMISSIONS_1_SCHEMA_AUDIT_WRONG_SLOT_CONTEXT")
 results={}; blockers=[]
 for sid,kind,url in SOURCES:
  item={"source_id":sid,"kind":kind,"url":url,"downloaded":False,"schema_verified":False,"error":None}
  try:
   data,http=get(url); item.update({"downloaded":True,"http":http,"bytes":len(data),"sha256":hashlib.sha256(data).hexdigest()})
   if kind=="xlsx": schema=inspect_xlsx(data)
   elif kind=="xml": schema=xml_tags(data)
   elif kind=="zip": schema=inspect_zip(data)
   elif kind=="gml_listing":
    text=data.decode("utf-8",errors="replace"); links=re.findall(r'href=["\']([^"\']+\.gml(?:\?[^"\']*)?)["\']',text,re.I)
    schema={"gml_link_count":len(links),"sample_gml_urls":[urllib.parse.urljoin(url,x) for x in links[:10]],"schema_verified":bool(links)}
   else:
    text=data.decode("utf-8",errors="replace").lower(); keys=["ascii","geotiff","point source","shp","csv","licen"]
    schema={"package_evidence":{k:k in text for k in keys},"schema_verified":all(k in text for k in keys),"direct_download_resolved":False}
    blockers.append("NAEI_GRID_DYNAMIC_DIRECT_DOWNLOAD_ENDPOINT_NOT_RESOLVED")
   item["schema"]=schema; item["schema_verified"]=bool(schema.get("schema_verified"))
   if not item["schema_verified"]: blockers.append(sid.upper()+"_SCHEMA_NOT_VERIFIED")
  except Exception as e:
   item["error"]=type(e).__name__+": "+str(e); blockers.append(sid.upper()+"_DOWNLOAD_OR_SCHEMA_ERROR")
  results[sid]=item
 verified=sum(bool(x["schema_verified"]) for x in results.values())
 payload={"schema_version":1,"architecture_version":3,"workstream_id":"AAYS_21_SLOT_SAFE_PARALLEL_V1","slot_id":SLOT,"task_id":task,
          "parcel_partition":PART,"status":"PASS_OFFICIAL_DOWNLOAD_SCHEMA_VERIFICATION" if verified==len(results) and not blockers else "BLOCKED_OFFICIAL_DOWNLOAD_SCHEMA_VERIFICATION",
          "generated_at":now(),"source_count":len(results),"schema_verified_count":verified,"sources":results,"blockers":sorted(set(blockers)),
          "next_action":"Resolve remaining file-access/dynamic endpoint blockers, then use only official ID, documented grid containment/intersection or exact point-in-polygon.",
          "parcel_values_created":0,"measured_parcel_rows_created":0,"actual_business_data_rows_written":0,
          "output_semantics":"SOURCE_SCHEMA_EVIDENCE_ONLY_NO_PARCEL_VALUE","final_ready":False,"product_final_ready":False,
          "fake_data":False,"db_write":False,"migration":False,"production_deploy":False}
 paths=[root/"docs/chatgpt_status/gas_emissions/shards/gas_emissions_1/reports/gas_emissions_1_official_download_schema_latest.json",
        root/"docs/chatgpt_status/gas_emissions/shards/gas_emissions_1/status/gas_emissions_1_official_download_schema_latest.json",
        root/"england_map_web/data/aays_21_slots/gas_emissions_1/official_download_schema_latest.json"]
 for p in paths: p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 rows="".join("<tr><td>"+html.escape(x["source_id"])+"</td><td>"+html.escape(x["kind"])+"</td><td>"+("yes" if x["downloaded"] else "no")+"</td><td>"+("yes" if x["schema_verified"] else "no")+"</td><td>"+html.escape(x.get("error") or "")+"</td></tr>" for x in results.values())
 hp=root/"england_map_web/data/aays_21_slots/gas_emissions_1/official_download_schema.html"; hp.parent.mkdir(parents=True,exist_ok=True)
 hp.write_text(f'<!doctype html><html lang="tr"><meta charset="utf-8"><title>Gas Emissions 1 schema</title><body><h1>gas_emissions_1</h1><p>Parsel 1-30761 · Şema {verified}/{len(results)} · Ölçülmüş parsel 0</p><p>Bu kaynak/şema kanıtıdır; parsel ölçümü değildir.</p><table border="1"><tr><th>Kaynak</th><th>Tür</th><th>İndirildi</th><th>Şema</th><th>Hata</th></tr>{rows}</table></body></html>',encoding="utf-8")
 print(json.dumps(payload,ensure_ascii=False,indent=2)); return 0 if verified==len(results) and not blockers else 2
if __name__=="__main__": raise SystemExit(main())
