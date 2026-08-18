    sh(["git","push","origin",`HEAD:${CANONICAL_BRANCH}`]);
    sh(["git","fetch","origin",CANONICAL_BRANCH]);
    expectedRemoteHead=sh(["git","rev-parse",`origin/${CANONICAL_BRANCH}`],{capture:true});
    const rbm=JSON.parse(gitShow(`origin/${CANONICAL_BRANCH}`,MIRROR));
    const rbc=JSON.parse(gitShow(`origin/${CANONICAL_BRANCH}`,CHECKPOINT));
    const rbs=JSON.parse(gitShow(`origin/${CANONICAL_BRANCH}`,STATUS));
    const rbf=JSON.parse(gitShow(`origin/${CANONICAL_BRANCH}`,MANIFEST));
    const mc=assertMirror(rbm);
    if(mc!==currentCount || rbc.unique_evidenced_parcel_count_after!==currentCount || rbs.unique_evidenced_parcel_count_after!==currentCount || rbf.unique_evidenced_parcel_count!==currentCount) throw new Error("FINAL_STATE_COUNT_READBACK_FAIL");
    if(rbc.duplicate_count!==0||rbs.duplicate_count!==0||rbf.duplicate_count!==0) throw new Error("FINAL_STATE_DUP_READBACK_FAIL");
  }

  const report={
    schema_version:2,slot_id:SLOT,continuation_key:CONT,run_id:runId,
    requested_common_continuation_path:"F:\\TerraYield_AAYS_Portable\\docs\\deepseek_prompts\\AAYS_CHATGPT_PLAN_00_23_SLOT_COMMON_CONTINUATION_20260818.md",
    requested_common_continuation_file_read:false,
    requested_common_continuation_file_note:"Exact F: path is not mounted in the execution runtime. Execution follows the user's current continuation instruction plus authoritative future_growth_6 state/report/checkpoint/status/manifest/current-task/source-contract/write-ownership state.",
    requested_new_bounded_batches:BATCH_COUNT,completed_new_bounded_batches:BATCH_COUNT,
    batch_range:{first:EXPECTED_START_BATCH,last:finalBatch},
    counts:{before_unique_evidenced_parcels:before,added_unique_evidenced_parcels:totalAdded,after_unique_evidenced_parcels:currentCount,legacy_raw_feature_count:50,mirror_feature_count:currentCount,duplicate_count:0},
    quality_gates:{
      shard_checkpoint_status_manifest_count_invariant_equal:true,duplicate_count_zero:true,nearest_match_used:false,fake_data:false,cross_slot_writes:false,
      final_ready:false,production_merge:false,all_zero_windows_checkpointed:allZero,reused_window_count:0,own_slot_only:true,
      exact_single_canonical_parcel_required:true
    },
    artifact_paths:{shard:MIRROR,checkpoint:CHECKPOINT,status:STATUS,manifest:MANIFEST,report:REPORT},
    source_family:"Planning Data Brownfield Land authoritative site points + canonical south_west.pmtiles strict exact point-in-polygon",
    source_windows:runSources,
    blocker:allZero?"NO_EXACT_CANONICAL_PARCEL_MATCHES_IN_12_NEW_WINDOWS":null,
    next_batch_index:finalBatch+1,
    next_action:"Continue with the next unused allowed source family/window only; do not reuse batches 13-"+finalBatch+" or any window_key recorded in prior/current state."
  };
  expectedRemoteHead=finalReportPushReadback(expectedRemoteHead,report);
  console.log(JSON.stringify({event:"RUN_COMPLETE",report:REPORT,before,added:totalAdded,after:currentCount,batches:`${EXPECTED_START_BATCH}-${finalBatch}`,dup:0,remote_head:expectedRemoteHead}));
}
main().catch(e=>{console.error(e?.stack||String(e));process.exit(1);});
