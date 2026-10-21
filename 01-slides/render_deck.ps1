<#
.SYNOPSIS
  Export every slide of a PPTX to PNG (s001.png, s002.png, ...) with PowerPoint (COM).
  Opens the file read-only and windowless; never touches other open presentations.
  A machine-wide mutex serialises concurrent callers (several agents may render at once).
.EXAMPLE
  .\render_deck.ps1 -Pptx .\ml-platforms-workshop.pptx -OutDir .\out\render
#>
param(
  [Parameter(Mandatory = $true)][string]$Pptx,
  [Parameter(Mandatory = $true)][string]$OutDir,
  [int]$Width = 1600
)
$ErrorActionPreference = 'Stop'
$pptxPath = (Resolve-Path $Pptx).Path
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$outPath = (Resolve-Path $OutDir).Path
Get-ChildItem $outPath -Filter '*.PNG' -ErrorAction SilentlyContinue | Remove-Item -Force

$mutex = New-Object System.Threading.Mutex($false, 'Global\ml-workshop-ppt-com')
$locked = $false
try {
  try { $locked = $mutex.WaitOne([TimeSpan]::FromMinutes(10)) } catch [System.Threading.AbandonedMutexException] { $locked = $true }
  if (-not $locked) { throw 'Timed out waiting for the PowerPoint COM mutex' }
  $ppt = New-Object -ComObject PowerPoint.Application
  $pres = $null
  try {
    # ReadOnly = true, Untitled = false, WithWindow = false
    $pres = $ppt.Presentations.Open($pptxPath, -1, 0, 0)
    $h = [int]($Width * 9 / 16)
    $count = $pres.Slides.Count
    $pres.Export($outPath, 'PNG', $Width, $h)
  }
  finally {
    if ($pres) { $pres.Close() }
  }
}
finally {
  if ($locked) { $mutex.ReleaseMutex() }
  $mutex.Dispose()
}

# PowerPoint names files after the UI language (Slide1.PNG / Diapositive1.PNG): normalise to s001.png
Get-ChildItem $outPath -Filter '*.PNG' | ForEach-Object {
  $num = [int]([regex]::Match($_.BaseName, '(\d+)$').Groups[1].Value)
  Rename-Item -LiteralPath $_.FullName -NewName ('s{0:000}.tmp' -f $num)
}
Get-ChildItem $outPath -Filter 's*.tmp' | ForEach-Object { Rename-Item -LiteralPath $_.FullName -NewName ($_.BaseName + '.png') }
Write-Output ("Exported {0} slides to {1}" -f $count, $outPath)
