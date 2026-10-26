$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.IO.Compression.FileSystem
Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.Drawing

$snap = "D:\isac\tmp\_kaiti_snapshot.docx"
$out  = "D:\isac\paper\开题报告_v3_修订版_新图_带批注.docx"
$figDir = "D:\isac\paper\figures_report"

# 图 i -> 媒体文件 image(i+1).png
$figs = @(
  @{ media = 'word/media/image2.png'; png = 'fig1_topology.png' },
  @{ media = 'word/media/image3.png'; png = 'fig2_coding_framing.png' },
  @{ media = 'word/media/image4.png'; png = 'fig3_gamma.png' },
  @{ media = 'word/media/image5.png'; png = 'fig4_micromotion.png' },
  @{ media = 'word/media/image6.png'; png = 'fig5_roadmap.png' },
  @{ media = 'word/media/image7.png'; png = 'fig6_latency.png' }
)

# 读取现文档
$zip = [System.IO.Compression.ZipFile]::OpenRead($snap)
$de = $zip.Entries | Where-Object { $_.FullName -eq 'word/document.xml' }
$sr = New-Object System.IO.StreamReader($de.Open()); $doc = $sr.ReadToEnd(); $sr.Close()
$zip.Dispose()

# 旧尺寸（wp:extent / a:ext）
$oldWp = @(2688590, 2980055, 2583815, 3075305, 3133090, 2075815)
$oldA  = @(2689072, 2980198, 2584411, 3075432, 3133251, 2076097)
$cxWp = 5168265
$cxA  = 5168823

for ($i = 0; $i -lt $figs.Count; $i++) {
    $p = Join-Path $figDir $figs[$i].png
    $img = [System.Drawing.Image]::FromFile($p)
    $ratio = [double]$img.Height / [double]$img.Width
    $img.Dispose()
    $newWp = [int][Math]::Round($cxWp * $ratio)
    $newA  = [int][Math]::Round($cxA * $ratio)
    $doc = $doc.Replace("<wp:extent cx=`"$cxWp`" cy=`"$($oldWp[$i])`"/>", "<wp:extent cx=`"$cxWp`" cy=`"$newWp`"/>")
    $doc = $doc.Replace("<a:ext cx=`"$cxA`" cy=`"$($oldA[$i])`"/>", "<a:ext cx=`"$cxA`" cy=`"$newA`"/>")
    Write-Host ("  {0}: ratio={1:N4}  wp.cy {2} -> {3}" -f $figs[$i].png, $ratio, $oldWp[$i], $newWp)
}

try { [xml]$null = $doc; $ok = $true } catch { $ok = $false; Write-Host "XML 错误: $($_.Exception.Message)" }
Write-Host "document.xml 良构: $ok"

if (Test-Path $out) { Remove-Item $out -Force }
$zin = [System.IO.Compression.ZipFile]::OpenRead($snap)
$fs = [System.IO.File]::Open($out, [System.IO.FileMode]::CreateNew)
$zout = New-Object System.IO.Compression.ZipArchive($fs, [System.IO.Compression.ZipArchiveMode]::Create)
foreach ($entry in $zin.Entries) {
    $name = $entry.FullName
    $ne = $zout.CreateEntry($name, [System.IO.Compression.CompressionLevel]::Optimal)
    $os = $ne.Open()
    if ($name -eq 'word/document.xml') {
        $b = [System.Text.Encoding]::UTF8.GetBytes($doc); $os.Write($b, 0, $b.Length); $os.Close()
    }
    elseif ($figs.media -contains $name) {
        $src = ($figs | Where-Object { $_.media -eq $name }).png
        $b = [System.IO.File]::ReadAllBytes((Join-Path $figDir $src))
        $os.Write($b, 0, $b.Length); $os.Close()
    }
    else {
        $is = $entry.Open(); $is.CopyTo($os); $is.Close(); $os.Close()
    }
}
$zout.Dispose(); $fs.Close(); $zin.Dispose()

Write-Host "输出: $out  大小: $((Get-Item $out).Length)"
