$roots = @(
  "C:\Users\cagda\Documents\GitHub",
  "C:\Users\cagda\Documents\Codex",
  "C:\Users\cagda\Documents\AAYS_D_DRIVE_ARCHIVE"
)

$markers = @(
  "package.json",
  "vite.config.js",
  "vite.config.ts",
  "next.config.js",
  "next.config.ts",
  "requirements.txt",
  "pyproject.toml",
  "app.py",
  "main.py"
)

$results = foreach ($root in $roots) {
  Get-ChildItem -Path $root -Recurse -File -Force -ErrorAction SilentlyContinue |
    Where-Object {
      $markers -contains $_.Name -and
      $_.FullName -notmatch "\\node_modules\\|\\node\\|\\.venv\\|\\.git\\|\\.cache\\|\\dist\\|\\build\\|\\__pycache__\\"
    } |
    ForEach-Object {
      [PSCustomObject]@{
        ProjectFolder = $_.DirectoryName
        MarkerFile = $_.Name
        FullName = $_.FullName
      }
    }
}

$results |
  Sort-Object ProjectFolder, MarkerFile -Unique |
  Format-Table -AutoSize | Out-String
