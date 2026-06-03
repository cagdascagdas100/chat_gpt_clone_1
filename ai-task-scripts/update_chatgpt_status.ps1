param(
  [Parameter(Mandatory=$true)][string]$PageKey,
  [Parameter(Mandatory=$true)][string]$ActiveTask,
  [Parameter(Mandatory=$true)][string]$Status,
  [int]$TechnicalProgress=0,
  [int]$OverallProgress=0,
  [string]$WaitMinutes='10-15',
  [string]$NextCommand='devam et',
  [string]$RunnerStatus='',
  [string]$RunnerMessage='',
  [string]$Blocker='',
  [string]$LastMessageText='devam et',
  [string]$LastMessageAt='',
  [bool]$DbWrite=$false,
  [bool]$ProductionDeploy=$false
)
$ErrorActionPreference='Stop'
$Root=Split-Path -Parent $PSScriptRoot
$Dir=Join-Path $Root 'docs/chatgpt_status'
New-Item -ItemType Directory -Force -Path $Dir|Out-Null
$JsonPath=Join-Path $Dir 'multi_page_status.json'
$MdPath=Join-Path $Dir 'status.md'
$Now=Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
if([string]::IsNullOrWhiteSpace($LastMessageAt)){$LastMessageAt=$Now}
if(Test-Path $JsonPath){$data=Get-Content -Raw -Encoding UTF8 $JsonPath|ConvertFrom-Json}else{$data=[pscustomobject]@{_meta=[pscustomobject]@{};pages=[pscustomobject]@{}}}
$data._meta|Add-Member -Force -NotePropertyName schema_version -NotePropertyValue 2
$data._meta|Add-Member -Force -NotePropertyName purpose -NotePropertyValue 'Shared live status file for multiple ChatGPT pages controlling AAYS/TerraYield tasks.'
$data._meta|Add-Member -Force -NotePropertyName status_dashboard -NotePropertyValue 'docs/chatgpt_status/index.html'
$data._meta|Add-Member -Force -NotePropertyName standalone_dashboard -NotePropertyValue 'docs/chatgpt_status/status_dashboard_standalone.html'
$data._meta|Add-Member -Force -NotePropertyName markdown_summary -NotePropertyValue 'docs/chatgpt_status/status.md'
$data._meta|Add-Member -Force -NotePropertyName update_helper -NotePropertyValue 'ai-task-scripts/update_chatgpt_status.ps1'
$data._meta|Add-Member -Force -NotePropertyName updated_at -NotePropertyValue $Now
if(-not $data.pages){$data|Add-Member -Force -NotePropertyName pages -NotePropertyValue ([pscustomobject]@{})}
$page=[pscustomobject]@{
 active_task=$ActiveTask
 status=$Status
 technical_progress=$TechnicalProgress
 overall_progress=$OverallProgress
 wait_minutes=$WaitMinutes
 next_command=$NextCommand
 runner_status=$RunnerStatus
 runner_message=$RunnerMessage
 blocker=$Blocker
 last_message_text=$LastMessageText
 last_message_at=$LastMessageAt
 db_write=$DbWrite
 production_deploy=$ProductionDeploy
 updated_at=$Now
}
$data.pages|Add-Member -Force -NotePropertyName $PageKey -NotePropertyValue $page
$data|ConvertTo-Json -Depth 10|Set-Content -Encoding UTF8 $JsonPath
$lines=@('# ChatGPT Multi Page Status','',('Updated: '+$Now),'')
foreach($p in $data.pages.PSObject.Properties){$v=$p.Value;$lines+=('## '+$p.Name);$lines+=('Active task: '+$v.active_task);$lines+=('Status: '+$v.status);$lines+=('Overall progress: '+$v.overall_progress);$lines+=('Wait minutes: '+$v.wait_minutes);$lines+=('Last message at: '+$v.last_message_at);$lines+=('Last message: '+$v.last_message_text);$lines+=('Blocker: '+$v.blocker);$lines+=''}
$lines|Set-Content -Encoding UTF8 $MdPath
Write-Output "updated $PageKey at $Now"
