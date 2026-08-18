import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import { execFileSync } from "node:child_process";
import { PMTiles } from "pmtiles";
import { VectorTile } from "@mapbox/vector-tile";
import Pbf from "pbf";
import booleanPointInPolygon from "@turf/boolean-point-in-polygon";
import { point as turfPoint } from "@turf/helpers";

const SLOT = "future_growth_6";
const CONT = "future_growth_6_open_source_v2_20260813";
const CANONICAL_BRANCH = "codex/aays-single-runner-v5-20260706";
const EXPECTED_START_BATCH = 301;
const BATCH_COUNT = 12;
const EXPECTED_BEFORE = 7;
const ROOT = process.cwd();

const MIRROR = "AAYS/england_map_web/data/future_growth/shards/future_growth_6_latest.geojson";
const CHECKPOINT = "state/slots/future_growth_6/checkpoint_latest.json";
const STATUS = "state/slots/future_growth_6/status_latest.json";
const MANIFEST = "state/slots/future_growth_6/evidence_manifest_latest.json";
const REPORT = "state/slots/future_growth_6/report_latest.json";
const LEGACY_DOC_CP = "docs/chatgpt_status/_shared/slots_21/future_growth_6/checkpoint_latest.json";
const CONFIG = "england_map_web/config/regions.local.json";

const ALLOWED_WRITE = new Set([MIRROR, CHECKPOINT, STATUS, MANIFEST, REPORT]);

const LPA_WINDOWS = [
  {entity:626288, slug:"bath_and_north_east_somerset"},
  {entity:626289, slug:"bournemouth_christchurch_poole"},
  {entity:626290, slug:"bristol"},
  {entity:626291, slug:"cornwall"},
  {entity:626292, slug:"dorset"},
  {entity:626293, slug:"isles_of_scilly"},
  {entity:626294, slug:"north_somerset"},
  {entity:626295, slug:"plymouth"},
  {entity:626296, slug:"south_gloucestershire"},
  {entity:626297, slug:"swindon"},
  {entity:626298, slug:"torbay"},
  {entity:626299, slug:"wiltshire"},
];

function readJson(p) { return JSON.parse(fs.readFileSync(path.join(ROOT,p),"utf8")); }
function writeJson(p, obj) {
  const full=path.join(ROOT,p);
  fs.mkdirSync(path.dirname(full),{recursive:true});
  fs.writeFileSync(full,JSON.stringify(obj,null,2)+"\n");
}
function sha256Text(s){ return crypto.createHash("sha256").update(s).digest("hex"); }
function now(){ return new Date().toISOString(); }
function sh(args, opts={}) {
  return execFileSync(args[0], args.slice(1), {cwd:ROOT, encoding:"utf8", stdio:opts.capture?["ignore","pipe","pipe"]:"inherit"}).trim();
}
function gitShow(ref,p) {
  return execFileSync("git",["show",`${ref}:${p}`],{cwd:ROOT,encoding:"utf8"});
}
function normalize(s){ return String(s??"").toLowerCase().replace(/[^a-z0-9]+/g,"_").replace(/^_+|_+$/g,""); }

function uniqueProgramIds(fc) {
  const ids = [];
  for (const f of (fc.features||[])) {
    const id=f?.properties?.program_parcel_id;
    if (!id || typeof id!=="string") throw new Error("MIRROR_FEATURE_WITHOUT_PROGRAM_PARCEL_ID");
    ids.push(id);
  }
  return new Set(ids);
}
function assertMirror(fc) {
  if (fc?.type!=="FeatureCollection" || !Array.isArray(fc.features)) throw new Error("INVALID_MIRROR");
  const ids=uniqueProgramIds(fc);
  if (ids.size!==fc.features.length) throw new Error(`DUPLICATE_MIRROR:${fc.features.length-ids.size}`);
  for(const f of fc.features){
    if(f?.properties?.slot_id!==SLOT) throw new Error("CROSS_SLOT_FEATURE");
    if(f?.properties?.fake_data!==false) throw new Error("FAKE_DATA_FLAG");
    if(f?.properties?.nearest_match_used===true) throw new Error("NEAREST_MATCH_FLAG");
  }
  return ids.size;
}
function recursiveStrings(x, out=[]) {
  if (typeof x==="string") out.push(x);
  else if (Array.isArray(x)) for(const v of x) recursiveStrings(v,out);
  else if (x && typeof x==="object") for(const v of Object.values(x)) recursiveStrings(v,out);
  return out;
}
function findSouthWestPmtilesUrl(cfg) {
  const candidates=recursiveStrings(cfg).filter(s=>/^https?:\/\//.test(s) && /south[_-]west/i.test(s) && /\.pmtiles(?:\?|$)/i.test(s));
  const preferred=candidates.find(s=>/huggingface\.co/.test(s)) || candidates[0];
  if(!preferred) throw new Error("SOUTH_WEST_PMTILES_URL_NOT_FOUND");
  return preferred;
}
async function getJson(url, params={}) {
  const u=new URL(url);
  for(const [k,v] of Object.entries(params)){
    if(Array.isArray(v)) for(const x of v) u.searchParams.append(k,String(x));
    else if(v!==undefined && v!==null) u.searchParams.append(k,String(v));
  }
  let lastErr;
  for(let attempt=1;attempt<=4;attempt++){
    try{
      const r=await fetch(u,{headers:{"user-agent":"TerraYield-AAYS-future_growth_6/20260818","accept":"application/json"}});
      if(!r.ok) throw new Error(`HTTP_${r.status}_${await r.text()}`);
      const text=await r.text();
      return {url:u.toString(), text, json:JSON.parse(text)};
    }catch(e){
      lastErr=e;
      if(attempt<4) await new Promise(res=>setTimeout(res,attempt*1200));
    }
  }
  throw lastErr;
}
function entitiesFrom(j) {
  if(Array.isArray(j)) return j;
  for(const k of ["entities","results","data"]){
    if(Array.isArray(j?.[k])) return j[k];
  }
  return [];
}
function parsePointWkt(wkt) {
  const m=String(wkt||"").match(/POINT\s*\(\s*(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)\s*\)/i);
  if(!m) return null;
  const lon=Number(m[1]), lat=Number(m[2]);
  if(!Number.isFinite(lon)||!Number.isFinite(lat)) return null;
  return [lon,lat];
}
function lonLatToTile(lon,lat,z){
  const n=2**z;
  const x=Math.floor((lon+180)/360*n);
  const lr=Math.max(-85.05112878,Math.min(85.05112878,lat))*Math.PI/180;
  const y=Math.floor((1-Math.asinh(Math.tan(lr))/Math.PI)/2*n);
  return [Math.max(0,Math.min(n-1,x)),Math.max(0,Math.min(n-1,y))];
}
function geometryContainsPoint(geo, lon, lat){
  if(!geo || !["Polygon","MultiPolygon"].includes(geo.type)) return false;
  try { return booleanPointInPolygon(turfPoint([lon,lat]), geo, {ignoreBoundary:false}); }
  catch { return false; }
}
function parcelFeatureId(vtf){
  if(vtf.id!==undefined && vtf.id!==null && String(vtf.id)!=="") return String(vtf.id);
  const p=vtf.properties||{};
