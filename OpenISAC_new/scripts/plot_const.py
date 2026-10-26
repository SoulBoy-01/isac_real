# -*- coding: utf-8 -*-
"""
OFDM 星座图实时可视化工具 (v2)

在原始版本基础上增加:
  - QAM 参考网格叠加 (QPSK / 16QAM / 64QAM / 256QAM)
  - 键盘快捷键切换调制制式与显示选项
  - 接收数据自动归一化,使网格与散点正确对齐
  - 图例中显示当前调制类型与网格状态

键盘快捷键:
  1-5 : 切换参考网格 (1=无, 2=QPSK, 3=16QAM, 4=64QAM, 5=256QAM)
  g   : 切换保护带子载波显示
  r   : 重置坐标轴范围
"""

import socket

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# UDP receiver configuration
UDP_IP = "0.0.0.0"       # Listen on all interfaces
UDP_PORT = 12346          # Port number
FFT_SIZE = 1024           # OFDM symbol FFT size (number of subcarriers)
MAX_PACKET_SIZE = 8192    # Maximum packet size (1024 points * 8 bytes/complex)
SHOW_GUARD_BAND = False   # Macro switch: whether to display guard band constellation points

# QAM reference grid selection
GRID_MODE = "QPSK"        # "无" / "QPSK" / "16QAM" / "64QAM" / "256QAM"
GRID_OPTIONS = ["无", "QPSK", "16QAM", "64QAM", "256QAM"]

# Create UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))
sock.settimeout(0.001)  # Set timeout for non-blocking behavior

# Define subcarrier indices:
# - pilot_indices: Pilot subcarrier indices
# - all_active_indices: All non-guard band subcarriers
# - data_indices: Data subcarriers (excluding pilots)
pilot_indices = [571, 631, 692, 752, 812, 872, 933, 993, 29, 89, 150, 210, 270, 330, 391, 451]
all_active_indices = np.concatenate([np.arange(1, 490), np.arange(535, 1024)])
data_indices = np.setdiff1d(all_active_indices, pilot_indices)
guard_band_indices = np.arange(490, 534)


# ====================== QAM 参考网格 ======================
def compute_qam_grid(mode: str):
    """返回 (xs, ys) 两个等长 list, 坐标已按平均能量=1 归一。"""
    if not mode or mode == "无":
        return [], []
    if mode.startswith("QPSK"):
        sc = 1.0 / np.sqrt(2.0)
        xs = [-sc, -sc, sc, sc]
        ys = [-sc, sc, -sc, sc]
        return xs, ys
    if mode.startswith("16-QAM") or mode.startswith("16QAM"):
        levels = [-3, -1, 1, 3]
        sc = 1.0 / np.sqrt(10.0)
    elif mode.startswith("64-QAM") or mode.startswith("64QAM"):
        levels = [-7, -5, -3, -1, 1, 3, 5, 7]
        sc = 1.0 / np.sqrt(42.0)
    elif mode.startswith("256-QAM") or mode.startswith("256QAM"):
        levels = list(range(-15, 16, 2))
        sc = 1.0 / np.sqrt(170.0)
    else:
        return [], []
    xs, ys = [], []
    for i in levels:
        for q in levels:
            xs.append(i * sc)
            ys.append(q * sc)
    return xs, ys


# Create figure and axes
fig, ax = plt.subplots(figsize=(8, 7))
ax.grid(True)
ax.set_title(f"OFDM Constellation  |  参考网格: {GRID_MODE}", fontsize=12)
ax.set_xlabel("Real (I)")
ax.set_ylabel("Imaginary (Q)")
ax.set_xlim([-2, 2])
ax.set_ylim([-2, 2])

# Initialize scatter plots for three types of subcarriers
data_plot = ax.scatter([], [], alpha=0.6, c='blue', label='Data Subcarriers', s=10)
guard_plot = ax.scatter(
    [], [], alpha=0.6, c='red', marker='*',
    label='Guard Band' if SHOW_GUARD_BAND else '_nolegend_', s=40,
)
pilot_plot = ax.scatter([], [], alpha=0.6, c='orange', marker='x',
                        label='Pilot Subcarriers', s=50)
guard_plot.set_visible(SHOW_GUARD_BAND)

# QAM reference grid layer (red '+' markers)
gx_init, gy_init = compute_qam_grid(GRID_MODE)
grid_plot = ax.scatter(gx_init, gy_init, alpha=0.8, c='red', marker='+',
                       s=80, label='QAM Reference' if gx_init else '_nolegend_',
                       zorder=10)

ax.legend(loc='upper right')

# Help text
help_text = ax.text(0.02, 0.98,
                    "Keys: 1-5=Grid  g=Guard  r=Reset",
                    transform=ax.transAxes, fontsize=8,
                    verticalalignment='top',
                    bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

# Global variable: stores current OFDM symbol
current_symbol = np.zeros(FFT_SIZE, dtype=np.complex64)


def update(frame):
    """Animation update function, called periodically by FuncAnimation"""
    global current_symbol, SHOW_GUARD_BAND, GRID_MODE

    # Try to receive new data
    try:
        # Receive UDP packet
        data, addr = sock.recvfrom(MAX_PACKET_SIZE)

        # Check if packet size is valid (FFT_SIZE * 8 bytes)
        if len(data) != FFT_SIZE * 8:
            return data_plot, guard_plot, pilot_plot, grid_plot

        # Convert byte data to complex array
        symbol = np.frombuffer(data, dtype=np.complex64)
        if symbol.size != FFT_SIZE:
            return data_plot, guard_plot, pilot_plot, grid_plot

        current_symbol = symbol  # Update current symbol

    except socket.timeout:  # Skip if no data
        pass
    except Exception as e:  # Catch other exceptions
        print(f"Error: {e}")

    # Update constellation with current symbol
    if current_symbol is not None:
        # Extract subcarrier types
        data_sc = current_symbol[data_indices]     # Data subcarriers
        pilot_sc = current_symbol[pilot_indices]   # Pilot subcarriers

        # Normalize: scale so max |I| or |Q| ≈ 1.0 for grid alignment
        all_active = current_symbol[all_active_indices]
        amp = float(max(np.max(np.abs(all_active.real)),
                       np.max(np.abs(all_active.imag)), 1e-12))
        norm_factor = 1.0 / amp if amp > 0 else 1.0

        data_sc_norm = data_sc * norm_factor
        pilot_sc_norm = pilot_sc * norm_factor

        # Update scatter plot data
        data_plot.set_offsets(np.column_stack([data_sc_norm.real, data_sc_norm.imag]))
        if SHOW_GUARD_BAND:
            guard_sc = current_symbol[guard_band_indices] * norm_factor
            guard_plot.set_offsets(np.column_stack([guard_sc.real, guard_sc.imag]))
        else:
            guard_plot.set_offsets(np.empty((0, 2)))
        pilot_plot.set_offsets(np.column_stack([pilot_sc_norm.real, pilot_sc_norm.imag]))

    # Return graphics elements that need updating
    return data_plot, guard_plot, pilot_plot, grid_plot


def on_key_press(event):
    """Keyboard interaction handler."""
    global SHOW_GUARD_BAND, GRID_MODE

    if event.key in ['1', '2', '3', '4', '5']:
        idx = int(event.key) - 1
        GRID_MODE = GRID_OPTIONS[idx]
        gx, gy = compute_qam_grid(GRID_MODE)
        grid_plot.set_offsets(np.column_stack([gx, gy]) if gx else np.empty((0, 2)))
        # Update legend visibility
        if gx:
            grid_plot.set_label('QAM Reference')
        else:
            grid_plot.set_label('_nolegend_')
        ax.set_title(f"OFDM Constellation  |  参考网格: {GRID_MODE}", fontsize=12)
        ax.legend(loc='upper right')
        fig.canvas.draw_idle()
        print(f"[plot_const] 参考网格: {GRID_MODE}")

    elif event.key == 'g':
        SHOW_GUARD_BAND = not SHOW_GUARD_BAND
        guard_plot.set_visible(SHOW_GUARD_BAND)
        if SHOW_GUARD_BAND:
            guard_plot.set_label('Guard Band')
        else:
            guard_plot.set_label('_nolegend_')
        ax.legend(loc='upper right')
        fig.canvas.draw_idle()
        print(f"[plot_const] 保护带显示: {'ON' if SHOW_GUARD_BAND else 'OFF'}")

    elif event.key == 'r':
        ax.set_xlim([-2, 2])
        ax.set_ylim([-2, 2])
        fig.canvas.draw_idle()
        print("[plot_const] 坐标轴已重置")


# Connect keyboard handler
fig.canvas.mpl_connect('key_press_event', on_key_press)

# Create animation object
ani = FuncAnimation(
    fig,
    update,
    interval=10,       # Update interval (milliseconds)
    blit=True,         # Enable efficient rendering
    cache_frame_data=False  # Don't cache frame data to save memory
)

plt.tight_layout()
print(f"[plot_const] 启动完成。UDP={UDP_IP}:{UDP_PORT}, 网格={GRID_MODE}")
print("[plot_const] 按键: 1=无 2=QPSK 3=16QAM 4=64QAM 5=256QAM  g=保护带  r=重置")
plt.show()
