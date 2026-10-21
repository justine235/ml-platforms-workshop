<#
.SYNOPSIS
  Layout QA through PowerPoint's real layout engine: text overflow, out-of-bounds shapes,
  footer intrusion and overlapping text. Writes a JSON report and prints a summary.
  Opens the file read-only and windowless. A machine-wide mutex serialises concurrent callers.
.EXAMPLE
  .\qa_deck.ps1 -Pptx .\ml-platforms-workshop.pptx -OutJson .\out\qa-report.json
#>
param(
  [Parameter(Mandatory = $true)][string]$Pptx,
  [string]$OutJson = '',
  [double]$BodyBottomIn = 6.93
)
$ErrorActionPreference = 'Stop'
$pptxPath = (Resolve-Path $Pptx).Path
$issues = New-Object System.Collections.Generic.List[object]
function Add-Issue($slide, $shape, $kind, $detail) {
  $issues.Add([pscustomobject]@{ slide = $slide; shape = $shape; kind = $kind; detail = $detail }) | Out-Null
}

$mutex = New-Object System.Threading.Mutex($false, 'Global\ml-workshop-ppt-com')
$locked = $false
$count = 0
try {
  try { $locked = $mutex.WaitOne([TimeSpan]::FromMinutes(10)) } catch [System.Threading.AbandonedMutexException] { $locked = $true }
  if (-not $locked) { throw 'Timed out waiting for the PowerPoint COM mutex' }
  $ppt = New-Object -ComObject PowerPoint.Application
  $pres = $null
  try {
    $pres = $ppt.Presentations.Open($pptxPath, -1, 0, 0)
    $slideW = $pres.PageSetup.SlideWidth
    $slideH = $pres.PageSetup.SlideHeight
    $bodyBottom = $BodyBottomIn * 72
    foreach ($s in $pres.Slides) {
      $n = $s.SlideIndex
      $boxes = New-Object System.Collections.Generic.List[object]
      $badges = New-Object System.Collections.Generic.List[object]
      $texts = New-Object System.Collections.Generic.List[object]
      foreach ($sh in $s.Shapes) {
        $name = $sh.Name
        if ($sh.Left -lt -1 -or $sh.Top -lt -1 -or ($sh.Left + $sh.Width) -gt ($slideW + 1) -or ($sh.Top + $sh.Height) -gt ($slideH + 1)) {
          Add-Issue $n $name 'out-of-bounds' ("L{0:N0} T{1:N0} W{2:N0} H{3:N0}" -f $sh.Left, $sh.Top, $sh.Width, $sh.Height)
        }
        $isFooter = ($name -like 'footer*') -or ($name -like 'bleed*')
        $isBadge = ($name -like 'badge*')
        if (-not $isFooter -and ($sh.Top + $sh.Height) -gt $bodyBottom -and $sh.Type -ne 14) {
          Add-Issue $n $name 'intrudes-footer' ("bottom {0:N2} in" -f (($sh.Top + $sh.Height) / 72))
        }
        if ($isBadge) {
          $badges.Add([pscustomobject]@{ name = $name; l = $sh.Left; t = $sh.Top; r = $sh.Left + $sh.Width; b = $sh.Top + $sh.Height }) | Out-Null
        }
        if ($sh.HasTextFrame -eq -1 -and $sh.TextFrame2.HasText -eq -1) {
          $tf = $sh.TextFrame2
          $tr = $tf.TextRange
          $availH = $sh.Height - $tf.MarginTop - $tf.MarginBottom
          $availW = $sh.Width - $tf.MarginLeft - $tf.MarginRight
          if ($tr.BoundHeight -gt ($availH + 1.5)) {
            Add-Issue $n $name 'text-overflow' ("text {0:N1} pt > box {1:N1} pt" -f $tr.BoundHeight, $availH)
          }
          if ($tr.BoundWidth -gt ($availW + 1.5)) {
            Add-Issue $n $name 'text-too-wide' ("text {0:N1} pt > box {1:N1} pt" -f $tr.BoundWidth, $availW)
          }
          if (-not $isFooter -and -not $isBadge) {
            $rec = [pscustomobject]@{ name = $name; sh = $sh; l = $tr.BoundLeft; t = $tr.BoundTop; r = $tr.BoundLeft + $tr.BoundWidth; b = $tr.BoundTop + $tr.BoundHeight }
            $boxes.Add($rec) | Out-Null
          }
        }
        if ($sh.HasTable -eq -1) {
          if (($sh.Top + $sh.Height) -gt $bodyBottom) {
            Add-Issue $n $name 'table-too-tall' ("bottom {0:N2} in" -f (($sh.Top + $sh.Height) / 72))
          }
        }
      }
      # text vs text (whole text block bounds)
      for ($i = 0; $i -lt $boxes.Count; $i++) {
        for ($j = $i + 1; $j -lt $boxes.Count; $j++) {
          $a = $boxes[$i]; $b = $boxes[$j]
          $w = [Math]::Min($a.r, $b.r) - [Math]::Max($a.l, $b.l)
          $h = [Math]::Min($a.b, $b.b) - [Math]::Max($a.t, $b.t)
          if ($w -gt 2 -and $h -gt 2) {
            Add-Issue $n ($a.name + ' x ' + $b.name) 'text-overlap' ("{0:N0} x {1:N0} pt" -f $w, $h)
          }
        }
      }
      # number badges sit over an indented title line: compare paragraph by paragraph
      foreach ($bd in $badges) {
        foreach ($bx in $boxes) {
          $w0 = [Math]::Min($bd.r, $bx.r) - [Math]::Max($bd.l, $bx.l)
          $h0 = [Math]::Min($bd.b, $bx.b) - [Math]::Max($bd.t, $bx.t)
          if ($w0 -le 2 -or $h0 -le 2) { continue }
          $tr = $bx.sh.TextFrame2.TextRange
          $np = ($tr.Text -split "`r").Count
          for ($k = 1; $k -le $np; $k++) {
            $p = $tr.Paragraphs($k)
            $pw = [Math]::Min($bd.r, $p.BoundLeft + $p.BoundWidth) - [Math]::Max($bd.l, $p.BoundLeft)
            $ph = [Math]::Min($bd.b, $p.BoundTop + $p.BoundHeight) - [Math]::Max($bd.t, $p.BoundTop)
            if ($pw -gt 2 -and $ph -gt 2) {
              Add-Issue $n ($bd.name + ' x ' + $bx.name) 'badge-overlap' ("{0:N0} x {1:N0} pt (paragraph {2})" -f $pw, $ph, $k)
              break
            }
          }
        }
      }
    }
    $count = $pres.Slides.Count
  }
  finally {
    if ($pres) { $pres.Close() }
  }
}
finally {
  if ($locked) { $mutex.ReleaseMutex() }
  $mutex.Dispose()
}

if ($OutJson) {
  $dir = Split-Path -Parent $OutJson
  if ($dir) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
  $issues | ConvertTo-Json -Depth 4 | Set-Content -Path $OutJson -Encoding UTF8
}
Write-Output ("Checked {0} slides: {1} issue(s)" -f $count, $issues.Count)
$issues | Group-Object kind | ForEach-Object { Write-Output ("  {0}: {1}" -f $_.Name, $_.Count) }
$issues | Select-Object -First 80 | Format-Table slide, kind, shape, detail -AutoSize | Out-String -Width 220
