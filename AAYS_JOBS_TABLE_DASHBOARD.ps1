Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$ErrorActionPreference = 'SilentlyContinue'

$BridgeRoot = 'C:\Users\cagda\Documents\chat_gpt_clone_1'
$ProjectRoot = 'C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$RefreshSeconds = 30
$Script:LastCpuSnapshot = @{}
$Script:LastSnapshotTime = Get-Date

$Jobs = @(
    [ordered]@{
        Name='Backend';
        TaskId='terrayield-060A-backend';
        Descriptor='ai-tasks\parallel\terrayield-060A-backend.json';
        Keywords=@('python','alembic','docker','managed_sales','backend','terrayield_land_intelligence')
    },
    [ordered]@{
        Name='Frontend';
        TaskId='terrayield-060B-frontend';
        Descriptor='ai-tasks\parallel\terrayield-060B-frontend.json';
        Keywords=@('node','frontend','admin','map','england_map_web')
    },
    [ordered]@{
        Name='Ops';
        TaskId='terrayield-060C-ops';
        Descriptor='ai-tasks\parallel\terrayield-060C-ops.json';
        Keywords=@('powershell','backup','cache','ops','health')
    },
    [ordered]@{
        Name='Mega Batch';
        TaskId='terrayield-062-mega-parallel-pickup-project-root';
        Descriptor='ai-tasks\current-task.json';
        Keywords=@('powershell','terrayield-061-mega-batch','mega','parallel')
    }
)

function Read-FileText {
    param([string]$Path, [int]$MaxChars = 20000)
    try {
        if (-not (Test-Path -LiteralPath $Path)) { return '' }
        $t = Get-Content -LiteralPath $Path -Raw -Encoding UTF8
        if ($t.Length -gt $MaxChars) { return $t.Substring($t.Length - $MaxChars) }
        return $t
    } catch { return '' }
}

function Parse-JsonSafe {
    param([string]$Text)
    try { return ($Text | ConvertFrom-Json) } catch { return $null }
}

function Get-CurrentTask {
    $p = Join-Path $BridgeRoot 'ai-tasks\current-task.json'
    $j = Parse-JsonSafe (Read-FileText $p)
    return $j
}

function Get-Heartbeat {
    param([string]$Name)
    $p = Join-Path $BridgeRoot ('ai-heartbeat\' + $Name)
    $txt = Read-FileText $p 4000
    $timeLine = (($txt -split "`n") | Where-Object { $_ -match '^Time:' } | Select-Object -First 1)
    $statusLine = (($txt -split "`n") | Where-Object { $_ -match '^Status:' } | Select-Object -First 1)
    $dt = $null
    if ($timeLine) {
        $raw = ($timeLine -replace '^Time:\s*','').Trim()
        [datetime]::TryParse($raw, [ref]$dt) | Out-Null
    }
    return [ordered]@{
        Text = (($timeLine + ' | ' + $statusLine).Trim())
        Time = $dt
        Status = (($statusLine -replace '^Status:\s*','').Trim())
        Raw = $txt
    }
}

function Get-ResultForTask {
    param([string]$TaskId)
    $result1 = Join-Path $BridgeRoot ('ai-results\Runner V4 result ' + $TaskId + '.md')
    if (Test-Path -LiteralPath $result1) { return $result1 }
    $dir = Join-Path $BridgeRoot 'ai-results'
    if (-not (Test-Path -LiteralPath $dir)) { return '' }
    $m = Get-ChildItem -LiteralPath $dir -File -Filter ('*' + $TaskId + '*.md') | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($m) { return $m.FullName }
    return ''
}

function Get-ResultSummary {
    param([string]$TaskId)
    $p = Get-ResultForTask $TaskId
    if (-not $p) { return [ordered]@{ Exists=$false; Path=''; Exit=''; Summary='' } }
    $txt = Read-FileText $p 6000
    $exit = ''
    $m = [regex]::Match($txt, 'Exit Code\s*\r?\n\s*([0-9\-]+)', 'IgnoreCase')
    if ($m.Success) { $exit = $m.Groups[1].Value }
    if (-not $exit) {
        $m2 = [regex]::Match($txt, 'exit=([0-9\-]+)', 'IgnoreCase')
        if ($m2.Success) { $exit = $m2.Groups[1].Value }
    }
    $summary = (($txt -split "`n") | Where-Object { $_ -match 'RESULT:|WORKDIR_NOT_ALLOWED|ERROR|NEXT:|PROGRESS:' } | Select-Object -Last 4) -join ' | '
    return [ordered]@{ Exists=$true; Path=$p; Exit=$exit; Summary=$summary }
}

function Get-SystemUsage {
    $cpu = '?'
    $ram = '?'
    try {
        $cpuObj = Get-CimInstance Win32_PerfFormattedData_PerfOS_Processor | Where-Object { $_.Name -eq '_Total' } | Select-Object -First 1
        if ($cpuObj) { $cpu = ([int]$cpuObj.PercentProcessorTime).ToString() + '%' }
    } catch {}
    try {
        $os = Get-CimInstance Win32_OperatingSystem
        $total = [double]$os.TotalVisibleMemorySize
        $free = [double]$os.FreePhysicalMemory
        if ($total -gt 0) {
            $usedPct = [math]::Round((($total - $free) / $total) * 100, 0)
            $ram = $usedPct.ToString() + '%'
        }
    } catch {}
    return [ordered]@{ Cpu=$cpu; Ram=$ram }
}

function Get-ProcessCpuMap {
    $now = Get-Date
    $elapsed = [math]::Max(1, ($now - $Script:LastSnapshotTime).TotalSeconds)
    $logical = [Environment]::ProcessorCount
    $map = @{}
    try {
        $procs = Get-Process | Where-Object { $_.ProcessName -match 'powershell|pwsh|python|node|docker|git' }
        foreach ($p in $procs) {
            $cpuNow = 0
            try { $cpuNow = [double]$p.CPU } catch { $cpuNow = 0 }
            $prev = $Script:LastCpuSnapshot[$p.Id]
            $pct = 0
            if ($null -ne $prev) {
                $delta = $cpuNow - [double]$prev
                if ($delta -gt 0) { $pct = [math]::Round(($delta / ($elapsed * $logical)) * 100, 1) }
            }
            $map[$p.Id] = [ordered]@{ Name=$p.ProcessName; Cpu=$pct; CpuTotal=$cpuNow }
        }
        $newSnap = @{}
        foreach ($p in $procs) {
            try { $newSnap[$p.Id] = [double]$p.CPU } catch {}
        }
        $Script:LastCpuSnapshot = $newSnap
        $Script:LastSnapshotTime = $now
    } catch {}
    return $map
}

function Estimate-JobProcessInfo {
    param($Job, $CpuMap)
    $names = New-Object System.Collections.Generic.List[string]
    $sum = 0.0
    foreach ($kv in $CpuMap.GetEnumerator()) {
        $pn = [string]$kv.Value.Name
        $hit = $false
        foreach ($k in $Job.Keywords) {
            if ($pn.ToLowerInvariant().Contains(([string]$k).ToLowerInvariant())) { $hit = $true }
        }
        if ($hit -or ($Job.Name -eq 'Backend' -and $pn -match 'python|docker') -or ($Job.Name -eq 'Frontend' -and $pn -match 'node') -or ($Job.Name -eq 'Ops' -and $pn -match 'powershell|pwsh') -or ($Job.Name -eq 'Mega Batch' -and $pn -match 'powershell|pwsh')) {
            $sum += [double]$kv.Value.Cpu
            if ($names.Count -lt 4) { $names.Add($pn + '#' + $kv.Key) | Out-Null }
        }
    }
    return [ordered]@{ Cpu=[math]::Round($sum,1); Processes=($names -join ', ') }
}

function Build-Rows {
    $current = Get-CurrentTask
    $runner = Get-Heartbeat 'runner-v4.md'
    $watchdog = Get-Heartbeat 'user-mode-watchdog.md'
    $sys = Get-SystemUsage
    $cpuMap = Get-ProcessCpuMap
    $rows = New-Object System.Collections.Generic.List[object]

    foreach ($job in $Jobs) {
        $descriptorPath = Join-Path $BridgeRoot $job.Descriptor
        $descriptorExists = Test-Path -LiteralPath $descriptorPath
        $result = Get-ResultSummary $job.TaskId
        $pinfo = Estimate-JobProcessInfo $job $cpuMap
        $isCurrent = $false
        $progress = ''
        $timeout = 0
        $note = ''
        if ($current -and $current.id -eq $job.TaskId) {
            $isCurrent = $true
            $progress = [string]$current.progress
            $timeout = [int]$current.timeout_seconds
            $note = [string]$current.note
        }
        if (-not $progress) {
            if ($result.Exists) {
                $m = [regex]::Match($result.Summary, 'PROGRESS:\s*([0-9]+)', 'IgnoreCase')
                if ($m.Success) { $progress = $m.Groups[1].Value }
            }
        }
        if (-not $progress) { $progress = '?' }

        $status = 'Bekliyor'
        $evidence = 'descriptor=' + $descriptorExists
        $wait = '-'
        $real = 'Hayır'

        $runnerRecent = $false
        if ($runner.Time) { $runnerRecent = (((Get-Date) - $runner.Time).TotalSeconds -lt 120) }
        if ($isCurrent -and $runner.Status -match 'started|running') {
            $status = 'Çalışıyor'
            $real = 'Evet'
            $evidence = 'runner heartbeat current task'
        } elseif ($result.Exists) {
            if ($result.Exit -eq '0') { $status = 'Bitti' } else { $status = 'Hata/Blokaj' }
            $evidence = $result.Summary
        } elseif ($isCurrent -and $runnerRecent) {
            $status = 'Pickup bekliyor'
            $real = 'Kısmen'
            $evidence = 'current task var, heartbeat güncel'
        } elseif ($pinfo.Cpu -gt 0.5) {
            $status = 'Süreç var'
            $real = 'Kısmen'
            $evidence = 'ilgili process CPU üretiyor'
        } elseif ($descriptorExists) {
            $status = 'Kuyrukta'
        } else {
            $status = 'Kayıt yok'
        }

        if ($isCurrent -and $runner.Time -and $timeout -gt 0) {
            $elapsed = [math]::Max(0, [int]((Get-Date) - $runner.Time).TotalSeconds)
            $left = [math]::Max(0, $timeout - $elapsed)
            $wait = ([math]::Round($left / 60, 1)).ToString() + ' dk'
        } elseif ($status -eq 'Kuyrukta' -or $status -eq 'Pickup bekliyor') {
            $wait = 'bilinmiyor'
        }

        $rows.Add([pscustomobject]@{
            'İş' = $job.Name
            'Task ID' = $job.TaskId
            'Durum' = $status
            'Gerçek işlem' = $real
            'İlerleme' = ($progress + '%')
            'Kalan/Bekleme' = $wait
            'İş CPU' = ($pinfo.Cpu.ToString() + '%')
            'Sistem CPU' = $sys.Cpu
            'RAM' = $sys.Ram
            'Process' = $pinfo.Processes
            'Kanıt' = $evidence
        }) | Out-Null
    }
    return $rows
}

$form = New-Object System.Windows.Forms.Form
$form.Text = 'AAYS TerraYield İş Takip Paneli'
$form.Size = New-Object System.Drawing.Size(1450, 650)
$form.StartPosition = 'CenterScreen'
$form.BackColor = [System.Drawing.Color]::White
$form.Font = New-Object System.Drawing.Font('Segoe UI', 9)

$title = New-Object System.Windows.Forms.Label
$title.Text = 'TerraYield - Gerçek İşlem ve Performans Tablosu'
$title.AutoSize = $true
$title.Font = New-Object System.Drawing.Font('Segoe UI', 15, [System.Drawing.FontStyle]::Bold)
$title.Location = New-Object System.Drawing.Point(15, 12)
$title.BackColor = [System.Drawing.Color]::White
$form.Controls.Add($title)

$statusLabel = New-Object System.Windows.Forms.Label
$statusLabel.Text = 'Hazırlanıyor...'
$statusLabel.AutoSize = $true
$statusLabel.Location = New-Object System.Drawing.Point(18, 45)
$statusLabel.BackColor = [System.Drawing.Color]::White
$form.Controls.Add($statusLabel)

$refreshButton = New-Object System.Windows.Forms.Button
$refreshButton.Text = 'Yenile'
$refreshButton.Size = New-Object System.Drawing.Size(100, 30)
$refreshButton.Location = New-Object System.Drawing.Point(1180, 18)
$form.Controls.Add($refreshButton)

$openResultsButton = New-Object System.Windows.Forms.Button
$openResultsButton.Text = 'Sonuçlar'
$openResultsButton.Size = New-Object System.Drawing.Size(100, 30)
$openResultsButton.Location = New-Object System.Drawing.Point(1290, 18)
$form.Controls.Add($openResultsButton)

$grid = New-Object System.Windows.Forms.DataGridView
$grid.Location = New-Object System.Drawing.Point(15, 78)
$grid.Size = New-Object System.Drawing.Size(1400, 500)
$grid.Anchor = 'Top,Bottom,Left,Right'
$grid.BackgroundColor = [System.Drawing.Color]::White
$grid.BorderStyle = 'FixedSingle'
$grid.AutoSizeColumnsMode = 'Fill'
$grid.AllowUserToAddRows = $false
$grid.AllowUserToDeleteRows = $false
$grid.ReadOnly = $true
$grid.RowHeadersVisible = $false
$grid.SelectionMode = 'FullRowSelect'
$grid.ColumnHeadersDefaultCellStyle.BackColor = [System.Drawing.Color]::WhiteSmoke
$grid.EnableHeadersVisualStyles = $false
$form.Controls.Add($grid)

$hint = New-Object System.Windows.Forms.Label
$hint.Text = 'Otomatik yenileme: 30 sn. Bu panel yalnızca tanımlı iş kayıtlarını okur; rastgele sistem taraması yapmaz.'
$hint.AutoSize = $true
$hint.Location = New-Object System.Drawing.Point(18, 590)
$hint.BackColor = [System.Drawing.Color]::White
$form.Controls.Add($hint)

function Refresh-Grid {
    try {
        $rows = Build-Rows
        $grid.DataSource = $null
        $grid.DataSource = [System.Collections.ArrayList]$rows
        $statusLabel.Text = 'Son güncelleme: ' + (Get-Date).ToString('yyyy-MM-dd HH:mm:ss') + ' | İş sayısı: ' + $rows.Count
        foreach ($row in $grid.Rows) {
            $durum = [string]$row.Cells['Durum'].Value
            if ($durum -eq 'Çalışıyor') { $row.DefaultCellStyle.BackColor = [System.Drawing.Color]::Honeydew }
            elseif ($durum -eq 'Hata/Blokaj') { $row.DefaultCellStyle.BackColor = [System.Drawing.Color]::MistyRose }
            elseif ($durum -eq 'Bitti') { $row.DefaultCellStyle.BackColor = [System.Drawing.Color]::AliceBlue }
            elseif ($durum -eq 'Kuyrukta' -or $durum -eq 'Pickup bekliyor') { $row.DefaultCellStyle.BackColor = [System.Drawing.Color]::LemonChiffon }
            else { $row.DefaultCellStyle.BackColor = [System.Drawing.Color]::White }
        }
    } catch {
        $statusLabel.Text = 'Panel hatası: ' + $_.Exception.Message
    }
}

$refreshButton.Add_Click({ Refresh-Grid })
$openResultsButton.Add_Click({ Start-Process (Join-Path $BridgeRoot 'ai-results') })

$timer = New-Object System.Windows.Forms.Timer
$timer.Interval = $RefreshSeconds * 1000
$timer.Add_Tick({ Refresh-Grid })
$timer.Start()

$form.Add_Shown({ Refresh-Grid })
[void]$form.ShowDialog()
