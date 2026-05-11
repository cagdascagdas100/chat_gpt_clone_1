# AAYS Autopilot Runner V5 Result

## Task
Install and run remote autopilot v6

## Task ID
terrayield-053-autopilot-v6-install-and-run

## Time
2026-05-11 18:48:51

## Working Directory
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence

## Timeout Seconds
600

## Exit Code
0

## Output
``text
[2026-05-11T18:48:44] PROJECT=terrayield
[2026-05-11T18:48:44] TASK=terrayield-053-autopilot-v6-install-and-run
[2026-05-11T18:48:44] MODE=install_remote_autopilot_v6
[2026-05-11T18:48:44] AUTOPILOT_SCRIPT_WRITTEN=C:\AAYS_GITHUB_BRIDGE_CLEAN\AAYS_REMOTE_AUTOPILOT_V6.ps1
[2026-05-11T18:48:44] STOP_OLD_RUNNER_PID=19604
[2026-05-11T18:48:45] SCHEDULED_TASK_REGISTERED=AAYS_TerraYield_RemoteAutopilotV6
[2026-05-11T18:48:45] AUTOPILOT_V6_STARTED
[2026-05-11T18:48:51] AUTOPILOT_V6_PROCESS_COUNT=0
[2026-05-11T18:48:51] PLAN_PROGRESS_PERCENT=18
[2026-05-11T18:48:51] NEXT_EXPECTED_ACTION=queue_contractor_install_task_after_v6_heartbeat
[2026-05-11T18:48:51] TASK_COMPLETION=100/100
[2026-05-11T18:48:51] TERRAYIELD_TASK_DONE

``

## Error
``text
Register-ScheduledTask : Erişim engellendi.
At C:\Users\cagda\Documents\chat_gpt_clone_1\ai-task-scripts\terrayield_053_autopilot_v6_install_and_run.ps1:171 char:3
+   Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger ...
+   ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : PermissionDenied: (PS_ScheduledTask:Root/Microsoft/...S_ScheduledTask) [Register-Schedul 
   edTask], CimException
    + FullyQualifiedErrorId : HRESULT 0x80070005,Register-ScheduledTask
 

``
