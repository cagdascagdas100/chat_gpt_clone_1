$ErrorActionPreference = 'Continue'

$TaskId = 'terrayield-133-install-reliability-streetview-package'
$ProjectRoot = 'C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$ExpectedWebRootName = 'england_map_web'
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$TempDir = Join-Path $env:TEMP ($TaskId + '-' + $Stamp)
$ZipPath = Join-Path $TempDir 'TERRAYIELD_RELIABILITY_STREETVIEW_APPLIED_050_20260507.zip'
$BackupRoot = Join-Path $ProjectRoot ('.aays_chatgpt_backups\' + $TaskId + '-' + $Stamp)
$ExpectedSha256 = 'e29df1bbec871888362e942befdaf47057ac669706f1dc755469522f97ffd417'

function Write-Step([string]$Text) {
  Write-Output ('[' + (Get-Date -Format 's') + '] ' + $Text)
}

function Backup-ExistingFile([string]$Path, [string]$RelativePath) {
  if (Test-Path -LiteralPath $Path) {
    $backupPath = Join-Path $BackupRoot $RelativePath
    $backupDir = Split-Path -Parent $backupPath
    New-Item -ItemType Directory -Force -Path $backupDir | Out-Null
    Copy-Item -LiteralPath $Path -Destination $backupPath -Force
    Write-Step ('BACKUP=' + $RelativePath)
  }
}

function Invoke-Safely([string]$Label, [scriptblock]$Block) {
  Write-Step ('BEGIN_' + $Label)
  try {
    & $Block
    Write-Step ('END_' + $Label + '=OK')
  } catch {
    Write-Step ('END_' + $Label + '=ERROR ' + $_.Exception.Message)
  }
}

Write-Output 'PROJECT=terrayield'
Write-Output 'DISPLAY_PROJECT=TerraYield'
Write-Output 'CHATGPT_PAGE_PROJECT=aays1'
Write-Output ('TASK=' + $TaskId)
Write-Output 'MODE=install_reliability_streetview_overlay_and_smoke_validate'
Write-Output ('PROJECT_ROOT=' + $ProjectRoot)
Write-Output ('EXPECTED_ZIP_SHA256=' + $ExpectedSha256)

if (-not (Test-Path -LiteralPath $ProjectRoot)) {
  Write-Output ('PROJECT_ROOT_EXISTS=FAIL path=' + $ProjectRoot)
  exit 2
}

$TargetWebRoot = Join-Path $ProjectRoot $ExpectedWebRootName
if (-not (Test-Path -LiteralPath $TargetWebRoot)) {
  Write-Output ('ENGLAND_MAP_WEB_EXISTS=FAIL path=' + $TargetWebRoot)
  exit 3
}

New-Item -ItemType Directory -Force -Path $TempDir, $BackupRoot | Out-Null

$ZipBase64 = @'
UEsDBAoAAAAAAOWIpFwAAAAAAAAAAAAAAAAQABwAZW5nbGFuZF9tYXBfd2ViL1VUCQADkckUaJzQ
FGh1eAsAAQSBAAAABIEAAABQSwMECgAAAAAA5YikXAAAAAAAAAAAAAAAAAAZABwAZW5nbGFuZF9t
YXBfd2ViL2FheXMvVVQJAAPCJBRonNAUaHV4CwABBIwAAAAEgAAAAFBLAwQKAAAAAADliKRcAAAA
AAAAAAAAAAAAAAA0ABwAZW5nbGFuZF9tYXBfd2ViL2FheXMvcmVsaWFiaWxpdHlfc3RyZWV0dmll
dy9VVAkAA8IkFGic0BRodXgLAAEEjAAAAASAAAAAUEsDBAoAAAAAAOWIpFwAAAAAAAAAAAAAAAA0
ABwAZW5nbGFuZF9tYXBfd2ViL2FheXMvcmVsaWFiaWxpdHlfc3RyZWV0dmlldy9ldmlkZW5jZS9V
VAkAA8IkFGic0BRodXgLAAEEjAAAAASAAAAAUEsDBAoAAAAAAOWIpFwAAAAAAAAAAAAAAAA4ABwA
ZW5nbGFuZF9tYXBfd2ViL2FheXMvcmVsaWFiaWxpdHlfc3RyZWV0dmlldy9ldmlkZW5jZS9yZWNv
cmRzL1VUCQADwiQUaJzQFGh1eAsAAQSMAAAABIAAAABQSwMECgAAAAAA5YikXAAAAAAAAAAAAAAA
AAAAADwAHABlbmdsYW5kX21hcF93ZWIvYWF5cy9yZWxpYWJpbGl0eV9zdHJlZXR2aWV3L2V2aWRl
bmNlL3JlY29yZHMvLmdpdGtlZXBVVAkAA8IkFGic0BRodXgLAAEEjAAAAASAAAAAUEsDBAoAAAAA
AOWIpFwAAAAAAAAAAAAAAAA6ABwAZW5nbGFuZF9tYXBfd2ViL2FheXMvcmVsaWFiaWxpdHlfc3Ry
ZWV0dmlldy9ldmlkZW5jZS90ZW1wbGF0ZXMvVVQJAAPCJBRonNAUaHV4CwABBIwAAAAEgAAAAFBL
AwQKAAAAAADliKRc1/zMvOsAAADrAAAAWwAcAGVuZ2xhbmRfbWFwX3dlYi9hYXlzL3JlbGlhYmls
aXR5X3N0cmVldHZpZXcvZXZpZGVuY2UvdGVtcGxhdGVzL2Fpcl9xdWFsaXR5X3NvdXJjZV9ldmlk
ZW5jZS50ZW1wbGF0ZS5qc29uVVQJAAPDJBRonNAUaHV4CwABBIwAAAAEgAAAAHsKICAidGVtcGxh
dGVfdHlwZSI6ICJhaXJfcXVhbGl0eV9zb3VyY2VfZXZpZGVuY2UiLAogICJzb3VyY2VfaWQiOiAi
IiwKICAic291cmNlX25hbWUiOiAiIiwKICAic291cmNlX3VybCI6ICIiLAogICJhY2Nlc3NlZF9h
dCI6ICIiLAogICJsaWNlbnNlIjogIiIsCiAgInJlZnJlc2hfY2FkZW5jZSI6ICIiLAogICJmaWVs
ZHNfY2hlY2tlZCI6IFtdLAogICJub3RlcyI6ICIiCn0KUEsDBAoAAAAAAOWIpFxUrGEfhQAAAIUA
AABWABwAZW5nbGFuZF9tYXBfd2ViL2FheXMvcmVsaWFiaWxpdHlfc3RyZWV0dmlldy9ldmlkZW5j
ZS90ZW1wbGF0ZXMvZGF0YV9saW5lYWdlX3JlY29yZC50ZW1wbGF0ZS5tZFVUCQADwyQUaJzQFGh1
eAsAAQSMAAAABIAAAAAtIERhdGFzZXQ6IAotIFNvdXJjZTogCi0gTGljZW5zZTogCi0gRG93bmxv
YWQgLyBBY2Nlc3M6IAotIFRyYW5zZm9ybWF0aW9uOiAKLSBQYXJjZWwgTWF0Y2ggS2V5OiAKLSBS
ZWxpYWJpbGl0eSBDaGVja3M6IAotIEtub3duIENvbmZsaWN0czogCi0gTmV4dCBSZWZyZXNoOiAK
UEsDBAoAAAAAAOWIpFzvO2RkBAEAAAQBAABXABwAZW5nbGFuZF9tYXBfd2ViL2FheXMvcmVsaWFi
aWxpdHlfc3RyZWV0dmlldy9ldmlkZW5jZS90ZW1wbGF0ZXMvcmVsaWFiaWxpdHlfc2NvcmVjYXJk
LnRlbXBsYXRlLmpzb25VVAkAA8MkFGic0BRodXgLAAEEjAAAAASAAAAAewogICJ0ZW1wbGF0ZV90
eXBlIjogInJlbGlhYmlsaXR5X3Njb3JlY2FyZCIsCiAgInBhcmNlbF9pZCI6ICIiLAogICJzY29y
ZXMiOiB7CiAgICAic291cmNlX3JlbGlhYmlsaXR5IjogbnVsbCwKICAgICJwYXJjZWxfbWF0Y2gi
OiBudWxsLAogICAgIm9wZXJhdGlvbmFsX2hlYWx0aCI6IG51bGwsCiAgICAib3ZlcmFsbF9jb25m
aWRlbmNlIjogbnVsbAogIH0sCiAgImRhdGFzZXRzIjogW10sCiAgIndhcm5pbmdzIjogW10sCiAg
ImV2aWRlbmNlX2xpbmtzIjogW10KfQpQSwMECgAAAAAA5YikXJeLKrwBAgAAAQIAAABUABwAZW5n
bGFuZF9tYXBfd2ViL2FheXMvcmVsaWFiaWxpdHlfc3RyZWV0dmlldy9ldmlkZW5jZS90ZW1wbGF0
ZXMvc291cmNlX2NvbmZsaWN0X2xvZy50ZW1wbGF0ZS5jc3ZVVAkAA8MkFGic0BRodXgLAAEEjAAA
AASAAAAAc291cmNlX2lkLGNvbmZsaWN0X3R5cGUsbG9jYXRpb24sZGV0ZWN0ZWRfYXQsZGV0YWls
LHJlc29sdXRpb25fc3RhdHVzCgpQSwMECgAAAAAA5YikXM73khgBAgAAAQIAAAA7ABwAZW5nbGFu
ZF9tYXBfd2ViL2FheXMvcmVsaWFiaWxpdHlfc3RyZWV0dmlldy9ldmlkZW5jZS90ZW1wbGF0ZXMv
c3RyZWV0dmlld19jb29yZGluYXRlX2V2aWRlbmNlLnRlbXBsYXRlLmpzb25VVAkAA8MkFGic0BRo
dXgLAAEEjAAAAASAAAAAewogICJ0ZW1wbGF0ZV90eXBlIjogInN0cmVldHZpZXdfY29vcmRpbmF0
ZV9ldmlkZW5jZSIsCiAgInBhcmNlbF9pZCI6ICIiLAogICJsYXQiOiBudWxsLAogICJsbmciOiBu
dWxsLAogICJnb29nbGVfc3RyZWV0dmlld191cmwiOiAiIiwKICAidmlld3BvaW50X2NvbmZpcm1l
ZCI6IGZhbHNlLAogICJoYW5kb2ZmX21ldGhvZCI6ICJ1cmxfb25seSIsCiAgIm5vdGVzIjogIiIK
fQpQSwMECgAAAAAA5YikXLX46PoWBAAAFgQAADwAHABlbmdsYW5kX21hcF93ZWIvYWF5cy9yZWxp
YWJpbGl0eV9zdHJlZXR2aWV3L3JlbGlhYmlsaXR5X3N0cmVldHZpZXdfbG9hZGVyLmpzVVQJAAPD
JBRonNAUaHV4CwABBIwAAAAEgAAAA...TRUNCATED_BY_TOOL...