# -*- coding: utf-8 -*-
"""开题报告插图（nature-figure skill / Python 独占后端）

契约
----
核心结论 : 一条 OFDM 波形上，"残差可观测性"由 RS 外码提供 —— 残差探针是视觉焦点。
证据链   : 图1 系统拓扑（谁在链路上）→ 图2 级联编解码（探针在哪）→ 图3 相位处理（感知怎么取相位）。
原型     : schematic-led composite（示意图主导 + 小型示意数据板）。
导出     : SVG 为主（文字可编辑）+ PNG 600 dpi（入 Word）。

几何纪律 : 每个虚线容器顶部预留 3 单位标题头；模块宽度按最长的中文行反算，禁止溢出。
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Polygon, Rectangle
import numpy as np
import os

OUT = r"D:\isac\thesis\figures"
os.makedirs(OUT, exist_ok=True)

# ── 强制字体 / SVG 规则（skill: MANDATORY）────────────────────────────
# font.family 用列表 → 开启 per-glyph fallback：拉丁走 Arial，中文回落 Microsoft YaHei
plt.rcParams["font.family"] = ["Arial", "Microsoft YaHei", "DejaVu Sans"]
plt.rcParams["font.sans-serif"] = ["Arial", "Microsoft YaHei", "DejaVu Sans"]
plt.rcParams["svg.fonttype"] = "none"
plt.rcParams["pdf.fonttype"] = 42
plt.rcParams["font.size"] = 7
plt.rcParams["axes.spines.right"] = False
plt.rcParams["axes.spines.top"] = False
plt.rcParams["legend.frameon"] = False

# ── 调色板：materials / mechanism 系；红色仅作标注 ─────────────────────
INK, MUTE, RED = "#272727", "#606060", "#E53935"
AQUA, TEAL, LILAC, VIOLET = "#77D7D1", "#33B5A5", "#B9A7E8", "#7C6CCF"
CREAM, SAGE = "#E8D9BE", "#C6D8B4"
PALE = {"aqua": "#E4F5F3", "teal": "#D3EEE9", "lilac": "#EFEAF9",
        "violet": "#E2DCF3", "cream": "#F8F2E7", "sage": "#EDF3E4",
        "grey": "#F3F3F3", "white": "#FFFFFF"}


def _mix(h, other, t):
    c, o = h.lstrip("#"), other.lstrip("#")
    v = [int(c[i:i + 2], 16) * (1 - t) + int(o[i:i + 2], 16) * t for i in (0, 2, 4)]
    return "#%02X%02X%02X" % tuple(int(round(x)) for x in v)


def lighten(h, t=0.45):
    return _mix(h, "#FFFFFF", t)


def darken(h, t=0.22):
    return _mix(h, "#000000", t)


def canvas(w_in, xlim, ylim):
    xr, yr = xlim[1] - xlim[0], ylim[1] - ylim[0]
    fig, ax = plt.subplots(figsize=(w_in, w_in * yr / xr))
    ax.set_xlim(*xlim); ax.set_ylim(*ylim)
    ax.set_aspect("equal"); ax.axis("off")
    fig.subplots_adjust(0, 0, 1, 1)
    return fig, ax


def mod(ax, x, y, w, h, text, fill, fs=6.9, ec=INK, lw=0.9, tc=INK, rs=0.9, bold=False, z=4):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={rs}",
                                fc=fill, ec=ec, lw=lw, zorder=z))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs,
            color=tc, zorder=z + 1, linespacing=1.55,
            fontweight="bold" if bold else "normal")


def container(ax, x, y, w, h, stage, tag, tint, ec, lw=1.0, fs=7.6, head=3.0):
    """虚线容器：左上角阶段标签 + 右下角英文模块名；顶部预留 head 单位标题头。"""
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=1.6",
                                fc=PALE[tint], ec=ec, lw=lw, ls=(0, (4, 2.5)), zorder=1))
    ax.text(x + 1.6, y + h - head / 2 - 0.2, stage, ha="left", va="center", fontsize=fs,
            fontweight="bold", color=darken(ec, 0.15), zorder=2)
    ax.text(x + w - 1.6, y + 1.4, tag, ha="right", va="center", fontsize=7.0,
            fontweight="bold", color=darken(ec, 0.1), zorder=2)


def arr(ax, p1, p2, color=INK, lw=0.95, ls="-", ms=7, rad=0.0, z=3):
    ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle="-|>", mutation_scale=ms,
                                 color=color, lw=lw, ls=ls, shrinkA=0.5, shrinkB=0.5,
                                 connectionstyle=f"arc3,rad={rad}", zorder=z))


def route(ax, pts, color=INK, lw=0.95, ls="-", ms=7):
    for a, b in zip(pts[:-2], pts[1:-1]):
        ax.plot([a[0], b[0]], [a[1], b[1]], color=color, lw=lw, ls=ls,
                zorder=3, solid_capstyle="round")
    arr(ax, pts[-2], pts[-1], color=color, lw=lw, ls=ls, ms=ms)


def badge(ax, cx, cy, glyph, r=1.3, fc="#FFFFFF", ec=INK, fs=7.0, tc=INK, z=8):
    ax.add_patch(plt.Circle((cx, cy), r, fc=fc, ec=ec, lw=0.95, zorder=z))
    ax.text(cx, cy, glyph, ha="center", va="center", fontsize=fs, color=tc, zorder=z + 1)


def iso_block(ax, x, y, w, h, d, fill, ec=INK, lw=0.8, z=5):
    ax.add_patch(Polygon([[x, y + h], [x + d, y + h + d], [x + w + d, y + h + d],
                          [x + w, y + h]], closed=True, fc=lighten(fill, 0.55),
                         ec=ec, lw=lw, zorder=z))
    ax.add_patch(Polygon([[x + w, y], [x + w + d, y + d], [x + w + d, y + h + d],
                          [x + w, y + h]], closed=True, fc=darken(fill, 0.18),
                         ec=ec, lw=lw, zorder=z))
    ax.add_patch(Rectangle((x, y), w, h, fc=fill, ec=ec, lw=lw, zorder=z + 1))


def iso_stack(ax, x, y, w, h, d, n, fill, dz=0.9, layer_lines=0, z=5):
    for i in range(n - 1, -1, -1):
        ox, oy = x + i * dz * 0.55, y + i * dz
        iso_block(ax, ox, oy, w, h, d, fill, z=z + (n - 1 - i) * 2)
        for j in range(1, layer_lines + 1):
            yy = oy + j * h / (layer_lines + 1)
            ax.plot([ox, ox + w], [yy, yy], color=darken(fill, 0.12), lw=0.4,
                    zorder=z + (n - 1 - i) * 2 + 1)


def split_slab(ax, x, y, w, h, d, f_info, f_par, k_frac, z=6):
    w1 = w * k_frac
    iso_block(ax, x, y, w1, h, d, f_info, z=z)
    iso_block(ax, x + w1, y, w - w1, h, d, f_par, ec=RED, z=z)


def iso_plate(ax, x, y, w, h, d, data, cmap, z=5):
    ax.add_patch(Polygon([[x, y + h], [x + d, y + h + d], [x + w + d, y + h + d],
                          [x + w, y + h]], closed=True, fc="#EDEDED", ec=INK,
                         lw=0.8, zorder=z))
    ax.add_patch(Polygon([[x + w, y], [x + w + d, y + d], [x + w + d, y + h + d],
                          [x + w, y + h]], closed=True, fc="#D9D9D9", ec=INK,
                         lw=0.8, zorder=z))
    ax.imshow(data, extent=(x, x + w, y, y + h), cmap=cmap, aspect="auto", zorder=z + 1)
    ax.add_patch(Rectangle((x, y), w, h, fc="none", ec=INK, lw=0.8, zorder=z + 2))


def legend_strip(ax, items, y, x0=1.8, dx=25.0, fs=7.0):
    for i, (kind, txt) in enumerate(items):
        x = x0 + i * dx
        if kind == "arrow":
            arr(ax, (x, y), (x + 2.4, y), ms=6.5)
        elif kind == "dash":
            arr(ax, (x, y), (x + 2.4, y), color=RED, ls=(0, (2.5, 1.8)), ms=6.5)
        elif kind == "tensor":
            iso_block(ax, x + 0.3, y - 0.9, 1.7, 1.4, 0.5, AQUA, lw=0.7, z=6)
        elif kind == "module":
            ax.add_patch(FancyBboxPatch((x + 0.2, y - 0.8), 2.1, 1.6,
                                        boxstyle="round,pad=0,rounding_size=0.35",
                                        fc=PALE["aqua"], ec=INK, lw=0.8, zorder=6))
        elif kind == "badge":
            badge(ax, x + 1.2, y, "⊗", r=0.85, fs=6.5)
        elif kind == "probe":
            badge(ax, x + 1.2, y, "◇", r=0.85, fs=6.5, ec=RED, tc=RED)
        ax.text(x + 3.4, y, txt, fontsize=fs, ha="left", va="center", color=MUTE)


def save(fig, name):
    fig.savefig(os.path.join(OUT, name + ".svg"), bbox_inches="tight", pad_inches=0.03)
    fig.savefig(os.path.join(OUT, name + ".png"), dpi=600, bbox_inches="tight",
                pad_inches=0.03, facecolor="white")
    plt.close(fig)
    print("saved", name)


# ── 示意数据（仅用于数据板，图上明确标注"示意"）──────────────────────
def rd_map(seed=3):
    rng = np.random.default_rng(seed)
    ny, nx = 46, 62
    yy, xx = np.mgrid[0:ny, 0:nx]
    z = 0.10 * rng.random((ny, nx))
    z += 0.45 * np.exp(-((yy - ny / 2) ** 2) / (2 * 2.2 ** 2))
    z += np.exp(-(((xx - 38) ** 2) / (2 * 1.5 ** 2) + ((yy - 32) ** 2) / (2 * 1.5 ** 2)))
    return z


def psd_curve():
    f = np.linspace(0.02, 2.4, 700)
    g = lambda f0, a, s: a * np.exp(-((f - f0) ** 2) / (2 * s ** 2))
    return f, (g(0.30, 1.0, 0.035) + g(0.60, 0.42, 0.035) + g(0.90, 0.22, 0.035)
               + g(1.25, 0.26, 0.030) + g(1.55, 0.12, 0.030) + 0.012)


# ═══════════════════════════ 图 1　系统拓扑 ═══════════════════════════
def fig_topology():
    fig, ax = canvas(12.0, (0, 112), (0, 58))
    legend_strip(ax, [("arrow", "视频业务数据流"), ("dash", "空口链路 / 感知回波"),
                      ("tensor", "码字 / 帧张量"), ("module", "平台处理模块"),
                      ("badge", "算子")], 56.0, dx=22.0)

    # 视频源
    container(ax, 0.8, 33.0, 12.0, 15.0, "视频源", "CAMERA", "cream", "#B99A5E", head=2.6)
    iso_stack(ax, 2.6, 38.5, 4.6, 2.8, 1.3, 3, CREAM, dz=0.95, layer_lines=1)
    ax.text(6.8, 36.6, "640×480 @ 20 fps", fontsize=6.3, ha="center", va="center", color=MUTE)
    arr(ax, (13.0, 40.0), (15.0, 40.0))

    # N320
    container(ax, 15.0, 12.0, 36.0, 40.0, "USRP N320（基站 BS · 单站自发自收）",
              "BASE STATION", "aqua", TEAL, head=3.2)
    mod(ax, 16.6, 40.5, 32.8, 7.6,
        "组帧：2 B 长度前缀 ＋ H.264 裸流\nRS(255, K) 外码 ＋ LDPC(1008, 504) 内码",
        "#FFFFFF", fs=6.7)
    mod(ax, 16.6, 31.4, 32.8, 7.6,
        "OFDM：1024-FFT / CP 128 / 50 MHz\n帧长 2.304 ms（≈434 帧/s）· QPSK / 16QAM",
        "#FFFFFF", fs=6.7)
    mod(ax, 16.6, 22.6, 32.8, 7.2,
        "感知处理：距离-多普勒 → 距离门相位\n（研究内容 3 的数据入口）", "#FFFFFF", fs=6.7)
    split_slab(ax, 18.4, 16.6, 7.2, 1.5, 1.1, AQUA, "#F3C9C7", 0.74)
    ax.text(28.0, 17.4, "码字块 255 B = K 信息 ＋ 32 B 校验", fontsize=6.0,
            ha="left", va="center", color=MUTE)
    ax.text(16.6, 13.6, "自干扰抑制：天线空间隔离 ＋ 可调衰减器", fontsize=6.2,
            ha="left", va="center", color=MUTE)
    arr(ax, (33.0, 40.5), (33.0, 39.2))
    arr(ax, (33.0, 31.4), (33.0, 30.0))

    # 天线 + 空口
    for cx in (32.0, 84.0):
        ax.plot([cx, cx], [52.2, 53.6], color=INK, lw=1.0, zorder=6)
        ax.add_patch(Polygon([[cx - 1.2, 53.6], [cx + 1.2, 53.6], [cx, 55.4]],
                             closed=True, fc=AQUA, ec=INK, lw=0.9, zorder=6))
    ax.annotate("", xy=(82.4, 54.6), xytext=(33.6, 54.6),
                arrowprops=dict(arrowstyle="<|-|>", color=RED, lw=1.0,
                                linestyle=(0, (4, 2.5)), shrinkA=0, shrinkB=0))
    ax.text(58.0, 53.4, "空口链路 3.1 GHz · 室内视距 ≈ 5 m", ha="center", va="top",
            fontsize=6.8, color=RED)

    # B210
    container(ax, 66.0, 16.0, 34.4, 36.0, "USRP B210（用户设备 UE）", "USER EQUIPMENT",
              "lilac", VIOLET, head=3.2)
    mod(ax, 67.6, 40.5, 31.2, 7.2, "OFDM 解调 ＋ ZF 均衡\n信道估计", "#FFFFFF", fs=6.7)
    mod(ax, 67.6, 31.4, 31.2, 7.6, "LDPC 软译码 → RS 外码译码\n→ 载荷还原（前缀截取）",
        "#FFFFFF", fs=6.7)
    mod(ax, 67.6, 22.6, 31.2, 7.2, "H.264 容错解码\n四级队列（深度 4–8）", "#FFFFFF", fs=6.7)
    arr(ax, (83.2, 40.5), (83.2, 39.2))
    arr(ax, (83.2, 31.4), (83.2, 30.0))

    # 显示
    mod(ax, 101.2, 40.0, 9.6, 4.6, "显示\n≈ 250 ms", PALE["cream"], ec="#B99A5E", fs=6.6)
    arr(ax, (100.6, 42.3), (101.2, 42.3))

    # 人体 + 回波（唯一强调色）
    container(ax, 48.0, 1.6, 18.0, 10.4, "人体目标", "HUMAN TARGET", "grey", "#9E9E9E",
              head=2.6)
    ax.text(57.0, 7.0, "呼吸 0.1–0.5 Hz\n心跳 0.8–2.0 Hz", ha="center", va="center",
            fontsize=6.6, color=INK, linespacing=1.6)
    arr(ax, (57.0, 12.2), (57.0, 51.6), color=RED, ls=(0, (4, 2.5)), lw=1.0)
    ax.text(58.2, 32.0, "回波（胸壁微动）  Δφ = 4πd/λ，λ ≈ 85.7 mm", rotation=90,
            ha="left", va="center", fontsize=6.3, color=RED)

    # 研究内容归属
    for i, (t, tint, ec) in enumerate([("研究内容 1（已完成）", "teal", TEAL),
                                      ("研究内容 2（拟研究）", "aqua", TEAL),
                                      ("研究内容 3（拟研究）", "lilac", VIOLET)]):
        ax.add_patch(FancyBboxPatch((0.8, 24.0 - i * 4.4), 11.4, 3.2,
                                    boxstyle="round,pad=0,rounding_size=0.7",
                                    fc=PALE[tint], ec=ec, lw=0.85, zorder=5))
        ax.text(6.5, 25.6 - i * 4.4, t, ha="center", va="center", fontsize=6.4,
                color=darken(ec, 0.2), zorder=6)
    save(fig, "fig_topology_v2")


# ═══════════════════════ 图 2　级联纠错编码链路 ═══════════════════════
def fig_coding():
    fig, ax = canvas(9.8, (0, 108), (0, 62))
    legend_strip(ax, [("arrow", "数据流方向"), ("tensor", "码字 / 内码张量"),
                      ("probe", "残差判据点"), ("dash", "红色标注")], 60.0)

    ax.text(54, 57.2,
            "四档配置   K=223（32 B 校验, 14.3%, T=16, Pareto 最优）｜ K=207（48 B, 23.2%, T=24）"
            "｜ K=191（64 B, 33.5%, T=32）｜ K=179（76 B, 42.5%, T=38）",
            ha="center", va="center", fontsize=6.5, color=MUTE)

    W, H = 15.0, 8.6
    XS = [2.4, 19.2, 36.0, 52.8, 69.6, 86.4]

    # TX
    container(ax, 1.2, 36.0, 105.6, 19.0, "发送链路（TX）", "TRANSMIT", "aqua", TEAL, head=3.0)
    ty = 38.6
    tx = [("视频帧\nH.264 裸 Annex B", CREAM, "#B99A5E"),
          ("组帧\n2 B 长度前缀", CREAM, "#B99A5E"),
          ("信息分块\n≤ K−2 B / 块", CREAM, "#B99A5E"),
          ("RS(255, K)\n系统式外码", LILAC, VIOLET),
          ("LDPC(1008, 504)\n内码", AQUA, TEAL),
          ("交织 / 加扰\nOFDM 映射", AQUA, TEAL)]
    for i, (t, f, e) in enumerate(tx):
        mod(ax, XS[i], ty, W, H, t, lighten(f, 0.62), ec=e, fs=6.8)
        if i:
            arr(ax, (XS[i - 1] + W, ty + H / 2), (XS[i], ty + H / 2))
    # 码字块：紧贴 RS 模块上方，表达"信息 + 校验"结构
    split_slab(ax, 55.2, 49.8, 7.6, 1.6, 1.1, AQUA, "#F3C9C7", 0.74)
    ax.text(64.2, 50.6, "255 B = K 信息 ＋ 32 B 校验", fontsize=6.1, ha="left",
            va="center", color=MUTE)
    ax.plot([60.0, 60.0], [48.4, 49.8], color=MUTE, lw=0.6, ls=(0, (2, 1.6)), zorder=4)

    # 信道
    mod(ax, 26.0, 29.5, 56.0, 4.2,
        "OFDM 空口信道 · 3.1 GHz · 50 MHz · QPSK / 16QAM · 帧长 2.304 ms",
        "#FFFFFF", fs=6.8, ec=TEAL)
    arr(ax, (93.9, ty), (93.9, 33.7))
    arr(ax, (93.9, 29.5), (93.9, 26.6))

    # RX（右 → 左）
    container(ax, 1.2, 7.0, 105.6, 19.0, "接收链路（RX）", "RECEIVE", "lilac", VIOLET, head=3.0)
    ry = 9.6
    rx = [("H.264 容错解码\n四级队列 4–8", CREAM, "#B99A5E"),
          ("载荷还原\n前缀截取 / 降级投递", CREAM, "#B99A5E"),
          ("三级判决\n无错・已纠正・不可纠", CREAM, "#B99A5E"),
          ("RS(255, K) 译码\n伴随式→BM→Chien→Forney", LILAC, VIOLET),
          ("LDPC 软译码\n6 次迭代・无收敛标志", AQUA, TEAL),
          ("OFDM 解调\n解交织 / 软解扰", AQUA, TEAL)]
    for i, (t, f, e) in enumerate(rx):
        mod(ax, XS[i], ry, W, H, t, lighten(f, 0.62), ec=e, fs=6.8)
    for i in range(5, 0, -1):
        arr(ax, (XS[i], ry + H / 2), (XS[i - 1] + W, ry + H / 2))

    # 残差探针
    px = XS[3]
    ax.add_patch(FancyBboxPatch((px - 1.0, ry - 1.0), W + 2.0, H + 2.0,
                                boxstyle="round,pad=0,rounding_size=1.2",
                                fc="none", ec=RED, lw=1.3, ls=(0, (3.5, 2)), zorder=9))
    badge(ax, px + W / 2, ry + H + 2.4, "◇", r=1.4, ec=RED, tc=RED, fs=7.2)
    ax.annotate("RS 伴随式 ＝ 本链路唯一在带内残差判据 → RS 不可纠率（fail_rate）统计点",
                xy=(px + W / 2, ry - 1.2), xytext=(px + W / 2, 1.2),
                ha="center", va="bottom", fontsize=6.8, color=RED,
                arrowprops=dict(arrowstyle="-|>", color=RED, lw=0.95))
    save(fig, "fig_coding_chain")


# ═══════════════════════ 图 3　微动感知处理 ═══════════════════════
def fig_sensing():
    fig, ax = canvas(9.8, (0, 108), (0, 64))
    legend_strip(ax, [("arrow", "处理流向"), ("tensor", "相位数据张量"),
                      ("badge", "算子"), ("dash", "红色标注 = 定量预算")], 61.6)

    # ① 回波获取
    container(ax, 1.2, 41.0, 105.6, 18.0, "① 回波获取与距离门分离", "RANGE–DOPPLER",
              "aqua", TEAL, head=3.0)
    ay, ah, aw = 47.4, 6.4, 17.0
    axs = [3.0, 22.6, 42.2]
    a = [("OFDM 解调输出\n导频相位 ＋ ZF 均衡", AQUA, TEAL),
         ("距离-多普勒处理\n分辨率 ≈ 3 m", AQUA, TEAL),
         ("目标距离门选取\n（人体所在单元）", AQUA, TEAL)]
    for i, (t, f, e) in enumerate(a):
        mod(ax, axs[i], ay, aw, ah, t, lighten(f, 0.62), ec=e, fs=6.8)
        if i:
            arr(ax, (axs[i - 1] + aw, ay + ah / 2), (axs[i], ay + ah / 2))
    iso_plate(ax, 61.8, 46.2, 15.0, 7.6, 1.5, rd_map(), "magma")
    ax.text(61.8, 44.9, "距离-多普勒图（示意）", fontsize=6.1, color=MUTE, ha="left")
    ax.annotate("", xy=(69.6, 53.3), xytext=(69.6, 49.4),
                arrowprops=dict(arrowstyle="-|>", color=RED, lw=0.85))
    ax.text(70.4, 51.2, "目标", fontsize=6.0, color=RED, ha="left", va="center")
    arr(ax, (59.4, ay + ah / 2), (61.8, 49.6), rad=-0.12)

    mod(ax, 80.0, 47.4, 12.0, 6.4, "共模相消\nφ_t − φ_r", PALE["lilac"], ec=VIOLET, fs=6.8)
    arr(ax, (78.6, 50.6), (80.0, 50.6))
    mod(ax, 80.0, 42.4, 12.0, 4.0, "直耦泄漏参考门", "#FFFFFF", ec="#9E9E9E", fs=6.3)
    arr(ax, (86.0, 46.4), (86.0, 47.4), color=RED)
    badge(ax, 86.0, 55.6, "⊗", r=1.4, fs=7.2)
    ax.plot([86.0, 86.0], [54.2, 53.8], color=INK, lw=0.6, ls=(0, (1.6, 1.4)), zorder=6)

    iso_block(ax, 95.6, 46.4, 8.4, 6.4, 1.2, LILAC, z=6)
    ph = np.linspace(0, 4 * np.pi, 300)
    wave = np.sin(ph) * 0.30 + 0.10 * np.sin(3.1 * ph)
    ax.plot(96.2 + np.linspace(0, 7.2, wave.size), 49.6 + wave * 2.4,
            color=VIOLET, lw=0.7, zorder=9)
    ax.text(99.8, 47.4, "φ_t(n)", fontsize=6.1, color=darken(VIOLET), ha="center", zorder=9)
    arr(ax, (92.2, 50.6), (95.6, 50.6))

    # ② 相位域处理
    container(ax, 1.2, 26.0, 105.6, 12.0, "② 相位域处理（抑制载波相位漂移）",
              "PHASE DOMAIN", "violet", VIOLET, head=3.0)
    by, bh, bw = 28.2, 6.0, 26.0
    bxs = [3.0, 36.8, 70.6]
    b = [("相位差分 ＋\n高通-带通级联滤波", LILAC, VIOLET),
         ("长时相参积累\n4096 点 ≈ 9.4 s", TEAL, TEAL),
         ("频率分辨率\n< 0.11 Hz", TEAL, TEAL)]
    for i, (t, f, e) in enumerate(b):
        mod(ax, bxs[i], by, bw, bh, t, lighten(f, 0.62), ec=e, fs=6.8)
        if i:
            arr(ax, (bxs[i - 1] + bw, by + bh / 2), (bxs[i], by + bh / 2))
    route(ax, [(99.8, 46.4), (99.8, 39.6), (16.0, 39.6), (16.0, by + bh)])

    # ③ 谱分离（右下）
    container(ax, 38.0, 2.0, 68.8, 19.0, "③ 谱分离与参数估计", "SPECTRAL SPLIT",
              "sage", "#6E8F52", head=3.0)
    dy, dh, dw = 4.6, 6.4, 19.0
    dxs = [39.8, 61.4, 83.0]
    d = [("呼吸带 0.1–0.5 Hz\n呼吸率估计", lighten(SAGE, 0.55), "#6E8F52"),
         ("呼吸谐波剥离\n逐分量 / 倒谱", lighten(CREAM, 0.45), "#B99A5E"),
         ("心跳带 0.8–2.0 Hz\n心率估计", "#F3C9C7", RED)]
    for i, (t, f, e) in enumerate(d):
        mod(ax, dxs[i], dy, dw, dh, t, f, ec=e, fs=6.5)
    arr(ax, (dxs[1] + dw, dy + dh / 2), (dxs[2], dy + dh / 2))

    # 相位谱示意曲线（置于容器内模块上方，避开标题头）
    f_, p_ = psd_curve()
    px0, pw0, py0, ph0 = 40.2, 26.0, 12.6, 3.4
    ax.plot(px0 + (f_ / f_.max()) * pw0, py0 + p_ / p_.max() * ph0,
            color=VIOLET, lw=0.9, zorder=8)
    for fx, lb in [(0.30, "f_r"), (1.25, "f_h")]:
        xx = px0 + (fx / f_.max()) * pw0
        ax.plot([xx, xx], [py0, py0 + ph0], color=RED, lw=0.55, ls=(0, (2, 1.6)), zorder=7)
        ax.text(xx, py0 - 0.9, lb, fontsize=5.9, color=RED, ha="center", zorder=8)
    ax.text(px0, py0 + ph0 + 0.45, "相位谱（示意）", fontsize=6.1, color=MUTE, ha="left")

    route(ax, [(83.5, by), (83.5, 23.4), (52.0, 23.4), (52.0, dy + dh)])
    route(ax, [(83.5, 23.4), (70.0, 23.4), (70.0, dy + dh)])
    ax.plot([83.5], [23.4], marker="o", ms=3.0, color=INK, zorder=4)

    # 预算卡片（左下，唯一强调色边框）
    ax.add_patch(FancyBboxPatch((1.2, 2.0), 34.6, 19.0,
                                boxstyle="round,pad=0,rounding_size=1.4",
                                fc="#FFFFFF", ec=RED, lw=1.1, zorder=5))
    ax.text(2.8, 18.9, "相位灵敏度预算", fontsize=7.4, color=RED, fontweight="bold",
            ha="left", va="center", zorder=6)
    ax.text(2.8, 16.4, "λ ≈ 85.7 mm @ 3.5 GHz", fontsize=6.4, color=RED,
            ha="left", va="center", zorder=6)
    ax.text(2.8, 13.6, "呼吸  4–8 mm → Δφ ≈ 34°–67°", fontsize=6.5, color=INK,
            ha="left", va="center", zorder=6)
    ax.text(2.8, 11.4, "心跳  0.2–0.5 mm → Δφ ≈ 1.7°–4°", fontsize=6.5, color=INK,
            ha="left", va="center", zorder=6)
    ax.text(2.8, 9.2, "（受系统相位噪声底限制，需先标定）", fontsize=6.1, color=MUTE,
            ha="left", va="center", zorder=6)
    ax.plot([2.8, 34.2], [8.2, 8.2], color="#EFC9C7", lw=0.7, zorder=6)
    for i, (t, tint, ec) in enumerate([("目标 C", "teal", TEAL), ("目标 B", "aqua", TEAL),
                                      ("目标 A", "lilac", VIOLET)]):
        ax.add_patch(FancyBboxPatch((2.8 + i * 10.8, 5.4), 9.6, 2.2,
                                    boxstyle="round,pad=0,rounding_size=0.55",
                                    fc=PALE[tint], ec=ec, lw=0.8, zorder=6))
        ax.text(7.6 + i * 10.8, 6.5, t, ha="center", va="center", fontsize=6.3,
                color=darken(ec, 0.2), zorder=7)
    ax.text(2.8, 3.4, "递进验证：能力基线 → 呼吸率 → 双参数", fontsize=5.9, color=MUTE,
            ha="left", va="center", zorder=6)
    save(fig, "fig_sensing")


if __name__ == "__main__":
    fig_topology()
    fig_coding()
    fig_sensing()
