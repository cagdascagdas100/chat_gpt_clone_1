# AAYS Portable Task Runner Result

## Task
TerraYield Cost Engine Step 051 smoke test

## Task ID
terrayield-cost-engine-051-smoke-test-20260520-01

## Time
2026-05-20 19:44:26

## Working Directory
C:/AAYS_GITHUB_BRIDGE_CLEAN2

## Exit Code
1

## Runner Mode
no-spawn-foreground-loop

## Output
```text
{
  "output_json": "C:\\AAYS_GITHUB_BRIDGE_CLEAN2\\ai-results\\terrayield_cost_engine\\run_20260520_194425\\output_detached_london_250m2.json",
  "totals": {
    "min_total_gbp": 1254610.0,
    "max_total_gbp": 1913110.0,
    "mid_total_gbp": 1583860.0,
    "initial_payment_gbp": 289010.0,
    "recurring_payment_gbp_per_month": 67922.22
  },
  "line_count": 12
}
powershell.exe : Traceback (most recent call last):
At C:\AAYS_GITHUB_BRIDGE_CLEAN2\AAYS_PORTABLE_TASK_RUNNER_FIXED.ps1:136 char:16
+ ...  $output = (& powershell.exe -NoProfile -ExecutionPolicy Bypass -File ...
+                 ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : NotSpecified: (Traceback (most recent call last)::String) [], RemoteException
    + FullyQualifiedErrorId : NativeCommandError
 
  File "C:\AAYS_GITHUB_BRIDGE_CLEAN2\terrayield_cost_engine\python_demo\terrayield_cost_engine_demo.py", line 390, in <
module>
    main()
  File "C:\AAYS_GITHUB_BRIDGE_CLEAN2\terrayield_cost_engine\python_demo\terrayield_cost_engine_demo.py", line 381, in m
ain
    inp = EstimateInput(**json.load(handle))
                          ^^^^^^^^^^^^^^^^^
  File "C:\Python312\Lib\json\__init__.py", line 293, in load
    return loads(fp.read(),
           ^^^^^^^^^^^^^^^^
  File "C:\Python312\Lib\json\__init__.py", line 335, in loads
    raise JSONDecodeError("Unexpected UTF-8 BOM (decode using utf-8-sig)",
json.decoder.JSONDecodeError: Unexpected UTF-8 BOM (decode using utf-8-sig): line 1 column 1 (char 0)
Get-Content : Cannot find path 'C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-results\terrayield_cost_engine\run_20260520_194425\outp
ut_industrial_demo_2500m2.json' because it does not exist.
At C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-task-scripts\terrayield_cost_engine_051_smoke_test_20260520.ps1:71 char:19
+ ... dustrialJson = Get-Content -Raw -Encoding UTF8 $IndustrialOut | Conve ...
+                    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : ObjectNotFound: (C:\AAYS_GITHUB_...emo_2500m2.json:String) [Get-Content], ItemNotFoundEx 
   ception
    + FullyQualifiedErrorId : PathNotFound,Microsoft.PowerShell.Commands.GetContentCommand
 


```

## Error
```text


```
