# AAYS / TerraYield Portable Task Bridge Config
# Farkli gorevlerde sadece bu dosyadaki yollar ve proje isimleri duzenlenir.

$env:AAYS_BRIDGE_ROOT = "C:\Users\cagda\Documents\chat_gpt_clone_1"
$env:AAYS_PROJECT_ROOT = "C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence"

$env:AAYS_PROJECT_CODE = "terrayield"
$env:AAYS_DISPLAY_PROJECT = "TerraYield"
$env:AAYS_CHATGPT_PAGE_PROJECT = "aays1"

$env:AAYS_RUNNER_POLL_SECONDS = "20"
$env:AAYS_TASK_TIMEOUT_SECONDS = "3000"

# Runner yalnizca bu klasordeki .ps1 task scriptlerini calistirir.
$env:AAYS_ALLOWED_SCRIPT_DIR = "ai-task-scripts"
