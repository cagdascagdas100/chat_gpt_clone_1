# AAYS Portable Adaptive Five-Worker V2 Result

- STATUS: `PASS_WITH_PHYSICAL_TEST_LIMITATIONS`
- USER_OVERRIDE: `F_ONLY_NO_D_INSTALL`
- WORKSTREAM_ID: `AAYS_5_SLOT_SAFE_PARALLEL_V1`
- ARCHITECTURE_VERSION: `2`
- REMOTE_HEAD_BEFORE: `b728543a91c6716a92c8ebf052bd8162e7a4e4a1`
- CODE_COMMIT_SHA: `cfbdc716d9bc9a72b9928ffaa9b2be12abaaa504`
- CODE_PUSH: `PASS`
- CODE_REMOTE_READBACK: `PASS`
- EVIDENCE_COMMIT_SHA: `5e41cc748613867a0449f16ff0d1c86bc772f154`
- EVIDENCE_PUSH: `PASS`
- EVIDENCE_REMOTE_READBACK: `PASS`
- F_PORTABLE_INSTALL: `PASS`
- D_PORTABLE_INSTALL: `NOT_CREATED_BY_USER_OVERRIDE`
- F_SOURCE_PRESERVED: `true`
- PORTABLE_DRIVE_RELATIVE: `true`
- COORDINATOR_PROCESS_COUNT: `1`
- MAX_CHILD_WORKERS: `5`
- MAX_SIMULTANEOUS_FIXTURE_RUNNING: `5`
- DISTINCT_CHILD_GIT_ROOTS: `5`
- CHILD_DIRECT_PUSH_FORBIDDEN: `true`
- SLOT_CHECKPOINT_MIGRATION: `PASS_5_OF_5`
- PANEL_START_STOP_RESTART: `PASS`
- SAFE_REMOVE_INDICATOR: `PASS`
- DISK_NETWORK_SLEEP_REBOOT_RECOVERY_SIMULATION: `PASS`
- PORT_8012: `PASS_3_OF_3_HTTP_200`
- REMAINING_BLOCKERS: `none`
- FINAL_READY: `false`

Tek coordinator, beş izole adaptive child kapasitesini yönetir. Slot başına yalnız bir mutating task çalışır. Child clone'ların doğrudan push URL'si kapalıdır. Git publish, runtime sync, browser acceptance, shared publish, RAM-heavy, raster, geometry, vision ve heavy disk işlemleri global semaforlarla seri tutulur. Beş hafif fixture aynı anda çalışmış, business dosyası değiştirmemiştir.

Fiziksel disk çıkarma, gerçek reboot, gerçek sleep/resume ve gerçek internet kesme kullanıcı izni olmadan yapılmadı; bu durum PASS sonucunun fiziksel test sınırlamasıdır.
