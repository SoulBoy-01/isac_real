"""
开题报告图件（v2.1）—— 统一风格重绘
Backend: Python / matplotlib (exclusive)

Figure contract
---------------
Fig1  核心结论：一条 OFDM 波形并发承载实时视频（通信链）与单站/双站感知
      archetype：schematic-led composite
Fig2  核心结论：2 字节长度前缀是分帧元数据，位于外码码字内部；有无外码决定其是否受保护
      archetype：schematic-led composite
Fig3  核心结论：同一物理误码流下，容器/解码器栈把有效失败概率放大 4x-500x，模型预测 7x
      archetype：quantitative grid（单一 hero 面板，对数横轴）
Fig4  核心结论：3.1 GHz 下呼吸相位 0.52-1.04 rad（充裕），心跳仅 0.026-0.065 rad（受限）
      archetype：schematic-led composite + subordinate quant
Fig5  核心结论：三条研究内容共享同一平台，按"分帧-容器-缓冲"→"激活点"→"微动"递进
      archetype：schematic-led composite
Fig6  核心结论：队列整形后端到端时延稳定在 250 ms 量级、5 分钟无累积，解码器占主导
      archetype：quantitative grid（hero trace + subordinate decomposition）

Export contract：报告版心约 16 cm；PNG 400 dpi 供 Word 插入 + PDF/SVG 矢量；
                 pdf.fonttype=42 / svg.fonttype=none（文字可编辑）。
数据来源：各章实测（参数与阈值见正文），无模拟数据。
"""
from __future__ import annotations

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

OUT = Path(r"D:\isac\paper\figures_report")
OUT.mkdir(parents=True, exist_ok=True)

INK = "#1A1A1A"
GREY = "#6E6E6E"
GREY_L = "#CFCFCF"
BLUE_D = "#2F5C8A"
BLUE_M = "#5B8DB8"
BLUE_L = "#DCE6EF"
WARM_D = "#B5533C"
WARM_L = "#F3E3DE"
GREEN_D = "#4C7A5A"
GREEN_L = "#E2ECE4"

mpl.rcParams.update({
    "font.family": ["Arial", "Microsoft YaHei"],
    "font.sans-serif": ["Arial", "Microsoft YaHei", "DejaVu Sans"],
    "font.size": 7,
    "axes.linewidth": 0.7,
    "axes.edgecolor": INK,
    "axes.labelcolor": INK,
    "text.color": INK,
    "xtick.color": INK,
    "ytick.color": INK,
    "xtick.major.width": 0.7,
    "ytick.major.width": 0.7,
    "xtick.labelsize": 6.5,
    "ytick.labelsize": 6.5,
    "axes.spines.right": False,
    "axes.spines.top": False,
    "legend.frameon": False,
    "figure.facecolor": "white",
    "savefig.facecolor": "white",
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "svg.fonttype": "none",
    "axes.unicode_minus": False,
    "lines.linewidth": 1.0,
})


def save(fig, stem: str):
    for ext in ("png", "pdf", "svg"):
        kw = {"bbox_inches": "tight", "pad_inches": 0.02}
        if ext == "png":
            kw["dpi"] = 400
        fig.savefig(OUT / f"{stem}.{ext}", **kw)
    plt.close(fig)
    print(f"[ok] {stem}")


def box(ax, x, y, w, h, text, fc="white", ec=INK, fs=6.4, bold=False, tc=INK, lw=0.75, z=3):
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.8",
        linewidth=lw, edgecolor=ec, facecolor=fc, zorder=z))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            fontsize=fs, color=tc, zorder=z + 1, linespacing=1.4,
            fontweight="bold" if bold else "normal")


def arrow(ax, p1, p2, color=INK, lw=0.8, ls="-", style="-|>", ms=7, z=2, conn="arc3"):
    ax.add_patch(FancyArrowPatch(
        p1, p2, arrowstyle=style, mutation_scale=ms, linewidth=lw,
        color=color, linestyle=ls, shrinkA=0, shrinkB=0, zorder=z,
        connectionstyle=conn))


def plabel(fig, x, y, s):
    fig.text(x, y, s, fontsize=8, fontweight="bold", ha="left", va="top", color=INK)


# =====================================================================
# Fig 1  系统拓扑
# =====================================================================
def fig1():
    fig = plt.figure(figsize=(6.5, 2.95))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 42)
    ax.axis("off")

    yc, hc = 28, 9
    ax.text(1, 39.6, "视频业务链（通信）", fontsize=6.6, color=GREY, style="italic")
    ax.text(1, 21.6, "感知链（与视频并发，共享同一波形）", fontsize=6.6, color=GREEN_D, style="italic")

    box(ax, 1, yc, 9.5, hc, "摄像头", fc=BLUE_L, ec=BLUE_M)
    box(ax, 12, yc, 12, hc, "H.264 编码\n(x264)", fc=BLUE_L, ec=BLUE_M)
    box(ax, 25.5, yc, 10, hc, "UDP\n:50000", fc="white", ec=GREY, fs=6.1)
    box(ax, 37, yc, 22, hc,
        "ISAC 发射机  N320\nRS(255,K) + LDPC(1008,504)\nOFDM 1024-FFT · QPSK",
        fc=WARM_L, ec=WARM_D, fs=5.9)
    box(ax, 61, yc, 13, hc, "无线\nOFDM 链路", fc="white", ec=GREY, fs=6.1)
    box(ax, 76, yc, 17, hc,
        "ISAC 接收机  B210\nLMMSE / ZF\nLDPC 译码",
        fc=WARM_L, ec=WARM_D, fs=6.0)

    for x1, x2 in [(10.5, 12), (24, 25.5), (35.5, 37), (59, 61), (74, 76)]:
        arrow(ax, (x1 + 0.15, yc + hc / 2), (x2 - 0.15, yc + hc / 2))

    ys, hs = 11.5, 8
    box(ax, 37, ys, 22, hs, "单站感知\nTX 副本 → 距离-多普勒", fc=GREEN_L, ec=GREEN_D, fs=6.0)
    arrow(ax, (48, yc - 0.15), (48, ys + hs + 0.15), color=GREEN_D, ls=(0, (3, 2)))
    box(ax, 61, ys, 13, hs, "双站感知\nUE 侧重构", fc=GREEN_L, ec=GREEN_D, fs=6.0)
    arrow(ax, (67.5, yc - 0.15), (67.5, ys + hs + 0.15), color=GREEN_D, ls=(0, (3, 2)))

    box(ax, 76, 15.0, 17, 7.5, "UDP :50001\n容错解码 (GStreamer)", fc=BLUE_L, ec=BLUE_M, fs=5.9)
    arrow(ax, (84.5, yc - 0.15), (84.5, 22.7))
    box(ax, 76, 4.0, 17, 6.5, "显示 / 记录", fc="white", ec=GREY, fs=6.1)
    arrow(ax, (84.5, 14.85), (84.5, 10.65))

    ax.text(1, 1.0,
            "帧结构：FFT 1024 · CP 128（12.5%）· 100 符号/帧 · 50 MHz · 帧长 2.304 ms（≈434 帧/s）\n"
            "业务：640×480@20 fps，1200 kbps，GOP 30；室内视距 ≈5 m，载波 3.1 GHz",
            fontsize=5.8, color=GREY, va="bottom", linespacing=1.5)
    save(fig, "fig1_topology")


# =====================================================================
# Fig 2  级联编码与分帧路径
# =====================================================================
def fig2():
    fig = plt.figure(figsize=(6.5, 3.55))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 64)
    ax.axis("off")

    yT, hT = 47, 9
    yR, hR = 27, 9

    ax.text(1, 59.6, "发送链", fontsize=6.8, color=GREY, style="italic")
    ax.text(1, 39.6, "接收链", fontsize=6.8, color=GREY, style="italic")

    box(ax, 1, yT, 12, hT, "UDP 载荷", fc="white", ec=GREY)
    box(ax, 15, yT, 14, hT, "长度前缀\n+ 载荷", fc=WARM_L, ec=WARM_D, bold=True)
    box(ax, 31, yT, 13, hT, "RS(255,K)\n外码", fc=BLUE_L, ec=BLUE_D)
    box(ax, 46, yT, 14, hT, "LDPC(1008,504)\n内码", fc=BLUE_L, ec=BLUE_D)
    box(ax, 62, yT, 14, hT, "交织 · 加扰\nQPSK 映射", fc=BLUE_L, ec=BLUE_M)
    box(ax, 78, yT, 16, hT, "OFDM 调制\n→ 空口", fc=WARM_L, ec=WARM_D)

    for x1, x2 in [(13, 15), (29, 31), (44, 46), (60, 62), (76, 78)]:
        arrow(ax, (x1 + 0.15, yT + hT / 2), (x2 - 0.15, yT + hT / 2))

    box(ax, 78, yR, 16, hR, "同步 / 信道估计\n软解映射", fc=WARM_L, ec=WARM_D)
    box(ax, 62, yR, 14, hR, "解交织 · 解扰", fc=BLUE_L, ec=BLUE_M)
    box(ax, 46, yR, 14, hR, "LDPC 译码", fc=BLUE_L, ec=BLUE_D)
    box(ax, 31, yR, 13, hR, "RS 译码", fc=BLUE_L, ec=BLUE_D)
    box(ax, 15, yR, 14, hR, "依前缀截取\n还原载荷", fc=WARM_L, ec=WARM_D, bold=True)
    box(ax, 1, yR, 12, hR, "重建视频", fc="white", ec=GREY)

    for x1, x2 in [(78, 76), (62, 60), (46, 44), (31, 29), (15, 13)]:
        arrow(ax, (x1 - 0.15, yR + hR / 2), (x2 + 0.15, yR + hR / 2))

    # 空口：从发送链末端下折到接收链首端
    arrow(ax, (86, yT - 0.2), (86, yR + hR + 0.2), color=GREY, ls=(0, (2, 2)), style="<|-|>", ms=6)
    ax.text(87.2, (yT + yR + hR) / 2 - 0.6, "空口", fontsize=5.8, color=GREY, va="center")

    # 关键提示
    ax.add_patch(FancyBboxPatch((1, 1.5), 93, 21,
                                boxstyle="round,pad=0.25,rounding_size=1.0",
                                linewidth=0.7, edgecolor=WARM_D, facecolor="#FBF6F4", zorder=1))
    ax.text(3, 19.4, "分帧元数据的位置决定了失效模式", fontsize=7.0, fontweight="bold", color=WARM_D)
    ax.text(3, 15.4, "有外码：2 字节长度前缀位于 RS 码字内部，受 t 字节纠错保护 → 载荷边界正确。",
            fontsize=6.2, va="center")
    ax.text(3, 10.9, "无外码：前缀裸露，单比特错误即破坏长度字段 → 接收端按错误长度切分 → 整条字节流错位。",
            fontsize=6.2, va="center")
    ax.text(3, 6.2, "因此外码的作用不止于纠错：它同时是分帧完整性的保护层（研究内容 1 的分帧子问题）。",
            fontsize=6.2, va="center", color=GREY)
    save(fig, "fig2_coding_framing")


# =====================================================================
# Fig 3  容器放大因子
# =====================================================================
def fig3():
    fig = plt.figure(figsize=(4.9, 2.55))
    ax = fig.add_axes([0.385, 0.30, 0.575, 0.62])

    labels = ["裸流 + GStreamer", "裸流 + ffplay", "MPEG-TS + ffplay", "MPEG-TS + VLC"]
    vals = [4, 8, 150, 500]
    colors = [BLUE_D, BLUE_D, WARM_D, WARM_D]
    y = np.arange(len(vals))

    ax.barh(y, vals, height=0.52, color=colors, edgecolor="none", zorder=2)
    ax.axvline(7, color=INK, lw=0.8, ls=(0, (3, 2)), zorder=3)
    ax.text(7.9, 4.25, "模型预测 γ ≈ 7（仅头部暴露）", fontsize=6.0, va="top", ha="left")

    for yi, v in zip(y, vals):
        ax.text(v * 1.2, yi, f"{v}×", va="center", ha="left", fontsize=6.6)

    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.set_xscale("log")
    ax.set_xlim(1, 1600)
    ax.set_ylim(-0.6, 4.35)
    ax.set_xlabel("实测容器放大因子 γ（对数轴）")
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.grid(axis="x", color=GREY_L, lw=0.4, zorder=0)
    ax.set_axisbelow(True)

    fig.text(0.055, 0.115, "压力工况：外码关闭，同一物理误码流", fontsize=5.9, color=GREY)
    fig.text(0.055, 0.035, "红：MPEG-TS 容器　蓝：裸 H.264 Annex B", fontsize=5.8, color=GREY)
    save(fig, "fig3_gamma")


# =====================================================================
# Fig 4  微动感知：处理链 + 相位预算
# =====================================================================
def fig4():
    fig = plt.figure(figsize=(6.5, 2.85))
    ax = fig.add_axes([0, 0.60, 1, 0.40])
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 18)
    ax.axis("off")

    y, h = 3, 9
    box(ax, 1, y, 16, h, "导频 / 信道估计\n(相位输出)", fc=BLUE_L, ec=BLUE_M, fs=6.0)
    box(ax, 20, y, 15, h, "目标距离门\n选择", fc=BLUE_L, ec=BLUE_M, fs=6.0)
    box(ax, 38, y, 19, h, "相位差分 · 共模相消\n+ 带通滤波", fc=BLUE_L, ec=BLUE_D, fs=6.0)
    box(ax, 60, y, 16, h, "呼吸 0.1–0.5 Hz\n心跳 0.8–2.0 Hz", fc=GREEN_L, ec=GREEN_D, fs=6.0)
    box(ax, 79, y, 19, h, "参数估计\n(谱 / 倒谱)", fc=GREEN_L, ec=GREEN_D, fs=6.0)
    for x1, x2 in [(17, 20), (35, 38), (57, 60), (76, 79)]:
        arrow(ax, (x1 + 0.15, y + h / 2), (x2 - 0.15, y + h / 2))

    ax.text(3.2, 16.4, "单站自发自收：收发共用本振，相噪在往返回波上呈共模，可经共模相消抑制",
            fontsize=6.0, color=GREY, va="center")
    ax.text(3.2, 13.6, "λ = 96.8 mm @ 3.1 GHz　·　相参窗 9.4 s（0.11 Hz 分辨率）",
            fontsize=6.0, color=GREY, va="center")

    ax2 = fig.add_axes([0.175, 0.115, 0.585, 0.32])
    items = ["心跳", "呼吸"]
    lo = [0.026, 0.52]
    hi = [0.065, 1.04]
    cols = [WARM_D, BLUE_D]
    yy = np.arange(len(items))
    for yi, l, hh, c in zip(yy, lo, hi, cols):
        ax2.plot([l, hh], [yi, yi], lw=3.4, color=c, solid_capstyle="round", zorder=3)
        ax2.text(hh * 1.28, yi, f"{l:g}–{hh:g} rad", va="center", fontsize=6.0, color=c)
    ax2.axvspan(0.004, 0.02, color=GREY_L, alpha=0.6, zorder=1)
    ax2.text(0.0044, 1.55, "相噪底（目标 C 待标定）", fontsize=5.7, color=GREY, va="bottom")
    ax2.set_yticks(yy)
    ax2.set_yticklabels(items)
    ax2.set_xscale("log")
    ax2.set_xlim(0.003, 4)
    ax2.set_ylim(-0.65, 1.85)
    ax2.set_xlabel("胸壁位移引起的相位变化 Δφ = 4πd/λ（rad，对数轴）", fontsize=6.2)
    ax2.spines["left"].set_visible(False)
    ax2.tick_params(axis="y", length=0)
    ax2.grid(axis="x", color=GREY_L, lw=0.4, zorder=0)
    ax2.set_axisbelow(True)

    fig.text(0.775, 0.20, "呼吸量级充裕；\n心跳逼近相噪底，\n是真正的难点", fontsize=5.9, color=GREY, va="top")
    plabel(fig, 0.012, 1.0, "a")
    plabel(fig, 0.012, 0.535, "b")
    save(fig, "fig4_micromotion")


# =====================================================================
# Fig 5  技术路线
# =====================================================================
def fig5():
    fig = plt.figure(figsize=(6.5, 3.35))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 56)
    ax.axis("off")

    box(ax, 1, 7, 16, 42,
        "统一平台\n\nOpenISAC\nN320 + B210\n\nOFDM 波形\n\n测量与数据\n基础设施",
        fc=BLUE_L, ec=BLUE_D, fs=6.0)

    rows = [
        (41, "研究内容 1\n跨层视频传输",
         ["分帧完整性\n(定长 vs 变长)", "容器与解码器\n(γ)", "缓冲与时延\n(250 ms 量级)", "调制与波形\n(16QAM/CP)"],
         BLUE_D, BLUE_L, "期刊论文 1"),
        (25, "研究内容 2\n信道自适应",
         ["受控衰减扫描\n(0–20 dB)", "激活点曲线\n(四档外码)", "在线码率映射\n(SNR → 档位)"],
         WARM_D, WARM_L, "期刊论文 2"),
        (9, "研究内容 3\n微动感知",
         ["目标 C\n能力基线", "目标 B\n呼吸率", "目标 A\n双参数"],
         GREEN_D, GREEN_L, "学位论文\n+ 数据集"),
    ]

    for y, title, subs, c_d, c_l, out in rows:
        box(ax, 19, y, 14, 11, title, fc=c_l, ec=c_d, fs=6.0, bold=True)
        n = len(subs)
        x0, x1 = 35, 77
        gap = 1.4
        w = (x1 - x0 - (n - 1) * gap) / n
        for i, s in enumerate(subs):
            x = x0 + i * (w + gap)
            box(ax, x, y + 1.0, w, 9.0, s, fc="white", ec=c_d, fs=5.8, lw=0.65)
            if i:
                arrow(ax, (x - gap + 0.1, y + 5.5), (x - 0.1, y + 5.5), color=c_d, ms=6)
        box(ax, 80, y + 1.0, 18, 9.0, out, fc=WARM_L, ec=WARM_D, fs=5.8, lw=0.7)
        arrow(ax, (77.2, y + 5.5), (79.8, y + 5.5), color=GREY, ms=6)

    for y1, y2 in [(41, 36), (25, 20)]:
        arrow(ax, (26, y1 - 0.2), (26, y2 + 0.2), color=GREY, ms=7)

    ax.text(1, 2.6,
            "递进关系：内容 1 建立跨层基线与测量方法 → 内容 2 引入信道维度 → 内容 3 在同一波形上开发感知维度",
            fontsize=5.9, color=GREY)
    save(fig, "fig5_roadmap")


# =====================================================================
# Fig 6  端到端时延
# =====================================================================
def fig6():
    fig = plt.figure(figsize=(6.5, 2.45))
    ax1 = fig.add_axes([0.085, 0.19, 0.39, 0.66])
    ax2 = fig.add_axes([0.585, 0.19, 0.365, 0.66])

    t = np.array([0, 20, 40, 74, 176, 205, 235, 277])
    lat = np.array([250, 250, 251, 250, 266, 233, 112, 38])

    ax1.axhspan(233, 266, color=BLUE_L, alpha=0.75, zorder=1, lw=0)
    ax1.plot(t[:6], lat[:6], color=BLUE_D, lw=0.9, zorder=2)
    ax1.plot(t[5:], lat[5:], color=WARM_D, lw=0.8, ls=(0, (2.5, 1.8)), zorder=2)
    ax1.scatter(t[:6], lat[:6], s=13, color=BLUE_D, zorder=3)
    ax1.scatter(t[6:], lat[6:], s=13, facecolor="white", edgecolor=WARM_D, lw=0.9, zorder=3)

    ax1.annotate("稳态 233–266 ms", xy=(150, 266), xytext=(120, 300),
                 fontsize=6.0, color=BLUE_D,
                 arrowprops=dict(arrowstyle="-", lw=0.6, color=BLUE_D))
    ax1.annotate("解码器缓冲重置\n（接收端软件行为）", xy=(238, 108), xytext=(128, 150),
                 fontsize=5.8, color=WARM_D,
                 arrowprops=dict(arrowstyle="-", lw=0.6, color=WARM_D, linestyle=(0, (2, 2))))
    ax1.set_xlabel("时间（s）")
    ax1.set_ylabel("端到端时延（ms）")
    ax1.set_ylim(0, 330)
    ax1.set_xlim(-10, 292)

    comp = ["H.264 解码 + 管道", "TX 队列", "H.264 编码", "RX 队列", "FEC 译码", "UDP (localhost)", "OFDM 成帧"]
    ms = [200, 18, 10, 9, 5, 5, 2.3]
    cols = [BLUE_D] + [GREY] * 6
    yy = np.arange(len(ms))[::-1]
    ax2.barh(yy, ms, height=0.55, color=cols, edgecolor="none", zorder=2)
    for yi, v in zip(yy, ms):
        ax2.text(v + 5, yi, f"{v:g}", va="center", fontsize=5.9)
    ax2.set_yticks(yy)
    ax2.set_yticklabels(comp, fontsize=5.9)
    ax2.set_xlim(0, 255)
    ax2.set_xlabel("时延贡献（ms）")
    ax2.spines["left"].set_visible(False)
    ax2.tick_params(axis="y", length=0)
    ax2.grid(axis="x", color=GREY_L, lw=0.4, zorder=0)
    ax2.set_axisbelow(True)

    plabel(fig, 0.005, 0.985, "a")
    plabel(fig, 0.505, 0.985, "b")
    save(fig, "fig6_latency")


if __name__ == "__main__":
    fig1(); fig2(); fig3(); fig4(); fig5(); fig6()
    print("OUT:", OUT)

