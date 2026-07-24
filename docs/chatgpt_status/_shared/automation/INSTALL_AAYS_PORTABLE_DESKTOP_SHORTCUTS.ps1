[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

function Find-PortableRoot {
    $candidate = [System.IO.Path]::GetFullPath($PSScriptRoot)
    if ($candidate.Length -gt [System.IO.Path]::GetPathRoot($candidate).Length) {
        $candidate = $candidate.TrimEnd("\")
    }
    for ($i = 0; $i -lt 10; $i++) {
        if (Test-Path -LiteralPath (Join-Path $candidate ".aays_portable_identity.json") -PathType Leaf) {
            return $candidate
        }
        $parent = Split-Path -Parent $candidate
        if ([string]::IsNullOrWhiteSpace($parent) -or $parent -eq $candidate) { break }
        $candidate = $parent
    }
    throw "AAYS_PORTABLE_ROOT_NOT_FOUND"
}

$root = Find-PortableRoot
$desktop = [Environment]::GetFolderPath("Desktop")
if ([string]::IsNullOrWhiteSpace($desktop)) { throw "WINDOWS_DESKTOP_NOT_FOUND" }

$startCmd = Join-Path $root "BASKA_BILGISAYARDA_AAYS_BASLAT.cmd"
$panelCmd = Join-Path $root "AAYS_PORTABLE_CONTROL_PANEL.cmd"
$runner = Join-Path $root "RUN_AAYS_ADAPTIVE_21_SLOT.ps1"
$systemPowerShell = Join-Path $env:SystemRoot "System32\WindowsPowerShell\v1.0\powershell.exe"
foreach ($required in @($startCmd, $panelCmd, $runner, $systemPowerShell)) {
    if (-not (Test-Path -LiteralPath $required -PathType Leaf)) { throw "REQUIRED_FILE_MISSING: $required" }
}

$shell = New-Object -ComObject WScript.Shell
$definitions = @(
    [ordered]@{
        Name = "AAYS TerraYield - Uygulama Runner Panel.lnk"
        Target = $startCmd
        Arguments = ""
        Icon = "$env:SystemRoot\System32\shell32.dll,137"
    },
    [ordered]@{
        Name = "AAYS TerraYield - Kontrol Paneli.lnk"
        Target = $panelCmd
        Arguments = ""
        Icon = "$env:SystemRoot\System32\shell32.dll,21"
    },
    [ordered]@{
        Name = "AAYS TerraYield - Runner Durdur.lnk"
        Target = $systemPowerShell
        Arguments = ('-NoProfile -ExecutionPolicy Bypass -File "{0}" -Action Stop' -f $runner)
        Icon = "$env:SystemRoot\System32\shell32.dll,28"
    }
)

$created = @()
foreach ($definition in $definitions) {
    $path = Join-Path $desktop $definition.Name
    $shortcut = $shell.CreateShortcut($path)
    $shortcut.TargetPath = $definition.Target
    $shortcut.Arguments = $definition.Arguments
    $shortcut.WorkingDirectory = $root
    $shortcut.IconLocation = $definition.Icon
    $shortcut.Description = "AAYS TerraYield portable - disk yolu bu bilgisayar icin kuruldu"
    $shortcut.Save()
    $created += $path
}

$proof = [ordered]@{
    schema_version = 1
    status = "PASS"
    portable_root = $root
    detected_drive = [System.IO.Path]::GetPathRoot($root)
    desktop = $desktop
    shortcuts = $created
    shortcut_count = $created.Count
    installed_at = [DateTime]::UtcNow.ToString("o")
    final_ready = $false
}
$proofPath = Join-Path $root "state\portable_desktop_shortcuts_latest.json"
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $proofPath) | Out-Null
[System.IO.File]::WriteAllText($proofPath, (($proof | ConvertTo-Json -Depth 8) + "`n"), (New-Object System.Text.UTF8Encoding($false)))
$proof | ConvertTo-Json -Depth 8
