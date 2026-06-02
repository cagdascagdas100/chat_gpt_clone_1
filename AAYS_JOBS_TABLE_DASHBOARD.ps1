Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$ErrorActionPreference = 'Continue'
$BridgeRoot = 'C:\Users\cagda\Documents\chat_gpt_clone_1'
$RefreshSeconds = 30
$script:LastCpu = @{}
$script:LastCpuTime = Get-Date
$script:IsRefreshing = $false
$script:PanelWarnings = New-Object System.Collections.Generic.List[string]
$script:PanelPid = $PID

$Jobs = @(
    [pscustomobject]@{ Job='Backend'; TaskId='terrayield-060A-backend'; Descriptor='ai-tasks\parallel\terrayield-060A-backend.json'; Proc='python,docker' },
    [pscustomobject]@{ Job='Frontend'; TaskId='terrayield-060B-frontend'; Descriptor='ai-tasks\parallel\terrayield-060B-frontend.json'; Proc='node' },
    [pscustomobject]@{ Job='Ops'; TaskId='terrayield-060C-ops'; Descriptor='ai-tasks\parallel\terrayield-060C-ops.json'; Proc='powershell,pwsh' },
    [pscustomobject]@{ Job='Active Pool'; TaskId='terrayield-065-five-slot-parallel-dispatcher-rerun'; Descriptor='ai-tasks\current-task.json'; Proc='powershell,pwsh,python,node,docker' },
    [pscustomobject]@{ Job='Mega Batch'; TaskId='terrayield-062-mega-parallel-pickup-project-root'; Descriptor='ai-tasks\current-task.json'; Proc='powershell,pwsh' }
)

function Add-WarningText {
    param([string]$Text)
    try {
        if ([string]::IsNullOrWhiteSpace($Text)) { return }
        $line = (Get-Date).ToString('HH:mm:ss') + ' ' + $Text
        $script:PanelWarnings.Add($line) | Out-Null
        while ($script:PanelWarnings.Count -gt 5) { $script:PanelWarnings.RemoveAt(0) }
    } catch {}
}

function ReadText {
    param([string]$Path, [int]$MaxChars = 20000)
    try {
        if (!(Test-Path -LiteralPath $Path -ErrorAction SilentlyContinue)) { return '' }
        $text = [System.IO.File]::ReadAllText($Path, [System.Text.Encoding]::UTF8)
        if ($text.Length -gt $MaxChars) { return $text.Substring($text.Length - $MaxChars) }
        return $text
    } catch [System.Management.Automation.PipelineStoppedException] {
        Add-WarningText 'Read skipped because PowerShell pipeline was stopping.'
        return ''
    } catch {
        Add-WarningText ('Read warning: ' + $_.Exception.Message)
        return ''
    }
}

function ReadJson {
    param([string]$Path)
    try {
        $t = ReadText -Path $Path -MaxChars 20000
        if ([string]::IsNullOrWhiteSpace($t)) { return $null }
        return ($t | ConvertFrom-Json -ErrorAction Stop)
    } catch {
        Add-WarningText ('JSON warning: ' + $_.Exception.Message)
        return $null
    }
}

function FirstLineStartingWith {
    param([string]$Text, [string]$Prefix)
    try {
        if ([string]::IsNullOrEmpty($Text)) { return '' }
        foreach ($line in ($Text -split "`r?`n")) {
            if ($line.StartsWith($Prefix)) { return $line }
        }
        return ''
    } catch { return '' }
}

function Parse-DateSafe {
    param([string]$Raw)
    if ([string]::IsNullOrWhiteSpace($Raw)) { return $null }
    $formats = @('dd/MM/yyyy HH:mm:ss','M/d/yyyy HH:mm:ss','MM/dd/yyyy HH:mm:ss','yyyy-MM-dd HH:mm:ss','yyyy-MM-ddTHH:mm:ss')
    foreach ($fmt in $formats) {
        try {
            return [datetime]::ParseExact($Raw.Trim(), $fmt, [System.Globalization.CultureInfo]::InvariantCulture)
        } catch {}
    }
    try { return [datetime]::Parse($Raw, [System.Globalization.CultureInfo]::InvariantCulture) } catch { return $null }
}

function ParseHeartbeat {
    param([string]$Name)
    try {
        $path = Join-Path $BridgeRoot ('ai-heartbeat\' + $Name)
        $text = ReadText -Path $path -MaxChars 4000
        $timeLine = FirstLineStartingWith -Text $text -Prefix 'Time:'
        $statusLine = FirstLineStartingWith -Text $text -Prefix 'Status:'
        $dt = $null
        if ($timeLine) { $dt = Parse-DateSafe (($timeLine -replace '^Time:\s*','').Trim()) }
        if ($dt -and $dt -gt (Get-Date).AddMinutes(5)) {
            Add-WarningText 'Heartbeat time looked like a future date; ignored for wait calculation.'
            $dt = $null
        }
        $status = ''
        if ($statusLine) { $status = ($statusLine -replace '^Status:\s*','').Trim() }
        return [pscustomobject]@{ Time=$dt; Status=$status; Text=(($timeLine + ' | ' + $statusLine).Trim()) }
    } catch {
        Add-WarningText ('Heartbeat warning: ' + $_.Exception.Message)
        return [pscustomobject]@{ Time=$null; Status='unknown'; Text='heartbeat read failed' }
    }
}

function CurrentTask {
    return ReadJson -Path (Join-Path $BridgeRoot 'ai-tasks\current-task.json')
}

function ResultInfo {
    param([string]$TaskId)
    try {
        $dir = Join-Path $BridgeRoot 'ai-results'
        $exact = Join-Path $dir ('Runner V4 result ' + $TaskId + '.md')
        $path = ''
        if (Test-Path -LiteralPath $exact -ErrorAction SilentlyContinue) { $path = $exact }
        elseif (Test-Path -LiteralPath $dir -ErrorAction SilentlyContinue) {
            $best = $null
            $bestTime = [datetime]::MinValue
            foreach ($file in [System.IO.Directory]::EnumerateFiles($dir, ('*' + $TaskId + '*.md'))) {
                try {
                    $info = New-Object System.IO.FileInfo($file)
                    if ($info.LastWriteTime -gt $bestTime) { $bestTime = $info.LastWriteTime; $best = $file }
                } catch {}
            }
            if ($best) { $path = $best }
        }
        if (!$path) { return [pscustomobject]@{ Exists=$false; Exit=''; Summary='No result file yet'; Path='' } }
        $t = ReadText -Path $path -MaxChars 8000
        $exit = ''
        $m = [regex]::Match($t, 'Exit Code\s*\r?\n\s*([0-9\-]+)', 'IgnoreCase')
        if ($m.Success) { $exit = $m.Groups[1].Value }
        $summaryLines = New-Object System.Collections.Generic.List[string]
        foreach ($line in ($t -split "`r?`n")) {
            if ($line -match 'RESULT:|WORKDIR_NOT_ALLOWED|BLOCKED_BY_RUNNER_SAFETY_POLICY|ERROR|NEXT:|PROGRESS:') {
                $summaryLines.Add($line.Trim()) | Out-Null
                while ($summaryLines.Count -gt 4) { $summaryLines.RemoveAt(0) }
            }
        }
        $sum = ($summaryLines -join ' | ')
        if (!$sum) { $sum = 'Result file exists' }
        return [pscustomobject]@{ Exists=$true; Exit=$exit; Summary=$sum; Path=$path }
    } catch {
        Add-WarningText ('Result warning: ' + $_.Exception.Message)
        return [pscustomobject]@{ Exists=$false; Exit=''; Summary='Result read warning'; Path='' }
    }
}

function SystemUsage {
    $cpu = '?'; $ram = '?'
    try {
        foreach ($item in @(Get-CimInstance Win32_PerfFormattedData_PerfOS_Processor -ErrorAction Stop)) {
            if ($item.Name -eq '_Total') { $cpu = ([int]$item.PercentProcessorTime).ToString() + '%'; break }
        }
    } catch { Add-WarningText ('CPU warning: ' + $_.Exception.Message) }
    try {
        $os = Get-CimInstance Win32_OperatingSystem -ErrorAction Stop
        $total = [double]$os.TotalVisibleMemorySize
        $free = [double]$os.FreePhysicalMemory
        if ($total -gt 0) { $ram = ([math]::Round((($total-$free)/$total)*100,0)).ToString() + '%' }
    } catch { Add-WarningText ('RAM warning: ' + $_.Exception.Message) }
    return [pscustomobject]@{ Cpu=$cpu; Ram=$ram }
}

function ProcessCpu {
    param([string]$NamesCsv)
    $names = @()
    foreach ($n in $NamesCsv.Split(',')) { if ($n.Trim()) { $names += $n.Trim().ToLowerInvariant() } }
    $now = Get-Date
    $elapsed = [math]::Max(1, ($now - $script:LastCpuTime).TotalSeconds)
    $cores = [math]::Max(1, [Environment]::ProcessorCount)
    $sum = 0.0
    $shown = New-Object System.Collections.Generic.List[string]
    try {
        $procs = @(Get-Process -ErrorAction Stop)
        $new = @{}
        foreach ($p in $procs) {
            if ($p.Id -eq $script:PanelPid) { continue }
            $pname = $p.ProcessName.ToLowerInvariant()
            if ($names -notcontains $pname) { continue }
            $cpuNow = 0.0
            try { $cpuNow = [double]$p.CPU } catch { $cpuNow = 0.0 }
            $prev = $script:LastCpu[$p.Id]
            if ($null -ne $prev) {
                $delta = $cpuNow - [double]$prev
                if ($delta -gt 0) { $sum += (($delta / ($elapsed * $cores)) * 100) }
            }
            $new[$p.Id] = $cpuNow
            if ($shown.Count -lt 5) { $shown.Add($p.ProcessName + '#' + $p.Id) | Out-Null }
        }
        $script:LastCpu = $new
        $script:LastCpuTime = $now
    } catch {
        Add-WarningText ('Process warning: ' + $_.Exception.Message)
    }
    return [pscustomobject]@{ Cpu=([math]::Round($sum,1)).ToString() + '%'; Processes=($shown -join ', ') }
}

function BuildTable {
    $current = CurrentTask
    $runner = ParseHeartbeat -Name 'runner-v4.md'
    $sys = SystemUsage
    $rows = New-Object System.Collections.Generic.List[object]
    foreach ($j in $Jobs) {
        try {
            $descPath = Join-Path $BridgeRoot $j.Descriptor
            $descExists = Test-Path -LiteralPath $descPath -ErrorAction SilentlyContinue
            $result = ResultInfo -TaskId $j.TaskId
            $pcpu = ProcessCpu -NamesCsv $j.Proc
            $isCurrent = ($current -and $current.id -eq $j.TaskId)
            $progress = '?'
            if ($isCurrent -and $null -ne $current.progress) { $progress = [string]$current.progress }
            elseif ($result.Summary -match 'PROGRESS:\s*([0-9]+)') { $progress = $Matches[1] }
            $status = 'Active descriptor'
            $real = 'No'
            $wait = '-'
            $evidence = ''
            if ($isCurrent -and $runner.Status -match 'started|running') {
                $status = 'Running'; $real = 'Yes'; $evidence = 'Runner heartbeat: ' + $runner.Status
                if ($runner.Time -and $current.timeout_seconds) {
                    $left = [int]$current.timeout_seconds - [int]((Get-Date) - $runner.Time).TotalSeconds
                    if ($left -lt 0) { $left = 0 }
                    if ($left -gt 86400) { $wait = '-' } else { $wait = ([math]::Round($left/60,1)).ToString() + ' min' }
                }
            } elseif ($isCurrent -and $runner.Status -match 'polling') {
                $status = 'Idle / polling only'
                $real = 'No'
                $wait = '-'
                $evidence = 'Runner is alive but only polling; no active work evidence.'
            } elseif ($result.Exists) {
                if ($result.Exit -eq '0') { $status = 'Finished' } else { $status = 'Blocked/Error' }
                $real = 'Finished evidence'
                $evidence = $result.Summary
            } elseif ($pcpu.Cpu -ne '0%' -and $pcpu.Cpu -ne '0.0%') {
                $status = 'Process activity'; $real = 'Maybe'; $evidence = 'Matching process CPU detected'
            } elseif ($descExists) {
                $status = 'Active descriptor'; $evidence = 'Descriptor exists'
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
        } catch {
            Add-WarningText ('Row warning for ' + $j.Job + ': ' + $_.Exception.Message)
            $rows.Add([pscustomobject]@{ Job=$j.Job; TaskId=$j.TaskId; Status='Panel row warning'; RealWork='Unknown'; Progress='?%'; WaitLeft='-'; JobCPU='?'; SystemCPU=$sys.Cpu; RAM=$sys.Ram; Processes=''; Evidence=$_.Exception.Message }) | Out-Null
        }
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
$grid.Size = New-Object System.Drawing.Size(1400,470)
$grid.Anchor = 'Top,Bottom,Left,Right'
$grid.BackgroundColor = [System.Drawing.Color]::White
$grid.AutoSizeColumnsMode = 'Fill'
$grid.AllowUserToAddRows = $false
$grid.AllowUserToDeleteRows = $false
$grid.ReadOnly = $true
$grid.RowHeadersVisible = $false
$form.Controls.Add($grid)

$hint = New-Object System.Windows.Forms.Label
$hint.Text = 'Auto refresh: 30 seconds. Polling is not counted as real work.'
$hint.AutoSize = $true
$hint.Location = New-Object System.Drawing.Point(18,560)
$form.Controls.Add($hint)

$warningLabel = New-Object System.Windows.Forms.Label
$warningLabel.Text = ''
$warningLabel.AutoSize = $false
$warningLabel.Size = New-Object System.Drawing.Size(1380,40)
$warningLabel.Location = New-Object System.Drawing.Point(18,585)
$warningLabel.ForeColor = [System.Drawing.Color]::DarkRed
$form.Controls.Add($warningLabel)

function RefreshGrid {
    if ($script:IsRefreshing) { return }
    $script:IsRefreshing = $true
    try {
        $rows = BuildTable
        $grid.SuspendLayout()
        try {
            $grid.DataSource = $null
            $grid.DataSource = [System.Collections.ArrayList]$rows
            foreach ($row in $grid.Rows) {
                try {
                    $s = [string]$row.Cells['Status'].Value
                    if ($s -eq 'Running') { $row.DefaultCellStyle.BackColor = [System.Drawing.Color]::Honeydew }
                    elseif ($s -eq 'Blocked/Error') { $row.DefaultCellStyle.BackColor = [System.Drawing.Color]::MistyRose }
                    elseif ($s -eq 'Finished') { $row.DefaultCellStyle.BackColor = [System.Drawing.Color]::AliceBlue }
                    elseif ($s -eq 'Active descriptor' -or $s -eq 'Idle / polling only') { $row.DefaultCellStyle.BackColor = [System.Drawing.Color]::LemonChiffon }
                    else { $row.DefaultCellStyle.BackColor = [System.Drawing.Color]::White }
                } catch {}
            }
        } finally {
            $grid.ResumeLayout()
        }
        $statusLabel.Text = 'Last update: ' + (Get-Date).ToString('yyyy-MM-dd HH:mm:ss') + ' | Jobs: ' + $rows.Count
        $warningLabel.Text = ($script:PanelWarnings -join '   |   ')
    } catch {
        Add-WarningText ('Panel warning: ' + $_.Exception.Message)
        $warningLabel.Text = ($script:PanelWarnings -join '   |   ')
    } finally {
        $script:IsRefreshing = $false
    }
}

$btn.Add_Click({ try { RefreshGrid } catch { Add-WarningText ('Button warning: ' + $_.Exception.Message) } })
$btnResults.Add_Click({ try { Start-Process (Join-Path $BridgeRoot 'ai-results') } catch { Add-WarningText ('Open results warning: ' + $_.Exception.Message) } })
$timer = New-Object System.Windows.Forms.Timer
$timer.Interval = $RefreshSeconds * 1000
$timer.Add_Tick({ try { RefreshGrid } catch { Add-WarningText ('Timer warning: ' + $_.Exception.Message) } })
$form.Add_FormClosing({ try { $timer.Stop(); $timer.Dispose() } catch {} })
$form.Add_Shown({ try { $timer.Start(); RefreshGrid } catch { Add-WarningText ('Startup warning: ' + $_.Exception.Message) } })
[void]$form.ShowDialog()
