$h=Join-Path $PSScriptRoot 'update_chatgpt_status.ps1'
& $h -PageKey '10.1 Emlakci' -ActiveTask 'terrayield-cost-engine-057-long-self-healing-20260521' -Status 'waiting' -OverallProgress 69 -WaitMinutes '35-45' -NextCommand 'devam et' -RunnerStatus 'finished' -RunnerMessage '057 not picked up yet' -Blocker 'Estate pending; 057 result not confirmed.' -LastMessageText 'devam et' -DbWrite:$false -ProductionDeploy:$false
exit 0
