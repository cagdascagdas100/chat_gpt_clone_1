# ChatGPT Runner Result

## Task
TerraYield short diagnostic after empty report

## Task ID
terrayield-diagnostic-short-001

## Progress
62%

## Time
05/02/2026 23:03:55

## Working Directory
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence

## Exit Code
0

## Command
Write-Output 'TASK: TerraYield kisa tani'; Write-Output 'PROGRESS: 62%'; Write-Output 'ESTIMATED_WAIT: 2-3 dakika'; Write-Output 'START_TIME:'; Get-Date; Write-Output 'PROJECT:'; Get-Location; Write-Output 'KEY_FILES:'; Write-Output ('route=' + (Test-Path 'app\api\routes\aays_sales_layers.py')); Write-Output ('main=' + (Test-Path 'app\main.py')); Write-Output ('compose=' + (Test-Path 'docker-compose.yml')); Write-Output 'DOCKER_PS:'; docker compose ps 2>&1; Write-Output 'HEALTH:'; try { Invoke-WebRequest -Uri 'http://localhost:8010/health' -UseBasicParsing -TimeoutSec 15 | Select-Object StatusCode } catch { Write-Output $_.Exception.Message }; Write-Output 'END_TIME:'; Get-Date; Write-Output 'SHORT_DIAGNOSTIC_DONE'

## Output
TASK: TerraYield kisa tani
PROGRESS: 62%
ESTIMATED_WAIT: 2-3 dakika
START_TIME:

2 Mayıs 2026 Cumartesi 23:03:54
PROJECT:

Drive        : C
Provider     : Microsoft.PowerShell.Core\FileSystem
ProviderPath : C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence
Path         : C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence

KEY_FILES:
route=True
main=True
compose=True
DOCKER_PS:
NAME                      IMAGE                    COMMAND                  SERVICE   CREATED       STATUS        PORTS
terrayield_land_api       python:3.12-slim         "bash -lc 'pip instaÔÇĞ"   api       8 hours ago   Up 8 hours    0.0.0.0:8010->8010/tcp, [::]:8010->8010/tcp
terrayield_land_postgis   postgis/postgis:16-3.4   "docker-entrypoint.sÔÇĞ"   db        2 days ago    Up 33 hours   0.0.0.0:55460->5432/tcp, [::]:55460->5432/tcp
HEALTH:

StatusCode : 200

END_TIME:
2 Mayıs 2026 Cumartesi 23:03:55
SHORT_DIAGNOSTIC_DONE



