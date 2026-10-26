$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.IO.Compression.FileSystem
Add-Type -AssemblyName System.IO.Compression

$src = "D:\isac\paper\开题报告_v3_终稿_可提交.docx"
$out = "D:\isac\paper\开题报告_v3_终稿_可提交_v2.docx"

$zip = [System.IO.Compression.ZipFile]::OpenRead($src)
$de = $zip.Entries | Where-Object { $_.FullName -eq 'word/document.xml' }
$sr = New-Object System.IO.StreamReader($de.Open()); $doc = $sr.ReadToEnd(); $sr.Close()
$ce = $zip.Entries | Where-Object { $_.FullName -eq 'word/comments.xml' }
$sr2 = New-Object System.IO.StreamReader($ce.Open()); $cmts = $sr2.ReadToEnd(); $sr2.Close()
$zip.Dispose()

$edits = @(
  @{ anchor = '论文成果：'
     old = '已完成撰写（《Least-Sufficient Protection'
     new = '已完成（《Least-Sufficient Protection'
     note = '' },
  @{ anchor = '拟投 IEEE 系列期刊）。'
     old = '拟投 IEEE 系列期刊）。'
     new = '；因第三章外码结论撤回，拟按重测结果重写后投稿。'
     note = '【状态更正】"已完成撰写、拟投"与"结论撤回"矛盾，改为"初稿已完成、待重测后重写投稿"。' },
  @{ anchor = 'RS 外码参数的可重构化：'
     old = 'RS 外码参数的可重构化：将当前以编译期常量固定'
     new = 'RS 外码参数的可重构化（前置条件：先完成编解码器替换与单元自检）：将当前以编译期常量固定'
     note = '' }
)

$cid = 500
$added = New-Object System.Collections.ArrayList

foreach ($ed in $edits) {
    $idx = $doc.IndexOf($ed.anchor)
    if ($idx -lt 0) { Write-Host "MISS-ANCHOR: $($ed.anchor)"; continue }
    $pStart = $doc.LastIndexOf('<w:p ', $idx)
    if ($pStart -lt 0) { $pStart = $doc.LastIndexOf('<w:p>', $idx) }
    $pEnd = $doc.IndexOf('</w:p>', $idx) + 6
    $para = $doc.Substring($pStart, $pEnd - $pStart)

    # 段落纯文本
    $texts = [regex]::Matches($para, '<w:t[^>]*>(.*?)</w:t>', 'Singleline')
    $plain = ($texts | ForEach-Object { $_.Groups[1].Value }) -join ''
    if (-not $plain.Contains($ed.old)) { Write-Host "MISS-TEXT: $($ed.anchor)"; continue }
    $newPlain = $plain.Replace($ed.old, $ed.new)

    $pPrM = [regex]::Match($para, '<w:pPr>.*?</w:pPr>', 'Singleline')
    $pPr = if ($pPrM.Success) { $pPrM.Value } else { '' }
    $rPrM = [regex]::Match($para, '<w:rPr>.*?</w:rPr>', 'Singleline')
    $rPr = if ($rPrM.Success) { $rPrM.Value } else { '' }

    if ($ed.note -ne '') {
        $id = $cid; $cid++
        $body = "<w:commentRangeStart w:id=`"$id`"/><w:r>$rPr<w:t xml:space=`"preserve`">$newPlain</w:t></w:r><w:commentRangeEnd w:id=`"$id`"/><w:r><w:commentReference w:id=`"$id`"/></w:r>"
        [void]$added.Add(@{ id = $id; text = $ed.note })
    } else {
        $body = "<w:r>$rPr<w:t xml:space=`"preserve`">$newPlain</w:t></w:r>"
    }
    $newPara = "<w:p>$pPr$body</w:p>"
    $doc = $doc.Substring(0, $pStart) + $newPara + $doc.Substring($pEnd)
    Write-Host "OK: $($ed.anchor)"
}

$sb = New-Object System.Text.StringBuilder
foreach ($c in $added) {
    [void]$sb.Append("<w:comment w:id=`"$($c.id)`" w:author=`"修订说明`" w:date=`"2026-10-19T21:20:00Z`" w:initials=`"修`"><w:p><w:r><w:t xml:space=`"preserve`">$($c.text)</w:t></w:r></w:p></w:comment>")
}
$cmts = $cmts.Replace('</w:comments>', $sb.ToString() + '</w:comments>')

try { [xml]$null = $doc; Write-Host "document.xml 良构: True" } catch { Write-Host "XML 错误: $($_.Exception.Message)" }

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
Write-Host "输出: $out  大小: $((Get-Item $out).Length)"
