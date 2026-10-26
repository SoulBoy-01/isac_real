$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.IO.Compression.FileSystem
Add-Type -AssemblyName System.IO.Compression

$src = "D:\isac\paper\开题报告_v3_修订版_新图_带批注.docx"
$tmp = "D:\isac\tmp\_rebuild_caps.docx"

$zip = [System.IO.Compression.ZipFile]::OpenRead($src)
$de = $zip.Entries | Where-Object { $_.FullName -eq 'word/document.xml' }
$sr = New-Object System.IO.StreamReader($de.Open()); $doc = $sr.ReadToEnd(); $sr.Close()
$ce = $zip.Entries | Where-Object { $_.FullName -eq 'word/comments.xml' }
$sr2 = New-Object System.IO.StreamReader($ce.Open()); $cmts = $sr2.ReadToEnd(); $sr2.Close()
$zip.Dispose()

$edits = @(
  @{ anchor = '图 1　OpenISAC 平台上实时视频传输与雷达感知的系统拓扑'
     old = '图 1　OpenISAC 平台上实时视频传输与雷达感知的系统拓扑'
     new = '图 1　OpenISAC 平台上实时视频与雷达感知的系统拓扑：两条业务链共享同一 OFDM 波形'
     note = '' }
  @{ anchor = '图 2　级联纠错编码链路架构'
     old = '图 2　级联纠错编码链路架构：RS(255, K) 外码与 LDPC(1008, 504) 内码的级联编解码流程，虚线框内为残差判据点（RS 伴随式）'
     new = '图 2　级联编码与分帧路径：2 字节长度前缀位于外码码字内部，是分帧完整性的保护点；无外码时前缀裸露，单比特错误即可导致整条字节流错位'
     note = '【图题重写】原图把 RS 伴随式画成“残差判据点”，与修订后“外码实现存在缺陷、正在替换”的表述冲突。新图改为展示分帧元数据的位置与失效模式，与新增的“分帧完整性”子问题一致。' }
  @{ anchor = '图 3　容器误码放大因子'
     old = '图 3　容器误码放大因子 γ：模型预测与四种传输栈实测对比（RS 外码禁用压力测试）'
     new = '图 3　容器误码放大因子 γ：同一物理误码流下四种传输栈的实测对比（压力工况：关闭外码）'
     note = '【图题更正】“RS 外码禁用”改为“压力工况：关闭外码”，避免暗示外码此前在正常工作。' }
  @{ anchor = '图 4　非接触微动感知处理架构'
     old = '图 4　非接触微动感知处理架构：由目标距离门相位到呼吸/心跳参数估计的处理流程与灵敏度预算'
     new = '图 4　非接触微动感知处理架构与相位灵敏度预算：λ = 96.8 mm @ 3.1 GHz；呼吸 0.52–1.04 rad，心跳 0.026–0.065 rad'
     note = '' }
  @{ anchor = '图 5　技术路线总图'
     old = '图 5　技术路线总图：统一平台支撑三个研究内容的递进关系'
     new = '图 5　技术路线总图：三条研究内容共享同一平台，按“分帧—容器—缓冲 → 激活点 → 微动”递进'
     note = '' }
  @{ anchor = '图 6　前期完成的端到端时延实测'
     old = '图 6　前期完成的端到端时延实测：(a) 五分钟秒表轨迹（5 分钟内无累积趋势）；(b) 时延分解（视频解码环节占主导）'
     new = '图 6　前期完成的端到端时延实测：(a) 五分钟采样轨迹（稳态 233–266 ms，无累积趋势）；(b) 时延分解（解码环节约占 80%）'
     note = '【图题更正】“250.3 ± 0.5 ms”与秒表法 33 ms 的分辨率不符，改为实测区间 233–266 ms。' }
)

$newComments = New-Object System.Collections.ArrayList
$cid = 300
foreach ($ed in $edits) {
    $i = $doc.IndexOf($ed.anchor)
    if ($i -lt 0) { Write-Host "MISS: $($ed.anchor)"; continue }
    $tOpen = $doc.LastIndexOf('<w:t', $i)
    $tGt = $doc.IndexOf('>', $tOpen)
    $tClose = $doc.IndexOf('</w:t>', $i)
    $inner = $doc.Substring($tGt + 1, $tClose - $tGt - 1)
    $newInner = $inner.Replace($ed.old, $ed.new)
    if ($newInner -eq $inner) { Write-Host "NOCHANGE: $($ed.anchor)"; continue }
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
    Write-Host "OK: $($ed.anchor)"
}

# 正文中引用图 2 的那句
$bodyOld = '级联编解码结构与残差判据的统计位置如图 2 所示。'
$bodyNew = '级联编解码结构与分帧元数据的位置如图 2 所示。'
if ($doc.Contains($bodyOld)) {
    $doc = $doc.Replace($bodyOld, $bodyNew)
    Write-Host "OK: 正文图2 引用句"
}

# 追加批注
$sb = New-Object System.Text.StringBuilder
foreach ($c in $newComments) {
    [void]$sb.Append("<w:comment w:id=`"$($c.id)`" w:author=`"修订说明`" w:date=`"2026-10-19T18:45:00Z`" w:initials=`"修`"><w:p><w:r><w:t xml:space=`"preserve`">$($c.text)</w:t></w:r></w:p></w:comment>")
}
$cmts = $cmts.Replace('</w:comments>', $sb.ToString() + '</w:comments>')

try { [xml]$null = $doc; Write-Host "document.xml 良构: True" } catch { Write-Host "XML 错误: $($_.Exception.Message)" }
try { [xml]$null = $cmts; Write-Host "comments.xml 良构: True" } catch { Write-Host "comments XML 错误" }

if (Test-Path $tmp) { Remove-Item $tmp -Force }
$zin = [System.IO.Compression.ZipFile]::OpenRead($src)
$fs = [System.IO.File]::Open($tmp, [System.IO.FileMode]::CreateNew)
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
Copy-Item $tmp $src -Force
Write-Host "已更新: $src  大小: $((Get-Item $src).Length)"
