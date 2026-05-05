Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$ErrorActionPreference = 'SilentlyContinue'
$BridgeRoot = 'C:\Users\cagda\Documents\chat_gpt_clone_1'
$RefreshSeconds = 30
$script:LastCpu = @{}
$script:LastCpuTime = Get-Date

$Jobs = @(
    [pscustomobject]@{ Job='Backend'; TaskId='terrayield-060A-backend'; Descriptor='ai-tasks\parallel\terrayield-060A-backend.json'; Proc='python,docker' },
    [pscustomobject]@{ Job='Frontend'; TaskId='terrayield-060B-frontend'; Descriptor='ai-tasks\parallel\terrayield-060B-frontend.json'; Proc='node' },
    [pscustomobject]@{ Job='Ops'; TaskId='terrayield-060C-ops'; Descriptor='ai-tasks\parallel\terrayield-060C-ops.json'; Proc='powershell,pwsh' },
    [pscustomobject]@{ Job='Mega Batch'; TaskId='terrayield-062-mega-parallel-pickup-project-root'; Descriptor='ai-tasks\current-task.json'; Proc='powershell,pwsh' }
)

function ReadText($Path, $MaxChars) {
    try {
        if (!(Test-Path -LiteralPath $Path)) { return '' }
        $text = Get-Content -LiteralPath $Path -Raw -Encoding UTF8
        if ($text.Length -gt $MaxChars) { return $text.Substring($text.Length - $MaxChars) }
        return $text
    } catch { return '' }
}

function ReadJson($Path) {
    try {
        $t = ReadText $Path 20000
        if (!$t) { return $null }
        return ($t | ConvertFrom-Json)
    } catch { return $null }
}

function ParseHeartbeat($Name) {
    $path = Join-Path $BridgeRoot ('ai-heartbeat\' + $Name)
    $text = ReadText $path 4000
    $timeLine = (($text -split "`n") | Where-Object { $_ -like 'Time:*' } | Select-Object -First 1)
    $statusLine = (($text -split "`n") | Where-Object { $_ -like 'Status:*' } | Select-Object -First 1)
    $dt = $null
    if ($timeLine) {
        $raw = ($timeLine -replace '^Time:\s*','').Trim()
        try { $dt = [datetime]::Parse($raw) } catch { $dt = $null }
    }
    $status = ''
    if ($statusLine) { $status = ($statusLine -replace '^Status:\s*','').Trim() }
    return [pscustomobject]@{ Time=$dt; Status=$status; Text=(($timeLine + ' | ' + $statusLine).Trim()) }
}

function CurrentTask() {
    return ReadJson (Join-Path $BridgeRoot 'ai-tasks\current-task.json')
}

function ResultInfo($TaskId) {
    $dir = Join-Path $BridgeRoot 'ai-results'
    $exact = Join-Path $dir ('Runner V4 result ' + $TaskId + '.md')
    $path = ''
    if (Test-Path -LiteralPath $exact) { $path = $exact }
    elseif (Test-Path -LiteralPath $dir) {
        $f = Get-ChildItem -LiteralPath $dir -File -Filter ('*' + $TaskId + '*.md') | Sort-Object LastWriteTime -Descending | Select-Object -First 1
        if ($f) { $path = $f.FullName }
    }
    if (!$path) { return [pscustomobject]@{ Exists=$false; Exit=''; Summary='No result file yet'; Path='' } }
    $t = ReadText $path 8000
    $exit = ''
    $m = [regex]::Match($t, 'Exit Code\s*\r?\n\s*([0-9\-]+)', 'IgnoreCase')
    if ($m.Success) { $exit = $m.Groups[1].Value }
    $lines = ($t -split "`n") | Where-Object { $_ -match 'RESULT:|WORKDIR_NOT_ALLOWED|ERROR|NEXT:|PROGRESS:' } | Select-Object -Last 4
    $sum = ($lines -join ' | ')
    if (!$sum) { $sum = 'Result file exists' }
    return [pscustomobject]@{ Exists=$true; Exit=$exit; Summary=$sum; Path=$path }
}

function SystemUsage() {
    $cpu = '?'; $ram = '?'
    try {
        $c = Get-CimInstance Win32_PerfFormattedData_PerfOS_Processor | Where-Object { $_.Name -eq '_Total' } | Select-Object -First 1
        if ($c) { $cpu = ([int]$c.PercentProcessorTime).ToString() + '%' }
    } catch {}
    try {
        $os = Get-CimInstance Win32_OperatingSystem
        $total = [double]$os.TotalVisibleMemorySize
        $free = [double]$os.FreePhysicalMemory
        if ($total -gt 0) { $ram = ([math]::Round((($total-$free)/$total)*100,0)).ToString() + '%' }
    } catch {}
    return [pscustomobject]@{ Cpu=$cpu; Ram=$ram }
}

function ProcessCpu($NamesCsv) {
    $names = $NamesCsv.Split(',')
    $now = Get-Date
    $elapsed = [math]::Max(1, ($now - $script:LastCpuTime).TotalSeconds)
    $cores = [math]::Max(1, [Environment]::ProcessorCount)
    $sum = 0.0
    $shown = New-Object System.Collections.Generic.List[string]
    try {
        $procs = Get-Process | Where-Object { $names -contains $_.ProcessName }
        foreach ($p in $procs) {
            $cpuNow = 0.0
            try { $cpuNow = [double]$p.CPU } catch { $cpuNow = 0.0 }
            $prev = $script:LastCpu[$p.Id]
            if ($null -ne $prev) {
                $delta = $cpuNow - [double]$prev
                if ($delta -gt 0) { $sum += (($delta / ($elapsed * $cores)) * 100) }
            }
            if ($shown.Count -lt 5) { $shown.Add($p.ProcessName + '#' + $p.Id) | Out-Null }
        }
        $new = @{}
        foreach ($p in (Get-Process | Where-Object { $names -contains $_.ProcessName })) {
            try { $new[$p.Id] = [double]$p.CPU } catch {}
        }
        foreach ($k in $script:LastCpu.Keys) { if (!$new.ContainsKey($k)) { $new[$k] = $script:LastCpu[$k] } }
        $script:LastCpu = $new
        $script:LastCpuTime = $now
    } catch {}
    return [pscustomobject]@{ Cpu=([math]::Round($sum,1)).ToString() + '%'; Processes=($shown -join ', ') }
}

function BuildTable() {
    $current = CurrentTask
    $runner = ParseHeartbeat 'runner-v4.md'
    $sys = SystemUsage
    $rows = New-Object System.Collections.Generic.List[object]
    foreach ($j in $Jobs) {
        $descPath = Join-Path $BridgeRoot $j.Descriptor
        $descExists = Test-Path -LiteralPath $descPath
        $result = ResultInfo $j.TaskId
        $pcpu = ProcessCpu $j.Proc
        $isCurrent = ($current -and $current.id -eq $j.TaskId)
        $progress = '?'
        if ($isCurrent -and $current.progress -ne $null) { $progress = [string]$current.progress }
        elseif ($result.Summary -match 'PROGRESS:\s*([0-9]+)') { $progress = $Matches[1] }
        $status = 'Queued'
        $real = 'No'
        $wait = '-'
        $evidence = ''
        if ($isCurrent -and $runner.Status -match 'started|running') {
            $status = 'Running'; $real = 'Yes'; $evidence = 'Runner heartbeat shows current task'
            if ($runner.Time -and $current.timeout_seconds) {
                $left = [int]$current.timeout_seconds - [int]((Get-Date) - $runner.Time).TotalSeconds
                if ($left -lt 0) { $left = 0 }
                $wait = ([math]::Round($left/60,1)).ToString() + ' min'
            }
        } elseif ($result.Exists) {
            if ($result.Exit -eq '0') { $status = 'Finished' } else { $status = 'Blocked/Error' }
            $real = 'Finished evidence'
            $evidence = $result.Summary
        } elseif ($pcpu.Cpu -ne '0%' -and $pcpu.Cpu -ne '0.0%') {
            $status = 'Process activity'; $real = 'Maybe'; $evidence = 'Matching process CPU detected'
        } elseif ($descExists) {
            $status = 'Queued'; $evidence = 'Descriptor exists'
        } else {
            $status = 'Not registered'; $evidence = 'No descriptor/result found'
        }
        $rows.Add([pscustomobject]@{
            Job=$j.Job
            TaskId=$j.TaskId
            Status=$status
            RealWork=$real
            Progress=($progress + '%')
            WaitLeft=$wait
            JobCPU=$pcpu.Cpu
            SystemCPU=$sys.Cpu
            RAM=$sys.Ram
            Processes=$pcpu.Processes
            Evidence=$evidence
        }) | Out-Null
    }
    return $rows
}

$form = New-Object System.Windows.Forms.Form
$form.Text = 'AAYS TerraYield Job Monitor'
$form.Size = New-Object System.Drawing.Size(1450,650)
$form.StartPosition = 'CenterScreen'
$form.BackColor = [System.Drawing.Color]::White
$form.Font = New-Object System.Drawing.Font('Segoe UI',9)

$title = New-Object System.Windows.Forms.Label
$title.Text = 'TerraYield - Real Work and Performance Table'
$title.Font = New-Object System.Drawing.Font('Segoe UI',15,[System.Drawing.FontStyle]::Bold)
$title.AutoSize = $true
$title.Location = New-Object System.Drawing.Point(15,12)
$form.Controls.Add($title)

$statusLabel = New-Object System.Windows.Forms.Label
$statusLabel.Text = 'Loading...'
$statusLabel.AutoSize = $true
$statusLabel.Location = New-Object System.Drawing.Point(18,45)
$form.Controls.Add($statusLabel)

$btn = New-Object System.Windows.Forms.Button
$btn.Text = 'Refresh'
$btn.Size = New-Object System.Drawing.Size(105,30)
$btn.Location = New-Object System.Drawing.Point(1180,18)
$form.Controls.Add($btn)

$btnResults = New-Object System.Windows.Forms.Button
$btnResults.Text = 'Results'
$btnResults.Size = New-Object System.Drawing.Size(105,30)
$btnResults.Location = New-Object System.Drawing.Point(1295,18)
$form.Controls.Add($btnResults)

$grid = New-Object System.Windows.Forms.DataGridView
$grid.Location = New-Object System.Drawing.Point(15,80)
$grid.Size = New-Object System.Drawing.Size(1400,500)
$grid.Anchor = 'Top,Bottom,Left,Right'
$grid.BackgroundColor = [System.Drawing.Color]::White
$grid.AutoSizeColumnsMode = 'Fill'
$grid.AllowUserToAddRows = $false
$grid.AllowUserToDeleteRows = $false
$grid.ReadOnly = $true
$grid.RowHeadersVisible = $false
$form.Controls.Add($grid)

$hint = New-Object System.Windows.Forms.Label
$hint.Text = 'Auto refresh: 30 seconds. This panel reads only the configured job records and runner evidence.'
$hint.AutoSize = $true
$hint.Location = New-Object System.Drawing.Point(18,590)
$form.Controls.Add($hint)

function RefreshGrid() {
    try {
        $rows = BuildTable
        $grid.DataSource = $null
        $grid.DataSource = [System.Collections.ArrayList]$rows
        $statusLabel.Text = 'Last update: ' + (Get-Date).ToString('yyyy-MM-dd HH:mm:ss') + ' | Jobs: ' + $rows.Count
        foreach ($row in $grid.Rows) {
            $s = [string]$row.Cells['Status'].Value
            if ($s -eq 'Running') { $row.DefaultCellStyle.BackColor = [System.Drawing.Color]::Honeydew }
            elseif ($s -eq 'Blocked/Error') { $row.DefaultCellStyle.BackColor = [System.Drawing.Color]::MistyRose }
            elseif ($s -eq 'Finished') { $row.DefaultCellStyle.BackColor = [System.Drawing.Color]::AliceBlue }
            elseif ($s -eq 'Queued') { $row.DefaultCellStyle.BackColor = [System.Drawing.Color]::LemonChiffon }
            else { $row.DefaultCellStyle.BackColor = [System.Drawing.Color]::White }
        }
    } catch {
        $statusLabel.Text = 'Panel error: ' + $_.Exception.Message
    }
}

$btn.Add_Click({ RefreshGrid })
$btnResults.Add_Click({ Start-Process (Join-Path $BridgeRoot 'ai-results') })
$timer = New-Object System.Windows.Forms.Timer
$timer.Interval = $RefreshSeconds * 1000
$timer.Add_Tick({ RefreshGrid })
$timer.Start()
$form.Add_Shown({ RefreshGrid })
[void]$form.ShowDialog()
