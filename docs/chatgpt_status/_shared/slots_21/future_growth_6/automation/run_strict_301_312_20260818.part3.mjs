    sh(["git","rebase",`origin/${CANONICAL_BRANCH}`]);
  }
  sh(["git","push","origin",`HEAD:${CANONICAL_BRANCH}`]);
  sh(["git","fetch","origin",CANONICAL_BRANCH]);
  const remoteAfter=sh(["git","rev-parse",`origin/${CANONICAL_BRANCH}`],{capture:true});
  const rb=JSON.parse(gitShow(`origin/${CANONICAL_BRANCH}`,REPORT));
  if(rb.run_id!==reportObj.run_id || rb.counts?.after_unique_evidenced_parcels!==reportObj.counts.after_unique_evidenced_parcels) throw new Error("FINAL_REPORT_READBACK_FAIL");
  console.log(JSON.stringify({event:"FINAL_REPORT_READBACK_PASS",path:REPORT,remote_head:remoteAfter}));
  return remoteAfter;
}

async function main(){
  sh(["git","status","--porcelain"],{capture:true});
  const cp0=readJson(CHECKPOINT), st0=readJson(STATUS), mf0=readJson(MANIFEST), rp0=readJson(REPORT), mirror=readJson(MIRROR);
  if(cp0.slot_id!==SLOT || st0.slot_id!==SLOT || mf0.slot_id!==SLOT || rp0.slot_id!==SLOT) throw new Error("SLOT_ID_MISMATCH");
  if(cp0.continuation_key!==CONT || st0.continuation_key!==CONT || mf0.continuation_key!==CONT) throw new Error("CONTINUATION_KEY_MISMATCH");
  if(cp0.next_batch_index!==EXPECTED_START_BATCH || st0.next_batch_index!==EXPECTED_START_BATCH || mf0.next_batch_index!==EXPECTED_START_BATCH || rp0.next_batch_index!==EXPECTED_START_BATCH) throw new Error("CURSOR_MOVED_FROM_301");
  if(cp0.duplicate_count!==0 || st0.duplicate_count!==0 || mf0.duplicate_count!==0) throw new Error("BASELINE_DUP_NONZERO");
  const before=assertMirror(mirror);
  if(before!==EXPECTED_BEFORE || cp0.unique_evidenced_parcel_count_after!==before || st0.unique_evidenced_parcel_count_after!==before || mf0.unique_evidenced_parcel_count!==before) throw new Error(`BASELINE_COUNT_MISMATCH:${before}`);
  const allPriorText=[JSON.stringify(cp0),JSON.stringify(st0),JSON.stringify(mf0),JSON.stringify(rp0)];
  if(fs.existsSync(path.join(ROOT,LEGACY_DOC_CP))) allPriorText.push(fs.readFileSync(path.join(ROOT,LEGACY_DOC_CP),"utf8"));
  for(const [i,w] of LPA_WINDOWS.entries()){
    const key=`planning_data_brownfield_land_south_west:lpa_${w.entity}:${w.slug}:offset_0_limit_50`;
    if(allPriorText.some(t=>t.includes(key))) throw new Error(`REUSED_WINDOW:${key}`);
  }
  const cfg=readJson(CONFIG);
  const pmtilesUrl=findSouthWestPmtilesUrl(cfg);
  const pm=new PMTiles(pmtilesUrl);
  const header=await pm.getHeader();
  if(!(header.minLon<=-6.7 && header.maxLon>=-1.7 && header.minLat<=49.8 && header.maxLat>=51.4)) {
    console.log("PMTILES_HEADER",header);
  }
  if(header.maxZoom<10) throw new Error("PMTILES_MAX_ZOOM_TOO_LOW");

  // Validate LPA entities against the authoritative Planning Data endpoint.
  const lpaResp=await getJson("https://www.planning.data.gov.uk/entity.json",{dataset:"local-planning-authority",limit:500,field:["name","entity"]});
  const lpas=entitiesFrom(lpaResp.json);
  const lpaById=new Map(lpas.map(e=>[Number(e.entity),e]));
  for(const w of LPA_WINDOWS){
    const ent=lpaById.get(w.entity);
    if(!ent) throw new Error(`LPA_NOT_FOUND:${w.entity}`);
  }

  let expectedRemoteHead=sh(["git","rev-parse","HEAD"],{capture:true});
  sh(["git","fetch","origin",CANONICAL_BRANCH]);
  const remote0=sh(["git","rev-parse",`origin/${CANONICAL_BRANCH}`],{capture:true});
  if(remote0!==expectedRemoteHead) throw new Error(`CANONICAL_MOVED_BEFORE_RUN:${expectedRemoteHead}:${remote0}`);

  const runId=`common_continuation_20260818_batches_${EXPECTED_START_BATCH}_${EXPECTED_START_BATCH+BATCH_COUNT-1}_south_west_brownfield_exact_pmtiles`;
  const runSources=[];
  const baseIds=uniqueProgramIds(mirror);
  let currentMirror=mirror;
  let currentCount=before;
  let totalAdded=0;

  for(let idx=0;idx<BATCH_COUNT;idx++){
    const batch=EXPECTED_START_BATCH+idx;
    const w=LPA_WINDOWS[idx];
    const lpa=lpaById.get(w.entity);
    const windowKey=`planning_data_brownfield_land_south_west:lpa_${w.entity}:${w.slug}:offset_0_limit_50`;
    const accessed=now();
    let sourceResult;
    let responseHash=null;
    let candidates=0, exactOne=0, skippedNoPoint=0, skippedNoMatch=0, skippedAmbiguous=0, skippedDuplicate=0;
    const addedFeatures=[];
    let sourceUrl=`https://www.planning.data.gov.uk/entity.json?dataset=brownfield-land&geometry_entity=${w.entity}&geometry_relation=within&quality=authoritative&limit=50&offset=0`;

    try{
      const resp=await getJson("https://www.planning.data.gov.uk/entity.json",{
        dataset:"brownfield-land",geometry_entity:w.entity,geometry_relation:"within",quality:"authoritative",limit:50,offset:0
      });
      sourceUrl=resp.url;
      responseHash=sha256Text(resp.text);
      const rows=entitiesFrom(resp.json);
      candidates=rows.length;
      for(const b of rows){
        const p=parsePointWkt(b.point);
        if(!p){ skippedNoPoint++; continue; }
        const [lon,lat]=p;
        let hit;
        try { hit=await exactCanonicalParcelAt(pm,header,lon,lat); }
        catch(e){ console.log("PMTILES_CANDIDATE_ERROR",batch,b.entity,String(e)); skippedNoMatch++; continue; }
        if(hit.status==="EXACT_ONE"){
          exactOne++;
          const parcel=hit.matches[0];
          const programId=`pmtiles:south_west:${parcel.parcel_id}`;
          if(baseIds.has(programId) || currentMirror.features.some(f=>f.properties?.program_parcel_id===programId)) { skippedDuplicate++; continue; }
          const f=featureFor(parcel,b,{url:resp.url,accessed_at:accessed,sha256:responseHash},pmtilesUrl,windowKey,batch);
          addedFeatures.push(f);
        } else if(hit.status==="AMBIGUOUS_MULTIPLE_CANONICAL_MATCHES") skippedAmbiguous++;
        else skippedNoMatch++;
      }
      sourceResult=addedFeatures.length>0?"ADDED_STRICT_CANONICAL_PARCELS":"ZERO_SAFE_CANONICAL_MATCHES";
    }catch(e){
      sourceResult="ZERO_SOURCE_QUERY_ERROR";
      console.log("SOURCE_WINDOW_ERROR",batch,String(e));
    }

    // Deterministic de-duplication within this window by canonical program parcel id.
    const uniq=[];
    const seen=new Set(currentMirror.features.map(f=>f.properties.program_parcel_id));
    for(const f of addedFeatures){
      const id=f.properties.program_parcel_id;
      if(seen.has(id)){ skippedDuplicate++; continue; }
      seen.add(id); uniq.push(f);
    }
    currentMirror={type:"FeatureCollection",features:[...currentMirror.features,...uniq]};
    currentCount=assertMirror(currentMirror);
    totalAdded=currentCount-before;

    const sourceEntry={
      batch,window_key:windowKey,
      source_family:"Planning Data Brownfield Land authoritative site points + canonical south_west.pmtiles exact point-in-polygon",
      source_name:`Brownfield Land within ${lpa.name||w.slug}`,
      source_ref:sourceUrl,
      source_sha256:responseHash,
      lpa_entity:w.entity,
      lpa_name:lpa.name||null,
      candidates,
      exact_one_canonical_matches:exactOne,
      new_features:uniq.length,
      skipped_no_point:skippedNoPoint,
      skipped_no_exact_canonical_match:skippedNoMatch,
      skipped_ambiguous_multiple_canonical_matches:skippedAmbiguous,
      skipped_duplicate_canonical_parcels:skippedDuplicate,
      result:sourceResult,
      readback:"PENDING"
    };
    runSources.push(sourceEntry);

    const common={
      slot_id:SLOT,continuation_key:CONT,run_id:runId,
      unique_evidenced_parcel_count_before:before,
      unique_evidenced_parcel_count_after:currentCount,
      new_unique_evidenced_parcels:totalAdded,
      mirror_feature_count:currentCount,duplicate_count:0,
      fake_data:false,nearest_match_used:false,demo_only:true,final_ready:false,production_merge:false,
      cross_slot_writes:false,
      last_batch_index:batch,next_batch_index:batch+1,
