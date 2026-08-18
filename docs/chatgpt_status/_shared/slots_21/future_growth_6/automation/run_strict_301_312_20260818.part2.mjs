  for(const k of ["parcel_id","parcelid","id","fid","FID","OBJECTID","objectid"]){
    if(p[k]!==undefined && p[k]!==null && String(p[k])!=="") return String(p[k]);
  }
  return null;
}
async function exactCanonicalParcelAt(pm, header, lon, lat) {
  if(lon<header.minLon || lon>header.maxLon || lat<header.minLat || lat>header.maxLat) {
    return {status:"OUTSIDE_PMTILES_BOUNDS", matches:[]};
  }
  const z=header.maxZoom;
  const [x,y]=lonLatToTile(lon,lat,z);
  const tileResp=await pm.getZxy(z,x,y);
  if(!tileResp) return {status:"NO_CANONICAL_TILE",matches:[],z,x,y};
  const vt=new VectorTile(new Pbf(new Uint8Array(tileResp.data)));
  const found=new Map();
  for(const [layerName,layer] of Object.entries(vt.layers||{})){
    for(let i=0;i<layer.length;i++){
      const f=layer.feature(i);
      const pid=parcelFeatureId(f);
      if(!pid) continue;
      let geo;
      try { geo=f.toGeoJSON(x,y,z); } catch { continue; }
      if(!geometryContainsPoint(geo.geometry,lon,lat)) continue;
      const key=String(pid);
      if(!found.has(key)) found.set(key,{parcel_id:key, layer:layerName, geometry:geo.geometry, properties:f.properties||{}, z,x,y});
    }
  }
  const matches=[...found.values()];
  if(matches.length===1) return {status:"EXACT_ONE",matches,z,x,y};
  if(matches.length===0) return {status:"NO_EXACT_CANONICAL_MATCH",matches,z,x,y};
  return {status:"AMBIGUOUS_MULTIPLE_CANONICAL_MATCHES",matches,z,x,y};
}
function featureFor(parcel,brownfield,sourceMeta,pmtilesUrl,windowKey,batch) {
  const [lon,lat]=parsePointWkt(brownfield.point);
  const pid=parcel.parcel_id;
  const bfRef=String(brownfield.reference ?? brownfield.entity ?? "");
  return {
    type:"Feature",
    id:`future_growth_6-brownfield-${bfRef}-${pid}`,
    geometry:{type:"Point",coordinates:[lon,lat]},
    properties:{
      topic_id:"future-growth",
      slot_id:SLOT,
      parcel_id:pid,
      program_parcel_id:`pmtiles:south_west:${pid}`,
      future_growth_value:null,
      future_growth_probability:null,
      future_growth_confidence_1_to_4:3,
      future_growth_source_granularity:"official Planning Data Brownfield Land point + canonical south_west.pmtiles parcel polygon",
      future_growth_geometry_relation:"strict authoritative brownfield-land source point within exactly one canonical PMTiles parcel polygon",
      future_growth_drivers:["Brownfield redevelopment"],
      future_growth_project_name:String(brownfield.name || brownfield["site-address"] || bfRef),
      future_growth_project_stage:String(brownfield["planning-permission-status"] || "brownfield-land-register"),
      future_growth_scoring_status:"METHODOLOGY_APPROVAL_REQUIRED",
      future_growth_source_url:sourceMeta.url,
      source_url:sourceMeta.url,
      source_accessed_at:sourceMeta.accessed_at,
      source_sha256:sourceMeta.sha256,
      source_license:"Open Government Licence v3.0; Planning Data brownfield-land dataset",
      source_record_scope:{
        dataset:"brownfield-land",
        entity:brownfield.entity ?? null,
        reference:bfRef,
        organisation_entity:brownfield["organisation-entity"] ?? brownfield.organisation_entity ?? null,
        batch,
        window_key:windowKey
      },
      parcel_geometry_source:"south_west.pmtiles",
      parcel_geometry_url:pmtilesUrl,
      parcel_geometry_relation:"exact point-in-polygon at PMTiles max zoom; exactly one canonical parcel required",
      parcel_geometry_layer:parcel.layer,
      evidence_level:3,
      demo_only:true,
      fake_data:false,
      nearest_match_used:false,
      final_ready:false,
      production_merge:false,
      generated_at:sourceMeta.accessed_at
    }
  };
}
function stagedPaths(){
  const out=execFileSync("git",["diff","--cached","--name-only"],{cwd:ROOT,encoding:"utf8"}).trim();
  return out?out.split(/\r?\n/):[];
}
function assertOnlyAllowedStaged(){
  const ps=stagedPaths();
  const bad=ps.filter(p=>!ALLOWED_WRITE.has(p));
  if(bad.length) throw new Error("CROSS_SLOT_STAGED:"+bad.join(","));
  return ps;
}
function fg6PathsChanged(base, head){
  if(base===head) return [];
  const out=execFileSync("git",["diff","--name-only",`${base}..${head}`],{cwd:ROOT,encoding:"utf8"}).trim();
  const ps=out?out.split(/\r?\n/):[];
  return ps.filter(p=>p===MIRROR || p.startsWith("state/slots/future_growth_6/"));
}
function commitPushReadback(batch, expectedRemoteHead, expectedCount) {
  sh(["git","add",MIRROR,CHECKPOINT,STATUS,MANIFEST]);
  const staged=assertOnlyAllowedStaged();
  if(staged.length===0) throw new Error(`BATCH_${batch}_NO_STAGED_STATE`);
  sh(["git","commit","-m",`future_growth_6: process strict batch ${batch}`]);
  sh(["git","fetch","origin",CANONICAL_BRANCH]);
  let remote=sh(["git","rev-parse",`origin/${CANONICAL_BRANCH}`],{capture:true});
  if(remote!==expectedRemoteHead){
    const conflicts=fg6PathsChanged(expectedRemoteHead,remote);
    if(conflicts.length) throw new Error(`CONCURRENT_FG6_WRITE_BEFORE_BATCH_${batch}:`+conflicts.join(","));
    sh(["git","rebase",`origin/${CANONICAL_BRANCH}`]);
  }
  sh(["git","push","origin",`HEAD:${CANONICAL_BRANCH}`]);
  sh(["git","fetch","origin",CANONICAL_BRANCH]);
  const remoteAfter=sh(["git","rev-parse",`origin/${CANONICAL_BRANCH}`],{capture:true});
  const local=sh(["git","rev-parse","HEAD"],{capture:true});
  if(remoteAfter!==local) throw new Error(`REMOTE_HEAD_MISMATCH_BATCH_${batch}`);
  const rbMirror=JSON.parse(gitShow(`origin/${CANONICAL_BRANCH}`,MIRROR));
  const rbCp=JSON.parse(gitShow(`origin/${CANONICAL_BRANCH}`,CHECKPOINT));
  const rbSt=JSON.parse(gitShow(`origin/${CANONICAL_BRANCH}`,STATUS));
  const rbMf=JSON.parse(gitShow(`origin/${CANONICAL_BRANCH}`,MANIFEST));
  const mc=assertMirror(rbMirror);
  if(mc!==expectedCount) throw new Error(`READBACK_MIRROR_COUNT_BATCH_${batch}:${mc}:${expectedCount}`);
  const vals=[rbCp.unique_evidenced_parcel_count_after,rbSt.unique_evidenced_parcel_count_after,rbMf.unique_evidenced_parcel_count];
  if(vals.some(v=>v!==expectedCount)) throw new Error(`READBACK_COUNT_INVARIANT_BATCH_${batch}:`+JSON.stringify(vals));
  if(rbCp.duplicate_count!==0 || rbSt.duplicate_count!==0 || rbMf.duplicate_count!==0) throw new Error(`READBACK_DUP_NONZERO_BATCH_${batch}`);
  if(rbCp.fake_data!==false || rbSt.fake_data!==false || rbMf.fake_data!==false) throw new Error(`READBACK_FAKE_FLAG_BATCH_${batch}`);
  if(rbCp.nearest_match_used!==false || rbSt.nearest_match_used!==false || rbMf.nearest_match_used!==false) throw new Error(`READBACK_NEAREST_FLAG_BATCH_${batch}`);
  if(rbCp.last_batch?.batch!==batch || rbSt.last_batch_index!==batch) throw new Error(`READBACK_CURSOR_BATCH_${batch}`);
  console.log(JSON.stringify({event:"BATCH_READBACK_PASS",batch,count:expectedCount,dup:0,remote_head:remoteAfter}));
  return remoteAfter;
}
function finalReportPushReadback(expectedRemoteHead, reportObj) {
  writeJson(REPORT,reportObj);
  sh(["git","add",REPORT]);
  const staged=assertOnlyAllowedStaged();
  if(staged.length!==1 || staged[0]!==REPORT) throw new Error("FINAL_REPORT_STAGE_INVARIANT");
  sh(["git","commit","-m",`future_growth_6: report strict batches ${EXPECTED_START_BATCH}-${EXPECTED_START_BATCH+BATCH_COUNT-1}`]);
  sh(["git","fetch","origin",CANONICAL_BRANCH]);
  let remote=sh(["git","rev-parse",`origin/${CANONICAL_BRANCH}`],{capture:true});
  if(remote!==expectedRemoteHead){
    const conflicts=fg6PathsChanged(expectedRemoteHead,remote);
    if(conflicts.length) throw new Error("CONCURRENT_FG6_WRITE_BEFORE_REPORT:"+conflicts.join(","));
