# -*- coding: utf-8 -*-
"""
图 5  技术路线总图（nature-figure / Python 后端）
------------------------------------------------
核心结论：三条研究内容共享同一试验平台，按「跨层基线 → 激活点 → 共存 → 微动延伸」逐层递进。
图型：schematic-led composite（示意主导），白底、无阴影、直接标注。
导出：PNG(400 dpi, 供 Word) + PDF/SVG(矢量, 文字可编辑)。

运行：
    python make_fig5_route.py
产物（与脚本同目录）：
    fig5_route.png / fig5_route.pdf / fig5_route.svg
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib import font_manager

# ---------------------------------------------------------------- 字体
CJK_CANDIDATES = [
    "Microsoft YaHei", "SimHei", "Source Han Sans SC", "Noto Sans CJK SC",
    "PingFang SC", "WenQuanYi Zen Hei", "Arial Unicode MS",
]


def pick_cjk():
    installed = {f.name for f in font_manager.fontManager.ttflist}
    for name in CJK_CANDIDATES:
        if name in installed:
            return name
    return "DejaVu Sans"


CJK = pick_cjk()

mpl.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": [CJK, "Arial", "Helvetica", "DejaVu Sans"],
    "svg.fonttype": "none",
    "pdf.fonttype": 42,
    "font.size": 7,
    "axes.linewidth": 0.8,
    "figure.facecolor": "white",
    "savefig.facecolor": "white",
})

# ---------------------------------------------------------------- 配色（一套中性 + 一套信号 + 一个强调）
INK = "#1A1A1A"
SUB = "#4A4A4A"
MUTED = "#6B7280"

PLAT_FC, PLAT_EC = "#EEF1F4", "#44505E"
CORE_FC, CORE_EC = "#E9EFF8", "#2F5597"
OUT_FC, OUT_EC = "#FFFFFF", "#9AA7B4"
EXT_FC, EXT_EC = "#F7F7F7", "#8A8A8A"
BAND_FC, BAND_EC = "#F4F4F4", "#D0D0D0"

W, H = 100.0, 64.0
fig = plt.figure(figsize=(7.2, 4.61))
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, W)
ax.set_ylim(0, H)
ax.axis("off")


def box(x, y, w, h, fc, ec, lw=0.9, ls="-", r=1.0, z=2):
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad=0,rounding_size={r}",
        linewidth=lw, edgecolor=ec, facecolor=fc, linestyle=ls, zorder=z,
    ))


def arrow(x1, y1, x2, y2, color=PLAT_EC, lw=0.9):
    ax.add_patch(FancyArrowPatch(
        (x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=8.5,
        linewidth=lw, color=color, shrinkA=0, shrinkB=0, zorder=3,
    ))


def txt(x, y, s, size=6.8, color=INK, ha="center", va="center", weight="normal", z=4):
    ax.text(x, y, s, fontsize=size, color=color, ha=ha, va=va,
            weight=weight, zorder=z, linespacing=1.55)


# ---------------------------------------------------------------- 1 平台层
box(2, 55.0, 96, 7.6, PLAT_FC, PLAT_EC, lw=1.0, r=1.2)
txt(50, 60.9, "统一试验平台", size=7.6, weight="bold")
txt(50, 57.6,
    "OpenISAC（USRP N320 → B210）｜OFDM 1024-FFT / CP 128 / 50 MHz｜QPSK / 16QAM｜RS + LDPC 级联｜实时视频管道｜单站感知",
    size=6.4, color=SUB)

# ---------------------------------------------------------------- 2 三条研究内容
STAGE_Y, STAGE_H = 31.0, 20.0
cols = [
    (2.0, 31.0, "研究内容 1　跨层基线", [
        "分帧 · 容器 · 缓冲",
        "容器放大 γ 的建模与实测",
        "外码保护边界（重测中）",
        "队列整形与端到端时延",
    ]),
    (35.5, 29.0, "研究内容 2　激活点与自适应", [
        "受控衰减扫描 0–20 dB",
        "SNR–纠错事件率曲线",
        "码率映射与在线热切换",
    ]),
    (68.5, 29.5, "研究内容 3　共存（必做）", [
        "开 / 关视频业务对照",
        "payload / sensing_pilot 配比",
        "检测性能折中曲线",
    ]),
]

for (x, w, title, items) in cols:
    box(x, STAGE_Y, w, STAGE_H, CORE_FC, CORE_EC, lw=1.0, r=1.2)
    txt(x + w / 2, STAGE_Y + STAGE_H - 3.0, title, size=7.4, weight="bold")
    ax.plot([x + 2.0, x + w - 2.0], [STAGE_Y + STAGE_H - 5.4] * 2,
            color=CORE_EC, lw=0.6, alpha=0.55, zorder=3)
    for i, it in enumerate(items):
        txt(x + 2.2, STAGE_Y + STAGE_H - 8.4 - i * 3.35, "· " + it,
            size=6.5, color=SUB, ha="left")

# 平台 → 三列
for (x, w, _, _) in cols:
    arrow(x + w / 2, 54.7, x + w / 2, STAGE_Y + STAGE_H + 0.4, color=MUTED)
# 三列之间递进
arrow(cols[0][0] + cols[0][1] + 0.4, STAGE_Y + STAGE_H / 2,
      cols[1][0] - 0.4, STAGE_Y + STAGE_H / 2)
arrow(cols[1][0] + cols[1][1] + 0.4, STAGE_Y + STAGE_H / 2,
      cols[2][0] - 0.4, STAGE_Y + STAGE_H / 2)

# ---------------------------------------------------------------- 3 阶段产出
OUT_Y, OUT_H = 17.0, 10.0
outs = [
    (2.0, 31.0, "容器放大模型 · 保护边界估计\n端到端时延 ≤ 300 ms，无累积"),
    (35.5, 29.0, "四档激活点 · 最优切换区段\n切换失步率 ≤ 10⁻³"),
    (68.5, 29.5, "检测性能–负载折中曲线\n资源配比建议"),
]
for (x, w, s) in outs:
    box(x, OUT_Y, w, OUT_H, OUT_FC, OUT_EC, lw=0.8, ls=(0, (3, 2)), r=0.9)
    txt(x + w / 2, OUT_Y + OUT_H / 2, s, size=6.4, color=SUB)

for (x, w, _, _) in cols:
    arrow(x + w / 2, STAGE_Y - 0.4, x + w / 2, OUT_Y + OUT_H + 0.4, color=MUTED, lw=0.8)

txt(2.4, OUT_Y + OUT_H + 1.6, "阶段产出", size=6.2, color=MUTED, ha="left")

# ---------------------------------------------------------------- 4 延伸层
EXT_X, EXT_Y, EXT_W, EXT_H = 62.0, 4.2, 36.0, 9.6
box(EXT_X, EXT_Y, EXT_W, EXT_H, EXT_FC, EXT_EC, lw=0.9, ls=(0, (4, 2)), r=1.0)
txt(EXT_X + EXT_W / 2, EXT_Y + EXT_H - 2.4,
    "延伸目标（条件性）：微动感知", size=6.9, weight="bold", color=INK)
txt(EXT_X + EXT_W / 2, EXT_Y + 3.6,
    "相位提取 · 长时相参积累 · 相位噪声底标定 → 呼吸率 / 心率",
    size=6.2, color=SUB)
arrow(83.2, OUT_Y - 0.4, 83.2, EXT_Y + EXT_H + 0.4, color=EXT_EC, lw=0.8)

# ---------------------------------------------------------------- 5 说明
txt(2.4, 11.6, "说明", size=6.4, color=MUTED, ha="left", weight="bold")
txt(2.4, 6.6,
    "研究内容 1、2 构成“跨层基线 + 自适应”主线；\n"
    "研究内容 3 的共存层为必做，微动感知为目标 0/C 成立后的条件性延伸；\n"
    "三条内容共享同一硬件链路、同一套测量脚本与同一组对照基线。",
    size=6.2, color=SUB, ha="left", va="center")

# ---------------------------------------------------------------- 6 方法底栏
box(2, 0.6, 96, 3.4, BAND_FC, BAND_EC, lw=0.7, r=0.7)
txt(50, 2.3,
    "方法：逐层打点测量 · 受控衰减实验 · 资源配比扫描 · 单元自检 · 可复现脚本与数据集",
    size=6.2, color=SUB)

# ---------------------------------------------------------------- 导出
import os
out_base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fig5_route")
fig.savefig(out_base + ".png", dpi=400, bbox_inches="tight", pad_inches=0.04)
fig.savefig(out_base + ".pdf", bbox_inches="tight", pad_inches=0.04)
fig.savefig(out_base + ".svg", bbox_inches="tight", pad_inches=0.04)
print("CJK font :", CJK)
print("written  :", out_base + ".png / .pdf / .svg")
