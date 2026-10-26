from pathlib import Path
from zipfile import ZipFile
from lxml import etree
import re,shutil,json,sys,tempfile
sys.path.insert(0,str(Path(tempfile.gettempdir())/'openisac-docx-edit-deps'))
b=Path(r'D:\isac\OpenISAC_new\docs\project_report');qa=b/'.single_station_edit_qa';qa.mkdir(exist_ok=True)
src=b/'OpenISAC_项目验收报告.docx';backup=qa/'before.docx'
if not backup.exists():shutil.copy2(src,backup)
# Rebuild the three affected diagrams from their original drawing source.
graph=(b/'gen_figs.py').read_text('utf8').replace('OCXO','外部时钟')
ns={'__name__':'diagram_rebuild','__file__':str(b/'gen_figs.py')}
exec(compile(graph,'gen_figs.py','exec'),ns);ns['OUT']=str(qa)
exec(r'''
def fig_sys_arch():
    fig, ax = new_ax(12, 6.4, (0, 120), (0, 64))
    container(ax, 5, 3, 50, 45, 'BS 基站节点')
    container(ax, 65, 3, 50, 45, 'UE 通信终端节点')
    box(ax, 9, 8, 14, 8, 'PC 主机\n(i9-12900K)', GREEN_F, GREEN_E)
    box(ax, 31, 8, 16, 8, 'USRP\n(NI X310)', CYAN_F, CYAN_E)
    arrow(ax, 23, 12, 31, 12, double=True)
    ax.text(27, 13.8, '10GbE', ha='center', fontsize=8.5)
    box(ax, 34, 21, 10, 6, '外部时钟\n(10 MHz)', PURPLE_F, PURPLE_E, fs=8.5)
    arrow(ax, 39, 21, 39, 16)
    ax.text(40.2, 18.3, 'REFCLK', ha='left', fontsize=8)
    antenna(ax, 22, 34);antenna(ax, 48, 34)
    ax.text(22, 40.6, 'TX 天线\n(喇叭 16 dBi)', ha='center', va='bottom', fontsize=8.5)
    ax.text(48, 40.6, '感知 RX 天线\n(喇叭 16 dBi)', ha='center', va='bottom', fontsize=8.5)
    ax.plot([33, 22], [16, 32], color='black', lw=1.2, zorder=2)
    ax.plot([45, 48], [16, 32], color='black', lw=1.2, zorder=2)
    box(ax, 74, 8, 14, 8, 'USRP\n(NI X310)', CYAN_F, CYAN_E)
    box(ax, 94, 8, 14, 8, 'PC 主机\n(i9-12900K)', GREEN_F, GREEN_E)
    arrow(ax, 88, 12, 94, 12, double=True)
    ax.text(91, 13.8, '10GbE', ha='center', fontsize=8.5)
    box(ax, 76, 21, 10, 6, '外部时钟', PURPLE_F, PURPLE_E, fs=8.5)
    arrow(ax, 81, 21, 81, 16)
    ax.text(82.2, 18.3, 'REFCLK', ha='left', fontsize=8)
    antenna(ax, 69, 34)
    ax.text(69, 40.6, '接收天线\n(全向 3 dBi)', ha='center', va='bottom', fontsize=8.5)
    ax.plot([74, 69], [12, 32], color='black', lw=1.2, zorder=2)
    human(ax, 60, 51);ax.text(60, 61.8, '感知目标（人体）', ha='center', fontsize=9.5)
    arrow(ax, 24, 39.5, 55, 49, color=ORANGE_LINE, style='--', lw=1.6)
    ax.text(33, 47.5, '单站雷达回波', fontsize=8.5, color=ORANGE_LINE)
    arrow(ax, 65.5, 49, 50, 40, color=ORANGE_LINE, style='--', lw=1.6)
    arrow(ax, 24, 31.5, 67.4, 31.5, color=PURPLE_LINE, style='--', lw=1.6)
    ax.text(45, 28.9, '下行通信链路', fontsize=8.5, color=PURPLE_LINE)
    ax.plot([14, 22], [1.5, 1.5], color=ORANGE_LINE, ls='--', lw=1.6)
    ax.text(23, 1.5, '单站回波链路', fontsize=9, va='center')
    ax.plot([50, 58], [1.5, 1.5], color=PURPLE_LINE, ls='--', lw=1.6)
    ax.text(59, 1.5, '下行通信链路', fontsize=9, va='center')
    save(fig, 'fig_sys_arch.png')

def fig_soft_ue():
    fig, ax = new_ax(12, 5.6, (0, 120), (0, 56))
    box(ax, 4, 44, 18, 10, '控制命令线程\n(UDP 9999)', CTRL_F, CTRL_E, fs=9)
    ax.text(25, 49, 'Python 控制命令', ha='left', fontsize=9)
    arrow(ax, 25, 47, 22, 47)
    arrow(ax, 10, 44, 10, 36, color=CTRL_E, style='--')
    arrow(ax, 22, 44, 50, 36, color=CTRL_E, style='--')
    box(ax, 6, 24, 16, 12, 'USRP-RX 线程', GREEN_F, GREEN_E)
    arrow(ax, 22, 30, 26, 30)
    box(ax, 26, 24, 12, 12, 'RX 波形 FIFO', GRAY_F, GRAY_E, dashed=True, fs=8)
    arrow(ax, 38, 30, 42, 30)
    box(ax, 42, 24, 24, 12, 'OFDM 解调线程\n(帧同步、均衡)', YELLOW_F, YELLOW_E, fs=9.5)
    arrow(ax, 66, 30, 70, 30)
    box(ax, 70, 24, 12, 12, '数据 LLR\nFIFO', GRAY_F, GRAY_E, dashed=True, fs=8.5)
    arrow(ax, 82, 30, 86, 30)
    box(ax, 86, 24, 22, 12, '比特处理线程\n(解扰、LDPC+RS 译码)', ORANGE_F, ORANGE_E, fs=9)
    arrow(ax, 108, 30, 111, 30)
    ax.text(111.5, 30, 'UDP 业务\n输出', ha='left', va='center', fontsize=8.5)
    box(ax, 6, 4, 26, 12, '硬件同步控制器\n(外部时钟)', GREEN_F, GREEN_E, fs=10)
    arrow(ax, 14, 16, 14, 24)
    ax.text(15.2, 20, '参考时钟', ha='left', va='center', fontsize=8.5)
    save(fig, 'fig_soft_ue.png')
''',ns)
# Receiver frame acquisition stays; remove the OTA hardware correction and sensing timing branch.
flow=graph[graph.index('def fig_flow_ue():'):graph.index("if __name__ == '__main__':")]
flow=flow.replace('(数字重调频 / 外部时钟)','(数字重调频 / 样本调整)')
flow=flow[:flow.index('    # delay tracking box')]+"    save(fig, 'fig_flow_ue.png')\n"
exec(flow,ns)
for fn in ['fig_sys_arch','fig_soft_ue','fig_flow_ue']:ns[fn]()
W='http://schemas.openxmlformats.org/wordprocessingml/2006/main';N={'w':W}
def text(p):return ''.join(n.text or '' for n in p.findall('.//w:t',N))
def substitute(p,old,new):
    nodes=p.findall('.//w:t',N);combined=''.join(n.text or '' for n in nodes)
    for m in reversed(list(re.finditer(re.escape(old),combined))):
        positions=[];pos=0
        for n in nodes:positions.append(pos);pos+=len(n.text or '')
        i=next(i for i,n in enumerate(nodes) if positions[i]<=m.start()<positions[i]+len(n.text or ''))
        j=next(j for j,n in enumerate(nodes) if positions[j]<m.end()<=positions[j]+len(n.text or ''))
        first=nodes[i].text or '';last=nodes[j].text or ''
        if i==j:nodes[i].text=first[:m.start()-positions[i]]+new+first[m.end()-positions[i]:]
        else:
            nodes[i].text=first[:m.start()-positions[i]]+new
            for k in range(i+1,j):nodes[k].text=''
            nodes[j].text=last[m.end()-positions[j]:]
changes=[];removed=[]
with ZipFile(backup) as zin:
    root=etree.fromstring(zin.read('word/document.xml'));body=root.find('w:body',N)
    deleting=False
    for el in list(body):
        t=text(el)
        if t.startswith('5.4 UE 双站感知') or t.startswith('6.5 双站感知'):deleting=True
        if deleting and (t.startswith('六、') or t.startswith('七、')):deleting=False
        if deleting:
            # Preserve the section boundary page break before chapter seven.
            if el.find('.//w:br[@w:type="page"]',N) is not None:continue
            removed.append(t);body.remove(el)
    for tr in list(root.findall('.//w:tr',N)):
        ts=text(tr)
        if '双站与空口同步' in ts or 'Over-the-Air Synchronization' in ts:
            removed.append(ts);tr.getparent().remove(tr)
    replace_pairs=[
        ('真实空口（Over-the-Air, OTA）验证','真实空口验证'),('三大工程瓶颈','两大工程瓶颈'),
        ('、终端（UE）无线空口同步（OTA Synchronization）及双站感知',''),
        ('、双站感知（OTA 同步开关对比、人体目标）',''),
        ('通信与双站感知终端节点（UE）','通信终端节点（UE）'),
        ('UE 接收/双站感知/OTA 时钟驯服','UE 通信接收'),
        ('运行 OFDMDemodulator、双站感知与 OTA 驯服控制','运行 OFDMDemodulator 后端进行通信接收与译码'),
        ('可驯服参考时钟','外部参考时钟'),('外部时钟 + USB DAC 模块','外部时钟（10 MHz）'),
        ('USB + SMA','SMA'),('接收主机指令调节 DAC 输出电压（VADJ），牵引校准外部时钟','为 UE USRP 提供参考时钟'),
        ('接收直达径通信信号与目标散射的双站多径信号','接收下行通信信号'),
        ('、USB 驯服外部时钟/DAC 模块',''),
        ('图 4-2 UE 侧软件架构（同步状态机 → 解调/均衡 → LDPC 译码 → 双站感知 + OTA 同步）','图 4-2 UE 侧软件架构（帧同步 → 解调/均衡 → LDPC 与 RS 译码）'),
        ('，重构发射参考符号，输出译码器输入与 {RX, TX} 符号对','，完成通信帧同步、信道估计与均衡，输出译码器输入'),
        ('经 USB DAC 微调 UE 外部时钟，配合自适应卡尔曼滤波（AKF）实现长期相干性维护','使用外部时钟为 UE USRP 提供参考时钟'),
        ('、双站前端',''),('经数字重调频或 外部时钟调整、样本填充/丢弃完成时频校正','经数字重调频、样本填充/丢弃完成通信接收时频校正'),
        ('USB 驯服外部时钟/DAC','外部时钟'),
        ('支持无有线空口同步、覆盖单/双站感知与宽带实时通信','支持单站感知与宽带实时通信'),
        ('；双站侧 OTA 同步在 ±0.5 ppm 时钟偏差下取得 17–22 dB 的 MSR 改善，双站人体目标点迹明确',''),
    ]
    for p in list(root.findall('.//w:p',N)):
        t=text(p)
        if t.startswith('异地双站同步受限：') or t.startswith('感知线程：消费 {RX, TX}'):
            removed.append(t);p.getparent().remove(p);continue
        before=t
        if t.startswith('终端通信解调与双站感知链路（UE 接收端）：'):
            substitute(p,'终端通信解调与双站感知链路','终端通信解调链路')
            substitute(p,t.split('：',1)[1],'远端 UE 捕获下行通信信号后，完成帧同步、信道均衡与业务数据译码，恢复业务负载。')
        else:
            for old,new in replace_pairs:
                if old in text(p):substitute(p,old,new)
        if before!=text(p):changes.append({'before':before,'after':text(p)})
        # Keep image and its caption on the same page.
        if p.find('.//w:drawing',N) is not None:
            pr=p.find('w:pPr',N)
            if pr is None:pr=etree.Element('{'+W+'}pPr');p.insert(0,pr)
            if pr.find('w:keepNext',N) is None:etree.SubElement(pr,'{'+W+'}keepNext')
    # Renumber deliverable rows after removing the paper entry about OTA synchronization.
    for tbl in root.findall('.//w:tbl',N):
        rows=tbl.findall('w:tr',N)
        if rows and '交付物' in text(rows[0]):
            for i,row in enumerate(rows[1:],1):
                p=row.find('w:tc/w:p',N);substitute(p,text(p),str(i))
    # Keep table rows intact and repeat headers across pages.
    for tbl in root.findall('.//w:tbl',N):
        rows=tbl.findall('w:tr',N)
        for i,row in enumerate(rows):
            pr=row.find('w:trPr',N)
            if pr is None:pr=etree.Element('{'+W+'}trPr');row.insert(0,pr)
            if pr.find('w:cantSplit',N) is None:etree.SubElement(pr,'{'+W+'}cantSplit')
            if i==0 and pr.find('w:tblHeader',N) is None:etree.SubElement(pr,'{'+W+'}tblHeader')
    # Maintain the aspect ratio of the rebuilt UE diagram.
    from PIL import Image
    iw,ih=Image.open(qa/'fig_soft_ue.png').size
    for drawing in root.findall('.//w:drawing',N):
        if drawing.find('.//{http://schemas.openxmlformats.org/drawingml/2006/main}blip').get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')=='rId12':
            ext=drawing.find('.//{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}extent')
            if ext is not None:
                cy=round(int(ext.get('cx'))*ih/iw);ext.set('cy',str(cy))
                for e in drawing.findall('.//{http://schemas.openxmlformats.org/drawingml/2006/main}ext'):e.set('cy',str(cy))
    content=etree.tostring(root,encoding='UTF-8',xml_declaration=True,standalone=True)
    assert not re.search('双站|OTA|空口同步|驯服|Over-the-Air Synchronization|OCXO|USB DAC|VADJ',content.decode('utf8'),re.I)
    image_updates={'word/media/image1.png':qa/'fig_sys_arch.png','word/media/image3.png':qa/'fig_soft_ue.png','word/media/image7.png':qa/'fig_flow_ue.png'}
    out=qa/'modified.docx'
    with ZipFile(out,'w') as zout:
        for info in zin.infolist():
            data=zin.read(info.filename)
            if info.filename=='word/document.xml':data=content
            elif info.filename in image_updates:data=image_updates[info.filename].read_bytes()
            zout.writestr(info,data)
with ZipFile(out) as z:assert z.testzip() is None
try:
    shutil.copyfile(out,src)
    final=src
except PermissionError:
    final=b/'OpenISAC_项目验收报告_修订版.docx'
    shutil.copyfile(out,final)
(qa/'changes.json').write_text(json.dumps({'updated':changes,'deleted':removed},ensure_ascii=False,indent=2),'utf8')
print('Updated paragraphs',len(changes),'Removed paragraphs/table rows',len(removed),'Updated diagrams',len(image_updates))
print('Saved',final)
