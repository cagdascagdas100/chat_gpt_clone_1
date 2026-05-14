# AAYS 054 Supervisor Recovery Status
Generated: 2026-05-14T14:46:24
mode: recovery_status_read_only

## PowerShell processes


ProcessId       : 4268
ParentProcessId : 13960
CommandLine     : C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe

ProcessId       : 23916
ParentProcessId : 4268
CommandLine     : "C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass -NoExi
                  t -File "C:\AAYS_GITHUB_BRIDGE_CLEAN2\AAYS_SAFE_CONTINUE_BRIDGE_V2.ps1" 

ProcessId       : 22544
ParentProcessId : 13960
CommandLine     : C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe

ProcessId       : 7188
ParentProcessId : 13960
CommandLine     : C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe

ProcessId       : 19308
ParentProcessId : 27096
CommandLine     : "C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass -File 
                  C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-task-scripts\aays_053_auto_clean_cluster_db_dryrun_20260514.ps1

ProcessId       : 15900
ParentProcessId : 13960
CommandLine     : C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe

ProcessId       : 11144
ParentProcessId : 13960
CommandLine     : C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe

ProcessId       : 13816
ParentProcessId : 11144
CommandLine     : "C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass -File 
                  .\AAYS_AUTOPILOT_RUNNER_V6_SAFE_SYNC.ps1

ProcessId       : 19520
ParentProcessId : 13960
CommandLine     : C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe

ProcessId       : 25364
ParentProcessId : 19520
CommandLine     : "C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass -NoExi
                  t -File C:\AAYS_GITHUB_BRIDGE_CLEAN2\AAYS_AUTOPILOT_SUPERVISOR_V1.ps1 

ProcessId       : 27476
ParentProcessId : 13960
CommandLine     : C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe

ProcessId       : 25584
ParentProcessId : 13960
CommandLine     : C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe

ProcessId       : 24104
ParentProcessId : 25364
CommandLine     : "C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass -File 
                  C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-task-scripts\aays_054_supervisor_recovery_status_20260514.ps1 





## PostgreSQL processes


ProcessId       : 14440
ParentProcessId : 13480
Name            : postgres.exe
CommandLine     : "C:/Program Files/PostgreSQL/18/bin/postgres.exe"  -D "E:/AAYS_DATA/postgresql18_aays_cluster" -p 543
                  3 

ProcessId       : 17244
ParentProcessId : 14440
Name            : postgres.exe
CommandLine     : "C:/Program Files/PostgreSQL/18/bin/postgres.exe" --forkchild="io_worker" 5888

ProcessId       : 17976
ParentProcessId : 14440
Name            : postgres.exe
CommandLine     : "C:/Program Files/PostgreSQL/18/bin/postgres.exe" --forkchild="checkpointer" 5848

ProcessId       : 5356
ParentProcessId : 14440
Name            : postgres.exe
CommandLine     : "C:/Program Files/PostgreSQL/18/bin/postgres.exe" --forkchild="bgwriter" 5856

ProcessId       : 23700
ParentProcessId : 14440
Name            : postgres.exe
CommandLine     : "C:/Program Files/PostgreSQL/18/bin/postgres.exe" --forkchild="wal_writer" 5824

ProcessId       : 21516
ParentProcessId : 14440
Name            : postgres.exe
CommandLine     : "C:/Program Files/PostgreSQL/18/bin/postgres.exe" --forkchild="autovacuum launcher" 5816

ProcessId       : 24804
ParentProcessId : 14440
Name            : postgres.exe
CommandLine     : "C:/Program Files/PostgreSQL/18/bin/postgres.exe" --forkchild="io_worker" 5864

ProcessId       : 24980
ParentProcessId : 14440
Name            : postgres.exe
CommandLine     : "C:/Program Files/PostgreSQL/18/bin/postgres.exe" --forkchild="bgworker" 5684

ProcessId       : 24088
ParentProcessId : 14440
Name            : postgres.exe
CommandLine     : "C:/Program Files/PostgreSQL/18/bin/postgres.exe" --forkchild="io_worker" 5844

ProcessId       : 13340
ParentProcessId : 26048
Name            : postgres.exe
CommandLine     : "C:/Program Files/PostgreSQL/18/bin/postgres.exe"  -D "E:/AAYS_DATA/postgresql18_aays_auto_cluster_20
                  260514_125125" -p 5434 -h 127.0.0.1 

ProcessId       : 20408
ParentProcessId : 13340
Name            : postgres.exe
CommandLine     : "C:/Program Files/PostgreSQL/18/bin/postgres.exe" --forkchild="io_worker" 5996

ProcessId       : 11428
ParentProcessId : 13340
Name            : postgres.exe
CommandLine     : "C:/Program Files/PostgreSQL/18/bin/postgres.exe" --forkchild="io_worker" 6016

ProcessId       : 2324
ParentProcessId : 13340
Name            : postgres.exe
CommandLine     : "C:/Program Files/PostgreSQL/18/bin/postgres.exe" --forkchild="io_worker" 6000

ProcessId       : 22564
ParentProcessId : 13340
Name            : postgres.exe
CommandLine     : "C:/Program Files/PostgreSQL/18/bin/postgres.exe" --forkchild="checkpointer" 5948

ProcessId       : 20692
ParentProcessId : 13340
Name            : postgres.exe
CommandLine     : "C:/Program Files/PostgreSQL/18/bin/postgres.exe" --forkchild="bgwriter" 5936

ProcessId       : 9228
ParentProcessId : 13340
Name            : postgres.exe
CommandLine     : "C:/Program Files/PostgreSQL/18/bin/postgres.exe" --forkchild="wal_writer" 5904

ProcessId       : 14112
ParentProcessId : 13340
Name            : postgres.exe
CommandLine     : "C:/Program Files/PostgreSQL/18/bin/postgres.exe" --forkchild="autovacuum launcher" 5920

ProcessId       : 25772
ParentProcessId : 13340
Name            : postgres.exe
CommandLine     : "C:/Program Files/PostgreSQL/18/bin/postgres.exe" --forkchild="bgworker" 5896

ProcessId       : 4188
ParentProcessId : 5260
Name            : postgres.exe
CommandLine     : "C:/Program Files/PostgreSQL/18/bin/postgres.exe"  -D "E:/AAYS_DATA/postgresql18_aays_auto_cluster_20
                  260514_125923" -p 5435 -h 127.0.0.1 

ProcessId       : 23656
ParentProcessId : 4188
Name            : postgres.exe
CommandLine     : "C:/Program Files/PostgreSQL/18/bin/postgres.exe" --forkchild="io_worker" 6004

ProcessId       : 13024
ParentProcessId : 4188
Name            : postgres.exe
CommandLine     : "C:/Program Files/PostgreSQL/18/bin/postgres.exe" --forkchild="io_worker" 6000

ProcessId       : 12416
ParentProcessId : 4188
Name            : postgres.exe
CommandLine     : "C:/Program Files/PostgreSQL/18/bin/postgres.exe" --forkchild="io_worker" 5968

ProcessId       : 11504
ParentProcessId : 4188
Name            : postgres.exe
CommandLine     : "C:/Program Files/PostgreSQL/18/bin/postgres.exe" --forkchild="checkpointer" 5956

ProcessId       : 16240
ParentProcessId : 4188
Name            : postgres.exe
CommandLine     : "C:/Program Files/PostgreSQL/18/bin/postgres.exe" --forkchild="bgwriter" 5940

ProcessId       : 8552
ParentProcessId : 4188
Name            : postgres.exe
CommandLine     : "C:/Program Files/PostgreSQL/18/bin/postgres.exe" --forkchild="wal_writer" 5924

ProcessId       : 24568
ParentProcessId : 4188
Name            : postgres.exe
CommandLine     : "C:/Program Files/PostgreSQL/18/bin/postgres.exe" --forkchild="autovacuum launcher" 5908

ProcessId       : 23776
ParentProcessId : 4188
Name            : postgres.exe
CommandLine     : "C:/Program Files/PostgreSQL/18/bin/postgres.exe" --forkchild="bgworker" 5888

ProcessId       : 18488
ParentProcessId : 6108
Name            : postgres.exe
CommandLine     : "C:/Program Files/PostgreSQL/18/bin/postgres.exe"  -D "E:/AAYS_DATA/postgresql18_aays_auto_cluster_20
                  260514_131229" -p 5436 -h 127.0.0.1 

ProcessId       : 13408
ParentProcessId : 18488
Name            : postgres.exe
CommandLine     : "C:/Program Files/PostgreSQL/18/bin/postgres.exe" --forkchild="io_worker" 6000

ProcessId       : 412
ParentProcessId : 18488
Name            : postgres.exe
CommandLine     : "C:/Program Files/PostgreSQL/18/bin/postgres.exe" --forkchild="io_worker" 6004

ProcessId       : 26580
ParentProcessId : 18488
Name            : postgres.exe
CommandLine     : "C:/Program Files/PostgreSQL/18/bin/postgres.exe" --forkchild="io_worker" 5968

ProcessId       : 16328
ParentProcessId : 18488
Name            : postgres.exe
CommandLine     : "C:/Program Files/PostgreSQL/18/bin/postgres.exe" --forkchild="checkpointer" 5956

ProcessId       : 23704
ParentProcessId : 18488
Name            : postgres.exe
CommandLine     : "C:/Program Files/PostgreSQL/18/bin/postgres.exe" --forkchild="bgwriter" 5948

ProcessId       : 8696
ParentProcessId : 18488
Name            : postgres.exe
CommandLine     : "C:/Program Files/PostgreSQL/18/bin/postgres.exe" --forkchild="wal_writer" 5916

ProcessId       : 13660
ParentProcessId : 18488
Name            : postgres.exe
CommandLine     : "C:/Program Files/PostgreSQL/18/bin/postgres.exe" --forkchild="autovacuum launcher" 5936

ProcessId       : 14412
ParentProcessId : 18488
Name            : postgres.exe
CommandLine     : "C:/Program Files/PostgreSQL/18/bin/postgres.exe" --forkchild="bgworker" 5932

ProcessId       : 27960
ParentProcessId : 10244
Name            : postgres.exe
CommandLine     : "C:/Program Files/PostgreSQL/18/bin/postgres.exe"  -D "E:/AAYS_DATA/postgresql18_aays_auto_cluster_20
                  260514_134847" -p 5437 -h 127.0.0.1 

ProcessId       : 18992
ParentProcessId : 27960
Name            : postgres.exe
CommandLine     : "C:/Program Files/PostgreSQL/18/bin/postgres.exe" --forkchild="io_worker" 6000

ProcessId       : 21668
ParentProcessId : 27960
Name            : postgres.exe
CommandLine     : "C:/Program Files/PostgreSQL/18/bin/postgres.exe" --forkchild="io_worker" 6012

ProcessId       : 26920
ParentProcessId : 27960
Name            : postgres.exe
CommandLine     : "C:/Program Files/PostgreSQL/18/bin/postgres.exe" --forkchild="io_worker" 5980

ProcessId       : 19040
ParentProcessId : 27960
Name            : postgres.exe
CommandLine     : "C:/Program Files/PostgreSQL/18/bin/postgres.exe" --forkchild="checkpointer" 5944

ProcessId       : 26292
ParentProcessId : 27960
Name            : postgres.exe
CommandLine     : "C:/Program Files/PostgreSQL/18/bin/postgres.exe" --forkchild="bgwriter" 5932

ProcessId       : 12396
ParentProcessId : 27960
Name            : postgres.exe
CommandLine     : "C:/Program Files/PostgreSQL/18/bin/postgres.exe" --forkchild="wal_writer" 5912

ProcessId       : 10884
ParentProcessId : 27960
Name            : postgres.exe
CommandLine     : "C:/Program Files/PostgreSQL/18/bin/postgres.exe" --forkchild="autovacuum launcher" 5904

ProcessId       : 21788
ParentProcessId : 27960
Name            : postgres.exe
CommandLine     : "C:/Program Files/PostgreSQL/18/bin/postgres.exe" --forkchild="bgworker" 5916

ProcessId       : 18688
ParentProcessId : 22032
Name            : postgres.exe
CommandLine     : "C:/Program Files/PostgreSQL/18/bin/postgres.exe"  -D "E:/AAYS_DATA/postgresql18_aays_auto_cluster_20
                  260514_135633" -p 5438 -h 127.0.0.1 

ProcessId       : 14900
ParentProcessId : 18688
Name            : postgres.exe
CommandLine     : "C:/Program Files/PostgreSQL/18/bin/postgres.exe" --forkchild="io_worker" 6000

ProcessId       : 15308
ParentProcessId : 18688
Name            : postgres.exe
CommandLine     : "C:/Program Files/PostgreSQL/18/bin/postgres.exe" --forkchild="io_worker" 5992

ProcessId       : 9508
ParentProcessId : 18688
Name            : postgres.exe
CommandLine     : "C:/Program Files/PostgreSQL/18/bin/postgres.exe" --forkchild="io_worker" 5964

ProcessId       : 10620
ParentProcessId : 18688
Name            : postgres.exe
CommandLine     : "C:/Program Files/PostgreSQL/18/bin/postgres.exe" --forkchild="checkpointer" 5952

ProcessId       : 26928
ParentProcessId : 18688
Name            : postgres.exe
CommandLine     : "C:/Program Files/PostgreSQL/18/bin/postgres.exe" --forkchild="bgwriter" 5936

ProcessId       : 21060
ParentProcessId : 18688
Name            : postgres.exe
CommandLine     : "C:/Program Files/PostgreSQL/18/bin/postgres.exe" --forkchild="wal_writer" 5908

ProcessId       : 25172
ParentProcessId : 18688
Name            : postgres.exe
CommandLine     : "C:/Program Files/PostgreSQL/18/bin/postgres.exe" --forkchild="autovacuum launcher" 5904

ProcessId       : 28056
ParentProcessId : 18688
Name            : postgres.exe
CommandLine     : "C:/Program Files/PostgreSQL/18/bin/postgres.exe" --forkchild="bgworker" 5924





## Repo status
 M ai-heartbeat/autopilot-supervisor.md
?? AAYS_AUTOPILOT_RUNNER_V6_SAFE_SYNC.ps1.bak
?? AAYS_AUTOPILOT_RUNNER_V6_SAFE_SYNC.ps1.disabled
?? AAYS_DEVAM_LOOP.ps1.disabled
?? AAYS_RUNNER_COMPATIBILITY_RULE.txt
?? ai-results/aays-054-supervisor-recovery-status-20260514_144624.md


plan_progress_percent: 82
AAYS_054_SUPERVISOR_RECOVERY_STATUS_DONE=true
