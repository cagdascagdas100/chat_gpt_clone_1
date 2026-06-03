# AAYS ChatGPT Runner V4 Result

## Task
Run Plan L final pack wide QA after runner recovery

## Task ID
terrayield-115-plan-l-final-pack-wide-qa

## Progress
88%

## Action


## Time
05/07/2026 13:28:49

## Working Directory
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence

## Timeout Seconds
7200

## Exit Code
0

## Output
``text
# TerraYield 112 Plan L Recovery Final Pack
MODE=single_devam_maximal_safe_batch; recover_previous; rerun_if_needed; build_final_package; no_secrets; no_deploy
PLAN_BASE=D:\6 color parcells\plan_l_run01
FINAL_DIR=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_132555
RESULT=ok
QA_DIR=D:\6 color parcells\plan_l_run01\output\qa
REPORT_JSON=D:\6 color parcells\plan_l_run01\output\qa\plan_l_deep_qa_report.json
REPORT_MD=D:\6 color parcells\plan_l_run01\output\qa\PLAN_L_DEEP_QA_REPORT.md
## Consolidated final status
RESULT=needs_attention_recovery_final_pack
CLASSIFIER_EXIT=0
DEEP_QA_EXIT=0
CSV_ROWS=34864
GEOJSON_FEATURES=34864
FINAL_DIR=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_132555
FINAL_ZIP=D:\6 color parcells\plan_l_run01\final_packages\terrayield-112-plan-l-recovery-final-pack_20260507_132555.zip
## Class summary
class6,color,parcel_count,percent,area_m2_sum,avg_confidence
Sanayi,#F4C542,758,2.17,60822582.0,3.0
Ofis,#1F4E9E,634,1.82,3064594.11,3.0
Perakende,#7FD3FF,747,2.14,2272177.0,3.0
Apartman,#2E7D32,6425,18.43,60071255.55,3.0
Müstakil,#A8E6A1,26300,75.44,4955306.59,3.0
## Confidence summary
confidence_score,parcel_count,percent
3,34864,100.0
## QA report head
# Plan L Deep QA Report

Generated: 2026-05-07T10:26:13.402934Z

## Counts
- classified_rows: 34864
- market_rows: 3110
- voa_rows: 334617
- geojson_features: 34864

## Class counts
- : 34864

## Confidence counts
- : 34864

## Warnings
- missing expected columns: use6_class,use6_color,use6_confidence,use6_sources

NEXT_COMMAND=devam et
NEXT_COMMAND=devam et

``

## Error
``text
Set-Content : Akış okunabilir değildi.
At C:\Users\cagda\Documents\chat_gpt_clone_1\ai-task-scripts\terrayield_112_plan_l_recovery_final_pack.ps1:22 char:144
+ ... PlanBase) | Set-Content -Encoding UTF8 (Join-Path $BeatDir ($TaskId + ...
+                 ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidArgument: (C:\Users\cagda\...y-final-pack.md:String) [Set-Content], ArgumentExcep 
   tion
    + FullyQualifiedErrorId : GetContentWriterArgumentError,Microsoft.PowerShell.Commands.SetContentCommand
 
python.exe : D:\6 color parcells\plan_l_run01\scripts\plan_l_deep_qa.py:77: DeprecationWarning: datetime.datetime.utcno
w() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in U
TC: datetime.datetime.now(datetime.UTC).
At C:\Users\cagda\Documents\chat_gpt_clone_1\ai-task-scripts\terrayield_112_plan_l_recovery_final_pack.ps1:65 char:123
+ ... -Object -FilePath $qaLog } else { & $PythonExe $targetQA 2>&1 | Tee-O ...
+                                       ~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : NotSpecified: (D:\6 color parc...(datetime.UTC).:String) [], RemoteException
    + FullyQualifiedErrorId : NativeCommandError
 
  report = {'generated_at': datetime.utcnow().isoformat() + 'Z', 'base_dir': BASE_DIR, 'files': {}, 'counts': {}, 'warn
ings': []}

``
