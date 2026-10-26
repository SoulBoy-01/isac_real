$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.IO.Compression.FileSystem
Add-Type -AssemblyName System.IO.Compression

$src = 'D:\isac\paper\开题报告_v3_终稿.docx'
$out = 'D:\isac\paper\开题报告_v4_终稿.docx'

$zip = [System.IO.Compression.ZipFile]::OpenRead($src)
$de = $zip.Entries | Where-Object { $_.FullName -eq 'word/document.xml' }
$sr = New-Object System.IO.StreamReader($de.Open()); $doc = $sr.ReadToEnd(); $sr.Close()
$ce = $zip.Entries | Where-Object { $_.FullName -eq 'word/comments.xml' }
$sr2 = New-Object System.IO.StreamReader($ce.Open()); $cmts = $sr2.ReadToEnd(); $sr2.Close()
$zip.Dispose()

$new28 = '[28] XUE W, WANG R, LIU L, WU D. Accurate multi-target vital signs detection method for FMCW radar[J]. Measurement, 2023, 223: 113715. DOI: 10.1016/j.measurement.2023.113715.'
$new29 = '[29] XUE X, PARKAR S, YU S, ZHENG Y. AI-assisted composite ISAC for mmWave respiration pattern recognition[C]//2025 IEEE Annual Congress on Artificial Intelligence of Things (AIoT). 2025: 357-364. DOI: 10.1109/AIoT66900.2025.00059.'

$note28 = '[已替换] 原条目 WANG P 等、Multi-target vital signs detection using millimeter-wave FMCW radar、IEEE TIM 2024, 73: 1-13 无法核实：其 DOI（10.1109/TIM.2023.3334360）在 Crossref 中指向另一篇不相干论文，按标题也检不到该文。已换为同一主题、DOI 可核验的真实文献（Measurement, 2023, 223: 113715）。'
$note29 = '[已更正] 标题真实但著录信息有误：该文实为 2025 IEEE AIoT 会议论文（页码 357-364），作者为 Xue X、Parkar S、Yu S、Zheng Y，并非原条目所写的 WANG Y、ZHOU S、NIU Z 与 IEEE TWC 2025, 24(3): 1820-1835。已按 Crossref 记录更正。'
$noteDel = '[已删除] 原 [30]（arXiv:2603.08421）与 [31]（电子与信息学报 2025, 47(2)）存在两个问题：一是正文从未引用，不符合顺序编码制；二是 [30] 的正确 arXiv 号为 2606.22195，[31] 检索不到对应文献。二者一并删除，文献总数由 31 条调整为 29 条，仍满足不少于 20 篇的要求。'

function Add-Comment($xmlText, $id, $note) {
    $frag = '<w:comment w:id="' + $id + '" w:author="修订说明" w:date="2026-10-19T21:40:00Z" w:initials="修"><w:p><w:r><w:t xml:space="preserve">' + $note + '</w:t></w:r></w:p></w:comment>'
    return $xmlText.Replace('</w:comments>', $frag + '</w:comments>')
}

$items = @(
    @{ anchor = '[28] WANG P'; text = $new28; note = $note28; id = 600 },
    @{ anchor = '[29] WANG Y'; text = $new29; note = $note29; id = 601 }
)

foreach ($it in $items) {
    $idx = $doc.IndexOf($it.anchor)
    if ($idx -lt 0) { Write-Host ('MISS ' + $it.anchor); continue }
    $pStart = $doc.LastIndexOf('<w:p ', $idx); if ($pStart -lt 0) { $pStart = $doc.LastIndexOf('<w:p>', $idx) }
    $pEnd = $doc.IndexOf('</w:p>', $idx) + 6
    $para = $doc.Substring($pStart, $pEnd - $pStart)
    $pPrM = [regex]::Match($para, '<w:pPr>.*?</w:pPr>', 'Singleline')
    $pPr = ''
    if ($pPrM.Success) { $pPr = $pPrM.Value }
    $runM = [regex]::Match($para, '<w:r>.*?</w:r>', 'Singleline')
    $rPr = ''
    if ($runM.Success) {
        $rPrM = [regex]::Match($runM.Value, '<w:rPr>.*?</w:rPr>', 'Singleline')
        if ($rPrM.Success) { $rPr = $rPrM.Value }
    }
    $body = '<w:commentRangeStart w:id="' + $it.id + '"/><w:r>' + $rPr + '<w:t xml:space="preserve">' + $it.text + '</w:t></w:r><w:commentRangeEnd w:id="' + $it.id + '"/><w:r><w:commentReference w:id="' + $it.id + '"/></w:r>'
    $doc = $doc.Substring(0, $pStart) + ('<w:p>' + $pPr + $body + '</w:p>') + $doc.Substring($pEnd)
    $cmts = Add-Comment $cmts $it.id $it.note
    Write-Host ('OK replace ' + $it.anchor)
}

foreach ($a in @('[30] ZHOU T', '[31] 李晓柏')) {
    $idx = $doc.IndexOf($a)
    if ($idx -lt 0) { Write-Host ('MISS delete ' + $a); continue }
    $pStart = $doc.LastIndexOf('<w:p ', $idx); if ($pStart -lt 0) { $pStart = $doc.LastIndexOf('<w:p>', $idx) }
    $pEnd = $doc.IndexOf('</w:p>', $idx) + 6
    $doc = $doc.Substring(0, $pStart) + $doc.Substring($pEnd)
    Write-Host ('OK delete ' + $a)
}
$cmts = Add-Comment $cmts 610 $noteDel

try { [xml]$null = $doc; Write-Host 'document.xml OK' } catch { Write-Host ('XML ERROR ' + $_.Exception.Message) }
try { [xml]$null = $cmts; Write-Host 'comments.xml OK' } catch { Write-Host 'comments XML ERROR' }

if (Test-Path $out) { Remove-Item $out -Force }
$zin = [System.IO.Compression.ZipFile]::OpenRead($src)
$fs = [System.IO.File]::Open($out, [System.IO.FileMode]::CreateNew)
$zout = New-Object System.IO.Compression.ZipArchive($fs, [System.IO.Compression.ZipArchiveMode]::Create)
foreach ($entry in $zin.Entries) {
    $ne = $zout.CreateEntry($entry.FullName, [System.IO.Compression.CompressionLevel]::Optimal)
    $os = $ne.Open()
    if ($entry.FullName -eq 'word/document.xml') {
        $b = [System.Text.Encoding]::UTF8.GetBytes($doc); $os.Write($b, 0, $b.Length); $os.Close()
    } elseif ($entry.FullName -eq 'word/comments.xml') {
        $b = [System.Text.Encoding]::UTF8.GetBytes($cmts); $os.Write($b, 0, $b.Length); $os.Close()
    } else {
        $is = $entry.Open(); $is.CopyTo($os); $is.Close(); $os.Close()
    }
}
$zout.Dispose(); $fs.Close(); $zin.Dispose()
Write-Host ('OUT ' + $out + '  ' + (Get-Item $out).Length + ' bytes')
