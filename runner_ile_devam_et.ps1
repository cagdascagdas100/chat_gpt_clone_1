param([int]$MaxTasks = 1)
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$cmd = Join-Path $here 'devam.ps1'
& $cmd -MaxTasks $MaxTasks
exit $LASTEXITCODE
