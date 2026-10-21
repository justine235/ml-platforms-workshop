<#
.SYNOPSIS
  One-shot check of a content module: build, lint, PowerPoint QA, render, contact sheets, text dump.
.EXAMPLE
  powershell -NoProfile -ExecutionPolicy Bypass -File .\check.ps1 content_p2
#>
param(
    [Parameter(Mandatory = $true)][string]$Module,
    [int]$Cols = 2,
    [int]$Rows = 3
)
$ErrorActionPreference = "Continue"
Set-Location $PSScriptRoot

$dir = Join-Path $PSScriptRoot "out\dev\$Module"
$pptx = Join-Path $dir "$Module.pptx"
if (Test-Path $pptx) { Remove-Item $pptx -Force }

# devbuild exits 1 on lint warnings or problems but still saves the deck, so keep going to see the slides.
python devbuild.py $Module
$buildRc = $LASTEXITCODE
if (-not (Test-Path $pptx)) { Write-Host "BUILD FAILED: no pptx was produced (see the error above)"; exit 1 }

$render = Join-Path $dir "render"
if (Test-Path $render) { Remove-Item $render -Recurse -Force }
Get-ChildItem $dir -Filter "sheet_*.png" -ErrorAction SilentlyContinue | Remove-Item -Force

Write-Host "--- PowerPoint QA"
& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "qa_deck.ps1") -Pptx $pptx -OutJson (Join-Path $dir "qa.json")

Write-Host "--- Render"
& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "render_deck.ps1") -Pptx $pptx -OutDir $render

Write-Host "--- Contact sheets"
python contact_sheet.py $render (Join-Path $dir "sheet") --cols $Cols --rows $Rows

Write-Host "--- Text dump"
python dump_text.py $pptx (Join-Path $dir "text.md")

Write-Host ""
Write-Host "Outputs in $dir : sheet_NN.png (overview), render\s###.png (one slide each), text.md, slide-index.md, qa.json"
if ($buildRc -ne 0) { Write-Host "RESULT: NOT CLEAN - fix the LINT / PROBLEM lines printed by devbuild above, then run again."; exit 1 }
Write-Host "RESULT: build is clean (also confirm 'Checked N slides: 0 issue(s)' above and look at the sheets)."
