# AAYS ChatGPT Runner V4 Result

## Task
Probe runner and run Plan L minipack

## Task ID
terrayield-114-runner-probe-plan-l-minipack

## Progress
84%

## Action


## Time
05/07/2026 13:20:48

## Working Directory
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence

## Timeout Seconds
1800

## Exit Code
0

## Output
``text
# TerraYield 114 runner probe and Plan L minipack
RUN=20260507_131920
BRIDGE_EXISTS=True
PLAN_BASE_EXISTS=True
current-task.json=exists bytes=688
ai-task-scripts=exists bytes=1
ai-results=exists bytes=1
london_parcels_geometry.geojson=exists bytes=66833726
market_3110.csv=exists bytes=12443391
voa_london.csv=exists bytes=176645275
build_london_6color.py=exists bytes=28510
london_6color.csv=exists bytes=5604070
london_6color.geojson=exists bytes=74633267
london_6color_summary.csv=exists bytes=276
london_6color_confidence_summary.csv=exists bytes=57
PYTHON=C:\Python312\python.exe
2026-05-07 13:19:29,213 | INFO | build_london_6color ba■lad²
2026-05-07 13:19:32,687 | INFO | GeoJSON okundu: D:\6 color parcells\plan_l_run01\input\london_parcels_geometry.geojson | feature=34864
2026-05-07 13:19:33,205 | INFO | CSV okundu: D:\6 color parcells\plan_l_run01\input\market_3110.csv | sat²r=3110 | s³tun=37
2026-05-07 13:19:45,335 | INFO | CSV okundu: D:\6 color parcells\plan_l_run01\input\voa_london.csv | sat²r=334617 | s³tun=51
2026-05-07 13:19:45,711 | INFO | Market index haz²r: anahtar=2554
2026-05-07 13:19:45,726 | WARNING | voa_london.csv iin parsel/inspire e■le■tirme kolonu bulunamad²; VOA sinyali atlan²yor.
2026-05-07 13:19:48,128 | INFO | ¦■lenen feature: 10000 / 34864
2026-05-07 13:19:50,744 | INFO | ¦■lenen feature: 20000 / 34864
2026-05-07 13:19:53,291 | INFO | ¦■lenen feature: 30000 / 34864
2026-05-07 13:20:33,121 | INFO | GeoJSON yaz²ld²: D:\6 color parcells\plan_l_run01\output\london_6color.geojson
2026-05-07 13:20:37,841 | INFO | Parsel CSV yaz²ld²: D:\6 color parcells\plan_l_run01\output\london_6color.csv | sat²r=34864
2026-05-07 13:20:37,908 | INFO | S²n²f ÷zet CSV yaz²ld²: D:\6 color parcells\plan_l_run01\output\london_6color_summary.csv
2026-05-07 13:20:37,931 | INFO | G³ven ÷zeti CSV yaz²ld²: D:\6 color parcells\plan_l_run01\output\london_6color_confidence_summary.csv
2026-05-07 13:20:37,937 | INFO | S²n²f da­²l²m²: {'Apartman': 6425, 'M³stakil': 26300, 'Ofis': 634, 'Perakende': 747, 'Sanayi': 758}
2026-05-07 13:20:37,937 | INFO | build_london_6color tamamland²
PLAN_L_RUN_EXIT=0
CLASSIFIED_ROWS=34864
CLASS_SUMMARY_BEGIN
class6,color,parcel_count,percent,area_m2_sum,avg_confidence
Sanayi,#F4C542,758,2.17,60822582.0,3.0
Ofis,#1F4E9E,634,1.82,3064594.11,3.0
Perakende,#7FD3FF,747,2.14,2272177.0,3.0
Apartman,#2E7D32,6425,18.43,60071255.55,3.0
Müstakil,#A8E6A1,26300,75.44,4955306.59,3.0
CLASS_SUMMARY_END
CONFIDENCE_SUMMARY_BEGIN
confidence_score,parcel_count,percent
3,34864,100.0
CONFIDENCE_SUMMARY_END

``

## Error
``text
Add-Content : Akış okunabilir değildi.
At C:\Users\cagda\Documents\chat_gpt_clone_1\ai-task-scripts\terrayield_114_runner_probe_plan_l_minipack.ps1:12 char:33
+ ... Write-Output $x; Add-Content -Encoding UTF8 -Path $Summary -Value $x}
+                      ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidArgument: (C:\Users\cagda\...pack-summary.md:String) [Add-Content], ArgumentExcep 
   tion
    + FullyQualifiedErrorId : GetContentWriterArgumentError,Microsoft.PowerShell.Commands.AddContentCommand
 
Add-Content : Akış okunabilir değildi.
At C:\Users\cagda\Documents\chat_gpt_clone_1\ai-task-scripts\terrayield_114_runner_probe_plan_l_minipack.ps1:12 char:33
+ ... Write-Output $x; Add-Content -Encoding UTF8 -Path $Summary -Value $x}
+                      ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidArgument: (C:\Users\cagda\...pack-summary.md:String) [Add-Content], ArgumentExcep 
   tion
    + FullyQualifiedErrorId : GetContentWriterArgumentError,Microsoft.PowerShell.Commands.AddContentCommand
 
Add-Content : Akış okunabilir değildi.
At C:\Users\cagda\Documents\chat_gpt_clone_1\ai-task-scripts\terrayield_114_runner_probe_plan_l_minipack.ps1:12 char:33
+ ... Write-Output $x; Add-Content -Encoding UTF8 -Path $Summary -Value $x}
+                      ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidArgument: (C:\Users\cagda\...pack-summary.md:String) [Add-Content], ArgumentExcep 
   tion
    + FullyQualifiedErrorId : GetContentWriterArgumentError,Microsoft.PowerShell.Commands.AddContentCommand
 
Add-Content : Akış okunabilir değildi.
At C:\Users\cagda\Documents\chat_gpt_clone_1\ai-task-scripts\terrayield_114_runner_probe_plan_l_minipack.ps1:12 char:33
+ ... Write-Output $x; Add-Content -Encoding UTF8 -Path $Summary -Value $x}
+                      ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidArgument: (C:\Users\cagda\...pack-summary.md:String) [Add-Content], ArgumentExcep 
   tion
    + FullyQualifiedErrorId : GetContentWriterArgumentError,Microsoft.PowerShell.Commands.AddContentCommand
 
Add-Content : Akış okunabilir değildi.
At C:\Users\cagda\Documents\chat_gpt_clone_1\ai-task-scripts\terrayield_114_runner_probe_plan_l_minipack.ps1:12 char:33
+ ... Write-Output $x; Add-Content -Encoding UTF8 -Path $Summary -Value $x}
+                      ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidArgument: (C:\Users\cagda\...pack-summary.md:String) [Add-Content], ArgumentExcep 
   tion
    + FullyQualifiedErrorId : GetContentWriterArgumentError,Microsoft.PowerShell.Commands.AddContentCommand
 
Add-Content : Akış okunabilir değildi.
At C:\Users\cagda\Documents\chat_gpt_clone_1\ai-task-scripts\terrayield_114_runner_probe_plan_l_minipack.ps1:12 char:33
+ ... Write-Output $x; Add-Content -Encoding UTF8 -Path $Summary -Value $x}
+                      ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidArgument: (C:\Users\cagda\...pack-summary.md:String) [Add-Content], ArgumentExcep 
   tion
    + FullyQualifiedErrorId : GetContentWriterArgumentError,Microsoft.PowerShell.Commands.AddContentCommand
 
Add-Content : Akış okunabilir değildi.
At C:\Users\cagda\Documents\chat_gpt_clone_1\ai-task-scripts\terrayield_114_runner_probe_plan_l_minipack.ps1:12 char:33
+ ... Write-Output $x; Add-Content -Encoding UTF8 -Path $Summary -Value $x}
+                      ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidArgument: (C:\Users\cagda\...pack-summary.md:String) [Add-Content], ArgumentExcep 
   tion
    + FullyQualifiedErrorId : GetContentWriterArgumentError,Microsoft.PowerShell.Commands.AddContentCommand
 
Add-Content : Akış okunabilir değildi.
At C:\Users\cagda\Documents\chat_gpt_clone_1\ai-task-scripts\terrayield_114_runner_probe_plan_l_minipack.ps1:12 char:33
+ ... Write-Output $x; Add-Content -Encoding UTF8 -Path $Summary -Value $x}
+                      ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidArgument: (C:\Users\cagda\...pack-summary.md:String) [Add-Content], ArgumentExcep 
   tion
    + FullyQualifiedErrorId : GetContentWriterArgumentError,Microsoft.PowerShell.Commands.AddContentCommand
 
Add-Content : Akış okunabilir değildi.
At C:\Users\cagda\Documents\chat_gpt_clone_1\ai-task-scripts\terrayield_114_runner_probe_plan_l_minipack.ps1:12 char:33
+ ... Write-Output $x; Add-Content -Encoding UTF8 -Path $Summary -Value $x}
+                      ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidArgument: (C:\Users\cagda\...pack-summary.md:String) [Add-Content], ArgumentExcep 
   tion
    + FullyQualifiedErrorId : GetContentWriterArgumentError,Microsoft.PowerShell.Commands.AddContentCommand
 
Add-Content : Akış okunabilir değildi.
At C:\Users\cagda\Documents\chat_gpt_clone_1\ai-task-scripts\terrayield_114_runner_probe_plan_l_minipack.ps1:12 char:33
+ ... Write-Output $x; Add-Content -Encoding UTF8 -Path $Summary -Value $x}
+                      ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidArgument: (C:\Users\cagda\...pack-summary.md:String) [Add-Content], ArgumentExcep 
   tion
    + FullyQualifiedErrorId : GetContentWriterArgumentError,Microsoft.PowerShell.Commands.AddContentCommand
 
Add-Content : Akış okunabilir değildi.
At C:\Users\cagda\Documents\chat_gpt_clone_1\ai-task-scripts\terrayield_114_runner_probe_plan_l_minipack.ps1:12 char:33
+ ... Write-Output $x; Add-Content -Encoding UTF8 -Path $Summary -Value $x}
+                      ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidArgument: (C:\Users\cagda\...pack-summary.md:String) [Add-Content], ArgumentExcep 
   tion
    + FullyQualifiedErrorId : GetContentWriterArgumentError,Microsoft.PowerShell.Commands.AddContentCommand
 
Add-Content : Akış okunabilir değildi.
At C:\Users\cagda\Documents\chat_gpt_clone_1\ai-task-scripts\terrayield_114_runner_probe_plan_l_minipack.ps1:12 char:33
+ ... Write-Output $x; Add-Content -Encoding UTF8 -Path $Summary -Value $x}
+                      ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidArgument: (C:\Users\cagda\...pack-summary.md:String) [Add-Content], ArgumentExcep 
   tion
    + FullyQualifiedErrorId : GetContentWriterArgumentError,Microsoft.PowerShell.Commands.AddContentCommand
 
Add-Content : Akış okunabilir değildi.
At C:\Users\cagda\Documents\chat_gpt_clone_1\ai-task-scripts\terrayield_114_runner_probe_plan_l_minipack.ps1:12 char:33
+ ... Write-Output $x; Add-Content -Encoding UTF8 -Path $Summary -Value $x}
+                      ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidArgument: (C:\Users\cagda\...pack-summary.md:String) [Add-Content], ArgumentExcep 
   tion
    + FullyQualifiedErrorId : GetContentWriterArgumentError,Microsoft.PowerShell.Commands.AddContentCommand
 

``
