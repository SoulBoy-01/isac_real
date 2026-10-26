# -*- coding: utf-8 -*-
"""
通感一体 (ISAC) 实时感知系统 —— 展台演示前端 (v3)

基于 plot_sensing_fast.py 的 MainWindow 派生而成。
* 复用原文件全部 UDP / DSP / 控件 / 命令逻辑(零侵入)
* 深色科技风主题，适合公开展览
* 重排布局:RD 图保留在原位,其余图表收纳进 RD 下方的 Tab 切换区
* 控件标签全面中文化(专业术语)

运行方式:
    python plot_sensing_isac_demo.py [与原文件相同的参数]
"""

from __future__ import annotations

import sys
import time
from collections import deque

import numpy as np
from PyQt6 import QtCore, QtGui, QtWidgets
import pyqtgraph as pg

# 复用原文件的全部模块逻辑(网络线程、DSP 工作线程、全局变量等)
import plot_sensing_fast as core
from plot_sensing_fast import (
    CHANNELS,
    aggregate_frame_queue,
    BUFFER_LENGTH,
    get_display_range_bin_limit,
    get_display_doppler_bin_limit,
)


# ====================== 三套主题配色方案 ======================
THEMES = {
    "dark": {
        "window_bg":   "#0c0c0c", "plot_bg":   "#1a1a1a", "panel_bg":   "#1c2128",
        "panel_div":   "#30363d", "grid_line":  "#2a2a2a", "axis_text":   "#8c8c8c",
        "i_curve":     "#58a6ff", "q_curve":   "#f0883e", "mag_curve":   "#f78166",
        "accent":      "#58a6ff", "accent_hover": "#79b8ff",
        "gold":        "#ffd700", "green_live": "#3fb950", "red_idle":    "#f85149",
        "text_primary":"#e0e0e0", "text_second":"#8c8c8c", "text_muted":  "#505050",
        "border":      "#333333", "border_hover":"#58a6ff",
        "status_label_bg": "#222222",
        "widget_bg":   "#2a2a2a", "widget_hover": "#333333",
        "widget_pressed": "#252525", "widget_checked": "#2d3a3a",
        "combo_dropdown_bg": "#2a2a2a", "combo_item_bg": "#2d3a3a",
        "scroll_handle": "#3a3a3a", "scroll_handle_hover": "#555555",
        "tab_hover_bg": "#252525",
        "label": "Dark | 暗色",
        "arrow_border_top": "#8c8c8c",  # QComboBox down-arrow color
    },
    "navy": {
        "window_bg":   "#0a1628", "plot_bg":   "#0f1f38", "panel_bg":   "#111d33",
        "panel_div":   "#1e3050", "grid_line":  "#1a2d4a", "axis_text":   "#7b92b0",
        "i_curve":     "#4fc3f7", "q_curve":   "#ffb74d", "mag_curve":   "#ff8a65",
        "accent":      "#4fc3f7", "accent_hover": "#81d4fa",
        "gold":        "#ffd700", "green_live": "#3fb950", "red_idle":    "#f85149",
        "text_primary":"#e3ecf5", "text_second":"#7b92b0", "text_muted":  "#4a5f78",
        "border":      "#1e3050", "border_hover":"#4fc3f7",
        "status_label_bg": "#152238",
        "widget_bg":   "#152238", "widget_hover": "#1a2d4a",
        "widget_pressed": "#111d33", "widget_checked": "#1e3050",
        "combo_dropdown_bg": "#152238", "combo_item_bg": "#1e3050",
        "scroll_handle": "#1e3050", "scroll_handle_hover": "#2a4060",
        "tab_hover_bg": "#111d33",
        "label": "Navy | 深蓝",
        "arrow_border_top": "#7b92b0",
    },
    "light": {
        "window_bg":   "#f5f5f5", "plot_bg":   "#ffffff", "panel_bg":   "#fafafa",
        "panel_div":   "#cccccc", "grid_line":  "#e0e0e0", "axis_text":   "#666666",
        "i_curve":     "#1976d2", "q_curve":   "#e65100", "mag_curve":   "#c62828",
        "accent":      "#1976d2", "accent_hover": "#42a5f5",
        "gold":        "#b8860b", "green_live": "#2e7d32", "red_idle":    "#c62828",
        "text_primary":"#222222", "text_second":"#555555", "text_muted":  "#888888",
        "border":      "#cccccc", "border_hover":"#1976d2",
        "status_label_bg": "#eeeeee",
        "widget_bg":   "#e8e8e8", "widget_hover": "#dcdcdc",
        "widget_pressed": "#d0d0d0", "widget_checked": "#dce8f5",
        "combo_dropdown_bg": "#ffffff", "combo_item_bg": "#dce8f5",
        "scroll_handle": "#cccccc", "scroll_handle_hover": "#aaaaaa",
        "tab_hover_bg": "#e8e8e8",
        "label": "Light | 亮色",
        "arrow_border_top": "#555555",
    },
}

# 默认主题（模块级常量，指向 dark，用于初始化阶段）
_D = THEMES["dark"]
COLOR_WINDOW_BG    = _D["window_bg"]
COLOR_PLOT_BG      = _D["plot_bg"]
COLOR_PANEL_BG     = _D["panel_bg"]
COLOR_PANEL_DIV    = _D["panel_div"]
COLOR_GRID_LINE    = _D["grid_line"]
COLOR_AXIS_TEXT    = _D["axis_text"]
COLOR_I_CURVE      = _D["i_curve"]
COLOR_Q_CURVE      = _D["q_curve"]
COLOR_MAG_CURVE    = _D["mag_curve"]
COLOR_ACCENT       = _D["accent"]
COLOR_ACCENT_HOVER = _D["accent_hover"]
COLOR_GOLD         = _D["gold"]
COLOR_GREEN_LIVE   = _D["green_live"]
COLOR_RED_IDLE     = _D["red_idle"]
COLOR_TEXT_PRIMARY = _D["text_primary"]
COLOR_TEXT_SECOND  = _D["text_second"]
COLOR_TEXT_MUTED   = _D["text_muted"]
COLOR_BORDER       = _D["border"]
COLOR_BORDER_HOVER = _D["border_hover"]

# 抑制 pyqtgraph 默认配置
pg.setConfigOptions(
    background=COLOR_PLOT_BG,
    foreground=COLOR_TEXT_SECOND,
    antialias=True,
)

# ====================== 自定义 RD Colormap ======================
# turbo 全谱，低端 20% 平缓压黑 (纯黑底噪)，高端保持 turbo 明亮信号色
_turbo_full = pg.colormap.get('turbo').getLookupTable(nPts=256).astype(np.float32)
_ramp_len = 51  # 0–50 (前 20%) 渐变压黑
_ramp = np.linspace(0.0, 1.0, _ramp_len, dtype=np.float32).reshape(-1, 1)
_turbo_full[:_ramp_len] *= _ramp
_custom_rd_lut = np.clip(_turbo_full, 0, 255).astype(np.uint8)
CUSTOM_RD_COLORMAP = pg.ColorMap(pos=np.linspace(0, 1, 256), color=_custom_rd_lut)


# ====================== 常量 ======================
WATERFALL_HISTORY_LEN = 240
THROUGHPUT_REFRESH_S = 0.8


# ====================== 控件标签中英文映射 ======================
LABEL_TRANSLATIONS = {
    "Display CH:": "显示通道:",
    "Range Bin:": "距离单元:",
    "Delay FFT:": "时延 FFT 长度:",
    "Doppler FFT:": "多普勒 FFT 长度:",
    "Delay View:": "时延显示窗:",
    "Doppler View:": "多普勒显示窗:",
    "Delay Doppler dB:": "距离-多普勒 dB:",
    "MicroDoppler dB:": "微多普勒 dB:",
    "Delay Estimator:": "时延估计算法:",
    "Peak Rel(dB):": "相对峰值阈值(dB):",
    "Local Detector:": "本地检测器:",
    "Min": "最小",
    "Max": "最大",
    "Set": "设定",
    "Apply": "应用",
}

BUTTON_TRANSLATIONS_PREFIX = {
    "Micro-Doppler:": "微多普勒:",
    "Local OS-CFAR:": "本地 OS-CFAR:",
    "Local CLEAN:": "本地 CLEAN:",
    "Detector:": "检测器:",
}

ON_OFF_TRANSLATIONS = {"ON": "启用", "OFF": "关闭"}


def _translate_label_text(text: str) -> str:
    text = text.strip()
    return LABEL_TRANSLATIONS.get(text, text)


def _translate_button_text(text: str) -> str:
    for en_prefix, zh_prefix in BUTTON_TRANSLATIONS_PREFIX.items():
        if text.startswith(en_prefix):
            tail = text[len(en_prefix):].strip()
            for en, zh in ON_OFF_TRANSLATIONS.items():
                if tail == en:
                    return f"{zh_prefix} {zh}"
            return f"{zh_prefix} {tail}"
    return text


# ====================== 动态样式表生成 ======================

def generate_stylesheet(t: dict) -> str:
    """根据主题字典生成完整 QSS 样式表。"""
    return f"""
QMainWindow          {{ background-color: {t['window_bg']}; }}
QWidget              {{ color: {t['text_primary']}; font-size: 12px; }}
QWidget#qt_scrollarea_viewport {{ background-color: {t['panel_bg']}; }}

QTabWidget::pane     {{ border: none; background-color: {t['plot_bg']}; top: -1px; }}
QTabBar::tab         {{ background: {t['window_bg']}; color: {t['text_second']};
                        padding: 6px 16px; margin-right: 2px;
                        border-bottom: 2px solid transparent; font-size: 12px; }}
QTabBar::tab:selected {{ color: {t['accent']}; border-bottom: 2px solid {t['accent']};
                          background: {t['plot_bg']}; }}
QTabBar::tab:hover:!selected {{ color: {t['text_primary']}; background: {t['tab_hover_bg']}; }}

QScrollArea          {{ border: none; background-color: {t['panel_bg']}; }}
QLabel               {{ color: {t['text_second']}; background: transparent; border: none; font-size: 11px; }}

QComboBox            {{ background-color: {t['widget_bg']}; color: {t['text_primary']};
                        border: 1px solid {t['border']}; border-radius: 4px;
                        padding: 4px 8px; font-size: 11px; min-width: 100px;
                        outline: none; }}
QComboBox:hover      {{ border-color: {t['border_hover']}; }}
QComboBox::drop-down {{ border: none; width: 20px; subcontrol-origin: padding;
                        subcontrol-position: right center; }}
QComboBox::down-arrow {{ image: none; border-left: 4px solid transparent;
                          border-right: 4px solid transparent;
                          border-top: 5px solid {t['arrow_border_top']}; margin-right: 6px; }}
QComboBox QAbstractItemView {{
    background-color: {t['panel_bg']};
    color: {t['text_primary']};
    selection-background-color: {t['accent']};
    selection-color: #ffffff;
    border: 1px solid {t['border']};
    outline: none;
    padding: 2px;
}}
QComboBox QAbstractItemView::item {{
    padding: 4px 8px;
    min-height: 20px;
}}
QComboBox QAbstractItemView::item:hover {{
    background-color: {t['widget_hover']};
    color: {t['text_primary']};
}}
QComboBox QAbstractItemView::item:selected {{
    background-color: {t['accent']};
    color: #ffffff;
}}

QPushButton          {{ background-color: {t['widget_bg']}; color: {t['text_primary']};
                        border: 1px solid {t['border']}; border-radius: 4px;
                        padding: 5px 14px; font-size: 11px; min-width: 60px; }}
QPushButton:hover    {{ background-color: {t['widget_hover']}; border-color: {t['accent']}; }}
QPushButton:pressed  {{ background-color: {t['widget_pressed']}; }}
QPushButton:checked  {{ background-color: {t['widget_checked']};
                        border-color: {t['accent']}; color: {t['accent']}; }}

QSlider::groove:horizontal {{ background: {t['widget_bg']}; height: 4px; border-radius: 2px; }}
QSlider::handle:horizontal {{ background: {t['accent']}; width: 14px; height: 14px;
                               margin: -5px 0; border-radius: 7px; }}
QSlider::handle:horizontal:hover {{ background: {t['accent_hover']}; }}
QSlider::sub-page:horizontal {{ background: {t['accent']}; border-radius: 2px; }}

QSpinBox, QDoubleSpinBox {{ background-color: {t['widget_bg']}; color: {t['text_primary']};
    border: 1px solid {t['border']}; border-radius: 4px; padding: 3px 6px; font-size: 11px; }}
QSpinBox:hover, QDoubleSpinBox:hover {{ border-color: {t['border_hover']}; }}

QGroupBox            {{ background-color: {t['panel_bg']}; color: {t['text_second']};
                        border: 1px solid {t['border']}; border-radius: 4px;
                        margin-top: 8px; padding-top: 8px; font-weight: bold; }}
QGroupBox::title     {{ subcontrol-origin: margin; left: 10px; padding: 0 4px; }}

QStatusBar           {{ background-color: {t['window_bg']}; color: {t['text_second']};
                        border-top: 1px solid {t['border']}; font-size: 10px; }}

QScrollBar:vertical  {{ background: {t['window_bg']}; width: 8px; margin: 0; }}
QScrollBar::handle:vertical {{ background: {t['scroll_handle']}; min-height: 30px; border-radius: 4px; }}
QScrollBar::handle:vertical:hover {{ background: {t['scroll_handle_hover']}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
QScrollBar:horizontal {{ background: {t['window_bg']}; height: 8px; margin: 0; }}
QScrollBar::handle:horizontal {{ background: {t['scroll_handle']}; min-width: 30px; border-radius: 4px; }}
"""


# ====================== 主窗口 ======================
class MainWindowDemo(core.MainWindow):
    """通感一体演示主窗口。继承原 MainWindow,深色科技风 GUI。"""

    def __init__(self):
        super().__init__()

        # 立即压制 targets_window,避免启动瞬间闪窗
        try:
            self.targets_window.hide()
            self.targets_window.setVisible(False)
        except Exception:
            pass

        # ----- 累计/吞吐量状态 -----
        self._waterfall_history = deque(maxlen=WATERFALL_HISTORY_LEN)
        self._byte_counter = 0
        self._byte_counter_t0 = time.time()
        self._last_thru_frame_id = None
        self._cum_bytes_total = 0
        self._frames_since_t0 = 0
        self._data_received = False
        self._time_x_cache = np.arange(4096, dtype=np.float32)
        self._time_last_w = 0
        self._debug_frame_count = 0

        # ----- 主题系统 -----
        _settings = QtCore.QSettings("ISAC", "Demo")
        self.theme_name = _settings.value("theme", "dark")
        if self.theme_name not in THEMES:
            self.theme_name = "dark"
        self.theme = THEMES[self.theme_name]
        self._apply_stylesheet()
        self._last_target_count = 0
        self._flash_timer = QtCore.QTimer(self)
        self._flash_timer.setSingleShot(True)
        self._flash_timer.timeout.connect(self._clear_target_flash)

        # ----- 重新组织界面 -----
        self._build_new_plots()
        self._chinese_relayout()
        self._localize_control_panel()
        self._add_extra_status_labels()
        self._build_theme_combo()
        self._build_collapse_button()
        self._build_status_bar()

        self._enforce_control_panel_floor()
        self._apply_theme_to_plots()
        QtCore.QTimer.singleShot(200, self._position_watermark)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        QtCore.QTimer.singleShot(0, self._position_watermark)

    def closeEvent(self, event):
        """安全退出：先关闭被隐藏/分离的窗口，避免 Qt 清理顺序冲突。"""
        for attr in ('targets_window', 'phase_curve_plot'):
            try:
                w = getattr(self, attr, None)
                if w is not None:
                    w.hide()
                    w.close()
            except Exception:
                pass
        super().closeEvent(event)

    # ──────────────────────── 主题系统 ────────────────────────

    def _apply_stylesheet(self):
        """应用当前主题的 QSS 样式表。"""
        app = QtWidgets.QApplication.instance()
        if app is not None:
            app.setStyleSheet(generate_stylesheet(self.theme))

    def _apply_theme_to_plots(self):
        """为所有 PlotWidget 应用当前主题的背景和坐标轴颜色。"""
        t = self.theme
        for attr in ('rd_plot', 'md_plot', 'time_plot', 'waterfall_plot',
                     'target_sector_plot', 'phase_curve_plot'):
            pw = getattr(self, attr, None)
            if pw is not None:
                pw.setBackground(t['plot_bg'])
                for axis_name in ('left', 'bottom', 'top', 'right'):
                    axis = pw.getPlotItem().getAxis(axis_name)
                    if axis is not None:
                        axis.setPen(pg.mkPen(t['axis_text'], width=1))
                        axis.setTextPen(pg.mkPen(t['axis_text']))

    def _apply_theme(self, theme_name: str):
        """切换主题并刷新所有视觉元素。"""
        if theme_name not in THEMES:
            return
        self.theme_name = theme_name
        self.theme = THEMES[theme_name]
        t = self.theme
        # 1. QSS
        self._apply_stylesheet()
        # 2. 图表背景 + 坐标轴
        self._apply_theme_to_plots()
        # 3. 曲线颜色
        try:
            self.time_glow_i.setPen(pg.mkPen(t['i_curve'], width=6))
            self.time_glow_q.setPen(pg.mkPen(t['q_curve'], width=6))
            self.time_glow_mag.setPen(pg.mkPen(t['mag_curve'], width=8))
            self.time_curve_i.setPen(pg.mkPen(t['i_curve'], width=1.2))
            self.time_curve_q.setPen(pg.mkPen(t['q_curve'], width=1.2))
            self.time_curve_mag.setPen(pg.mkPen(t['mag_curve'], width=1.8))
        except Exception:
            pass
        # 4. 状态标签
        for lbl in self._status_labels:
            try:
                lbl.setStyleSheet(
                    f"QLabel {{ color: {t['text_primary']}; "
                    f"background-color: {t['status_label_bg']}; "
                    f"border: 1px solid {t['border']}; "
                    f"padding: 2px 6px; border-radius: 3px; }}")
            except Exception:
                pass
        # 5. 水印
        try:
            self._rd_watermark.setColor(t['text_muted'])
            self._watermark.setStyleSheet(
                f"color: {t['text_muted']}; background: transparent; "
                f"font-size: 9px; padding: 2px 8px;")
        except Exception:
            pass
        # 6. 中央组件背景
        try:
            cw = self.centralWidget()
            if cw is not None:
                cw.setStyleSheet(f"background-color: {t['window_bg']};")
        except Exception:
            pass
        # 7. 控制面板
        try:
            self.control_scroll.setStyleSheet(
                f"background-color: {t['panel_bg']}; border: none;")
            self.control_panel.setStyleSheet(
                f"background-color: {t['panel_bg']};")
        except Exception:
            pass
        # 8. 状态栏颜色
        try:
            sb = self.statusBar()
            sb.setStyleSheet(
                f"QStatusBar {{ background-color: {t['window_bg']}; "
                f"color: {t['text_second']}; "
                f"border-top: 1px solid {t['border']}; font-size: 10px; }}")
            for row, color in ((self._status_row1, None),
                               (self._status_row2, t['text_second']),
                               (self._status_row3, t['text_muted'])):
                if row is not None and color is not None:
                    row.setStyleSheet(f"color: {color}; background: transparent;")
        except Exception:
            pass
        # 10. 主题下拉框自身的 label 颜色
        try:
            self._theme_combo_label.setStyleSheet(
                f"color: {t['text_second']}; background: transparent; font-size: 11px;")
            self._theme_combo.blockSignals(True)
            self._theme_combo.setCurrentIndex(
                {"dark": 0, "navy": 1, "light": 2}[theme_name])
            self._theme_combo.blockSignals(False)
        except Exception:
            pass
        # 11. 强制刷新所有 QComboBox（系统样式可能缓存）
        if hasattr(self, 'control_panel'):
            for combo in self.control_panel.findChildren(QtWidgets.QComboBox):
                try:
                    combo.style().unpolish(combo)
                    combo.style().polish(combo)
                except Exception:
                    pass
        # 12. 保存
        QtCore.QSettings("ISAC", "Demo").setValue("theme", theme_name)

    def _build_theme_combo(self):
        """在控制面板顶部插入主题选择下拉框。"""
        if not hasattr(self, 'control_panel'):
            return
        ctrl_layout = self.control_panel.layout()
        self._theme_combo_label = QtWidgets.QLabel("Theme | 主题:")
        self._theme_combo_label.setStyleSheet(
            f"color: {self.theme['text_second']}; background: transparent; font-size: 11px;")
        self._theme_combo = QtWidgets.QComboBox()
        self._theme_combo.addItems([THEMES[k]["label"] for k in ("dark", "navy", "light")])
        self._theme_combo.setCurrentIndex({"dark": 0, "navy": 1, "light": 2}[self.theme_name])
        self._theme_combo.currentIndexChanged.connect(self._on_theme_combo_changed)
        theme_row = QtWidgets.QWidget()
        theme_row.setStyleSheet("background: transparent;")
        row_layout = QtWidgets.QHBoxLayout(theme_row)
        row_layout.setContentsMargins(0, 0, 0, 2)
        row_layout.setSpacing(6)
        row_layout.addWidget(self._theme_combo_label)
        row_layout.addWidget(self._theme_combo, stretch=1)
        self._theme_row = theme_row
        ctrl_layout.insertWidget(0, theme_row)

    def _on_theme_combo_changed(self, idx: int):
        """主题下拉框切换回调（避免 lambda 闭包 + 阻断重复触发）。"""
        name = ["dark", "navy", "light"][idx]
        if name != self.theme_name:
            self._apply_theme(name)

    # ──────────────────────── 折叠面板 ────────────────────────

    def _build_collapse_button(self):
        """在控制面板顶部插入折叠/展开按钮。"""
        if not hasattr(self, 'control_panel'):
            return
        ctrl_layout = self.control_panel.layout()
        self._panel_collapsed = False
        self._collapse_btn = QtWidgets.QPushButton("▲ 收起参数")
        self._collapse_btn.setFixedHeight(24)
        self._collapse_btn.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self._collapse_btn.clicked.connect(self._toggle_panel_collapse)
        ctrl_layout.insertWidget(0, self._collapse_btn)

    def _toggle_panel_collapse(self):
        """折叠/展开控制面板。"""
        self._panel_collapsed = not self._panel_collapsed
        cp = self.control_panel
        cs = self.control_scroll

        if self._panel_collapsed:
            self._collapse_btn.setText("▼ 展开参数")
            cs.setFixedWidth(60)
            # 隐藏控制面板中除折叠按钮和主题行外的所有子控件
            for i in range(cp.layout().count()):
                w = cp.layout().itemAt(i).widget()
                if w is not None and w is not self._collapse_btn and w is not getattr(self, '_theme_row', None):
                    w.setVisible(False)
        else:
            self._collapse_btn.setText("▲ 收起参数")
            cs.setFixedWidth(0)  # 恢复自动宽度（由 _apply_control_panel_width 控制）
            cs.setMinimumWidth(self._control_panel_min_width)
            for i in range(cp.layout().count()):
                w = cp.layout().itemAt(i).widget()
                if w is not None:
                    w.setVisible(True)
            self._apply_control_panel_width()

    # ──────────────────────── 状态栏 ────────────────────────

    def _build_status_bar(self):
        """构建三行演示信息带，替换原有状态栏。"""
        sb = self.statusBar()
        sb.setStyleSheet(
            f"QStatusBar {{ background-color: {self.theme['window_bg']}; "
            f"color: {self.theme['text_second']}; "
            f"border-top: 1px solid {self.theme['border']}; font-size: 10px; }}")

        container = QtWidgets.QWidget()
        container.setStyleSheet("background: transparent;")
        layout = QtWidgets.QVBoxLayout(container)
        layout.setContentsMargins(12, 4, 12, 2)
        layout.setSpacing(1)

        t = self.theme
        row1_font = QtGui.QFont(
            "Microsoft YaHei UI" if sys.platform.startswith("win")
            else "Noto Sans CJK SC", 9, QtGui.QFont.Weight.Medium)
        row2_font = QtGui.QFont(
            "Microsoft YaHei UI" if sys.platform.startswith("win")
            else "Noto Sans CJK SC", 9)
        row3_font = QtGui.QFont(
            "Microsoft YaHei UI" if sys.platform.startswith("win")
            else "Noto Sans CJK SC", 8, QtGui.QFont.Weight.Light)

        self._status_row1 = QtWidgets.QLabel("○ IDLE  |  -- fps  |  -- ms  |  -- Mbps")
        self._status_row1.setFont(row1_font)
        self._status_row1.setStyleSheet(f"color: {t['text_primary']}; background: transparent;")

        self._status_row2 = QtWidgets.QLabel("Targets: --  |  Nearest: -- m  |  Farthest: -- m")
        self._status_row2.setFont(row2_font)
        self._status_row2.setStyleSheet(f"color: {t['text_second']}; background: transparent;")

        self._status_row3 = QtWidgets.QLabel("ISAC Demo System  |  Real-time Sensing  |  v2.0")
        self._status_row3.setFont(row3_font)
        self._status_row3.setStyleSheet(f"color: {t['text_muted']}; background: transparent;")

        layout.addWidget(self._status_row1)
        layout.addWidget(self._status_row2)
        layout.addWidget(self._status_row3)

        sb.addPermanentWidget(container, stretch=1)
        # 清空父类原有状态标签（保留 QStatusBar 自身，只隐藏旧标签）
        for lbl in sb.findChildren(QtWidgets.QLabel):
            if lbl not in (self._status_row1, self._status_row2, self._status_row3):
                try:
                    lbl.hide()
                except Exception:
                    pass

    def _update_status_info(self):
        """每帧刷新三行状态信息。"""
        t = self.theme
        ch = self._get_display_channel_runtime()
        data_flowing = (ch is not None and ch.current_display_data is not None
                        and ch.current_display_data.get('rd') is not None)

        # ── 行 1: 实时指标 ──
        if data_flowing:
            fps_val = self._frames_since_t0 / max(
                time.time() - self._byte_counter_t0, 0.1)
            mbps_val = (self._byte_counter * 8.0) / max(
                time.time() - self._byte_counter_t0, 0.1) / 1e6
            self._status_row1.setText(
                f"● LIVE  |  {fps_val:5.1f} fps  |  -- ms  |  {mbps_val:6.1f} Mbps")
            self._status_row1.setStyleSheet(
                f"color: {t['green_live']}; background: transparent;")
        else:
            self._status_row1.setText("○ IDLE  |  -- fps  |  -- ms  |  -- Mbps")
            self._status_row1.setStyleSheet(
                f"color: {t['text_muted']}; background: transparent;")

        # ── 行 2: 目标摘要 ──
        if data_flowing:
            txt = self.targets_text.toPlainText()
            # 从 targets_text 提取摘要行
            lines = [l for l in txt.split('\n') if l.strip() and not l.startswith('Top Targets')]
            n_targets = len([l for l in lines if l[0].isdigit()])
            self._status_row2.setText(
                f"Targets: {n_targets}  |  {lines[0] if lines else 'No targets'}")
            self._status_row2.setStyleSheet(
                f"color: {t['text_second']}; background: transparent;")
        else:
            self._status_row2.setText("Targets: --  |  Nearest: -- m  |  Farthest: -- m")
            self._status_row2.setStyleSheet(
                f"color: {t['text_muted']}; background: transparent;")

        # ── 行 3: 品牌脚注 ──
        self._status_row3.setText("ISAC Demo System  |  Real-time Sensing  |  v2.0")
        self._status_row3.setStyleSheet(
            f"color: {t['text_muted']}; background: transparent;")

        # ── 窗口标题实时指示 ──
        prefix = "● LIVE" if data_flowing else "○ IDLE"
        self.setWindowTitle(f"{prefix}  |  通感一体化实时感知系统")

    # ──────────────────────── 原主题方法 ────────────────────────

    def _apply_dark_theme_to_plot(self, pw: pg.PlotWidget):
        """为单个 PlotWidget 设置背景/网格/坐标轴（使用当前主题颜色）。"""
        t = self.theme
        pw.setBackground(t['plot_bg'])
        for axis_name in ('left', 'bottom', 'top', 'right'):
            axis = pw.getPlotItem().getAxis(axis_name)
            if axis is not None:
                axis.setPen(pg.mkPen(t['axis_text'], width=1))
                axis.setTextPen(pg.mkPen(t['axis_text']))

        # 网格
        pw.showGrid(x=True, y=True, alpha=0.25)
        # 网格线颜色通过 setBackground 后自动跟随，但可以显式设置
        grid_pen = pg.mkPen(COLOR_GRID_LINE, width=0.5)
        pw.getPlotItem().getAxis('bottom').setGrid(255)
        pw.getPlotItem().getAxis('left').setGrid(255)

        # 标题
        pw.setTitle(None)  # 清除默认标题样式，后续单独设置
        title_item = pw.getPlotItem().titleLabel
        title_item.setText('')  # 保留空，由 setTitle 再覆盖

    def _apply_dark_theme_to_all_plots(self):
        """为所有 PlotWidget 应用暗色主题。"""
        for attr in ('rd_plot', 'md_plot', 'time_plot', 'waterfall_plot',
                     'target_sector_plot', 'phase_curve_plot'):
            pw = getattr(self, attr, None)
            if pw is not None:
                self._apply_dark_theme_to_plot(pw)

    # ---------------- 关键修复:控制面板下限 ----------------
    def _enforce_control_panel_floor(self):
        try:
            target_min = self._scale_px(720)
            target_base = self._scale_px(800)
            target_max = self._scale_px(960)
        except Exception:
            target_min, target_base, target_max = 720, 800, 960

        self._control_panel_min_width = max(self._control_panel_min_width, target_min)
        self._control_panel_base_width = max(self._control_panel_base_width, target_base)
        self._control_panel_max_width = max(self._control_panel_max_width, target_max)

        try:
            self._apply_control_panel_width()
        except Exception:
            pass

        plot_min = 720
        self.setMinimumWidth(self._control_panel_min_width + plot_min)
        self.setMinimumHeight(720)

    # ---------------- 新增图表 ----------------
    def _build_new_plots(self):
        # 1) 时域信号图
        self.time_plot = pg.PlotWidget(title="Time Domain Signal | 时域信号")
        self.time_plot.setLabel('left', 'Amplitude | 幅度')
        self.time_plot.setLabel('bottom', 'Sample Index | 采样点')
        self.time_plot.showGrid(x=True, y=True, alpha=0.25)
        self.time_plot.addLegend(offset=(8, 8))
        # Glow 底层：宽半透明笔刷，模拟发光
        self.time_glow_i = self.time_plot.plot(
            [], [], pen=pg.mkPen(COLOR_I_CURVE, width=6), opacity=0.35)
        self.time_glow_q = self.time_plot.plot(
            [], [], pen=pg.mkPen(COLOR_Q_CURVE, width=6), opacity=0.35)
        self.time_glow_mag = self.time_plot.plot(
            [], [], pen=pg.mkPen(COLOR_MAG_CURVE, width=8), opacity=0.35)
        # 主线
        self.time_curve_i = self.time_plot.plot(
            [], [], pen=pg.mkPen(COLOR_I_CURVE, width=1.2), name='I | 同相')
        self.time_curve_q = self.time_plot.plot(
            [], [], pen=pg.mkPen(COLOR_Q_CURVE, width=1.2), name='Q | 正交')
        self.time_curve_mag = self.time_plot.plot(
            [], [], pen=pg.mkPen(COLOR_MAG_CURVE, width=1.8), name='|·| | 模值')
        # 自动降采样兜底 + 裁剪
        for c in (self.time_curve_i, self.time_curve_q, self.time_curve_mag):
            c.setDownsampling(auto=True, method='peak')
        self.time_plot.setClipToView(True)
        try:
            self.time_plot.useOpenGL(True)
        except Exception:
            pass

        # 2) 距离功率瀑布图
        self.waterfall_plot = pg.PlotWidget(
            title="Range Power Waterfall | 距离功率瀑布图")
        self.waterfall_plot.setLabel('left', 'Frame History (older ↑) | 历史帧序')
        self.waterfall_plot.setLabel('bottom', 'Range Bin | 距离单元')
        self.waterfall_img = pg.ImageItem(axisOrder='row-major')
        self.waterfall_plot.addItem(self.waterfall_img)
        self.waterfall_img.setLookupTable(pg.colormap.get('viridis').getLookupTable())
        wf_levels = (-40.0, 0.0)
        self.waterfall_colorbar = pg.ColorBarItem(
            values=wf_levels,
            colorMap=pg.colormap.get('viridis'),
            interactive=False,
        )
        self.waterfall_colorbar.setImageItem(
            self.waterfall_img, insert_in=self.waterfall_plot.plotItem)
        self.waterfall_img.setLevels(wf_levels)

        # 3) 目标检测点图
        try:
            self.target_sector_plot.setTitle(
                "Target Detection Sector | 目标检测扇区图")
            self.target_sector_plot.setLabel('left',
                'Forward Distance (m) | 前向距离')
            self.target_sector_plot.setLabel('bottom',
                'Lateral Distance (m) | 横向距离')
        except Exception:
            pass

    # ---------------- 整体布局重排 ----------------
    def _chinese_relayout(self):
        self.setWindowTitle("通感一体化实时感知系统")

        # 应用暗色主题到所有图表
        self._apply_dark_theme_to_all_plots()

        # RD 图: 双语标题 + plasma colormap + ColorBar
        self.rd_plot.setTitle(
            "Range-Doppler Spectrum | 距离-多普勒谱")
        self.rd_plot.setLabel('left', 'Range Bin | 距离单元')
        self.rd_plot.setLabel('bottom', 'Doppler Bin | 多普勒单元')
        # RD 图用 plasma colormap
        try:
            rd_img = self.rd_plot.getPlotItem().items[0]
            if hasattr(rd_img, 'setLookupTable'):
                rd_img.setLookupTable(CUSTOM_RD_COLORMAP.getLookupTable())
        except Exception:
            pass
        # RD ColorBar：复用父类已有的 rd_colorbar，只更新 colormap 和初始范围
        try:
            self.rd_colorbar.setColorMap(CUSTOM_RD_COLORMAP)
            self.rd_colorbar.setLevels(values=(-20.0, 20.0))
        except Exception:
            pass

        # 网格虚线样式
        for axis_name in ('left', 'bottom'):
            axis = self.rd_plot.getPlotItem().getAxis(axis_name)
            if axis is not None:
                axis.setPen(pg.mkPen(COLOR_AXIS_TEXT, width=1))

        self.md_plot.setTitle(
            "Micro-Doppler Spectrogram | 微多普勒时频谱")
        self.md_plot.setLabel('left', 'Doppler | 多普勒')
        self.md_plot.setLabel('bottom', 'Time | 时间')

        # RD 图右上角水印
        self._rd_watermark = pg.TextItem(
            "ISAC Demo System", color=COLOR_TEXT_MUTED, anchor=(1, 1))
        self._rd_watermark.setOpacity(0.6)
        self._rd_watermark.setFont(QtGui.QFont(
            "Microsoft YaHei UI" if sys.platform.startswith("win")
            else "Noto Sans CJK SC", 10, QtGui.QFont.Weight.Light))
        self.rd_plot.addItem(self._rd_watermark)
        # 水印位置需要延迟到 resize 后设置，用单次定时器
        QtCore.QTimer.singleShot(100, self._position_watermark)

        # 取出原中央组件
        old_central = self.centralWidget()
        old_layout = old_central.layout() if old_central is not None else None

        for w in (self.rd_plot, self.md_plot, self.phase_curve_plot,
                  self.control_scroll):
            try:
                if old_layout is not None:
                    old_layout.removeWidget(w)
            except Exception:
                pass
            w.setParent(None)

        try:
            self.phase_curve_plot.hide()
        except Exception:
            pass

        # 解出 target_sector_plot
        try:
            tw_layout = self.targets_window.layout()
            if tw_layout is not None:
                tw_layout.removeWidget(self.target_sector_plot)
        except Exception:
            pass
        self.target_sector_plot.setParent(None)

        # 目标扇形图 PPI 虚线环 + 辐条
        try:
            _dash_pen = pg.mkPen(COLOR_ACCENT, width=1.0, style=QtCore.Qt.PenStyle.DashLine)
            for item in self.target_sector_ring_items:
                item.setPen(_dash_pen)
            _dot_pen = pg.mkPen(COLOR_TEXT_SECOND, width=0.8, style=QtCore.Qt.PenStyle.DotLine)
            for item in self.target_sector_spoke_items:
                item.setPen(_dot_pen)
            self.target_sector_outline_item.setPen(
                pg.mkPen(COLOR_TEXT_PRIMARY, width=1.4))
            self.target_sector_base_item.setPen(
                pg.mkPen(COLOR_TEXT_SECOND, width=1.2))
        except Exception:
            pass

        # 新建中央组件
        new_central = QtWidgets.QWidget()
        new_central.setStyleSheet(
            f"background-color: {self.theme['window_bg']};")
        main_layout = QtWidgets.QHBoxLayout(new_central)
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.setSpacing(6)

        # ---------- 左:可视化区 ----------
        plot_holder = QtWidgets.QWidget()
        plot_holder.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Expanding,
        )
        plot_layout = QtWidgets.QVBoxLayout(plot_holder)
        plot_layout.setContentsMargins(0, 0, 0, 0)
        plot_layout.setSpacing(4)

        plot_layout.addWidget(self.rd_plot, stretch=5)

        # 目标闪烁标记（半透明大圆点，初始隐藏）
        self._flash_item = pg.ScatterPlotItem(
            [], [], size=40, symbol='o',
            pen=pg.mkPen(None),
            brush=pg.mkBrush(255, 215, 0, 180),
        )
        self.rd_plot.addItem(self._flash_item)

        # Tab 切换区
        self.tab_widget = QtWidgets.QTabWidget()
        self.tab_widget.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Expanding,
        )
        self.tab_widget.addTab(self.md_plot,
            "Micro-Doppler | 微多普勒谱")
        self.tab_widget.addTab(self.time_plot,
            "Time Domain | 时域信号")
        self.tab_widget.addTab(self.waterfall_plot,
            "Waterfall | 距离瀑布图")
        self.tab_widget.addTab(self.target_sector_plot,
            "Targets | 目标检测点")

        # Tab 切换淡入过渡
        self._tab_fade = QtWidgets.QGraphicsOpacityEffect(self.tab_widget)
        self._tab_fade.setOpacity(1.0)
        self.tab_widget.setGraphicsEffect(self._tab_fade)
        self._tab_anim = QtCore.QPropertyAnimation(self._tab_fade, b"opacity")
        self._tab_anim.setDuration(180)
        self._tab_anim.setStartValue(0.4)
        self._tab_anim.setEndValue(1.0)
        self.tab_widget.currentChanged.connect(self._on_tab_changed)

        plot_layout.addWidget(self.tab_widget, stretch=4)

        main_layout.addWidget(plot_holder, stretch=1)

        # 分隔竖线 (1px)
        divider = QtWidgets.QWidget()
        divider.setFixedWidth(1)
        divider.setStyleSheet(
            f"background-color: {self.theme['panel_div']};")
        main_layout.addWidget(divider, stretch=0)

        # ---------- 右:控制面板 ----------
        # 显式设置面板底色
        t = self.theme
        self.control_scroll.setStyleSheet(
            f"background-color: {t['panel_bg']}; border: none;")
        try:
            self.control_panel.setStyleSheet(
                f"background-color: {t['panel_bg']};")
        except Exception:
            pass
        main_layout.addWidget(self.control_scroll, stretch=0)

        # 右下角水印
        self._watermark = QtWidgets.QLabel("ISAC Demo System", new_central)
        self._watermark.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignBottom)
        self._watermark.setStyleSheet(
            f"color: {COLOR_TEXT_MUTED}; background: transparent; "
            f"font-size: 9px; padding: 2px 8px;")
        self._watermark.setAttribute(QtCore.Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        self.setCentralWidget(new_central)
        if old_central is not None:
            old_central.deleteLater()

    def _on_tab_changed(self, _idx: int):
        """Tab 切换时触发淡入动画。"""
        try:
            self._tab_anim.stop()
            self._tab_fade.setOpacity(0.4)
            self._tab_anim.start()
        except Exception:
            pass

    def _position_watermark(self):
        """RD 图水印 + 右下角窗口水印。"""
        try:
            vb = self.rd_plot.getPlotItem().getViewBox()
            x_max = vb.viewRange()[0][1]
            y_max = vb.viewRange()[1][1]
            self._rd_watermark.setPos(x_max * 0.96, y_max * 0.94)
        except Exception:
            pass
        try:
            cw = self.centralWidget()
            if cw is not None:
                ww, wh = cw.width(), cw.height()
                self._watermark.setGeometry(ww - 180, wh - 22, 172, 18)
        except Exception:
            pass

    # ---------------- 控件本地化 ----------------
    def _localize_control_panel(self):
        if not hasattr(self, 'control_panel'):
            return
        for lbl in self.control_panel.findChildren(QtWidgets.QLabel):
            if lbl in self._status_labels:
                continue
            translated = _translate_label_text(lbl.text())
            if translated != lbl.text():
                lbl.setText(translated)

        for btn in self.control_panel.findChildren(QtWidgets.QPushButton):
            translated = _translate_button_text(btn.text())
            if translated != btn.text():
                btn.setText(translated)

        self._localize_status_labels_initial()

    def _localize_status_labels_initial(self):
        try:
            self._set_status_label_text(self.lbl_display, "显示通道:CH1")
            self._set_status_label_text(self.lbl_fps, "帧率: 0.0 fps | 处理时延: -- ms")
            self._set_status_label_text(self.lbl_queue, "队列(聚合/显示): 0")
            self._set_status_label_text(self.lbl_sender, "发送端: 等待检测...")
            self._set_status_label_text(self.lbl_params, "参数: 等待握手...")
            self._set_status_label_text(self.lbl_buffer, "微多普勒缓冲: 0/" + str(BUFFER_LENGTH))
            self._set_status_label_text(self.lbl_cfar, "检测器: 未启用")
            self._set_status_label_text(self.lbl_phase_sync, "相位同步: 等待同步聚合帧")
            self._set_status_label_text(self.lbl_phase_clicked, "点选相位: 在 RD 图上点击查询")
            self._set_status_label_text(self.lbl_aoa_status, "到达角(AoA): 等待校准/点击")
        except Exception:
            pass

    # ---------------- 新增状态标签 ----------------
    def _add_extra_status_labels(self):
        self.lbl_zh_summary = QtWidgets.QLabel("[System | 系统] 等待数据流入...")
        self.lbl_throughput = QtWidgets.QLabel("[Throughput | 吞吐量] -- Mbps  Frame: -- KB")
        self.lbl_data_volume = QtWidgets.QLabel("[Total | 累计] 0.00 MB | Frames: 0")
        self.lbl_frame_rate = QtWidgets.QLabel("[FPS | 帧率] -- fps")

        fixed_font = QtGui.QFontDatabase.systemFont(
            QtGui.QFontDatabase.SystemFont.FixedFont)

        for lbl in (self.lbl_zh_summary, self.lbl_throughput,
                    self.lbl_data_volume, self.lbl_frame_rate):
            lbl.setWordWrap(False)
            lbl.setTextFormat(QtCore.Qt.TextFormat.PlainText)
            lbl.setSizePolicy(
                QtWidgets.QSizePolicy.Policy.Fixed,
                QtWidgets.QSizePolicy.Policy.Fixed,
            )
            lbl.setFixedWidth(self._status_label_text_width)
            lbl.setFont(fixed_font)
            t = self.theme
            lbl.setStyleSheet(
                f"QLabel {{ color: {t['text_primary']}; "
                f"background-color: {t['status_label_bg']}; "
                f"border: 1px solid {t['border']}; "
                f"padding: 2px 6px; border-radius: 3px; }}")
            self._status_labels.append(lbl)

        if hasattr(self, 'control_panel'):
            ctrl_layout = self.control_panel.layout()
            ctrl_layout.insertWidget(0, self.lbl_zh_summary)
            ctrl_layout.insertWidget(1, self.lbl_throughput)
            ctrl_layout.insertWidget(2, self.lbl_data_volume)
            ctrl_layout.insertWidget(3, self.lbl_frame_rate)

    # ---------------- 主刷新流程 ----------------
    def update_plots(self):
        super().update_plots()
        # RD 图动态范围：第 5 / 99.5 百分位，带钳位
        try:
            self._apply_rd_percentile_levels()
        except Exception as exc:
            print(f"[Demo] rd_levels update failed: {exc}")
        # RD 图坐标轴范围跟随 Delay View / Doppler View 参数
        try:
            self._sync_rd_view_range()
        except Exception as exc:
            print(f"[Demo] rd_view_range update failed: {exc}")
        try:
            self._update_time_plot()
        except Exception as exc:
            print(f"[Demo] time_plot update failed: {exc}")
        try:
            self._update_waterfall_plot()
        except Exception as exc:
            print(f"[Demo] waterfall_plot update failed: {exc}")
        try:
            self._update_throughput_panel()
        except Exception as exc:
            print(f"[Demo] throughput update failed: {exc}")
        try:
            self._update_status_info()
        except Exception as exc:
            print(f"[Demo] status_info update failed: {exc}")
        try:
            self._maybe_flash_targets()
        except Exception as exc:
            print(f"[Demo] target_flash update failed: {exc}")

    def _maybe_flash_targets(self):
        """检测到新目标时在 RD 图上短暂闪烁（200ms 后消失）。"""
        ch = self._get_display_channel_runtime()
        if ch is None or ch.current_display_data is None:
            return
        pts = ch.current_display_data.get('detected_points')
        if pts is None:
            pts = ch.current_display_data.get('cfar_points')
        n = len(pts) if pts is not None and hasattr(pts, '__len__') else 0
        if n > self._last_target_count:
            # 新目标出现 → 闪一下
            if pts is not None and hasattr(pts, 'shape') and pts.shape[0] > 0:
                # pts shape: (N, 2) — (doppler_idx, range_idx)
                self._flash_item.setData(
                    x=pts[:5, 0].astype(float),
                    y=pts[:5, 1].astype(float),
                )
                self._flash_timer.start(200)
        self._last_target_count = n

    def _clear_target_flash(self):
        """清除目标闪烁标记。"""
        try:
            self._flash_item.setData([], [])
        except Exception:
            pass

    def _apply_rd_percentile_levels(self):
        """RD 图每帧取第 5/99.5 百分位，下限钳位到 -40，上限钳位到 -10。"""
        ch = self._get_display_channel_runtime()
        if ch is None or ch.current_display_data is None:
            return
        rd = ch.current_display_data.get('rd')
        if rd is None:
            return
        rd_arr = np.asarray(rd)
        if rd_arr.ndim != 2 or rd_arr.size < 10:
            return
        lo = float(np.percentile(rd_arr, 5.0))
        hi = float(np.percentile(rd_arr, 99.5))
        if lo < -40.0:
            lo = -40.0
        if hi < -10.0:
            hi = -10.0
        if hi <= lo:
            hi = lo + 1e-3
        self.rd_img.setLookupTable(CUSTOM_RD_COLORMAP.getLookupTable())
        self.rd_img.setLevels((lo, hi))
        self.rd_colorbar.setLevels(values=(lo, hi))

    def _sync_rd_view_range(self):
        """RD 图 X/Y 轴显示范围跟随 Delay View / Doppler View 参数。"""
        vb = self.rd_plot.getPlotItem().getViewBox()
        range_limit = get_display_range_bin_limit()
        doppler_limit = get_display_doppler_bin_limit()
        vb.setRange(
            xRange=(-0.5 * doppler_limit, 0.5 * doppler_limit),
            yRange=(0.0, float(range_limit)),
            padding=0.0,
            update=True,
        )

    # ---------------- 时域信号图刷新 ----------------
    def _update_time_plot(self):
        ch = self._get_display_channel_runtime()
        if ch is None or ch.current_display_data is None:
            return
        latest = ch.current_display_data
        raw = latest.get('raw')

        # 自适应目标点数：至少 512，至多屏幕像素 ×2
        pw = self.time_plot.width()
        if pw < 1:
            pw = 1024
        n_target = max(512, min(pw * 2, 4096))

        if raw is None:
            rd = latest.get('rd')
            if rd is None:
                return
            rd_arr = np.asarray(rd)
            if rd_arr.ndim != 2 or rd_arr.size == 0:
                return
            arr = rd_arr[rd_arr.shape[0] // 2].astype(np.float32)
            arr = self._downsample_for_display(arr, n_target)
            x = self._get_time_x(len(arr))
            self.time_glow_i.setData([], [])
            self.time_glow_q.setData([], [])
            self.time_glow_mag.setData(x, arr)
            self.time_curve_i.setData([], [])
            self.time_curve_q.setData([], [])
            self.time_curve_mag.setData(x, arr)
            return

        try:
            arr = core.to_numpy(raw)
        except Exception:
            arr = np.asarray(raw)

        if arr.ndim > 1:
            arr = arr.reshape(-1)
        if arr.size == 0:
            return

        arr = self._downsample_for_display(arr, n_target)
        n = len(arr)
        x = self._get_time_x(n)

        if np.iscomplexobj(arr):
            re = arr.real.astype(np.float32, copy=False)
            im = arr.imag.astype(np.float32, copy=False)
            mag = np.abs(arr).astype(np.float32, copy=False)
            self.time_glow_i.setData(x, re)
            self.time_glow_q.setData(x, im)
            self.time_glow_mag.setData(x, mag)
            self.time_curve_i.setData(x, re)
            self.time_curve_q.setData(x, im)
            self.time_curve_mag.setData(x, mag)
        else:
            arr_f = arr.astype(np.float32, copy=False)
            self.time_glow_i.setData([], [])
            self.time_glow_q.setData([], [])
            self.time_glow_mag.setData(x, arr_f)
            self.time_curve_i.setData([], [])
            self.time_curve_q.setData([], [])
            self.time_curve_mag.setData(x, arr_f)

    @staticmethod
    def _downsample_for_display(arr, n_target):
        """分段均值降采样：每段取平均，保留信号特征，避免跳点丢失尖峰。"""
        n = arr.size
        if n <= n_target:
            return arr
        seg = n // n_target
        trim = seg * n_target
        trimmed = arr[:trim]
        # reshape → mean per segment
        if np.iscomplexobj(trimmed):
            reshaped = trimmed.reshape(n_target, seg)
            return np.mean(reshaped, axis=1)
        else:
            reshaped = trimmed.reshape(n_target, seg)
            return np.mean(reshaped, axis=1).astype(np.float32, copy=False)

    def _get_time_x(self, n):
        """预分配 x 轴缓存，仅在窗口大小变化时重新分配。"""
        w = self.time_plot.width()
        if w != self._time_last_w or n > len(self._time_x_cache):
            self._time_x_cache = np.arange(max(n, 4096), dtype=np.float32)
            self._time_last_w = w
        return self._time_x_cache[:n]

    # ---------------- 瀑布图刷新 ----------------
    def _update_waterfall_plot(self):
        ch = self._get_display_channel_runtime()
        if ch is None or ch.current_display_data is None:
            return
        rd = ch.current_display_data.get('rd')
        if rd is None:
            return
        rd_arr = np.asarray(rd)
        if rd_arr.ndim != 2 or rd_arr.size == 0:
            return
        range_profile = rd_arr.max(axis=0).astype(np.float32, copy=False)
        self._waterfall_history.append(range_profile)

        if len(self._waterfall_history) < 2:
            return

        min_len = min(p.size for p in self._waterfall_history)
        wf_img = np.stack(
            [p[:min_len] for p in self._waterfall_history], axis=0)

        self.waterfall_img.setImage(wf_img, autoLevels=False)
        wf_min = float(np.percentile(wf_img, 5.0))
        wf_max = float(np.percentile(wf_img, 99.5))
        if wf_min < -60.0:
            wf_min = -60.0
        if wf_max > 0.0:
            wf_max = 0.0
        if wf_max <= wf_min:
            wf_max = wf_min + 1e-3
        self.waterfall_img.setLevels((wf_min, wf_max))
        try:
            self.waterfall_colorbar.setLevels(values=(wf_min, wf_max))
        except Exception:
            pass

    # ---------------- 吞吐量与汇总指标 ----------------
    def _update_throughput_panel(self):
        ch = self._get_display_channel_runtime()
        if ch is None or ch.current_display_data is None:
            self._data_received = False
            return

        self._data_received = True

        params = core.get_viewer_params(ch)
        try:
            wire_fmt = int(getattr(params, 'wire_data_format', 0))
        except Exception:
            wire_fmt = 0
        bytes_per_complex = 4 if wire_fmt == 1 else 8

        n_ch = max(1, len(CHANNELS))
        active_rows = int(getattr(params, 'active_rows', 100))
        active_cols = int(getattr(params, 'active_cols', 1024))
        frame_bytes = active_rows * active_cols * bytes_per_complex * n_ch

        cur_frame_id = ch.last_frame_id
        if cur_frame_id is not None:
            if self._last_thru_frame_id is None:
                self._last_thru_frame_id = cur_frame_id
            elif cur_frame_id > self._last_thru_frame_id:
                delta = cur_frame_id - self._last_thru_frame_id
                self._byte_counter += delta * frame_bytes
                self._cum_bytes_total += delta * frame_bytes
                self._frames_since_t0 += delta
                self._last_thru_frame_id = cur_frame_id

        now = time.time()
        elapsed = now - self._byte_counter_t0
        if elapsed >= THROUGHPUT_REFRESH_S:
            mbps = (self._byte_counter * 8.0) / (elapsed * 1e6)
            fps = self._frames_since_t0 / elapsed if elapsed > 0 else 0.0

            self._set_status_label_text(
                self.lbl_throughput,
                f"[Throughput | 吞吐量] {mbps:7.2f} Mbps  "
                f"Frame: {frame_bytes/1024:7.1f} KB",
            )
            self._set_status_label_text(
                self.lbl_data_volume,
                f"[Total | 累计] {self._cum_bytes_total/(1024*1024):8.2f} MB"
                f"  Frame ID: {cur_frame_id if cur_frame_id is not None else '--'}",
            )
            self._set_status_label_text(
                self.lbl_frame_rate,
                f"[FPS | 帧率] {fps:6.2f} fps  Channels: {n_ch}",
            )
            self._set_status_label_text(
                self.lbl_zh_summary,
                f"[System | 系统] 运行中 | Queue: {aggregate_frame_queue.qsize()}"
                f" | Sender: {ch.sender_ip or 'detecting'}",
            )

            self._byte_counter = 0
            self._frames_since_t0 = 0
            self._byte_counter_t0 = now


# ====================== 入口 ======================
def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("ISAC Demo System")

    default_font = app.font()
    default_font.setFamily(
        "Microsoft YaHei UI" if sys.platform.startswith("win")
        else "Noto Sans CJK SC")
    default_font.setPointSize(10)
    app.setFont(default_font)

    window = MainWindowDemo()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
