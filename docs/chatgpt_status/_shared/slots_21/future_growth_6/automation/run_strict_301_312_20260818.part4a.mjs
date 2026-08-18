      new_run_bounded_batches_completed:idx+1
    };
    const checkpoint={
      schema_version:20,...common,state:"BOUNDED_RUN_IN_PROGRESS",
      prior_used_windows_contract:{through_batch:300,do_not_reuse_batch_range:"13-300"},
      new_run_used_window_keys:runSources.map(x=>x.window_key),
      last_batch:sourceEntry,
      source_contract:{
        project_family:"Planning Data Brownfield Land authoritative records in South West LPAs",
        source_api:"https://www.planning.data.gov.uk/entity.json",
        canonical_parcel_source:pmtilesUrl,
        canonical_parcel_region:"south_west",
        matching_rule:"STRICT_AUTHORITATIVE_SOURCE_POINT_WITHIN_EXACTLY_ONE_CANONICAL_PMTILES_PARCEL_POLYGON",
        no_nearest:true,no_address_crosswalk:true,no_implicit_id_crosswalk:true
      },
      blocker:null
    };
    const status={
      schema_version:17,...common,state:"BOUNDED_RUN_IN_PROGRESS",
      last_window_key:windowKey,last_result:sourceResult,previous_batch_readback:"PENDING",blocker:null
    };
    const manifest={
      schema_version:17,slot_id:SLOT,continuation_key:CONT,run_id:runId,
      unique_evidenced_parcel_count:currentCount,mirror_feature_count:currentCount,duplicate_count:0,
      legacy_raw_feature_count:50,new_run_sources:runSources,new_run_bounded_batches_completed:idx+1,
      next_batch_index:batch+1,run_result:"IN_PROGRESS",blocker:null,
      fake_data:false,nearest_match_used:false,final_ready:false,production_merge:false,cross_slot_writes:false
    };
    writeJson(MIRROR,currentMirror); writeJson(CHECKPOINT,checkpoint); writeJson(STATUS,status); writeJson(MANIFEST,manifest);
    expectedRemoteHead=commitPushReadback(batch,expectedRemoteHead,currentCount);
    sourceEntry.readback="PASS";
    // Persist PASS marker in next batch's state; final batch gets explicit final commit below.
  }

  const finalBatch=EXPECTED_START_BATCH+BATCH_COUNT-1;
  const allZero=runSources.every(x=>x.new_features===0);
  const finalState=totalAdded>0?"BOUNDED_RUN_COMPLETE_WITH_SAFE_ADDITIONS":"BOUNDED_RUN_COMPLETE_NO_SAFE_ADDITIONS";
  const finalCheckpoint=readJson(CHECKPOINT);
  Object.assign(finalCheckpoint,{state:finalState,last_batch_index:finalBatch,next_batch_index:finalBatch+1,new_run_bounded_batches_completed:BATCH_COUNT,
    unique_evidenced_parcel_count_after:currentCount,new_unique_evidenced_parcels:totalAdded,duplicate_count:0,
    blocker:allZero?"NO_EXACT_CANONICAL_PARCEL_MATCHES_IN_12_NEW_WINDOWS":null});
  finalCheckpoint.last_batch=runSources[runSources.length-1];
  const finalStatus=readJson(STATUS);
  Object.assign(finalStatus,{state:finalState,last_batch_index:finalBatch,next_batch_index:finalBatch+1,new_run_bounded_batches_completed:BATCH_COUNT,
    unique_evidenced_parcel_count_after:currentCount,new_unique_evidenced_parcels:totalAdded,duplicate_count:0,
    previous_batch_readback:"PASS",blocker:allZero?"NO_EXACT_CANONICAL_PARCEL_MATCHES_IN_12_NEW_WINDOWS":null});
  const finalManifest=readJson(MANIFEST);
  Object.assign(finalManifest,{run_result:totalAdded>0?"SAFE_ADDITIONS_COMMITTED":"NO_SAFE_ADDITIONS",next_batch_index:finalBatch+1,
    unique_evidenced_parcel_count:currentCount,mirror_feature_count:currentCount,duplicate_count:0,
    new_run_sources:runSources,new_run_bounded_batches_completed:BATCH_COUNT,
    blocker:allZero?"NO_EXACT_CANONICAL_PARCEL_MATCHES_IN_12_NEW_WINDOWS":null});
  writeJson(CHECKPOINT,finalCheckpoint); writeJson(STATUS,finalStatus); writeJson(MANIFEST,finalManifest);

  // Final state marker makes the last batch PASS explicit and is itself remote-read.
  sh(["git","add",CHECKPOINT,STATUS,MANIFEST]);
  assertOnlyAllowedStaged();
  if(stagedPaths().length){
    sh(["git","commit","-m",`future_growth_6: finalize strict batches ${EXPECTED_START_BATCH}-${finalBatch}`]);
    sh(["git","fetch","origin",CANONICAL_BRANCH]);
    let remote=sh(["git","rev-parse",`origin/${CANONICAL_BRANCH}`],{capture:true});
    if(remote!==expectedRemoteHead){
      const conflicts=fg6PathsChanged(expectedRemoteHead,remote);
      if(conflicts.length) throw new Error("CONCURRENT_FG6_WRITE_BEFORE_FINALIZE:"+conflicts.join(","));
      sh(["git","rebase",`origin/${CANONICAL_BRANCH}`]);
    }
