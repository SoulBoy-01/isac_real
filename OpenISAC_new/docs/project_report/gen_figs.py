# -*- coding: utf-8 -*-
"""Generate 7 original diagrams for the OpenISAC acceptance report (matplotlib, no external assets)."""
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Polygon, Circle, Rectangle, Patch
from matplotlib.lines import Line2D

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'figs')
os.makedirs(OUT, exist_ok=True)

BLUE_F, BLUE_E = '#E8F1FA', '#2C5F8A'
GREEN_F, GREEN_E = '#E3F2E6', '#2E7D4F'
ORANGE_F, ORANGE_E = '#FDF2E3', '#B26A00'
PURPLE_F, PURPLE_E = '#F3E8FA', '#6B3FA0'
YELLOW_F, YELLOW_E = '#FFF9DB', '#B59B00'
CYAN_F, CYAN_E = '#E0F4F4', '#0F6B6A'
GRAY_F, GRAY_E = '#F2F2F2', '#666666'
PEACH_F, PEACH_E = '#FDEBD8', '#C0653A'
CTRL_F, CTRL_E = '#C9DDF2', '#1F4E79'
PURPLE_LINE = '#7C4DA8'
ORANGE_LINE = '#D97B1F'


def new_ax(w, h, xlim, ylim):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.axis('off')
    return fig, ax


def box(ax, x, y, w, h, text, fc=BLUE_F, ec=BLUE_E, dashed=False, fs=10, lw=1.4):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                                boxstyle='round,pad=0.02,rounding_size=0.8',
                                fc=fc, ec=ec, ls='--' if dashed else '-',
                                lw=lw, zorder=2))
    ax.text(x + w / 2, y + h / 2, text, ha='center', va='center',
            fontsize=fs, color='black', zorder=3)


def container(ax, x, y, w, h, title=None, ec='#888888'):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                                boxstyle='round,pad=0.02,rounding_size=1.5',
                                fc='none', ec=ec, ls='--', lw=1.5, zorder=1))
    if title:
        ax.text(x + 2, y + h - 2.2, title, ha='left', va='center',
                fontsize=11, fontweight='bold', color='black', zorder=3)


def arrow(ax, x1, y1, x2, y2, color='black', style='-', label=None,
          lpos=0.5, loff=(0, 1.4), fs=8.5, double=False, lw=1.4):
    astyle = '<|-|>' if double else '-|>'
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1), zorder=4,
                arrowprops=dict(arrowstyle=astyle, color=color, ls=style,
                                lw=lw, mutation_scale=13,
                                shrinkA=0, shrinkB=0))
    if label:
        lx = x1 + (x2 - x1) * lpos + loff[0]
        ly = y1 + (y2 - y1) * lpos + loff[1]
        ha = 'center'
        if loff[0] > 0.5:
            ha = 'left'
        elif loff[0] < -0.5:
            ha = 'right'
        ax.text(lx, ly, label, ha=ha, va='center', fontsize=fs, color=color, zorder=4)


def polyline_arrow(ax, pts, color='black', style='-', lw=1.4):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    ax.plot(xs[:-1], ys[:-1], color=color, ls=style, lw=lw, zorder=4,
            solid_capstyle='round')
    ax.annotate('', xy=pts[-1], xytext=pts[-2], zorder=4,
                arrowprops=dict(arrowstyle='-|>', color=color, ls=style,
                                lw=lw, mutation_scale=13, shrinkA=0, shrinkB=0))


def antenna(ax, x, y, size=1.0, color='black'):
    """Simple antenna: stem + triangle. (x, y) is the base point."""
    ax.plot([x, x], [y - 2 * size, y], color=color, lw=1.6, zorder=3)
    ax.add_patch(Polygon([(x - 1.6 * size, y), (x + 1.6 * size, y),
                          (x, y + 4 * size)], closed=True, fc='white',
                         ec=color, lw=1.6, zorder=3))


def drone(ax, cx, cy, s=1.0, color='black'):
    """Simple quadcopter: X arms + rotors + body."""
    d = 6 * s
    for dx, dy in [(-d, d * 0.72), (d, d * 0.72), (-d, -d * 0.72), (d, -d * 0.72)]:
        ax.plot([cx, cx + dx], [cy, cy + dy], color=color, lw=2.0, zorder=3)
        ax.add_patch(Circle((cx + dx, cy + dy), 1.5 * s, fc='white', ec=color,
                            lw=1.8, zorder=3))
    ax.add_patch(FancyBboxPatch((cx - 2.2 * s, cy - 1.6 * s), 4.4 * s, 3.2 * s,
                                boxstyle='round,pad=0.02,rounding_size=0.6',
                                fc='#DDDDDD', ec=color, lw=1.6, zorder=4))


def human(ax, cx, cy, s=1.0, color='black'):
    """Simple walking person: head + body + arms + legs."""
    ax.add_patch(Circle((cx, cy + 6.2 * s), 1.7 * s, fc='white', ec=color, lw=1.8, zorder=3))
    ax.plot([cx, cx], [cy + 4.5 * s, cy - 1.5 * s], color=color, lw=2.2, zorder=3)
    ax.plot([cx - 4 * s, cx, cx + 4 * s], [cy + 1.2 * s, cy + 3.2 * s, cy + 1.2 * s],
            color=color, lw=2.0, zorder=3)
    ax.plot([cx, cx - 2.8 * s], [cy - 1.5 * s, cy - 6 * s], color=color, lw=2.0, zorder=3)
    ax.plot([cx, cx + 2.8 * s], [cy - 1.5 * s, cy - 6 * s], color=color, lw=2.0, zorder=3)


def save(fig, name):
    path = os.path.join(OUT, name)
    fig.savefig(path, dpi=200, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print('saved', path, os.path.getsize(path))


# ---------------------------------------------------------------- fig 1
def fig_sys_arch():
    fig, ax = new_ax(12, 6.4, (0, 120), (0, 64))

    container(ax, 5, 3, 50, 45, 'BS 基站节点')
    container(ax, 65, 3, 50, 45, 'UE 终端节点')

    # --- BS internals
    box(ax, 9, 8, 14, 8, 'PC 主机\n(i9-12900K)', GREEN_F, GREEN_E)
    box(ax, 31, 8, 16, 8, 'USRP\n(NI X310)', CYAN_F, CYAN_E)
    arrow(ax, 23, 12, 31, 12, double=True)
    ax.text(27, 13.8, '10GbE', ha='center', fontsize=8.5)
    box(ax, 34, 21, 10, 6, 'OCXO\n(10 MHz)', PURPLE_F, PURPLE_E, fs=8.5)
    arrow(ax, 39, 21, 39, 16)
    ax.text(40.2, 18.3, 'REFCLK', ha='left', fontsize=8)

    antenna(ax, 22, 34)
    antenna(ax, 48, 34)
    ax.text(22, 40.6, 'TX 天线\n(喇叭 16 dBi)', ha='center', va='bottom', fontsize=8.5)
    ax.text(48, 40.6, '感知 RX 天线\n(喇叭 16 dBi)', ha='center', va='bottom', fontsize=8.5)
    ax.plot([33, 22], [16, 32], color='black', lw=1.2, zorder=2)
    ax.plot([45, 48], [16, 32], color='black', lw=1.2, zorder=2)

    # --- UE internals
    box(ax, 74, 8, 14, 8, 'USRP\n(NI X310)', CYAN_F, CYAN_E)
    box(ax, 94, 8, 14, 8, 'PC 主机\n(i9-12900K)', GREEN_F, GREEN_E)
    arrow(ax, 88, 12, 94, 12, double=True)
    ax.text(91, 13.8, '10GbE', ha='center', fontsize=8.5)
    box(ax, 76, 21, 10, 6, 'OCXO', PURPLE_F, PURPLE_E)
    arrow(ax, 81, 21, 81, 16)
    ax.text(82.2, 18.3, 'REFCLK', ha='left', fontsize=8)
    box(ax, 97, 24, 13, 6, 'USB DAC', PEACH_F, PEACH_E, dashed=True)
    arrow(ax, 101, 16, 101, 24, style='--', label='USB', loff=(1.0, 0), fs=8)
    arrow(ax, 97, 27, 86, 25.5, style='--', label='VADJ', loff=(0, 1.2), fs=8)

    antenna(ax, 69, 34)
    ax.text(69, 40.6, '接收天线\n(全向 3 dBi)', ha='center', va='bottom', fontsize=8.5)
    ax.plot([74, 69], [12, 32], color='black', lw=1.2, zorder=2)

    # --- human target
    human(ax, 60, 51)
    ax.text(60, 61.8, '感知目标（人体）', ha='center', fontsize=9.5)

    # --- wireless links
    arrow(ax, 24, 39.5, 55, 49, color=ORANGE_LINE, style='--', lw=1.6)
    ax.text(33, 47.5, '单站雷达回波', fontsize=8.5, color=ORANGE_LINE)
    arrow(ax, 65.5, 49, 50, 40, color=ORANGE_LINE, style='--', lw=1.6)
    arrow(ax, 24, 31.5, 67.4, 31.5, color=PURPLE_LINE, style='--', lw=1.6)
    ax.text(45, 28.9, '下行通信 / 双站直达径', fontsize=8.5, color=PURPLE_LINE)
    arrow(ax, 64.5, 48.5, 70, 40, color=PURPLE_LINE, style='--', lw=1.6)
    ax.text(72.5, 50, '目标散射（双站）', fontsize=8.5, color=PURPLE_LINE, ha='left')

    # --- legend
    ax.plot([14, 22], [1.5, 1.5], color=ORANGE_LINE, ls='--', lw=1.6)
    ax.text(23, 1.5, '单站回波链路', fontsize=9, va='center')
    ax.plot([50, 58], [1.5, 1.5], color=PURPLE_LINE, ls='--', lw=1.6)
    ax.text(59, 1.5, '通信 / 双站链路', fontsize=9, va='center')

    save(fig, 'fig_sys_arch.png')


# ---------------------------------------------------------------- fig 2
def fig_soft_bs():
    fig, ax = new_ax(12, 6.5, (0, 120), (0, 65))

    # top row
    ax.text(2, 46, 'UDP 业务输入', ha='left', fontsize=9.5)
    arrow(ax, 14, 46, 15, 46)
    box(ax, 15, 40, 18, 12, '比特处理线程\n(RS+LDPC 编码、加扰)', ORANGE_F, ORANGE_E, fs=9.5)
    arrow(ax, 33, 46, 36, 46)
    box(ax, 36, 40, 12, 12, '数据包 FIFO', GRAY_F, GRAY_E, dashed=True, fs=8.5)
    arrow(ax, 48, 46, 52, 46)
    box(ax, 52, 40, 20, 12, 'OFDM 调制线程\n(QPSK/QAM、导频、IFFT+CP)', YELLOW_F, YELLOW_E, fs=9.5)
    arrow(ax, 72, 46, 76, 46)
    box(ax, 76, 40, 12, 12, 'TX 波形 FIFO', GRAY_F, GRAY_E, dashed=True, fs=8.5)
    arrow(ax, 88, 46, 92, 46)
    box(ax, 92, 40, 16, 12, 'USRP-TX 线程', GREEN_F, GREEN_E)

    # bottom row
    box(ax, 15, 10, 16, 12, 'USRP-RX 线程', GREEN_F, GREEN_E)
    arrow(ax, 31, 16, 35, 16)
    box(ax, 35, 10, 12, 12, 'RX 波形 FIFO', GRAY_F, GRAY_E, dashed=True, fs=8.5)
    arrow(ax, 47, 16, 49, 16)
    box(ax, 49, 10, 20, 12, '感知线程\n(除法、MTI、时延-多普勒)', ORANGE_F, ORANGE_E, fs=9.5)
    arrow(ax, 69, 16, 73, 16)
    ax.text(74, 16, '感知数据 → Python', ha='left', fontsize=9.5)

    # TX symbol FIFO branch
    box(ax, 57, 27, 10, 8, 'TX 符号 FIFO', GRAY_F, GRAY_E, dashed=True, fs=8.5)
    arrow(ax, 62, 40, 62, 35)
    arrow(ax, 62, 27, 62, 22)

    # control thread
    box(ax, 2, 26, 16, 10, '控制命令线程\n(UDP 9999)', CTRL_F, CTRL_E, fs=9)
    ax.text(2, 21.5, 'Python 控制命令', ha='left', fontsize=9)
    arrow(ax, 10, 23, 10, 26)
    arrow(ax, 12, 36, 18, 40, color=CTRL_E, style='--')
    arrow(ax, 12, 26, 18, 22, color=CTRL_E, style='--')
    polyline_arrow(ax, [(18, 31), (47, 31), (47, 22)], color=CTRL_E, style='--')

    ax.text(118, 4, 'FIFO = 环形缓冲区，I/O 与计算解耦', ha='right',
            fontsize=8.5, color='#888888')

    save(fig, 'fig_soft_bs.png')


# ---------------------------------------------------------------- fig 3
def fig_soft_ue():
    fig, ax = new_ax(12, 6.5, (0, 120), (0, 65))

    # control thread
    box(ax, 4, 48, 18, 10, '控制命令线程\n(UDP 9999)', CTRL_F, CTRL_E, fs=9)
    ax.text(4, 61.5, 'Python 控制命令', ha='left', fontsize=9)
    arrow(ax, 10, 60.5, 10, 58)
    arrow(ax, 10, 48, 10, 40, color=CTRL_E, style='--')
    arrow(ax, 22, 52, 42, 40, color=CTRL_E, style='--')
    polyline_arrow(ax, [(22, 56), (91, 60), (91, 56)], color=CTRL_E, style='--')

    # main row
    box(ax, 6, 28, 16, 12, 'USRP-RX 线程', GREEN_F, GREEN_E)
    arrow(ax, 22, 34, 26, 34)
    box(ax, 26, 28, 12, 12, 'RX 波形 FIFO', GRAY_F, GRAY_E, dashed=True, fs=8.5)
    arrow(ax, 38, 34, 40, 34)
    box(ax, 40, 28, 22, 12, 'OFDM 解调线程\n(同步状态机、均衡、符号重构)', YELLOW_F, YELLOW_E, fs=9.5)

    # sensing branch
    box(ax, 68, 44, 10, 10, '感知 FIFO', GRAY_F, GRAY_E, dashed=True, fs=8.5)
    arrow(ax, 60, 40, 72, 44)
    box(ax, 82, 42, 20, 14, '感知线程\n(双站时延-多普勒)', ORANGE_F, ORANGE_E)
    arrow(ax, 78, 49, 82, 49)
    arrow(ax, 102, 49, 104, 49)
    ax.text(104.5, 49, '感知数据 → Python', ha='left', fontsize=9.5)

    # bit branch
    box(ax, 68, 8, 12, 10, '数据 LLR FIFO', GRAY_F, GRAY_E, dashed=True, fs=8.5)
    arrow(ax, 60, 28, 74, 18)
    box(ax, 82, 6, 20, 14, '比特处理线程\n(解扰、LDPC+RS 译码)', ORANGE_F, ORANGE_E)
    arrow(ax, 78, 13, 82, 13)
    arrow(ax, 102, 13, 104, 13)
    ax.text(104.5, 13, 'UDP 业务输出', ha='left', fontsize=9.5)

    # hardware sync controller
    box(ax, 40, 10, 22, 12, '硬件同步控制器\n(USB DAC → OCXO VADJ)', GREEN_F, GREEN_E, fs=9)
    arrow(ax, 51, 28, 51, 22)
    ax.text(51.8, 25, '同步估计', ha='left', fontsize=8.5)

    save(fig, 'fig_soft_ue.png')


# ---------------------------------------------------------------- fig 4
def fig_packet_cw():
    fig, ax = new_ax(11, 4, (0, 110), (-7, 40))

    # packet radio
    fw, fh = 24, 10
    frames = [(10, 25), (40, 52), (59, 75), (85, 97)]
    for i, (x1, x2) in enumerate(frames):
        ax.add_patch(Rectangle((x1, 24), x2 - x1, fh, fc=YELLOW_F, ec=YELLOW_E, lw=1.4, zorder=2))
        ax.text((x1 + x2) / 2, 29, f'帧 {i}', ha='center', va='center', fontsize=10, zorder=3)
    for x1, x2, lab in [(25, 40, 'T0'), (52, 59, 'T1'), (75, 85, 'T2')]:
        arrow(ax, x1 + 0.6, 29, x2 - 0.6, 29, double=True)
        ax.text((x1 + x2) / 2, 31.8, lab, ha='center', fontsize=9)
    ax.text(101, 29, '……', ha='left', fontsize=12, va='center')
    ax.text(55, 18, '分组无线电（帧间隔不规则，跨帧相干积累受损）',
            ha='center', fontsize=10.5)

    # continuous wave
    ax.add_patch(Rectangle((10, 2), 87, 10, fc=GREEN_F, ec=GREEN_E, lw=1.4, zorder=2))
    for xv in [31.75, 53.5, 75.25]:
        ax.plot([xv, xv], [2, 12], color=GREEN_E, lw=1.2, zorder=3)
    for i, xc in enumerate([20.875, 42.625, 64.375, 86.125]):
        ax.text(xc, 7, f'帧 {i}', ha='center', va='center', fontsize=10, zorder=3)
    ax.text(101, 7, '……', ha='left', fontsize=12, va='center')
    ax.text(55, -3.5, '连续波无线电 CW-OFDM（帧间无间隙，本平台采用）',
            ha='center', fontsize=10.5)

    save(fig, 'fig_packet_cw.png')


# ---------------------------------------------------------------- fig 5
def fig_frame():
    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.set_xlim(-0.7, 14.3)
    ax.set_ylim(-2.8, 32.3)
    GREEN = '#7CBF6B'
    BLUE = '#4472C4'
    GRAY = '#EFEFEF'
    for m in range(14):
        for n in range(32):
            if m == 2:
                fc = GREEN
            elif n % 4 == 0:
                fc = BLUE
            else:
                fc = GRAY
            ax.add_patch(Rectangle((m + 0.04, n + 0.04), 0.92, 0.92, fc=fc, ec='white', lw=0.6))
    ax.set_xticks(range(14))
    ax.set_yticks(range(0, 32, 4))
    ax.set_xlabel('OFDM 符号索引 m', fontsize=10.5)
    ax.set_ylabel('子载波索引 n', fontsize=10.5)
    ax.tick_params(labelsize=9)
    for s in ['top', 'right']:
        ax.spines[s].set_visible(False)
    legend = [Patch(fc=GREEN, ec='white', label='同步符号（全带 ZC，根 29）'),
              Patch(fc=BLUE, ec='white', label='导频（ZC，梳状）'),
              Patch(fc=GRAY, ec='white', label='数据（RS+LDPC 编码 QPSK/QAM）')]
    ax.legend(handles=legend, loc='upper right', fontsize=8.5, framealpha=0.95)
    ax.text(0, -2.2, '示例 M=14、N=32；实测配置 M=100、N=1024（导频 8/16 可配）',
            fontsize=8.5, color='#888888')
    save(fig, 'fig_frame.png')


# ---------------------------------------------------------------- fig 6
def fig_flow_bs_sensing():
    fig, ax = new_ax(12, 4.8, (0, 120), (0, 48))

    ax.text(3, 33, '$y_{BS}[k]$', fontsize=11, ha='center', va='center')
    arrow(ax, 9, 33, 13, 33)
    box(ax, 13, 26, 14, 14, 'OFDM 解调\n(去 CP + FFT)', GRAY_F, GRAY_E, fs=9.5)
    arrow(ax, 27, 33, 33, 33, label='$B_{BS,\\gamma}$', loff=(0, 1.5))
    box(ax, 33, 26, 14, 14, '逐元素除法\n(÷ $b_{n,m,\\gamma}$)', BLUE_F, BLUE_E, fs=9.5)
    arrow(ax, 47, 33, 53, 33, label='$F_{BS,\\gamma}$', loff=(0, 1.5))
    box(ax, 53, 26, 16, 14, 'MTI 杂波抑制\n(因果 IIR 高通)', GREEN_F, GREEN_E, fs=9.5)

    arrow(ax, 69, 37, 75, 42)
    box(ax, 75, 36, 14, 12, '感知帧重打包', ORANGE_F, ORANGE_E, fs=9.5)
    arrow(ax, 89, 42, 93, 42)
    box(ax, 93, 36, 24, 12, '时延-多普勒处理\n(2D 周期图 + Hamming 窗)', PURPLE_F, PURPLE_E, fs=9)

    arrow(ax, 69, 29, 75, 20)
    box(ax, 75, 14, 22, 12, '微多普勒处理\n(距离门 IFFT + STFT)', YELLOW_F, YELLOW_E, fs=9)

    ax.text(118, 6, '可选步长 $M_D$ 下采样折衷负载与分辨率', ha='right',
            fontsize=8.5, color='#888888')

    save(fig, 'fig_flow_bs_sensing.png')


# ---------------------------------------------------------------- fig 7
def fig_flow_ue():
    fig, ax = new_ax(12, 7, (0, 120), (0, 70))
    container(ax, 2, 2, 116, 66, None)

    # upper zone
    ax.text(5, 64.5, 'SYNC_SEARCH（同步搜索态）', fontsize=10.5, fontweight='bold')
    ax.text(4, 56, '$y_{UE,sync}[k]$', fontsize=10.5, ha='center', va='center')
    arrow(ax, 11, 56, 14, 56)
    box(ax, 14, 50, 20, 12, 'ZC 相关搜索\n(归一化峰均比 $\\rho_{ZC}>100$)', GREEN_F, GREEN_E, fs=9)
    arrow(ax, 34, 56, 40, 56, label='$\\hat{k}_{TO}$', loff=(0, 1.5))
    box(ax, 40, 50, 16, 12, 'CP 尾相关\n(粗频偏估计)', ORANGE_F, ORANGE_E, fs=9)
    arrow(ax, 56, 56, 62, 56, label='$\\hat{f}_o$', loff=(0, 1.5))
    box(ax, 62, 50, 22, 12, '载频与定时校正\n(数字重调频 / OCXO)', ORANGE_F, ORANGE_E, fs=9)

    # transition
    arrow(ax, 24, 50, 24, 26)
    ax.text(22.5, 38, '同步成功', ha='right', fontsize=9)
    arrow(ax, 30, 26, 30, 50)
    ax.text(31.5, 38, '失锁退回', ha='left', fontsize=9)

    # lower zone
    ax.text(4, 29, 'NORMAL（正常工作态）', fontsize=10.5, fontweight='bold')
    ax.text(4, 20, '$y_{UE,\\gamma}[k]$', fontsize=10.5, ha='center', va='center')
    arrow(ax, 11, 20, 13, 20)
    box(ax, 13, 14, 14, 12, 'OFDM 解调\n(去 CP + FFT)', PURPLE_F, PURPLE_E, fs=9.5)
    arrow(ax, 27, 20, 32, 20, label='$B_{UE,\\gamma}$', loff=(0, 1.5))
    box(ax, 32, 14, 22, 12, '信道估计 (ZC) +\n导频 WLS (CFO/SFO 跟踪)', CYAN_F, CYAN_E, fs=9)
    arrow(ax, 54, 20, 58, 20)
    box(ax, 58, 14, 14, 12, '单抽头频域均衡', ORANGE_F, ORANGE_E, fs=9.5)
    arrow(ax, 72, 20, 76, 20)
    box(ax, 76, 14, 14, 12, 'QPSK/QAM 解映射\n(LLR 计算)', PURPLE_F, PURPLE_E, fs=9)
    arrow(ax, 90, 20, 94, 20)
    box(ax, 94, 14, 20, 12, '解扰 + LDPC 译码\n(+ RS 外码)', CYAN_F, CYAN_E, fs=9)

    # delay tracking box
    box(ax, 48, 35, 22, 7, '时延谱定时跟踪\n(desired_peak_pos)', GREEN_F, GREEN_E, fs=8.5)
    arrow(ax, 43, 26, 48, 35)
    arrow(ax, 60, 42, 70, 50, color=PURPLE_E, style='--')

    save(fig, 'fig_flow_ue.png')


if __name__ == '__main__':
    fig_sys_arch()
    fig_soft_bs()
    fig_soft_ue()
    fig_packet_cw()
    fig_frame()
    fig_flow_bs_sensing()
    fig_flow_ue()
    print('all done')
