$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.IO.Compression.FileSystem
Add-Type -AssemblyName System.IO.Compression

$src = "C:\Users\Administrator\.dsh\attachments\v1\files\db\dbd1f76068e9b6086b389f2081861073380c77f2ca15e759234bcf85480a7436\开题报告_v3_图文版.docx"
$dst = "D:\isac\paper\开题报告_v3_修订版_带批注.docx"

$zip = [System.IO.Compression.ZipFile]::OpenRead($src)
$e1 = $zip.Entries | Where-Object { $_.FullName -eq 'word/document.xml' }
$a = New-Object System.IO.StreamReader($e1.Open()); $doc = $a.ReadToEnd(); $a.Close()
$e2 = $zip.Entries | Where-Object { $_.FullName -eq '[Content_Types].xml' }
$b = New-Object System.IO.StreamReader($e2.Open()); $contentTypes = $b.ReadToEnd(); $b.Close()
$e3 = $zip.Entries | Where-Object { $_.FullName -eq 'word/_rels/document.xml.rels' }
$c = New-Object System.IO.StreamReader($e3.Open()); $rels = $c.ReadToEnd(); $c.Close()
$zip.Dispose()

$edits = @(
  @{ anchor = '级联纠错能力'; pattern = '级联纠错能力。'
     repl = '级联编码链路。该实现已于后续代码复核中确认存在缺陷，目前正在替换为成熟实现并建立单元自检（详见补充说明）。'
     note = '【已更正】该编解码器在报告提交后的复核中被确认存在三处实现缺陷（码表初始化被函数级 static 门控、伴随式取向与编码器相反、纠错计数未累加），实际从未执行纠错。表述由“级联纠错能力”改为“级联编码链路”，并注明正在替换。详见《开题报告补充说明（第 1 号）》。' }
  @{ anchor = '本课题前期实验（已闭环）表明'; pattern = '本课题前期实验（已闭环）表明：.*?显著冗余浪费。'
     repl = '本课题前期实验曾观察到“稳态未见纠错事件”，但后续代码级复核发现外码解码器存在实现缺陷、从未真正执行纠错，该观测不成立，相关结论已撤回（见补充说明）。LDPC 残差的真实统计特性，尚待以可用的级联译码链路重新测量。'
     note = '【结论撤回】“零纠错”观测来自一个从不纠错、且始终报告成功的解码器，因此不构成误码率上界。原文据此推出的 10⁻⁹ 量级一并撤回，残差统计改为待重测项。' }
  @{ anchor = '需强调，上述'; pattern = '需强调，上述.{0,8}零纠错.{0,8}是统计上界而非零：.*?呈现为静默错误。'
     repl = '需强调，内码译码器不返回收敛标志、亦无逐码字校验，其误纠对上层呈现为静默错误——这是引入外码（而非仅依赖强内码）的技术理由。'
     note = '【论证调整】原“统计上界”论证建立在无效的零事件观测之上，已删除；保留“内码无收敛标志”这一技术理由，因为它与实现缺陷无关，仍然成立。' }
  @{ anchor = '也是首个基于实测 LDPC 残差统计'; pattern = '本研究是首个对 ISAC 链路上视频容器放大因子 γ 进行系统实测并建模的工作，也是首个基于实测 LDPC 残差统计（而非信道模型假设）确定外码最小充分配置的工作。'
     repl = '本研究对 ISAC 链路上视频容器放大因子 γ 进行了实测与建模；外码最小充分配置的确定因实现缺陷转入重测，改由研究内容 2 的激活点曲线回答。'
     note = '【表述更正】两项“首个”中撤回其一：γ 的实测与建模保留；外码最小配置因数据无效撤回，改由研究内容 2 回答，避免继续主张未成立的结论。' }
  @{ anchor = '已验证：稳态下全部配置零纠错事件'; pattern = '已验证：稳态下全部配置零纠错事件.*?而非按最坏情况取最强配置。'
     repl = '该组结论已撤回：复核发现外码解码器从未执行纠错，“稳态零纠错”来自实现缺陷而非链路特性；RS(255,223) 的 8.4% 吞吐增益亦为码率比推算、未经端到端实测。原设“外码只需覆盖内码残差上界”的准则暂不作为结论，改由研究内容 2 的激活点曲线判定。'
     note = '【结论撤回】Pareto 最优与 8.4% 两项撤回：8.4% 为 223/191 的码率比推算，既未端到端实测，所依赖的实现也未生效。原“最小充分能力”准则不再作为结论，转为研究内容 2 的研究问题。' }
  @{ anchor = 'BER–速率扫描显示'; pattern = 'BER–速率扫描显示 3000 kbps 以下有效载荷零误码、视频速率下 2\.5 倍余量。'
     repl = 'BER–速率扫描的误差计数含测试脚本伪错，待改用 PRBS 比对重测；视频速率下的吞吐余量以重测结果为准。'
     note = '【口径更正】该句与论文表 7 的 0.015% 自相矛盾；误差计数混入了测试载荷的头部字节，不能作为“零误码”的依据。仓库已有 PRBS 比对功能，重测即可。' }
  @{ anchor = '研究点 1 实验数据（已闭环）'; pattern = '- 研究点 1 实验数据（已闭环）：.*?（代表性结果见图 6）。'
     repl = '- 研究点 1 实验数据（部分闭环）：容器放大因子四方案实测、队列优化前后 5 分钟延迟轨迹、调制/码率/GOP/CP 对比实验——以上数据已整理为 5 图 7 表（代表性结果见图 6）。RS 四配置 Pareto 扫描因外码实现缺陷撤回，待替换实现后重测。'
     note = '【状态更正】“已闭环”改为“部分闭环”：外码部分撤回；容器、时延、调制/码率/GOP/CP 四项数据有效。这一处决定答辩时“研究点 1 完成了什么”的口径。' }
  @{ anchor = '较前期部署配置的有效吞吐提升'; pattern = '较前期部署配置的有效吞吐提升 ≥ 8%；'
     repl = '外码档位的吞吐收益待激活点实验后给出；'
     note = '【指标调整】原“≥ 8%”依赖已撤回的测量。改为待激活点实验后给出，既保留指标位，又不承诺一个目前无法支撑的数字。' }
  @{ anchor = '在 3.5 GHz 载波下'; pattern = '在 3\.5 GHz 载波下波长 λ≈85\.7 mm'
     repl = '在 3.1 GHz 载波下波长 λ≈96.8 mm'
     note = '【数值更正】载波频率与 5.2 节的 3.1 GHz 统一。' }
  @{ anchor = '0.59–1.17 rad'; pattern = '0\.59–1\.17 rad（34°–67°）'
     repl = '0.52–1.04 rad（30°–60°）'
     note = '【重算】按 λ=96.8 mm 重算：呼吸 4–8 mm 对应 0.52–1.04 rad（30°–60°）。' }
  @{ anchor = '0.03–0.07 rad'; pattern = '0\.03–0\.07 rad（1\.7°–4°）'
     repl = '0.026–0.065 rad（1.5°–3.7°）'
     note = '【重算】心跳 0.2–0.5 mm 对应 0.026–0.065 rad。呼吸仍是送分题，心跳才是真正的难点，这一条决定研究内容 3 的目标分层。' }
  @{ anchor = '需说明，稳态零纠错是预期之中的结果'; pattern = '需说明，稳态零纠错是预期之中的结果.*?（前期唯一观测到的失败事件即发生于接收机启动同步锁定瞬态）。'
     repl = '需说明，即便外码工作正常，四档配置在良好 SNR 下也可能等价，此时 Pareto 前沿由吞吐损失单维决定，必然指向最轻档位；外码的真实作用域是启动锁定、深衰落与遮挡等非稳态条件。'
     note = '【前后一致】本段前半句已声明结论撤回，此句仍把“稳态零纠错”当作既成事实，故一并改写为条件式表述（“即便外码工作正常”）。' }
  @{ anchor = '研究点 1 已证明固定 RS(255,223)'; pattern = '研究点 1 已证明固定 RS\(255,223\) 在实验室稳态 SNR 下.{0,2}过保护.{0,2}，但该结论只在良好 SNR 的单点成立——四档配置在稳态下零纠错，无法区分优劣。'
     repl = '研究点 1 曾初步判断固定 RS(255,223) 在实验室稳态 SNR 下可能“过保护”，但该判断因外码实现缺陷而失效——四档配置的差异从未被真实测量。'
     note = '【前提更正】“已证明过保护”依赖于已撤回的测量；改为“曾初步判断”并注明失效原因，使研究内容 2 的立论建立在“尚未测量”而非“已经证明”之上。' }
)

$comments = New-Object System.Collections.ArrayList
$cid = 100
$log = New-Object System.Collections.ArrayList

foreach ($ed in $edits) {
    $i = $doc.IndexOf($ed.anchor)
    if ($i -lt 0) { [void]$log.Add("MISS-ANCHOR  $($ed.anchor)"); continue }
    $tOpen = $doc.LastIndexOf('<w:t', $i)
    $tGt = $doc.IndexOf('>', $tOpen)
    $tClose = $doc.IndexOf('</w:t>', $i)
    $inner = $doc.Substring($tGt + 1, $tClose - $tGt - 1)
    $newInner = [regex]::Replace($inner, $ed.pattern, $ed.repl, 'Singleline')
    if ($newInner -eq $inner) { [void]$log.Add("NO-CHANGE  $($ed.anchor)"); continue }
    $rOpen = $doc.LastIndexOf('<w:r>', $tOpen)
    if ($rOpen -lt 0) { $rOpen = $doc.LastIndexOf('<w:r ', $tOpen) }
    $rClose = $doc.IndexOf('</w:r>', $tClose) + 6
    $run = $doc.Substring($rOpen, $rClose - $rOpen)
    $rpr = ''
    $mm = [regex]::Match($run, '<w:rPr>.*?</w:rPr>', 'Singleline')
    if ($mm.Success) { $rpr = $mm.Value }
    $id = $cid; $cid++
    $replXml = "<w:commentRangeStart w:id=`"$id`"/><w:r>$rpr<w:t xml:space=`"preserve`">$newInner</w:t></w:r><w:commentRangeEnd w:id=`"$id`"/><w:r><w:commentReference w:id=`"$id`"/></w:r>"
    $doc = $doc.Substring(0, $rOpen) + $replXml + $doc.Substring($rClose)
    [void]$comments.Add(@{ id = $id; text = $ed.note })
    [void]$log.Add("OK  $($ed.anchor)")
}

# ---- 插入"分帧完整性"要点 ----
$insAnchor = '指导裸 H.264 Annex B + 容错解码器的架构选择'
$pi = $doc.IndexOf($insAnchor)
if ($pi -ge 0) {
    $pEnd = $doc.IndexOf('</w:p>', $pi) + 6
    $pStart = $doc.LastIndexOf('<w:p ', $pi)
    if ($pStart -lt 0) { $pStart = $doc.LastIndexOf('<w:p>', $pi) }
    $oldPara = $doc.Substring($pStart, $pEnd - $pStart)
    $pPrM = [regex]::Match($oldPara, '<w:pPr>.*?</w:pPr>', 'Singleline')
    if ($pPrM.Success) { $pPr = $pPrM.Value } else { $pPr = '' }
    $rPrM = [regex]::Match($oldPara, '<w:rPr>.*?</w:rPr>', 'Singleline')
    if ($rPrM.Success) { $rPr = $rPrM.Value } else { $rPr = '' }
    $id = $cid; $cid++
    $newText = '分帧完整性的作用定位（新增）：预研中发现，接收端用于切分 UDP 载荷的 2 字节长度前缀位于外码码字内部；不设外码时该前缀不受保护，一处比特错误即可导致整条字节流错位。据此提出一个问题：在强内码链路上，视频业务的约束究竟来自纠错强度，还是来自分帧元数据的完整性？拟以“变长前缀 + 无外码”与“定长分片 + 无外码”两组对照实验回答。'
    $newPara = "<w:p>$pPr<w:commentRangeStart w:id=`"$id`"/><w:r>$rPr<w:t xml:space=`"preserve`">$newText</w:t></w:r><w:commentRangeEnd w:id=`"$id`"/><w:r><w:commentReference w:id=`"$id`"/></w:r></w:p>"
    $doc = $doc.Substring(0, $pEnd) + $newPara + $doc.Substring($pEnd)
    [void]$comments.Add(@{ id = $id; text = '【新增】原外码结论撤回后，研究内容 1 缺一个可验证的核心问题。建议以“分帧完整性”补位：长度前缀位于码字内部、无外码时不受保护，一处比特错误即可导致流级失步。该问题可由“变长前缀 vs 定长分片”两组对照实验直接验证，成本低、结论硬。' })
    [void]$log.Add('OK  INSERT 分帧完整性')
} else { [void]$log.Add('MISS  INSERT') }

# ---- comments.xml ----
$sb = New-Object System.Text.StringBuilder
[void]$sb.Append('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>')
[void]$sb.Append('<w:comments xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">')
foreach ($cm in $comments) {
    [void]$sb.Append("<w:comment w:id=`"$($cm.id)`" w:author=`"修订说明`" w:date=`"2026-10-19T18:00:00Z`" w:initials=`"修`"><w:p><w:r><w:t xml:space=`"preserve`">$($cm.text)</w:t></w:r></w:p></w:comment>")
}
[void]$sb.Append('</w:comments>')
$commentsXml = $sb.ToString()

if ($contentTypes -notmatch 'word/comments\.xml') {
    $contentTypes = $contentTypes -replace '</Types>', '<Override PartName="/word/comments.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml"/></Types>'
}
if ($rels -notmatch 'comments\.xml') {
    $rels = $rels -replace '</Relationships>', '<Relationship Id="rIdComments1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments" Target="comments.xml"/></Relationships>'
}

try { [xml]$null = $doc; $docOk = $true } catch { $docOk = $false; $docErr = $_.Exception.Message }
try { [xml]$null = $commentsXml; $cmOk = $true } catch { $cmOk = $false }

if (Test-Path $dst) { Remove-Item $dst -Force }
$zipIn = [System.IO.Compression.ZipFile]::OpenRead($src)
$fs = [System.IO.File]::Open($dst, [System.IO.FileMode]::CreateNew)
$zipOut = New-Object System.IO.Compression.ZipArchive($fs, [System.IO.Compression.ZipArchiveMode]::Create)
foreach ($entry in $zipIn.Entries) {
    $name = $entry.FullName
    $ne = $zipOut.CreateEntry($name, [System.IO.Compression.CompressionLevel]::Optimal)
    $os = $ne.Open()
    if ($name -eq 'word/document.xml' -or $name -eq '[Content_Types].xml' -or $name -eq 'word/_rels/document.xml.rels') {
        $payload = $doc
        if ($name -eq '[Content_Types].xml') { $payload = $contentTypes }
        if ($name -eq 'word/_rels/document.xml.rels') { $payload = $rels }
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($payload)
        $os.Write($bytes, 0, $bytes.Length)
        $os.Close()
    } else {
        $is = $entry.Open()
        $is.CopyTo($os)
        $is.Close()
        $os.Close()
    }
}
$ce = $zipOut.CreateEntry('word/comments.xml', [System.IO.Compression.CompressionLevel]::Optimal)
$cs = $ce.Open()
$cb = [System.Text.Encoding]::UTF8.GetBytes($commentsXml)
$cs.Write($cb, 0, $cb.Length); $cs.Close()
$zipOut.Dispose(); $fs.Close(); $zipIn.Dispose()

"document.xml 良构: $docOk"
"comments.xml 良构: $cmOk  条数: $($comments.Count)"
"输出: $dst  大小: $((Get-Item $dst).Length)"
"---- 日志 ----"
$log | ForEach-Object { "  $_" }
