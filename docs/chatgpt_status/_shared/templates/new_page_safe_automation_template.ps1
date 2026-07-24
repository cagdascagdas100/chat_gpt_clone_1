param(
  [Parameter(Mandatory = $true)][string]$PageKey,
  [Parameter(Mandatory = $true)][string]$TaskId
)

& "$PSScriptRoot\..\automation\SAFE_STATUS_ONLY_PAGE_TASK_20260706.ps1" -PageKey $PageKey -TaskId $TaskId -Blocker "new_page_real_automation_missing"
