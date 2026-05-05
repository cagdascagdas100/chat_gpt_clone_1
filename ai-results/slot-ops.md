# ops TaskId: terrayield-064-five-slot-parallel-dispatcher Status: starting RealWork: Yes JobCPU: measuring Evidence: slot result file created Started: 2026-05-06T00:47:23 
```text
ops real work: git and process evidence
git : warning: could not open directory 'Application Data/': Permission denied
At line:23 char:7
+       git status --short 2>&1 | Out-String | ForEach-Object {L $_}
+       ~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : NotSpecified: (warning: could ...rmission denied:String) [], RemoteException
    + FullyQualifiedErrorId : NativeCommandError
 
warning: could not open directory 'Belgelerim/': Permission denied
warning: could not open directory 'Cookies/': Permission denied
warning: could not open directory 'Local Settings/': Permission denied
warning: could not open directory 'NetHood/': Permission denied
warning: could not open directory 'PrintHood/': Permission denied
warning: could not open directory 'Recent/': Permission denied
warning: could not open directory 'SendTo/': Permission denied
warning: could not open directory 'Start Menu/': Permission denied
warning: could not open directory 'Templates/': Permission denied
?? ../../../../.android/
?? ../../../../.azure/
?? ../../../../.bash_history
?? ../../../../.cache/
?? ../../../../.cagent/
?? ../../../../.chocolatey/
?? ../../../../.codex/
?? ../../../../.codex_backup/
?? ../../../../.config/
?? ../../../../.copilot/
?? ../../../../.dbus-keyrings/
?? ../../../../.docker/
?? ../../../../.dotnet/
?? ../../../../.gitconfig
?? ../../../../.gitignore
?? ../../../../.gk/
?? ../../../../.gradle/
?? ../../../../.ipynb_checkpoints/
?? ../../../../.ipython/
?? ../../../../.jupyter/
?? ../../../../.lesshst
?? ../../../../.matplotlib/
?? ../../../../.moe/
?? ../../../../.nuget/
?? ../../../../.openjfx/
?? ../../../../.platformio/
?? ../../../../.prefs/
?? ../../../../.sambox.cache
?? ../../../../.streamlit/
?? ../../../../.subversion/
?? ../../../../.swt/
?? ../../../../.templateengine/
?? ../../../../.venv/
?? ../../../../.vscode-shared/
?? ../../../../.vscode/
?? ../../../../.wdm/
?? ../../../../AppData/
?? ../../../../Contacts/
?? ../../../
?? ../../../../Downloads/
?? ../../../../Edalmo_OHS_1.2.svg
?? ../../../../Edalmo_OHS_Program_Team/
?? ../../../../Favorites/
?? ../../../../Games/
?? ../../../../Heatmap_BEST_Across_Models_noBaseline.xlsx
?? ../../../../Links/
?? ../../../../Music/
?? ../../../../NTUSER.DAT
?? ../../../../NTUSER.DAT{2ad838bb-efea-11ee-a54d-000d3a94eaa1}.TxR.0.regtrans-ms
?? ../../../../NTUSER.DAT{2ad838bb-efea-11ee-a54d-000d3a94eaa1}.TxR.1.regtrans-ms
?? ../../../../NTUSER.DAT{2ad838bb-efea-11ee-a54d-000d3a94eaa1}.TxR.2.regtrans-ms
?? ../../../../NTUSER.DAT{2ad838bb-efea-11ee-a54d-000d3a94eaa1}.TxR.blf
?? ../../../../NTUSER.DAT{2ad838bc-efea-11ee-a54d-000d3a94eaa1}.TM.blf
?? ../../../../NTUSER.DAT{2ad838bc-efea-11ee-a54d-000d3a94eaa1}.TMContainer00000000000000000001.regtrans-ms
?? ../../../../NTUSER.DAT{2ad838bc-efea-11ee-a54d-000d3a94eaa1}.TMContainer00000000000000000002.regtrans-ms
?? "../../../../OneDrive - hacettepe.edu.tr/"
?? ../../../../OneDrive/
?? ../../../../OpenVPN/
?? "../../../../Saved Games/"
?? ../../../../Searches/
?? ../../../../Tracing/
?? ../../../../UrbanVPN/
?? ../../../../VeePN/
?? ../../../../Videos/
?? "../../../../Yeni belge 1.2025_08_09_22_51_39.0.svg"
?? "../../../../Yeni belge 1.2025_09_19_22_04_41.0.svg"
?? "../../../../Yeni belge 2.2025_08_09_21_03_56.1.svg"
?? "../../../../Yeni belge 2.2025_08_09_22_51_39.1.svg"
?? ../../../../admin_maliyet.pdf
?? ../../../../alpha_sensitivity.png
?? ../../../../android-sdk/
?? ../../../../autogpt.py
?? ../../../../best_across_models_noBaseline.csv
?? "../../../../bite\305\237lem.png"
?? "../../../../bite\305\237lem.rar"
?? "../../../../bite\305\237lem.svg"
?? ../../../../chat_gpt_clone_1/
?? ../../../../domination-gradle-cache/
?? ../../../../errors.log
?? ../../../../evaluation_summary.txt
?? ../../../../figures/
?? ../../../../heat_map.png
?? ../../../../heatmap_BEST_across_models_noBaseline.png
?? ../../../../high_score.txt
?? ../../../../jdk8/
?? ../../../../konu_basliklari.docx
?? ../../../../model_outputs.csv
?? ../../../../model_selection_audit.csv
?? ../../../../model_selection_summary.txt
?? ../../../../ntuser.dat.LOG1
?? ../../../../ntuser.dat.LOG2
?? ../../../../ntuser.ini
?? ../../../../output/
?? ../../../../package-lock.json
?? ../../../../python
?? ../../../../quiz_source/
?? ../../../../rect2.png
?? ../../../../refresh_window.ps1
?? ../../../../result.txt
?? ../../../../risk_degerlendirme_tablosu.xlsx
?? ../../../../risk_diagrams.md
?? ../../../../risk_model_compare.pdf
?? ../../../../risk_model_compare.png
?? ../../../../risk_model_compare_percentile_anchors.csv
?? ../../../../risk_model_compare_percentile_anchors.txt
?? ../../../../risk_model_compare_risk_order.csv
?? ../../../../sachgruppen_worte_main.xlsx
?? ../../../../selections.json
?? ../../../../sim_audit_all.csv
?? ../../../../sim_audit_all.json
?? ../../../../split_csv/
?? ../../../../terrayield.svg
?? ../../../../worker_test_results.txt
?? ../../../../worker_test_results_2.txt
?? ../../../../worker_test_results_3.txt

git : fatal: Needed a single revision
At line:24 char:7
+       git rev-parse --short HEAD 2>&1 | Out-String | ForEach-Object { ...
+       ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : NotSpecified: (fatal: Needed a single revision:String) [], RemoteException
    + FullyQualifiedErrorId : NativeCommandError
 


ProcessName    Id      CPU StartTime         
-----------    --      --- ---------         
powershell   4152   0,5625 6.05.2026 00:47:23
powershell   4796 0,265625 6.05.2026 00:47:22
powershell   6540     0,75 6.05.2026 00:47:24
powershell   8284 2,828125 6.05.2026 00:31:25
powershell   8328 0,890625 6.05.2026 00:47:24
powershell  10280   0,6875 6.05.2026 00:47:24
powershell  10576 0,578125 6.05.2026 00:47:24
powershell  13148 1,484375 6.05.2026 00:41:40
powershell  16076 4,078125 5.05.2026 22:02:01
powershell  17948 3,578125 5.05.2026 23:50:06
powershell  18992  3,46875 6.05.2026 00:34:18
powershell  20808 0,515625 6.05.2026 00:47:23
python       8952 0,265625 6.05.2026 00:47:24
python      13428   0,0625 6.05.2026 00:47:24



RESULT=slot_completed
```
Finished: 2026-05-06T00:47:25
