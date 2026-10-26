# -*- coding: utf-8 -*-
"""开题答辩 PPT 生成器（nature-paper2ppt, paper_type=methods）"""
from pathlib import Path
import shutil

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn
from PIL import Image

ROOT = Path(r"D:\isac\paper")
FIG = ROOT / "figures_report"
OUT = ROOT / "ppt_out"
ASSETS = OUT / "assets" / "figures"
OUT.mkdir(parents=True, exist_ok=True)
ASSETS.mkdir(parents=True, exist_ok=True)

INK = RGBColor(0x1A, 0x1A, 0x1A)
GREY = RGBColor(0x6E, 0x6E, 0x6E)
GREY_L = RGBColor(0xD9, 0xD9, 0xD9)
BLUE_D = RGBColor(0x2F, 0x5C, 0x8A)
BLUE_M = RGBColor(0x5B, 0x8D, 0xB8)
BLUE_L = RGBColor(0xDC, 0xE6, 0xEF)
WARM_D = RGBColor(0xB5, 0x53, 0x3C)
WARM_L = RGBColor(0xF3, 0xE3, 0xDE)
GREEN_D = RGBColor(0x4C, 0x7A, 0x5A)
GREEN_L = RGBColor(0xE2, 0xEC, 0xE4)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

FONT_CN = "微软雅黑"
FONT_EN = "Arial"
FONT_MONO = "Consolas"

SW, SH = 13.333, 7.5
ML = 0.75
CW = SW - 2 * ML

prs = Presentation()
prs.slide_width = Inches(SW)
prs.slide_height = Inches(SH)

# 图件复制到 assets
for p in sorted(FIG.glob("*.png")):
    shutil.copy2(p, ASSETS / p.name)

# 技术路线图底部自带一行说明；幻灯片下方已用大字重述，裁掉底部 6.5% 以免重复
with Image.open(ASSETS / "fig5_roadmap.png") as im:
    _w, _h = im.size
    im.crop((0, 0, _w, int(_h * 0.918))).save(ASSETS / "fig5_roadmap_slide.png")


def set_font(run, size=16, bold=False, color=INK, ea=FONT_CN, latin=FONT_EN):
    f = run.font
    f.size = Pt(size)
    f.bold = bold
    f.color.rgb = color
    f.name = latin
    rPr = run._r.get_or_add_rPr()
    for tag, face in (("a:ea", ea), ("a:cs", ea)):
        el = rPr.find(qn(tag))
        if el is None:
            el = rPr.makeelement(qn(tag), {})
            rPr.append(el)
        el.set("typeface", face)


def textbox(slide, left, top, width, height, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP):
    tb = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = 0
    tf.margin_right = 0
    tf.margin_top = 0
    tf.margin_bottom = 0
    tf.vertical_anchor = anchor
    p = tf.paragraphs[0]
    p.alignment = align
    return tf


def put(tf, text, size=16, bold=False, color=INK, space_before=0, line=1.25,
        align=PP_ALIGN.LEFT, first=False, ea=FONT_CN, latin=FONT_EN):
    p = tf.paragraphs[0] if first else tf.add_paragraph()
    p.alignment = align
    p.line_spacing = line
    p.space_before = Pt(space_before)
    r = p.add_run()
    r.text = text
    set_font(r, size, bold, color, ea, latin)
    return p


def rect(slide, left, top, width, height, fill=None, line=None, lw=1.0, shape=MSO_SHAPE.RECTANGLE):
    sh = slide.shapes.add_shape(shape, Inches(left), Inches(top), Inches(width), Inches(height))
    if fill is None:
        sh.fill.background()
    else:
        sh.fill.solid()
        sh.fill.fore_color.rgb = fill
    if line is None:
        sh.line.fill.background()
    else:
        sh.line.color.rgb = line
        sh.line.width = Pt(lw)
    sh.shadow.inherit = False
    return sh


def slide_title(slide, title, kicker=None, accent=BLUE_D):
    if kicker:
        tf = textbox(slide, ML, 0.34, CW, 0.3)
        put(tf, kicker, 11, False, accent, first=True)
    tf = textbox(slide, ML, 0.62, CW, 0.62)
    put(tf, title, 25, True, INK, first=True, line=1.1)
    rect(slide, ML, 1.32, CW, 0.018, fill=GREY_L)


def footer(slide, idx, total=13):
    rect(slide, ML, 7.02, CW, 0.012, fill=GREY_L)
    tf = textbox(slide, ML, 7.10, 7.0, 0.26)
    put(tf, "OFDM 通感一体化 · 实时视频与微动感知", 9, False, GREY, first=True)
    tf = textbox(slide, SW - ML - 1.2, 7.10, 1.2, 0.26, align=PP_ALIGN.RIGHT)
    put(tf, f"{idx} / {total}", 9, False, GREY, first=True, align=PP_ALIGN.RIGHT)


def source(slide, text, top=6.72):
    tf = textbox(slide, ML, top, CW, 0.24)
    put(tf, text, 9, False, GREY, first=True)


def note(slide, text):
    slide.notes_slide.notes_text_frame.text = text


def pic(slide, name, left, top, width):
    path = ASSETS / name
    with Image.open(path) as im:
        w, h = im.size
    height = width * h / w
    slide.shapes.add_picture(str(path), Inches(left), Inches(top), Inches(width), Inches(height))
    return height


def bullet(slide, left, top, width, items, size=15, gap=0.52, color=BLUE_D):
    y = top
    for it in items:
        rect(slide, left, y + 0.09, 0.09, 0.09, fill=color)
        tf = textbox(slide, left + 0.24, y, width - 0.24, 0.44)
        put(tf, it, size, False, INK, first=True, line=1.2)
        y += gap
    return y


def stat(slide, left, top, w, big, label, color=BLUE_D):
    tf = textbox(slide, left, top, w, 0.5)
    put(tf, big, 21, True, color, first=True, latin=FONT_EN)
    tf = textbox(slide, left, top + 0.46, w, 0.3)
    put(tf, label, 10, False, GREY, first=True)


# ============================== S1 标题 ==============================
s = prs.slides.add_slide(prs.slide_layouts[6])
rect(s, 0, 0, 0.28, SH, fill=BLUE_D)
tf = textbox(s, 1.15, 1.55, 10.8, 1.5)
put(tf, "OFDM 通感一体化系统中", 34, True, INK, first=True, line=1.15)
put(tf, "实时视频传输与微动感知关键技术研究", 34, True, INK, line=1.15)
rect(s, 1.15, 3.32, 1.5, 0.05, fill=WARM_D)
tf = textbox(s, 1.15, 3.58, 10.8, 0.4)
put(tf, "硕士学位论文 · 开题报告", 16, False, GREY, first=True)
tf = textbox(s, 1.15, 4.55, 10.8, 1.0)
put(tf, "叶嘉锐　·　202530310195　·　通信工程", 13, False, INK, first=True, line=1.5)
put(tf, "校内导师：徐志京　　实践导师：丁鹏仁", 13, False, INK, line=1.5)
tf = textbox(s, 1.15, 6.35, 10.8, 0.3)
put(tf, "上海海事大学　·　2026 年 10 月", 12, False, GREY, first=True)
note(s, "各位老师上午好。我是通信工程专业的叶嘉锐，导师是徐志京老师，实践导师是丁鹏仁老师。"
        "我的题目是《OFDM 通感一体化系统中实时视频传输与微动感知关键技术研究》。"
        "接下来用十五分钟汇报选题背景、三条研究内容、前期基础和后续计划。")

# ============================== S2 背景 ==============================
s = prs.slides.add_slide(prs.slide_layouts[6])
slide_title(s, "一条波形同时跑视频和雷达，难点不在带宽", "研究背景")
bullet(s, ML, 1.62, 7.6, [
    "通感一体化：通信与感知共享波形、频谱与硬件，是 6G 的原生场景",
    "实时视频是最苛刻的业务：持续吞吐、有界时延、对残余误码零容忍",
    "误码不止于比特：容器与解码器会把一次错误放大成一个 GOP 的花屏",
    "真实平台上的端到端行为，公开测量几乎空白",
], size=15.5, gap=0.86)
rect(s, 9.0, 1.55, 3.55, 4.55, fill=BLUE_L, line=None)
tf = textbox(s, 9.28, 1.80, 3.0, 0.3)
put(tf, "实验平台关键参数", 11, True, BLUE_D, first=True)
stat(s, 9.28, 2.25, 3.0, "2.304 ms", "OFDM 帧长（434 帧/秒）")
stat(s, 9.28, 3.05, 3.0, "50 MHz", "采样率 · FFT 1024 · CP 128")
stat(s, 9.28, 3.85, 3.0, "640×480", "H.264 @ 20 fps，1200 kbps")
stat(s, 9.28, 4.65, 3.0, "≈5 m", "室内视距，3.1 GHz", color=GREEN_D)
footer(s, 2)
note(s, "为什么这个题目值得做？三个层面。第一，ISAC 是 6G 的原生场景，一条波形同时承载通信和感知。"
        "第二，视频是最苛刻的负载——它要持续吞吐、要时延有界不累积，而且对残余误码零容忍。"
        "第三，误码的影响不止在比特层：容器和解码器会把一次错误放大成一整个 GOP 的花屏。"
        "而真实平台上这类端到端行为，公开的测量几乎是空白。右边是我们平台的四个关键参数。")

# ============================== S3 问题 ==============================
s = prs.slides.add_slide(prs.slide_layouts[6])
slide_title(s, "现有研究停在物理层，三个问题没人回答", "问题定义")
qs = [
    ("Q1", "保护该加在哪一层？", "现有工作多把物理层当作既定条件，\n只优化应用层；而 ISAC 的物理层是可配的。",
     "本研究：把保护拆成分帧、容器、缓冲三层，分别实测。", BLUE_D, BLUE_L),
    ("Q2", "外码何时才真正起作用？", "传统按最坏情况定强度；\n实测的激活点在哪里，尚无数据。",
     "本研究：受控衰减扫描，画出四档外码的激活点。", WARM_D, WARM_L),
    ("Q3", "同一波形能否做微动感知？", "现有生命体征感知多依赖专用雷达或 Wi-Fi，\n承载实时业务时能否兼得，未经验证。",
     "本研究：同一波形的相位域提取，三级目标递进。", GREEN_D, GREEN_L),
]
x = ML
w = (CW - 0.6) / 3
for tag, q, sub, ans, cd, cl in qs:
    rect(s, x, 1.55, w, 4.45, fill=cl, line=None)
    tf = textbox(s, x + 0.3, 1.78, w - 0.6, 0.4)
    put(tf, tag, 13, True, cd, first=True)
    tf = textbox(s, x + 0.3, 2.12, w - 0.6, 1.05)
    put(tf, q, 17, True, INK, first=True, line=1.2)
    rect(s, x + 0.3, 3.30, 0.55, 0.035, fill=cd)
    tf = textbox(s, x + 0.3, 3.48, w - 0.6, 1.30)
    put(tf, sub, 11.5, False, GREY, first=True, line=1.45)
    rect(s, x + 0.3, 4.86, w - 0.6, 0.012, fill=cd)
    tf = textbox(s, x + 0.3, 5.00, w - 0.6, 0.90)
    put(tf, ans, 11.5, True, cd, first=True, line=1.4)
    x += w + 0.3
tf = textbox(s, ML, 6.22, CW, 0.4)
put(tf, "本课题定位：在一套开源平台上，把三个问题都做成可复现的实测，而不是仿真假设。",
    13.5, True, INK, first=True)
footer(s, 3)
note(s, "现有研究共同的局限是：把物理层当成既定条件，只在应用层做优化；但 ISAC 平台的物理层恰恰是可配的——"
        "外码强度、导频密度、循环前缀都能改。于是留下三个没人回答的问题："
        "保护应该加在哪一层？外码到底什么时候起作用？以及同一条波形能不能顺带做微动感知？"
        "我的定位是：三个问题都用实测回答，不做仿真假设。")

# ============================== S4 技术路线 ==============================
s = prs.slides.add_slide(prs.slide_layouts[6])
slide_title(s, "三条研究内容，共享一套平台与测量方法", "总体路线")
h = pic(s, "fig5_roadmap_slide.png", 2.17, 1.50, 9.0)
source(s, "图 5　技术路线总图（开题报告）", top=1.50 + h + 0.06)
tf = textbox(s, ML, 6.36, CW, 0.4)
put(tf, "递进关系：内容 1 建立基线与方法 → 内容 2 引入信道维度 → 内容 3 在同一波形上开发感知维度",
    13, True, BLUE_D, first=True)
footer(s, 4)
note(s, "整体路线是一张图：左边是统一的 OpenISAC 平台，中间三条研究内容，右边是产出。"
        "内容一做跨层视频，先建立测量基线和方法；内容二在它上面引入信道维度，回答外码的激活点；"
        "内容三在同一波形上做微动感知。三条内容不并行投入，是递进的，共享同一套脚本和硬件。")

# ============================== S5 平台 ==============================
s = prs.slides.add_slide(prs.slide_layouts[6])
slide_title(s, "系统由两部分组成：通信链跑视频，感知链共用波形", "平台与系统")
h = pic(s, "fig1_topology.png", ML, 1.52, 8.3)
source(s, "图 1　系统拓扑（开题报告）", top=1.52 + h + 0.06)
bullet(s, 9.45, 1.62, 3.4, [
    "BS：USRP N320，SFP+ 10G",
    "UE：USRP B210，USB 3.0",
    "外码 RS(255,K) + 内码 LDPC(1008,504)",
    "视频：GStreamer 裸流，无容器",
    "感知：单站 + 双站并发",
], size=11.5, gap=0.52)
footer(s, 5)
note(s, "系统分两条链。上面是视频业务链：摄像头、H.264 编码、UDP、ISAC 发射、空口、接收、解码显示。"
        "下面是感知链，单站在基站用发射副本做，双站在终端侧重构，与视频并发、共享同一波形。"
        "右边是硬件与参数。需要说明：平台是开源的，我在上面做了二次开发——多阶 QAM、外码模块、视频管道和队列整形。")

# ============================== S6 内容1 ==============================
s = prs.slides.add_slide(prs.slide_layouts[6])
slide_title(s, "跨层视频：先看保护加在哪，而不是加多少", "研究内容 1")
bullet(s, ML, 1.60, 4.1, [
    "分帧完整性：长度前缀的位置决定失效模式",
    "容器与解码器：同一条误码流，不同栈差两个数量级",
    "缓冲与时延：队列深度决定时延是否累积",
], size=13, gap=0.72)
h = pic(s, "fig2_coding_framing.png", 5.15, 1.52, 7.45)
source(s, "图 2　级联编码与分帧路径（开题报告）", top=1.52 + h + 0.06)
footer(s, 6)
note(s, "内容一有三个子问题。最基础的是分帧完整性：两字节长度前缀放在外码码字内部，受保护时边界正确；"
        "一旦没有外码保护，前缀裸露，一个比特错误就会让接收端按错误长度切分，整条字节流错位。"
        "这解释了一个现象——为什么关掉外码，实时流会崩，而 TS 文件还能放。"
        "第二是容器与解码器，第三是缓冲与时延，后面两页给结果。")

# ============================== S7 γ ==============================
s = prs.slides.add_slide(prs.slide_layouts[6])
slide_title(s, "同一条误码流，容器选择让失败概率差 100 倍", "前期结果 · 容器放大")
h = pic(s, "fig3_gamma.png", ML, 1.55, 7.6)
source(s, "图 3　容器放大因子 γ（开题报告）", top=1.55 + h + 0.06)
bullet(s, 8.35, 1.70, 4.5, [
    "MPEG-TS + VLC：≈500×",
    "MPEG-TS + ffplay：≈150×",
    "裸流 + ffplay：≈8×",
    "裸流 + GStreamer：≈4×",
], size=13, gap=0.45, color=WARM_D)
tf = textbox(s, 8.35, 3.62, 4.4, 1.0)
put(tf, "模型只预测头部暴露（7×）；实测的两端差异来自解码器状态机。",
    11.5, False, GREY, first=True, line=1.45)
rect(s, 8.35, 4.95, 4.40, 1.05, fill=BLUE_L, line=None)
tf = textbox(s, 8.55, 5.12, 4.0, 0.75)
put(tf, "容器与解码器的选择，比外码强度重要一个量级。", 12, True, BLUE_D, first=True, line=1.35)
footer(s, 7)
note(s, "这张图是内容一最硬的结果。同样的物理误码流，只换容器和解码器：MPEG-TS 配 VLC 放大约五百倍，"
        "裸流配 GStreamer 只有四倍。模型按头部暴露只预测七倍，说明差距主要来自解码器的状态机——"
        "VLC 会因为 PCR 时钟死锁。结论是：容器和解码器的选择，比外码强度重要一个量级。"
        "注意这是压力工况，外码是关闭的。")

# ============================== S8 时延 ==============================
s = prs.slides.add_slide(prs.slide_layouts[6])
slide_title(s, "时延瓶颈在解码器，不在射频", "前期结果 · 端到端时延")
h = pic(s, "fig6_latency.png", 1.07, 1.52, 11.2)
source(s, "图 6　端到端时延实测（开题报告）", top=1.52 + h + 0.05)
tf = textbox(s, ML, 6.05, CW, 0.75)
put(tf, "稳态 233–266 ms，5 分钟无累积趋势；解码环节约占 80%，射频链路约 3 ms。",
    14, True, BLUE_D, first=True, line=1.3)
put(tf, "测量方法为秒表法，分辨率约 33 ms，因此只报告量级与趋势，不报亚毫秒抖动。",
    10.5, False, GREY, line=1.3)
footer(s, 8)
note(s, "时延这条：把四级队列从三十二削到四到八，并用非阻塞丢弃替掉阻塞写入，"
        "把正反馈的累积环路切断了。稳态落在 233 到 266 毫秒之间，五分钟没有累积趋势。"
        "分解下来解码环节占八成，射频只有三毫秒。测量是秒表法，分辨率三十三毫秒，"
        "所以我只报量级和趋势，不报亚毫秒抖动。")

# ============================== S9 内容2 ==============================
s = prs.slides.add_slide(prs.slide_layouts[6])
slide_title(s, "外码不是“要不要”，而是“何时开始起作用”", "研究内容 2")
rect(s, ML, 1.55, 5.4, 4.35, fill=WARM_L, line=None)
tf = textbox(s, ML + 0.35, 1.80, 4.9, 0.35)
put(tf, "问题", 12, True, WARM_D, first=True)
tf = textbox(s, ML + 0.35, 2.15, 4.85, 3.4)
put(tf, "四档外码在良好 SNR 下表现一致，无法区分优劣；", 12.5, False, INK, first=True, line=1.5)
put(tf, "真正的问题是：从哪个 SNR 开始，外码才真正产生纠正？", 12.5, True, INK, space_before=10, line=1.5)
put(tf, "这个问题决定了外码的必要性与最优档位。", 12, False, GREY, space_before=10, line=1.5)
steps = [
    ("①", "受控衰减扫描", "0–20 dB，四档配置，记录纠错 / 不可纠事件率"),
    ("②", "激活点曲线", "功率–事件率曲线，定位各档工作区段"),
    ("③", "在线映射", "SNR 与残差统计 → 码率档位，GOP 边界热切换"),
]
y = 1.62
for i, (n, t, d) in enumerate(steps):
    rect(s, 6.55, y, 5.95, 1.28, fill=WHITE, line=GREY_L)
    tf = textbox(s, 6.78, y + 0.16, 0.5, 0.4)
    put(tf, n, 16, True, WARM_D, first=True)
    tf = textbox(s, 7.30, y + 0.14, 4.9, 0.35)
    put(tf, t, 13, True, INK, first=True)
    tf = textbox(s, 7.30, y + 0.56, 4.95, 0.6)
    put(tf, d, 10.5, False, GREY, first=True, line=1.3)
    y += 1.48
tf = textbox(s, 6.55, 6.24, 5.95, 0.4)
put(tf, "前置：先把外码实现替换为可验证版本并加单元自检。", 11, False, WARM_D, first=True)
footer(s, 9)
note(s, "内容二要回答的是：外码不是要不要，而是何时开始起作用。"
        "四档配置在良好信噪比下表现一样，区分不出优劣；真正的问题是激活点在哪里。"
        "办法是受控衰减扫描，从零扫到二十 dB，记录纠错和不可纠事件率，得到激活点曲线，"
        "再据此做在线码率映射，切换点放在 GOP 边界。前提是先有一个可验证的外码实现，这一点下面一页说明。")

# ============================== S10 内容3 ==============================
s = prs.slides.add_slide(prs.slide_layouts[6])
slide_title(s, "微动感知：呼吸是送分题，心跳才是难点", "研究内容 3")
h = pic(s, "fig4_micromotion.png", ML, 1.50, 8.6)
source(s, "图 4　微动感知处理链与相位预算（开题报告）", top=1.50 + h + 0.05)
bullet(s, 9.65, 1.62, 3.2, [
    "呼吸 0.52–1.04 rad：量级充裕",
    "心跳 0.026–0.065 rad：逼近相噪底",
    "单站共模相消抑制相噪",
], size=11.5, gap=0.62, color=GREEN_D)
tf = textbox(s, 9.65, 3.95, 3.2, 1.9)
put(tf, "三级目标", 11, True, GREEN_D, first=True)
put(tf, "C 能力基线 → B 呼吸率 → A 双参数", 11, False, INK, space_before=6, line=1.4)
put(tf, "每级均可独立成章", 10.5, False, GREY, space_before=4, line=1.4)
footer(s, 10)
note(s, "内容三是我最不确定的一块，所以先算了相位预算。三一吉赫兹下波长九十六点八毫米，"
        "呼吸位移四到八毫米对应零点五到一弧度，非常充裕；心跳只有零点零四弧度左右，逼近系统相噪底。"
        "单站自发自收收发共用本振，相噪是共模的，可以做共模相消。所以我把目标设成三级："
        "先做能力基线，再做呼吸率，最后才是双参数，每级都能独立成章。")

# ============================== S11 方法学校验 ==============================
s = prs.slides.add_slide(prs.slide_layouts[6])
slide_title(s, "在自查中发现并定位了外码实现的缺陷", "方法学校验")
rect(s, ML, 1.50, 6.55, 4.55, fill=WARM_L, line=None)
tf = textbox(s, ML + 0.32, 1.72, 5.95, 0.35)
put(tf, "三处缺陷（已定位到文件行号）", 12, True, WARM_D, first=True)
rows = [
    ("1", "码表初始化被函数级 static 门控，第 2 个实例起码表全零"),
    ("2", "伴随式多项式取向与编码器相反，合法码字被判为错"),
    ("3", "纠错计数声明后从未累加，无纠错统计"),
]
yy = 2.15
for n, t in rows:
    tf = textbox(s, ML + 0.32, yy, 0.35, 0.32)
    put(tf, n, 12, True, WARM_D, first=True)
    tf = textbox(s, ML + 0.70, yy, 5.55, 0.7)
    put(tf, t, 11.5, False, INK, first=True, line=1.35)
    yy += 0.98
tf = textbox(s, ML + 0.32, 5.10, 5.95, 0.8)
put(tf, "后果：除首个包外校验位恒为 0，解码恒判“无错”——外码从未真正生效。",
    11.5, True, INK, first=True, line=1.35)
rect(s, 7.70, 1.50, 4.85, 4.55, fill=RGBColor(0xF7, 0xF7, 0xF7), line=GREY_L)
tf = textbox(s, 7.95, 1.70, 4.4, 0.3)
put(tf, "自检输出（40 行程序，可复现）", 10.5, True, GREY, first=True)
tf = textbox(s, 7.95, 2.02, 4.45, 2.30)
put(tf, "[A] 第1/第2实例编码一致 : NO", 10.5, False, INK, first=True, line=1.45, latin=FONT_MONO, ea=FONT_MONO)
put(tf, "    32/255 字节不同；校验位全零: 是", 10.5, False, INK, line=1.45, latin=FONT_MONO, ea=FONT_MONO)
put(tf, "[B] 干净码字: ok=0 corrected=0", 10.5, False, INK, line=1.45, latin=FONT_MONO, ea=FONT_MONO)
put(tf, "[C] 注入 0~16 错误：全部 r=0", 10.5, False, INK, line=1.45, latin=FONT_MONO, ea=FONT_MONO)
put(tf, "结论: 未通过自检", 10.5, True, WARM_D, line=1.45, latin=FONT_MONO, ea=FONT_MONO)
rect(s, 7.95, 4.30, 4.30, 0.010, fill=GREY_L)
tf = textbox(s, 7.95, 4.45, 4.35, 0.70)
put(tf, "处理：替换为成熟实现 + 单元自检。", 10.5, False, INK, first=True, line=1.35)
tf = textbox(s, 7.95, 5.15, 4.35, 0.80)
put(tf, "影响：第三章“零失败”结论撤回，改由激活点重测回答。", 10.5, False, GREY, first=True, line=1.35)
tf = textbox(s, ML, 6.28, CW, 0.45)
put(tf, "意义：测量链本身也需要被验证——这一个缺陷此前被“完美”的日志掩盖。", 12.5, True, BLUE_D, first=True)
footer(s, 11)
note(s, "这一页是我主动加的。开题报告提交之后，我对测量链做了一次代码级复核，写了四十行自检程序。"
        "结果：第一个实例编码正常，第二个实例开始校验位全零，因为码表初始化用了函数级 static；"
        "更严重的是，即使码表正常，解码器也算不对伴随式，连干净码字都解不出来。"
        "所以之前那组“零失败”的结论不成立，已经全部撤回并列入重测。"
        "这件事的意义是：测量链本身也需要被验证，而这个缺陷此前被看起来很完美的日志掩盖了。")

# ============================== S12 计划 ==============================
s = prs.slides.add_slide(prs.slide_layouts[6])
slide_title(s, "近期四周先把外码修好，再谈边界", "研究计划")
rows = [
    ("W1", "替换外码实现 + 单元自检", "设备返回后做基线一致性核对", BLUE_D),
    ("W2", "受控衰减扫描（0–20 dB）", "四档配置 × 纠错/不可纠事件率", BLUE_D),
    ("W3", "激活点曲线 + 分帧验证", "定长分片 vs 变长前缀对照", WARM_D),
    ("W4", "数据整理与结论收敛", "研究内容 1、2 定稿", GREEN_D),
]
y = 1.58
for w, t, d, c in rows:
    rect(s, ML, y, 7.1, 1.02, fill=WHITE, line=GREY_L)
    tf = textbox(s, ML + 0.22, y + 0.30, 0.7, 0.35)
    put(tf, w, 13, True, c, first=True)
    tf = textbox(s, ML + 0.95, y + 0.16, 3.0, 0.35)
    put(tf, t, 12.5, True, INK, first=True)
    tf = textbox(s, ML + 0.95, y + 0.56, 5.9, 0.3)
    put(tf, d, 10.5, False, GREY, first=True)
    y += 1.18
rect(s, 8.35, 1.58, 4.2, 3.1, fill=BLUE_L, line=None)
tf = textbox(s, 8.60, 1.78, 3.75, 0.3)
put(tf, "学期粒度", 11, True, BLUE_D, first=True)
tf = textbox(s, 8.60, 2.12, 3.75, 2.4)
put(tf, "2026 秋：外码重测、内容 1 收尾", 10.5, False, INK, first=True, line=1.5)
put(tf, "2027 春：内容 2 实测、内容 3 基线", 10.5, False, INK, space_before=6, line=1.5)
put(tf, "2027 秋：微动实验、第二篇论文", 10.5, False, INK, space_before=6, line=1.5)
put(tf, "2028 春：成稿、送审、答辩", 10.5, False, INK, space_before=6, line=1.5)
rect(s, 8.35, 4.92, 4.2, 1.72, fill=WARM_L, line=None)
tf = textbox(s, 8.60, 5.08, 3.75, 0.3)
put(tf, "预期成果", 11, True, WARM_D, first=True)
tf = textbox(s, 8.60, 5.40, 3.75, 1.15)
put(tf, "学位论文 1 部", 10.5, False, INK, first=True, line=1.4)
put(tf, "期刊论文 1–2 篇", 10.5, False, INK, space_before=3, line=1.4)
put(tf, "可复现方法与数据集", 10.5, False, INK, space_before=3, line=1.4)
footer(s, 12)
note(s, "计划上，设备外展回来后第一件事不是跑新实验，是把外码换掉并做自检，再做基线一致性核对，"
        "确认搬运没有改变系统状态。然后两周做衰减扫描和激活点，第三周做分帧对照，第四周收敛数据。"
        "按学期看，这学期完成内容一收尾，明年上半年内容二实测和内容三基线，"
        "明年下半年微动实验和第二篇论文，后年春天成稿送审。")

# ============================== S13 总结 ==============================
s = prs.slides.add_slide(prs.slide_layouts[6])
rect(s, 0, 0, 0.28, SH, fill=BLUE_D)
tf = textbox(s, 1.15, 0.95, 11.0, 0.6)
put(tf, "总结", 26, True, INK, first=True)
items = [
    ("问题", "强编码 ISAC 链路上跑实时视频，瓶颈不在带宽，而在保护加在哪一层。"),
    ("方法", "同一平台、逐层打点：分帧完整性、容器与解码器、缓冲与时延，三条线各有实测。"),
    ("边界", "外码的真实作用域仍在定位；微动感知按三级目标推进，先保能力基线。"),
]
y = 1.95
for k, v in items:
    rect(s, 1.15, y + 0.10, 1.05, 0.42, fill=BLUE_L, line=None)
    tf = textbox(s, 1.15, y + 0.16, 1.05, 0.3, align=PP_ALIGN.CENTER)
    put(tf, k, 11, True, BLUE_D, first=True, align=PP_ALIGN.CENTER)
    tf = textbox(s, 2.45, y + 0.10, 9.3, 0.85)
    put(tf, v, 13.5, False, INK, first=True, line=1.45)
    y += 1.30
rect(s, 1.15, 5.85, 10.9, 0.02, fill=GREY_L)
tf = textbox(s, 1.15, 6.05, 11.0, 0.4)
put(tf, "请各位老师批评指正。", 16, True, BLUE_D, first=True)
note(s, "最后总结三句话。问题：强编码链路上跑实时视频，瓶颈不在带宽，而在保护加在哪一层。"
        "方法：同一个平台、逐层打点，分帧、容器、缓冲三条线都有实测。"
        "边界：外码的真实作用域还在定位，微动感知按三级目标推进，先保能力基线。"
        "请各位老师批评指正，谢谢。")

out = OUT / "final_presentation_cn.pptx"
prs.save(str(out))
print("saved", out, "slides:", len(prs.slides.__iter__.__self__._sldIdLst))


