$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.IO.Compression.FileSystem
Add-Type -AssemblyName System.IO.Compression

$src = "D:\isac\tmp\_final_snap.docx"
$out = "D:\isac\paper\开题报告_v3_终稿_可提交.docx"

$zip = [System.IO.Compression.ZipFile]::OpenRead($src)
$de = $zip.Entries | Where-Object { $_.FullName -eq 'word/document.xml' }
$sr = New-Object System.IO.StreamReader($de.Open()); $doc = $sr.ReadToEnd(); $sr.Close()
$ce = $zip.Entries | Where-Object { $_.FullName -eq 'word/comments.xml' }
$sr2 = New-Object System.IO.StreamReader($ce.Open()); $cmts = $sr2.ReadToEnd(); $sr2.Close()
$zip.Dispose()

$edits = @(
  @{ anchor = '研究内容 1：强编码 ISAC 链路上实时视频传输的跨层优化（已基本完成，收尾整理中）'
     old = '研究内容 1：强编码 ISAC 链路上实时视频传输的跨层优化（已基本完成，收尾整理中）'
     new = '研究内容 1：强编码 ISAC 链路上实时视频传输的跨层优化（部分完成：容器、时延、调制已完成，外码部分重测中）'
     note = '【状态更正】"已基本完成"会与后文"外码结论撤回"直接冲突，改为分项说明完成度。这是评审最先看到的一行，必须与正文一致。' }

  @{ anchor = '需特别指出：内码译码器既不返回收敛标志'
     old = '需特别指出：内码译码器既不返回收敛标志、也无逐码字校验，其误纠对上层是静默的——RS 译码器的伴随式因此是本链路唯一的在带内残差判据，兼具检测与纠错双重职能。这也是本研究必须在平台上引入外码（而非仅依赖强内码）的根本技术理由。'
     new = '需特别指出：内码译码器既不返回收敛标志、也无逐码字校验，其误纠对上层是静默的。因此设计上需要一个在带内的残差判据——RS 译码器的伴随式正好兼具检测与纠错双重职能，这也是本研究必须在平台上引入外码（而非仅依赖强内码）的根本技术理由；该判据的实现目前正在修正（见补充说明）。'
     note = '【表述修正】原句断言"RS 伴随式是本链路唯一的在带内残差判据"，但该判据的实现正是本次发现缺陷之处，现状下并不存在。改为"设计上需要…正好承担"，并注明实现待修正，避免把设计意图说成既成事实。' }

  @{ anchor = '完成小论文定稿与投稿；启动 RS 外码可重构化改造'
     old = '完成小论文定稿与投稿；启动 RS 外码可重构化改造'
     new = '完成外码实现替换与单元自检；完成小论文定稿与投稿；启动 RS 外码可重构化改造'
     note = '【计划补充】重测以"实现可用"为前提，必须先把替换与自检写进时间线，否则 2026.09–12 的任务无法落地。' }

  @{ anchor = '论文成果：基于研究点 1 的英文论文初稿已完成撰写'
     old = '论文成果：基于研究点 1 的英文论文初稿已完成撰写（《Least-Sufficient Protection: A Cross-Layer Experimental Study of Real-Time Video Transmission over an Open OFDM-ISAC Platform》，拟投 IEEE 系列期刊）。'
     new = '论文成果：基于研究点 1 的英文论文初稿已完成（《Least-Sufficient Protection: A Cross-Layer Experimental Study of Real-Time Video Transmission over an Open OFDM-ISAC Platform》）；因第三章外码结论撤回，拟按重测结果重写后投稿。'
     note = '【状态更正】"已完成撰写、拟投"与"结论撤回"矛盾。改为"初稿已完成、待重测后重写投稿"，与当前真实进度一致。' }

  @{ anchor = '英文期刊/会议论文 1–2 篇（研究点 1 论文已完成撰写'
     old = '英文期刊/会议论文 1–2 篇（研究点 1 论文已完成撰写；研究点 2 或 3 视结果产出第二篇）；'
     new = '英文期刊/会议论文 1–2 篇（研究点 1 初稿已完成、待重测后重写投稿；研究点 2 或 3 视结果产出第二篇）；'
     note = '' }

  @{ anchor = 'RS(255,K) 外码（自主实现）级联 LDPC(1008,504) 内码'
     old = 'RS(255,K) 外码（自主实现）级联 LDPC(1008,504) 内码'
     new = 'RS(255,K) 外码（自主实现，当前实现待替换）级联 LDPC(1008,504) 内码'
     note = '' }

  @{ anchor = '1. RS 外码参数的可重构化：'
     old = '1. RS 外码参数的可重构化：'
     new = '1. RS 外码参数的可重构化（前置条件：先完成编解码器替换与单元自检）：'
     note = '' }
)

$newComments = New-Object System.Collections.ArrayList
$cid = 400
foreach ($ed in $edits) {
    $i = $doc.IndexOf($ed.anchor)
    if ($i -lt 0) { Write-Host "MISS: $($ed.anchor)"; continue }
    $tOpen = $doc.LastIndexOf('<w:t', $i)
    $tGt = $doc.IndexOf('>', $tOpen)
    $tClose = $doc.IndexOf('</w:t>', $i)
    $inner = $doc.Substring($tGt + 1, $tClose - $tGt - 1)
    if (-not $inner.Contains($ed.old)) { Write-Host "NOT-IN-WT: $($ed.anchor)"; continue }
    $newInner = $inner.Replace($ed.old, $ed.new)
    $rOpen = $doc.LastIndexOf('<w:r>', $tOpen)
    if ($rOpen -lt 0) { $rOpen = $doc.LastIndexOf('<w:r ', $tOpen) }
    $rClose = $doc.IndexOf('</w:r>', $tClose) + 6
    $run = $doc.Substring($rOpen, $rClose - $rOpen)
    $mm = [regex]::Match($run, '<w:rPr>.*?</w:rPr>', 'Singleline')
    $rpr = if ($mm.Success) { $mm.Value } else { '' }
    if ($ed.note -ne '') {
        $id = $cid; $cid++
        $repl = "<w:commentRangeStart w:id=`"$id`"/><w:r>$rpr<w:t xml:space=`"preserve`">$newInner</w:t></w:r><w:commentRangeEnd w:id=`"$id`"/><w:r><w:commentReference w:id=`"$id`"/></w:r>"
        [void]$newComments.Add(@{ id = $id; text = $ed.note })
    } else {
        $repl = "<w:r>$rpr<w:t xml:space=`"preserve`">$newInner</w:t></w:r>"
    }
    $doc = $doc.Substring(0, $rOpen) + $repl + $doc.Substring($rClose)
    Write-Host "OK: $($ed.anchor.Substring(0, [Math]::Min(24, $ed.anchor.Length)))"
}

$sb = New-Object System.Text.StringBuilder
foreach ($c in $newComments) {
    [void]$sb.Append("<w:comment w:id=`"$($c.id)`" w:author=`"修订说明`" w:date=`"2026-10-19T21:10:00Z`" w:initials=`"修`"><w:p><w:r><w:t xml:space=`"preserve`">$($c.text)</w:t></w:r></w:p></w:comment>")
}
$cmts = $cmts.Replace('</w:comments>', $sb.ToString() + '</w:comments>')

try { [xml]$null = $doc; Write-Host "document.xml 良构: True" } catch { Write-Host "XML 错误" }
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

