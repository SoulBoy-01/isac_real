# -*- coding: utf-8 -*-
"""开题报告插图：参考"粉彩圆角框 + 虚线分组 + 顶部矢量图例"的架构图风格。
   fig_topology_v2  : 系统拓扑
   fig_coding_chain : 级联纠错编码链路架构
   fig_sensing      : 非接触微动感知处理架构
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Polygon
import os

OUT = r"D:\isac\thesis\figures"
matplotlib.rcParams.update({
    "font.sans-serif": ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "DejaVu Sans"],
    "axes.unicode_minus": False, "font.size": 10,
    "svg.fonttype": "none", "pdf.fonttype": 42,
})

INK, GRN, RED, MUTE = "#1f2933", "#2f6f5f", "#b03a2e", "#5b6770"
C = dict(mint="#cfe9e3", cream="#f7efdc", lilac="#e6d8ec", pink="#f8d7da",
         blue="#d8e8f6", sage="#e2ead4", sand="#f2e3c9", white="#ffffff",
         rose="#f6dfe0", teal="#bfe0d8")


def canvas(w, h, xlim, ylim):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(*xlim); ax.set_ylim(*ylim)
    ax.set_aspect("equal"); ax.axis("off")
    return fig, ax


def box(ax, x, y, w, h, text, fill="#ffffff", fs=9.2, bold=False, ec=INK,
        lw=1.3, rs=1.1, tc=INK, z=4):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={rs}",
                                fc=fill, ec=ec, lw=lw, zorder=z))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs,
            color=tc, fontweight="bold" if bold else "normal", zorder=z + 1,
            linespacing=1.5)


def grp(ax, x, y, w, h, label=None, fc="#eaf6f2", ec=GRN, ls=(0, (7, 5)),
        lw=2.0, fs=11, lab=None):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=1.8",
                                fc=fc, ec=ec, lw=lw, ls=ls, zorder=1))
    if label:
        lx, ly = lab if lab else (x + w / 2, y + h - 1.8)
        ax.text(lx, ly, label, ha="center", va="center", fontsize=fs,
                fontweight="bold", color=ec, zorder=2)


def arr(ax, p1, p2, color=INK, lw=1.6, ls="-", ms=11, rad=0.0, z=3):
    ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle="-|>", mutation_scale=ms,
                                 color=color, lw=lw, ls=ls, shrinkA=1, shrinkB=1,
                                 connectionstyle=f"arc3,rad={rad}", zorder=z))


def legend(ax, items, y, x0=2.5, dx=26, fs=9.4):
    for i, (kind, txt) in enumerate(items):
        x = x0 + i * dx
        if kind == "arrow":
            arr(ax, (x, y), (x + 2.8, y), lw=1.6, ms=10)
        elif kind == "dash":
            arr(ax, (x, y), (x + 2.8, y), color=RED, lw=1.7, ls=(0, (3, 2)), ms=10)
        elif kind == "group":
            ax.add_patch(FancyBboxPatch((x, y - 0.75), 2.8, 1.5,
                                        boxstyle="round,pad=0,rounding_size=0.4",
                                        fc="#eaf6f2", ec=GRN, lw=1.3, ls=(0, (3, 2)), zorder=6))
        elif kind == "node":
            ax.add_patch(FancyBboxPatch((x + 0.3, y - 0.75), 2.2, 1.5,
                                        boxstyle="round,pad=0,rounding_size=0.4",
                                        fc=C["lilac"], ec=INK, lw=1.1, zorder=6))
        elif kind == "probe":
            ax.add_patch(FancyBboxPatch((x + 0.2, y - 0.85), 2.4, 1.7,
                                        boxstyle="round,pad=0,rounding_size=0.4",
                                        fc="none", ec=RED, lw=1.7, ls=(0, (3, 2)), zorder=6))
        ax.text(x + 3.8, y, txt, fontsize=fs, ha="left", va="center", color=MUTE)


def pill(ax, x, y, w, h, text, fill, ec, fs=9):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.8",
                                fc=fill, ec=ec, lw=1.2, zorder=5))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs,
            color=ec, fontweight="bold", zorder=6)


def antenna(ax, cx, y0, y1):
    ax.plot([cx, cx], [y0, y1 - 1.1], color=INK, lw=1.8, zorder=6)
    ax.add_patch(Polygon([[cx - 1.0, y1 - 1.1], [cx + 1.0, y1 - 1.1], [cx, y1]],
                         closed=True, fc=C["blue"], ec=INK, lw=1.4, zorder=7))


def save(fig, name):
    for ext, kw in (("png", dict(dpi=300)), ("svg", {})):
        p = os.path.join(OUT, f"{name}.{ext}")
        fig.savefig(p, bbox_inches="tight", pad_inches=0.14, facecolor="white", **kw)
    plt.close(fig)
    print("saved", name)


def route(ax, pts, color=INK, lw=1.5, ls="-", ms=11):
    """肘形连线：前段折线 + 末段箭头。跨阶段走总线，避免斜线穿过方框。"""
    for a, b in zip(pts[:-2], pts[1:-1]):
        ax.plot([a[0], b[0]], [a[1], b[1]], color=color, lw=lw, ls=ls,
                zorder=3, solid_capstyle="round")
    arr(ax, pts[-2], pts[-1], color=color, lw=lw, ls=ls, ms=ms)


def junction(ax, p, color=INK):
    ax.plot([p[0]], [p[1]], marker="o", ms=6, color=color, zorder=3)


# ══════════════════ 图 1  系统拓扑 ══════════════════
def fig_topology():
    fig, ax = canvas(14.0, 7.0, (0, 108), (0, 56))
    legend(ax, [("arrow", "视频业务数据流"), ("dash", "空口链路 / 感知回波"),
                ("group", "平台分组"), ("node", "平台子模块")], 53.5)

    box(ax, 1, 34, 13, 7, "摄像机 / 视频源\n640×480 @ 20 fps", C["cream"], fs=8.8)
    arr(ax, (14, 37.5), (16, 37.5))

    # N320
    grp(ax, 16, 12, 35, 34, "USRP N320（基站 BS · 单站自发自收）", lab=(33.5, 43.4))
    box(ax, 18, 33.5, 31, 8,
        "组帧：2 B 长度前缀 ＋ H.264 裸流\nRS(255,K) 外码 ＋ LDPC(1008,504) 内码",
        C["lilac"], fs=8.6)
    box(ax, 18, 24.5, 31, 8,
        "OFDM：1024-FFT / CP 128 / 50 MHz\n帧长 2.304 ms（≈434 帧/s）· QPSK/16QAM",
        C["blue"], fs=8.6)
    box(ax, 18, 16.5, 31, 7,
        "感知处理：距离-多普勒 → 距离门相位\n（研究内容 3 的数据入口）", C["sage"], fs=8.6)
    box(ax, 18, 13, 31, 2.8, "自干扰抑制：天线空间隔离 ＋ 可调衰减器", C["pink"], fs=8.0)
    arr(ax, (33.5, 33.5), (33.5, 32.5))
    arr(ax, (33.5, 24.5), (33.5, 23.5))
    antenna(ax, 33.5, 46, 48.6)

    # B210
    grp(ax, 63, 22, 32, 24, "USRP B210（用户设备 UE）", fc="#eef4fb", ec="#2f5f8f",
        lab=(79, 43.4))
    box(ax, 65, 35.5, 28, 6.5, "OFDM 解调 ＋ ZF 均衡 / 信道估计", C["blue"], fs=8.6)
    box(ax, 65, 27, 28, 6.5, "LDPC 软译码 → RS 外码译码\n→ 载荷还原（前缀截取）",
        C["lilac"], fs=8.6)
    box(ax, 65, 23, 28, 2.8, "H.264 容错解码 ＋ 四级队列（4–8）", C["cream"], fs=8.0)
    arr(ax, (79, 35.5), (79, 33.5))
    arr(ax, (79, 27), (79, 25.8))
    antenna(ax, 79, 46, 48.6)

    # 空口链路
    ax.plot([34.7, 77.8], [47.4, 47.4], color=RED, lw=2.0, ls=(0, (6, 4)), zorder=5)
    ax.text(56.2, 49.2, "空口链路：3.1 GHz · 室内视距 ≈ 5 m", ha="center",
            va="bottom", fontsize=9.4, color=RED)

    # 显示
    box(ax, 95.3, 34, 11.7, 6.5, "显示\n端到端 ≈ 250 ms", C["cream"], fs=9)
    arr(ax, (95, 37.2), (95.3, 37.2))

    # 人体与回波
    box(ax, 47, 2, 15, 8.5, "人体目标\n呼吸 0.1–0.5 Hz\n心跳 0.8–2.0 Hz", C["rose"], fs=8.8)
    arr(ax, (54.5, 10.5), (54.5, 45.6), color=RED, ls=(0, (5, 4)), lw=1.8)
    ax.text(56.4, 27, "回波（胸壁微动）\nΔφ = 4πd/λ，λ ≈ 85.7 mm", rotation=90,
            ha="left", va="center", fontsize=8.6, color=RED)

    # 研究内容归属
    pill(ax, 1, 26, 14, 4, "研究内容 1（已完成）", C["teal"], GRN, fs=8.6)
    pill(ax, 1, 21, 14, 4, "研究内容 2（拟研究）", "#dce8f7", "#2f5f8f", fs=8.6)
    pill(ax, 1, 16, 14, 4, "研究内容 3（拟研究）", C["lilac"], "#6b4b7a", fs=8.6)

    save(fig, "fig_topology_v2")


# ══════════════════ 图 2  级联纠错编码链路 ══════════════════
def fig_coding():
    fig, ax = canvas(14.4, 7.8, (0, 108), (0, 62))
    legend(ax, [("arrow", "数据流方向"), ("node", "外码 / 内码级"),
                ("probe", "残差判据点"), ("group", "链路分组")], 60)

    ax.text(54, 57.6,
            "四档配置（K / 校验字节 / 冗余 / 纠错能力 T）：K=223（32 B, 14.3%, T=16，Pareto 最优）"
            "｜ K=207（48 B, 23.2%, T=24）", ha="center", va="center", fontsize=8.6, color=MUTE)
    ax.text(54, 55.4, "K=191（64 B, 33.5%, T=32）｜ K=179（76 B, 42.5%, T=38）",
            ha="center", va="center", fontsize=8.6, color=MUTE)

    W, TH = 15.2, 9.5
    XS = [3.0, 19.6, 36.2, 52.8, 69.4, 86.0]

    # TX
    grp(ax, 1.5, 36, 105, 17.5, "发送链路（TX）", lab=(96, 51.7))
    ty = 39.5
    tx = [("视频帧\n640×480 @ 20 fps\nH.264 裸 Annex B", C["cream"]),
          ("组帧\n2 B 长度前缀\n＋ 有效载荷", C["sand"]),
          ("信息分块\n≤ K−2 字节 / 块\n末块零填充", C["sand"]),
          ("RS(255, K)\n系统式外码编码\n32 B 校验", C["lilac"]),
          ("LDPC(1008,504)\n内码编码\n码率 ≈ 0.5", C["blue"]),
          ("交织 / 加扰\nOFDM 映射\n1024-FFT, CP 128", C["blue"])]
    for i, (t, f) in enumerate(tx):
        box(ax, XS[i], ty, W, TH, t, f, fs=8.6)
        if i:
            arr(ax, (XS[i - 1] + W, ty + TH / 2), (XS[i], ty + TH / 2))

    box(ax, 24, 28.5, 60, 4.6,
        "OFDM 空口信道 · 3.1 GHz · 50 MHz · QPSK / 16QAM · 帧长 2.304 ms",
        C["white"], fs=9.0, ec=GRN, lw=1.4)
    arr(ax, (93.6, ty), (93.6, 33.1))
    arr(ax, (93.6, 28.5), (93.6, 25.6))

    # RX（右 → 左）
    grp(ax, 1.5, 7.5, 105, 18, "接收链路（RX）", fc="#fdf1f1", ec=RED, lab=(96, 23.3))
    ry = 11.0
    rx = [("H.264 容错解码\n四级队列 4–8\n端到端 ≈ 250 ms", C["cream"]),
          ("载荷还原\n前缀截取（零填充对齐）\n不可纠则降级投递", C["sand"]),
          ("三级判决\n无错 / 已纠正\n/ 不可纠", C["sand"]),
          ("RS(255,K) 译码\n伴随式 → BM\n→ Chien → Forney", C["lilac"]),
          ("LDPC 软译码\n固定 6 次迭代\n无收敛标志 / 无 CRC", C["blue"]),
          ("OFDM 解调\n解交织 / 软解扰\n（LLR 域）", C["blue"])]
    for i, (t, f) in enumerate(rx):
        box(ax, XS[i], ry, W, TH, t, f, fs=8.6)
    for i in range(5, 0, -1):
        arr(ax, (XS[i], ry + TH / 2), (XS[i - 1] + W, ry + TH / 2))

    # 残差判据高亮（RS 译码：XS[3]）
    ax.add_patch(FancyBboxPatch((XS[3] - 0.9, ry - 0.9), W + 1.8, TH + 1.8,
                                boxstyle="round,pad=0,rounding_size=1.4",
                                fc="none", ec=RED, lw=2.2, ls=(0, (4, 3)), zorder=8))
    ax.annotate("RS 伴随式 ＝ 本链路唯一在带内残差判据\n→ RS 不可纠率（fail_rate）的统计点",
                xy=(XS[3] + W / 2, ry - 1.2), xytext=(XS[3] + W / 2, 1.2),
                ha="center", va="bottom", fontsize=9.0, color=RED,
                arrowprops=dict(arrowstyle="-|>", color=RED, lw=1.5))
    save(fig, "fig_coding_chain")


# ══════════════════ 图 3  微动感知处理架构 ══════════════════
def fig_sensing():
    fig, ax = canvas(14.0, 7.6, (0, 108), (0, 58))
    legend(ax, [("arrow", "处理流向"), ("node", "相位域处理"),
                ("probe", "定量预算"), ("group", "处理阶段")], 56.8)

    # ── ① 回波获取（单行四步 + 参考门 + 共模相消）──
    grp(ax, 1.5, 37.0, 105, 17.5,
        "① 回波获取与距离门分离（单站自发自收 · 直耦泄漏作参考门）", lab=(38, 53.0))
    ay, ah, aw = 44.5, 7.5, 18.0
    axs = [2.5, 23.0, 43.5, 64.0]
    a = [("OFDM 解调输出\n导频相位 ＋ ZF 均衡", C["blue"]),
         ("距离-多普勒处理\n距离分辨率 ≈ 3 m", C["sage"]),
         ("目标距离门选取\n（人体所在距离单元）", C["sage"]),
         ("目标相位序列\nφ_t(n) = 4πd(n)/λ", C["lilac"])]
    for i, (t, f) in enumerate(a):
        box(ax, axs[i], ay, aw, ah, t, f, fs=8.6)
        if i:
            arr(ax, (axs[i - 1] + aw, ay + ah / 2), (axs[i], ay + ah / 2))

    box(ax, 85.0, ay, 19.0, ah, "共模相消\nΔφ(n) = φ_t − φ_r", C["lilac"], fs=8.6)
    arr(ax, (82.0, ay + ah / 2), (85.0, ay + ah / 2))
    box(ax, 64.0, 37.5, 18.0, 5.5, "直耦泄漏参考门\nφ_r(n)（共模相位）", C["pink"], fs=8.4)
    route(ax, [(82.0, 40.2), (83.4, 40.2), (83.4, 47.0), (85.0, 47.0)], color=RED)

    # ── ② 相位域处理（左 → 右）──
    grp(ax, 1.5, 20.0, 105, 13, "② 相位域处理（抑制载波相位漂移）", fc="#f6f1f8",
        ec="#6b4b7a", lab=(54, 31.4))
    cy, ch, cw = 20.5, 7.0, 26.0
    cxs = [3.0, 37.0, 71.0]
    c = [("相位差分 ＋\n高通-带通级联滤波", C["lilac"]),
         ("长时相参积累\n4096 点 ≈ 9.4 s", C["teal"]),
         ("频率分辨率\n< 0.11 Hz", C["teal"])]
    for i, (t, f) in enumerate(c):
        box(ax, cxs[i], cy, cw, ch, t, f, fs=8.8)
        if i:
            arr(ax, (cxs[i - 1] + cw, cy + ch / 2), (cxs[i], cy + ch / 2))
    # ① → ② 肘形总线（走两组之间的空白带 y=35.2）
    route(ax, [(94.5, ay), (94.5, 35.2), (16.0, 35.2), (16.0, cy + ch)])

    # ── ③ 谱分离（右下）──
    grp(ax, 36.0, 1.5, 70.5, 14.5, "③ 谱分离与参数估计", fc="#f4f8f0", ec="#4a6b3a",
        lab=(96, 14.4))
    dy, dh, dw = 4.0, 7.0, 20.0
    dxs = [37.5, 62.0, 86.5]
    d = [("呼吸带 0.1–0.5 Hz\n呼吸率估计", C["sage"]),
         ("呼吸谐波剥离\n（逐分量 / 倒谱）", C["sand"]),
         ("心跳带 0.8–2.0 Hz\n心率估计", C["rose"])]
    for i, (t, f) in enumerate(d):
        box(ax, dxs[i], dy, dw, dh, t, f, fs=8.5)
    arr(ax, (dxs[1] + dw, dy + dh / 2), (dxs[2], dy + dh / 2))
    # ② → ③ 分支总线（走 y=17.8 空白带，分叉点打实心节点）
    route(ax, [(84.0, cy), (84.0, 17.8), (47.5, 17.8), (47.5, dy + dh)])
    route(ax, [(84.0, 17.8), (72.0, 17.8), (72.0, dy + dh)])
    junction(ax, (84.0, 17.8))

    # ── 灵敏度预算 + 分层目标（整块置于左下角）──
    box(ax, 1.5, 1.5, 32.0, 14.5, "", C["white"], ec=RED, lw=1.4)
    ax.text(2.7, 14.3, "相位灵敏度预算", fontsize=9.0, color=RED,
            fontweight="bold", ha="left", va="center", zorder=6)
    ax.text(2.7, 12.2, "（λ ≈ 85.7 mm @ 3.5 GHz）", fontsize=8.0, color=RED,
            ha="left", va="center", zorder=6)
    ax.text(2.7, 9.8, "呼吸 4–8 mm → Δφ ≈ 34°–67°", fontsize=8.3, color=INK,
            ha="left", va="center", zorder=6)
    ax.text(2.7, 7.8, "心跳 0.2–0.5 mm → Δφ ≈ 1.7°–4°", fontsize=8.3, color=INK,
            ha="left", va="center", zorder=6)
    ax.text(2.7, 5.9, "（受系统相位噪声底限制，需先标定）", fontsize=7.8, color=MUTE,
            ha="left", va="center", zorder=6)
    ax.plot([4.0, 31.0], [5.2, 5.2], color="#e2c8c8", lw=0.9, zorder=6)
    for i, (t, col, ec) in enumerate([("目标 C", C["teal"], GRN),
                                     ("目标 B", "#dce8f7", "#2f5f8f"),
                                     ("目标 A", C["lilac"], "#6b4b7a")]):
        pill(ax, 2.5 + i * 10.2, 2.4, 9.4, 2.4, t, col, ec, fs=8.2)

    save(fig, "fig_sensing")


if __name__ == "__main__":
    fig_topology(); fig_coding(); fig_sensing()
