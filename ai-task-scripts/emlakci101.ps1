$h=Join-Path $PSScriptRoot 'update_chatgpt_status.ps1'
& $h -PageKey '10.1 Emlakci' -ActiveTask 'current-watch' -Status 'waiting' -OverallProgress 69 -WaitMinutes '35-45' -NextCommand 'devam et' -RunnerStatus 'polling' -RunnerMessage 'watching current task' -Blocker '' -LastMessageText 'devam et' -DbWrite:$false -ProductionDeploy:$false
exit 0
