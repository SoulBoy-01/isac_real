"""技术路线总图 — v2 版本。

设计原则：白底扁平、低饱和度配色、清晰边框线、无渐变无阴影。
  - 平台顶栏：浅蓝灰底 #EFF2F7，深蓝边 #2F5496
  - 研究内容1（已完成）：蓝灰底 #EFF2F7，实线边 #2F5496
  - 研究内容2/3（拟研究）：白底，虚线边 #5B7DC4
  - 成果1（已形成）：浅绿底 #EEF4EC，深绿边 #3A7040
  - 成果2/3（预期）：白底，虚线边 #5B7DC4
  - 底栏：浅红底 #FAEAEA，深红边 #8B2020
  - 箭头：中性深灰 #444444
"""
from __future__ import annotations
from pathlib import Path
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import matplotlib.patheffects as pe

mpl.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Microsoft YaHei", "SimHei", "DejaVu Sans"],
    "axes.unicode_minus": False,
    "svg.fonttype": "none",
    "pdf.fonttype": 42,
})

OUT = Path(__file__).resolve().parent

# ── 颜色 token ──────────────────────────────────────────────────────────────
C = dict(
    blue_dark   = "#2F5496",
    blue_mid    = "#5B7DC4",
    blue_bg     = "#EFF2F7",
    green_dark  = "#3A7040",
    green_bg    = "#EEF4EC",
    red_dark    = "#8B2020",
    red_bg      = "#FAEAEA",
    arrow       = "#444444",
    text_head   = "#1A1A1A",
    text_body   = "#3D3D3D",
    white       = "#FFFFFF",
)

# ── 辅助函数 ─────────────────────────────────────────────────────────────────
def rounded_box(ax, x, y, w, h, *, fc, ec, lw=1.4, ls="-"):
    """画圆角矩形（无阴影，pad=0 避免内缩）。"""
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.012,rounding_size=0.018",
        fc=fc, ec=ec, lw=lw, ls=ls,
        zorder=2,
    ))


def title_text(ax, x, y, w, h, s, *, color, size=9.5, dy=0.94):
    ax.text(x + w/2, y + h*dy, s,
            ha="center", va="top",
            fontsize=size, color=color, fontweight="bold", zorder=3)


def body_text(ax, x, y, w, h, s, *, size=7.8, dy=0.78):
    ax.text(x + w/2, y + h*dy, s,
            ha="center", va="top",
            fontsize=size, color=C["text_body"],
            linespacing=1.55, zorder=3)


def down_arrow(ax, x, y1, y2):
    ax.annotate("", xy=(x, y2), xytext=(x, y1),
                arrowprops=dict(arrowstyle="-|>", color=C["arrow"],
                                lw=1.2, mutation_scale=11),
                zorder=4)


def horiz_arrow(ax, x1, x2, y, label=""):
    ax.annotate("", xy=(x2, y), xytext=(x1, y),
                arrowprops=dict(arrowstyle="-|>", color=C["blue_dark"],
                                lw=1.1, mutation_scale=10),
                zorder=4)
    if label:
        ax.text((x1+x2)/2, y + 0.022, label,
                ha="center", va="bottom",
                fontsize=6.8, color=C["blue_dark"], zorder=5)


# ── 画布 ─────────────────────────────────────────────────────────────────────
# 图幅：宽 10 寸（给三列正文足够空间），高 6 寸
# 坐标系 [0,10] x [0,6]，单位 = 寸
fig, ax = plt.subplots(figsize=(10.0, 6.2))
ax.set_xlim(0, 10); ax.set_ylim(0, 6.2)
ax.axis("off")
fig.patch.set_facecolor("white")

# ── 行坐标（单位：寸）────────────────────────────────────────────────────────
H_TOP = 0.82    # 平台顶栏高
H_MID = 2.10    # 研究内容行高
H_BTM = 0.90    # 成果行高
H_BAR = 0.54    # 底栏高
GAP   = 0.20    # 各行间距

Y_BAR = 0.18
Y_BTM = Y_BAR + H_BAR + GAP
Y_MID = Y_BTM + H_BTM + GAP
Y_TOP = Y_MID + H_MID + GAP

# 三列布局：左边距 0.25，列宽 2.90，列间距 0.375
COL_W  = 2.90
COL_G  = 0.375
X_L0   = 0.25
X_M0   = X_L0 + COL_W + COL_G
X_R0   = X_M0 + COL_W + COL_G
# 列中心 x（用于箭头）
X_L    = X_L0 + COL_W / 2
X_M    = X_M0 + COL_W / 2
X_R    = X_R0 + COL_W / 2
# 顶栏/底栏全宽
FULL_X0 = 0.25
FULL_W  = X_R0 + COL_W - X_L0

# ── 顶部：平台 ───────────────────────────────────────────────────────────────
rounded_box(ax, FULL_X0, Y_TOP, FULL_W, H_TOP,
            fc=C["blue_bg"], ec=C["blue_dark"], lw=1.8)
title_text(ax, FULL_X0, Y_TOP, FULL_W, H_TOP,
           "OpenISAC 开源 OFDM-ISAC 平台（统一试验载体）",
           color=C["blue_dark"], size=12)
body_text (ax, FULL_X0, Y_TOP, FULL_W, H_TOP,
           "USRP N320 + B210 空口链路  ｜  RS 外码（自主实现）+ LDPC 级联编码  ｜  实时视频与雷达感知并发  ｜  YAML 运行时配置",
           size=9, dy=0.50)

# ── 研究内容 1（已完成，实线）────────────────────────────────────────────────
rounded_box(ax, X_L0, Y_MID, COL_W, H_MID,
            fc=C["blue_bg"], ec=C["blue_dark"], lw=1.5)
title_text(ax, X_L0, Y_MID, COL_W, H_MID,
           "研究内容 1（已完成）\n实时视频传输跨层优化",
           color=C["blue_dark"], size=10)
body_text (ax, X_L0, Y_MID, COL_W, H_MID,
           "· RS 外码自主实现\n"
           "  （GF(2⁸), BM 译码 + Chien 搜索 + Forney）\n"
           "· RS Pareto 扫描（K = 223 / 207 / 191 / 179）\n"
           "· 容器误码放大因子 γ 模型与实测\n"
           "· 队列优化：端到端延迟约 250 ms，无累积\n"
           "· 调制 / 码率 / CP 参数边界",
           size=9, dy=0.72)

# ── 研究内容 2（拟研究，虚线）────────────────────────────────────────────────
rounded_box(ax, X_M0, Y_MID, COL_W, H_MID,
            fc=C["white"], ec=C["blue_mid"], lw=1.4, ls=(0,(5,3)))
title_text(ax, X_M0, Y_MID, COL_W, H_MID,
           "研究内容 2（拟研究）\n信道自适应可靠传输",
           color=C["blue_dark"], size=10)
body_text (ax, X_M0, Y_MID, COL_W, H_MID,
           "前提：RS 参数运行时可重构化\n"
           "  （运行期选 K，动态生成生成多项式 g(x)）\n\n"
           "· SNR / 残差统计量构造与信道状态估计\n"
           "· 参数档在线映射与热切换\n"
           "· 吞吐-可靠性联合评估",
           size=9, dy=0.72)

# ── 研究内容 3（拟研究，虚线）────────────────────────────────────────────────
rounded_box(ax, X_R0, Y_MID, COL_W, H_MID,
            fc=C["white"], ec=C["blue_mid"], lw=1.4, ls=(0,(5,3)))
title_text(ax, X_R0, Y_MID, COL_W, H_MID,
           "研究内容 3（拟研究）\n非接触微动感知",
           color=C["blue_dark"], size=10)
body_text (ax, X_R0, Y_MID, COL_W, H_MID,
           "· 导频相位提取 + 收发共模相消\n"
           "· 长时相参积累\n"
           "  （~9.4 s，多普勒分辨率 0.11 Hz）\n"
           "· 呼吸 / 心跳谱估计（谐波剥离 / 倒谱）\n"
           "· 分层目标 C→B→A 递进验证",
           size=9, dy=0.72)

# ── 成果行 ───────────────────────────────────────────────────────────────────
rounded_box(ax, X_L0, Y_BTM, COL_W, H_BTM,
            fc=C["green_bg"], ec=C["green_dark"], lw=1.4)
title_text(ax, X_L0, Y_BTM, COL_W, H_BTM,
           "成果 1（已形成）\n英文期刊论文已完稿",
           color=C["green_dark"], size=9.5)

rounded_box(ax, X_M0, Y_BTM, COL_W, H_BTM,
            fc=C["white"], ec=C["blue_mid"], lw=1.3, ls=(0,(5,3)))
title_text(ax, X_M0, Y_BTM, COL_W, H_BTM,
           "成果 2（预期）\n自适应传输实测对比",
           color=C["blue_dark"], size=9.5)

rounded_box(ax, X_R0, Y_BTM, COL_W, H_BTM,
            fc=C["white"], ec=C["blue_mid"], lw=1.3, ls=(0,(5,3)))
title_text(ax, X_R0, Y_BTM, COL_W, H_BTM,
           "成果 3（预期）\n微动感知与能力评估",
           color=C["blue_dark"], size=9.5)

# ── 底栏 ─────────────────────────────────────────────────────────────────────
rounded_box(ax, FULL_X0, Y_BAR, FULL_W, H_BAR,
            fc=C["red_bg"], ec=C["red_dark"], lw=1.6)
title_text(ax, FULL_X0, Y_BAR, FULL_W, H_BAR,
           "硕士学位论文 + 可复现实验方法与数据集",
           color=C["red_dark"], size=11)

# ── 竖向箭头 ─────────────────────────────────────────────────────────────────
for xc in (X_L, X_M, X_R):
    down_arrow(ax, xc, Y_TOP,            Y_MID + H_MID + 0.04)
    down_arrow(ax, xc, Y_MID,            Y_BTM + H_BTM + 0.04)
    down_arrow(ax, xc, Y_BTM,            Y_BAR + H_BAR + 0.04)

# ── 横向传递箭头（在研究内容行中段） ─────────────────────────────────────────
MID_MID = Y_MID + H_MID * 0.38
horiz_arrow(ax, X_L0 + COL_W + 0.04, X_M0 - 0.04, MID_MID, "方法迁移")
horiz_arrow(ax, X_M0 + COL_W + 0.04, X_R0 - 0.04, MID_MID, "相位基础")

# ── 保存 ─────────────────────────────────────────────────────────────────────
fig.savefig(OUT / "fig_route.png", dpi=300, bbox_inches="tight",
            facecolor="white")
fig.savefig(OUT / "fig_route.pdf", bbox_inches="tight",
            facecolor="white")
print("saved fig_route.png / fig_route.pdf")
