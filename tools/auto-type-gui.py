#!/usr/bin/env python3
"""
Auto-Type GUI v4 - 多窗口自动键盘输入工具
设计风格: 暗黑赛博朋克 | 工业控制台 | 霓虹高对比
"""

import sys
import subprocess
import threading
import time
import json
import os
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QComboBox, QSpinBox, QLineEdit, QTextEdit, QPushButton,
    QLabel, QGroupBox, QCheckBox, QMessageBox, QListWidget,
    QListWidgetItem, QFrame, QDialog, QDialogButtonBox,
    QTimeEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QFileDialog, QTabWidget, QGraphicsDropShadowEffect,
    QGridLayout, QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject, QTime, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import (
    QFont, QTextCursor, QKeySequence, QColor, QPalette,
    QLinearGradient, QBrush, QPainter, QPainterPath
)

# ── 配色方案 ──────────────────────────────────────────────
COLORS = {
    "bg_primary": "#0a0e17",       # 深空黑
    "bg_secondary": "#111827",     # 面板背景
    "bg_card": "#1a2235",          # 卡片背景
    "bg_input": "#0f1623",         # 输入框背景
    "border": "#1e293b",           # 边框
    "border_focus": "#3b82f6",     # 聚焦边框
    "accent_blue": "#3b82f6",      # 主蓝
    "accent_cyan": "#06b6d4",      # 青色
    "accent_green": "#10b981",     # 绿色
    "accent_amber": "#f59e0b",     # 琥珀
    "accent_red": "#ef4444",       # 红色
    "accent_purple": "#8b5cf6",    # 紫色
    "text_primary": "#f1f5f9",     # 主文本
    "text_secondary": "#94a3b8",   # 次文本
    "text_muted": "#475569",       # 暗文本
    "neon_glow": "#00fff7",        # 霓虹光
}

# ── 样式表 ────────────────────────────────────────────────
STYLESHEET = f"""
QMainWindow {{
    background-color: {COLORS['bg_primary']};
}}
QWidget {{
    color: {COLORS['text_primary']};
    font-family: 'Cascadia Code', 'JetBrains Mono', 'Fira Code', 'Consolas';
    font-size: 12px;
}}
QGroupBox {{
    background-color: {COLORS['bg_card']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    margin-top: 12px;
    padding: 16px 12px 12px 12px;
    font-weight: bold;
    font-size: 13px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 16px;
    padding: 0 8px;
    color: {COLORS['accent_cyan']};
    font-size: 13px;
}}
QTabWidget::pane {{
    background: {COLORS['bg_secondary']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
}}
QTabBar::tab {{
    background: {COLORS['bg_card']};
    color: {COLORS['text_secondary']};
    padding: 10px 24px;
    margin-right: 2px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    font-size: 13px;
    font-weight: bold;
}}
QTabBar::tab:selected {{
    background: {COLORS['bg_secondary']};
    color: {COLORS['neon_glow']};
    border-bottom: 2px solid {COLORS['accent_cyan']};
}}
QComboBox {{
    background-color: {COLORS['bg_input']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 8px 12px;
    color: {COLORS['text_primary']};
    min-height: 20px;
}}
QComboBox:hover {{
    border-color: {COLORS['accent_blue']};
}}
QComboBox::drop-down {{
    border: none;
    width: 30px;
}}
QComboBox QAbstractItemView {{
    background-color: {COLORS['bg_card']};
    border: 1px solid {COLORS['border']};
    color: {COLORS['text_primary']};
    selection-background-color: {COLORS['accent_blue']};
}}
QLineEdit, QSpinBox, QTimeEdit {{
    background-color: {COLORS['bg_input']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 8px 12px;
    color: {COLORS['text_primary']};
    min-height: 20px;
}}
QLineEdit:focus, QSpinBox:focus, QTimeEdit:focus {{
    border-color: {COLORS['accent_blue']};
}}
QLineEdit[readOnly="true"] {{
    background-color: {COLORS['bg_secondary']};
    color: {COLORS['accent_cyan']};
}}
QListWidget, QTableWidget {{
    background-color: {COLORS['bg_input']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    color: {COLORS['text_primary']};
    alternate-background-color: {COLORS['bg_card']};
}}
QListWidget::item, QTableWidget::item {{
    padding: 6px;
    border-bottom: 1px solid {COLORS['border']};
}}
QListWidget::item:selected, QTableWidget::item:selected {{
    background-color: {COLORS['accent_blue']};
    color: white;
}}
QHeaderView::section {{
    background-color: {COLORS['bg_card']};
    color: {COLORS['accent_cyan']};
    padding: 8px;
    border: none;
    border-bottom: 2px solid {COLORS['accent_cyan']};
    font-weight: bold;
}}
QTextEdit {{
    background-color: {COLORS['bg_input']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    color: {COLORS['text_primary']};
    padding: 8px;
}}
QCheckBox {{
    spacing: 8px;
    color: {COLORS['text_secondary']};
}}
QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 2px solid {COLORS['border']};
    background: {COLORS['bg_input']};
}}
QCheckBox::indicator:checked {{
    background: {COLORS['accent_blue']};
    border-color: {COLORS['accent_blue']};
}}
QScrollBar:vertical {{
    background: {COLORS['bg_primary']};
    width: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical {{
    background: {COLORS['border']};
    border-radius: 4px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: {COLORS['accent_blue']};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
"""


def glow_effect(color=COLORS['accent_cyan'], radius=15):
    """创建发光效果"""
    effect = QGraphicsDropShadowEffect()
    effect.setColor(QColor(color))
    effect.setBlurRadius(radius)
    effect.setOffset(0, 0)
    return effect


def create_button(text, color, bg_color=None, icon=None):
    """创建统一风格按钮"""
    btn = QPushButton(text)
    btn.setCursor(Qt.PointingHandCursor)
    btn.setMinimumHeight(36)
    style = f"""
        QPushButton {{
            background-color: {bg_color or color};
            color: white;
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            font-weight: bold;
            font-size: 12px;
        }}
        QPushButton:hover {{
            background-color: {color};
            opacity: 0.9;
        }}
        QPushButton:pressed {{
            background-color: {color};
            padding-top: 10px;
        }}
        QPushButton:disabled {{
            background-color: {COLORS['bg_card']};
            color: {COLORS['text_muted']};
        }}
    """
    btn.setStyleSheet(style)
    return btn


class KeyCaptureDialog(QDialog):
    keyCaptured = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🎯 捕获按键")
        self.setFixedSize(400, 250)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLORS['bg_primary']};
                border: 2px solid {COLORS['accent_cyan']};
                border-radius: 12px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        self.info_label = QLabel("请按下键盘按键...")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setFont(QFont("Cascadia Code", 16))
        self.info_label.setStyleSheet(f"color: {COLORS['text_secondary']}; border: none;")
        layout.addWidget(self.info_label)

        self.result_label = QLabel("")
        self.result_label.setAlignment(Qt.AlignCenter)
        self.result_label.setFont(QFont("Cascadia Code", 24, QFont.Bold))
        self.result_label.setStyleSheet(f"color: {COLORS['neon_glow']}; border: none;")
        self.result_label.setGraphicsEffect(glow_effect(COLORS['neon_glow'], 20))
        layout.addWidget(self.result_label)

        self.hint_label = QLabel("支持组合键 (Ctrl+C, Alt+Tab...)")
        self.hint_label.setAlignment(Qt.AlignCenter)
        self.hint_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px; border: none;")
        layout.addWidget(self.hint_label)

        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        btn_box.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['bg_card']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 8px 20px;
                min-width: 80px;
            }}
            QPushButton:hover {{
                border-color: {COLORS['accent_blue']};
            }}
        """)
        layout.addWidget(btn_box)

        self.captured_key = ""
        self.captured_keys = []
        self.capture_timer = QTimer()
        self.capture_timer.setSingleShot(True)
        self.capture_timer.timeout.connect(self.on_capture_done)
        QTimer.singleShot(100, self.grabKeyboard)

    def on_capture_done(self):
        if self.captured_keys:
            self.releaseKeyboard()
            self.captured_key = "+".join(self.captured_keys)
            self.result_label.setText(self.captured_key)
            self.info_label.setText("✅ 捕获完成")
            self.info_label.setStyleSheet(f"color: {COLORS['accent_green']}; border: none;")

    def keyPressEvent(self, event):
        key = event.key()
        if key in (Qt.Key_Control, Qt.Key_Alt, Qt.Key_Shift, Qt.Key_Meta):
            return
        modifiers = event.modifiers()
        mod_keys = []
        if modifiers & Qt.ControlModifier: mod_keys.append("ctrl")
        if modifiers & Qt.AltModifier: mod_keys.append("alt")
        if modifiers & Qt.ShiftModifier: mod_keys.append("shift")
        if modifiers & Qt.MetaModifier: mod_keys.append("super")

        KEY_MAP = {
            Qt.Key_Return: "Return", Qt.Key_Enter: "Return", Qt.Key_Tab: "Tab",
            Qt.Key_Backspace: "BackSpace", Qt.Key_Delete: "Delete", Qt.Key_Escape: "Escape",
            Qt.Key_Space: "space", Qt.Key_Up: "Up", Qt.Key_Down: "Down",
            Qt.Key_Left: "Left", Qt.Key_Right: "Right", Qt.Key_Home: "Home",
            Qt.Key_End: "End", Qt.Key_PageUp: "Page_Up", Qt.Key_PageDown: "Page_Down",
            Qt.Key_F1: "F1", Qt.Key_F2: "F2", Qt.Key_F3: "F3", Qt.Key_F4: "F4",
            Qt.Key_F5: "F5", Qt.Key_F6: "F6", Qt.Key_F7: "F7", Qt.Key_F8: "F8",
            Qt.Key_F9: "F9", Qt.Key_F10: "F10", Qt.Key_F11: "F11", Qt.Key_F12: "F12",
        }
        main_key = KEY_MAP.get(key)
        if main_key is None:
            text = QKeySequence(key).toString()
            main_key = text.lower() if text and len(text) == 1 else (event.text().lower() if event.text() else f"key_{key}")

        seen = set()
        self.captured_keys = [k for k in mod_keys + [main_key] if k not in seen and not seen.add(k)]
        display = "+".join(self.captured_keys)
        self.result_label.setText(display)
        self.result_label.setGraphicsEffect(glow_effect(COLORS['neon_glow'], 25))
        self.info_label.setText("捕获中... 500ms后确认")
        self.info_label.setStyleSheet(f"color: {COLORS['text_secondary']}; border: none;")
        self.capture_timer.start(500)

    def keyReleaseEvent(self, event):
        pass

    def reject(self):
        self.releaseKeyboard()
        super().reject()

    def accept(self):
        self.releaseKeyboard()
        if self.captured_key:
            self.keyCaptured.emit(self.captured_key)
        super().accept()


class WorkerSignals(QObject):
    log = pyqtSignal(str)
    finished = pyqtSignal(str)


class AutoTypeWorker(threading.Thread):
    def __init__(self, task_id, window_ids, interval, keys, is_key, count=0):
        super().__init__(daemon=True)
        self.task_id = task_id
        self.window_ids = window_ids if isinstance(window_ids, list) else [window_ids]
        self.interval = interval
        self.keys = keys if isinstance(keys, list) else [keys]
        self.is_key = is_key
        self.count = count
        self.running = False
        self.signals = WorkerSignals()

    def run(self):
        self.running = True
        i = 0
        key_idx = 0
        while self.running:
            i += 1
            current_key = self.keys[key_idx % len(self.keys)]
            for wid in self.window_ids:
                if not self.running:
                    break
                try:
                    if self.is_key:
                        cmd = ['xdotool', 'key', '--window', str(wid), current_key]
                    else:
                        cmd = ['xdotool', 'type', '--window', str(wid), '--delay', '50', current_key]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                    status = "✓" if result.returncode == 0 else "✗"
                    self.signals.log.emit(f"[{datetime.now().strftime('%H:%M:%S')}] #{i} {status} → {wid}: {current_key}")
                except Exception as e:
                    self.signals.log.emit(f"[{datetime.now().strftime('%H:%M:%S')}] #{i} ✗ 错误: {e}")
            key_idx += 1
            if self.count > 0 and i >= self.count:
                break
            wait = 0
            while wait < self.interval and self.running:
                time.sleep(0.1)
                wait += 0.1
        self.signals.finished.emit(self.task_id)

    def stop(self):
        self.running = False


class ScheduleManager:
    def __init__(self, log_callback):
        self.tasks = []
        self.log = log_callback
        self.workers = {}
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_tasks)
        self.timer.start(1000)
        self.load_tasks()

    def load_tasks(self):
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scheduled_tasks.json")
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    self.tasks = json.load(f)
            except:
                self.tasks = []

    def save_tasks(self):
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scheduled_tasks.json")
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.tasks, f, ensure_ascii=False, indent=2)

    def add_task(self, name, time_str, window_ids, keys, is_key, interval, count):
        task = {
            "id": f"task_{int(time.time()*1000)}",
            "name": name, "time": time_str, "window_ids": window_ids,
            "keys": keys, "is_key": is_key, "interval": interval,
            "count": count, "enabled": True, "executed": False
        }
        self.tasks.append(task)
        self.save_tasks()
        return task

    def remove_task(self, task_id):
        self.tasks = [t for t in self.tasks if t["id"] != task_id]
        self.save_tasks()

    def toggle_task(self, task_id):
        for t in self.tasks:
            if t["id"] == task_id:
                t["enabled"] = not t["enabled"]
                if not t["enabled"]:
                    t["executed"] = False
                break
        self.save_tasks()

    def check_tasks(self):
        current_time = datetime.now().strftime("%H:%M:%S")
        for task in self.tasks:
            if not task["enabled"] or task["executed"]:
                continue
            if task["time"] == current_time:
                task["executed"] = True
                self.log(f"⏰ 定时触发: {task['name']}")
                self.execute_task(task)

    def execute_task(self, task):
        worker = AutoTypeWorker(task["id"], task["window_ids"], task["interval"], task["keys"], task["is_key"], task["count"])
        worker.signals.log.connect(self.log)
        worker.signals.finished.connect(lambda tid: self.workers.pop(tid, None))
        self.workers[task["id"]] = worker
        worker.start()

    def stop_all(self):
        for w in self.workers.values():
            w.stop()
        self.workers.clear()

    def get_tasks(self):
        return self.tasks


class StatusIndicator(QWidget):
    """状态指示灯"""
    def __init__(self, text="就绪", color=COLORS['text_muted']):
        super().__init__()
        self.color = color
        self.text = text
        self.setFixedHeight(32)

    def set_status(self, text, color):
        self.text = text
        self.color = color
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        # 圆点
        painter.setBrush(QColor(self.color))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(8, 10, 10, 10)
        # 文本
        painter.setPen(QColor(self.color))
        painter.setFont(QFont("Cascadia Code", 11, QFont.Bold))
        painter.drawText(24, 10, self.width() - 24, 16, Qt.AlignVCenter, self.text)


class AutoTypeGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.worker = None
        self.windows = []
        self.schedule_mgr = None
        self.init_ui()
        self.refresh_windows()
        self.schedule_mgr = ScheduleManager(self.log)

    def init_ui(self):
        self.setWindowTitle('⌨ Auto-Type Console')
        self.setGeometry(100, 100, 960, 850)
        self.setStyleSheet(STYLESHEET)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(16, 16, 16, 16)

        # ── 标题栏 ──
        header = QHBoxLayout()
        title = QLabel("⌨ AUTO-TYPE CONSOLE")
        title.setFont(QFont("Cascadia Code", 18, QFont.Bold))
        title.setStyleSheet(f"color: {COLORS['neon_glow']}; letter-spacing: 2px;")
        title.setGraphicsEffect(glow_effect(COLORS['neon_glow'], 15))
        header.addWidget(title)
        header.addStretch()

        self.status = StatusIndicator("就绪", COLORS['text_muted'])
        header.addWidget(self.status)
        main_layout.addLayout(header)

        # ── Tab 切换 ──
        tabs = QTabWidget()
        tab_manual = QWidget()
        tab_schedule = QWidget()
        tabs.addTab(tab_manual, "🎮 手动控制")
        tabs.addTab(tab_schedule, "⏰ 定时任务")

        # ══════════════════════════════════════════════
        # 手动控制 Tab
        # ══════════════════════════════════════════════
        manual_layout = QVBoxLayout(tab_manual)
        manual_layout.setSpacing(12)

        # ── 窗口选择 ──
        win_group = QGroupBox("📡 目标窗口（支持多选）")
        win_layout = QVBoxLayout()

        win_row1 = QHBoxLayout()
        self.window_combo = QComboBox()
        self.window_combo.setMinimumHeight(36)
        win_row1.addWidget(self.window_combo, 1)
        win_row1.addWidget(create_button("🔄 刷新", COLORS['accent_blue'], COLORS['bg_card'], "🔄"))
        self.window_combo.parent_btn_refresh = win_row1.itemAt(1).widget()
        self.window_combo.parent_btn_refresh.clicked.connect(self.refresh_windows)
        win_row1.addWidget(create_button("➕ 添加", COLORS['accent_green'], COLORS['bg_card']))
        win_row1.itemAt(2).widget().clicked.connect(self.add_window_to_list)
        win_layout.addLayout(win_row1)

        self.window_list = QListWidget()
        self.window_list.setMaximumHeight(90)
        self.window_list.setAlternatingRowColors(True)
        win_layout.addWidget(self.window_list)

        win_btn_row = QHBoxLayout()
        rm_btn = create_button("➖ 删除选中", COLORS['accent_red'], COLORS['bg_card'])
        rm_btn.clicked.connect(self.remove_selected_window)
        clr_btn = create_button("🗑 清空", COLORS['text_muted'], COLORS['bg_card'])
        clr_btn.clicked.connect(self.window_list.clear)
        win_btn_row.addWidget(rm_btn)
        win_btn_row.addWidget(clr_btn)
        win_btn_row.addStretch()
        win_layout.addLayout(win_btn_row)

        win_group.setLayout(win_layout)
        manual_layout.addWidget(win_group)

        # ── 按键设置 ──
        key_group = QGroupBox("⌨ 按键设置")
        key_layout = QVBoxLayout()

        key_row = QHBoxLayout()
        self.key_display = QLineEdit()
        self.key_display.setReadOnly(True)
        self.key_display.setPlaceholderText("点击右侧按钮捕获键盘按键")
        self.key_display.setMinimumHeight(36)
        key_row.addWidget(self.key_display, 1)

        capture_btn = create_button("🎯 捕获按键", COLORS['accent_cyan'], COLORS['accent_cyan'])
        capture_btn.clicked.connect(self.open_capture_dialog)
        key_row.addWidget(capture_btn)

        add_key_btn = create_button("➕ 添加", COLORS['accent_green'], COLORS['bg_card'])
        add_key_btn.clicked.connect(self.add_key_to_list)
        key_row.addWidget(add_key_btn)
        key_layout.addLayout(key_row)

        self.key_list = QListWidget()
        self.key_list.setMaximumHeight(90)
        self.key_list.setAlternatingRowColors(True)
        key_layout.addWidget(self.key_list)

        key_btn_row = QHBoxLayout()
        rm_key = create_button("➖ 删除", COLORS['accent_red'], COLORS['bg_card'])
        rm_key.clicked.connect(self.remove_selected_key)
        clr_key = create_button("🗑 清空", COLORS['text_muted'], COLORS['bg_card'])
        clr_key.clicked.connect(self.key_list.clear)
        preset_btn = create_button("📋 预设", COLORS['accent_purple'], COLORS['bg_card'])
        preset_btn.clicked.connect(self.show_presets)
        key_btn_row.addWidget(rm_key)
        key_btn_row.addWidget(clr_key)
        key_btn_row.addWidget(preset_btn)
        key_btn_row.addStretch()
        key_layout.addLayout(key_btn_row)

        # 手动输入
        manual_row = QHBoxLayout()
        manual_row.addWidget(QLabel("手动输入:"))
        self.content_input = QLineEdit()
        self.content_input.setPlaceholderText("直接输入按键名 (Return, ctrl+c)")
        self.content_input.setMinimumHeight(36)
        manual_row.addWidget(self.content_input, 1)
        self.key_mode = QCheckBox("按键模式")
        self.key_mode.setChecked(True)
        manual_row.addWidget(self.key_mode)
        key_layout.addLayout(manual_row)

        key_group.setLayout(key_layout)
        manual_layout.addWidget(key_group)

        # ── 参数 ──
        param_group = QGroupBox("⚙ 执行参数")
        param_layout = QHBoxLayout()
        param_layout.addWidget(QLabel("间隔(秒):"))
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 3600)
        self.interval_spin.setValue(2)
        self.interval_spin.setMinimumHeight(36)
        param_layout.addWidget(self.interval_spin)
        param_layout.addWidget(QLabel("次数(0=无限):"))
        self.count_spin = QSpinBox()
        self.count_spin.setRange(0, 10000)
        self.count_spin.setValue(0)
        self.count_spin.setMinimumHeight(36)
        param_layout.addWidget(self.count_spin)
        param_layout.addStretch()
        param_group.setLayout(param_layout)
        manual_layout.addWidget(param_group)

        # ── 控制按钮 ──
        ctrl_row = QHBoxLayout()
        self.start_btn = create_button("▶ 开始执行", COLORS['accent_green'], COLORS['accent_green'])
        self.start_btn.setMinimumHeight(44)
        self.start_btn.setFont(QFont("Cascadia Code", 14, QFont.Bold))
        self.start_btn.clicked.connect(self.start_auto_type)

        self.stop_btn = create_button("⏹ 停止", COLORS['accent_red'], COLORS['accent_red'])
        self.stop_btn.setMinimumHeight(44)
        self.stop_btn.setFont(QFont("Cascadia Code", 14, QFont.Bold))
        self.stop_btn.clicked.connect(self.stop_auto_type)
        self.stop_btn.setEnabled(False)

        ctrl_row.addWidget(self.start_btn)
        ctrl_row.addWidget(self.stop_btn)
        manual_layout.addLayout(ctrl_row)
        manual_layout.addStretch()

        # ══════════════════════════════════════════════
        # 定时任务 Tab
        # ══════════════════════════════════════════════
        sched_layout = QVBoxLayout(tab_schedule)
        sched_layout.setSpacing(12)

        add_group = QGroupBox("➕ 添加定时任务")
        add_layout = QVBoxLayout()

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("任务名:"))
        self.sched_name = QLineEdit()
        self.sched_name.setPlaceholderText("任务名称")
        self.sched_name.setMinimumHeight(36)
        row1.addWidget(self.sched_name, 1)
        row1.addWidget(QLabel("触发时间:"))
        self.sched_time = QTimeEdit()
        self.sched_time.setDisplayFormat("HH:mm:ss")
        self.sched_time.setTime(QTime.currentTime().addSecs(60))
        self.sched_time.setMinimumHeight(36)
        row1.addWidget(self.sched_time)
        add_layout.addLayout(row1)

        hint = QLabel("💡 窗口和按键使用「手动控制」页的设置")
        hint.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px;")
        add_layout.addWidget(hint)

        row3 = QHBoxLayout()
        row3.addWidget(QLabel("间隔(秒):"))
        self.sched_interval = QSpinBox()
        self.sched_interval.setRange(1, 3600)
        self.sched_interval.setValue(2)
        self.sched_interval.setMinimumHeight(36)
        row3.addWidget(self.sched_interval)
        row3.addWidget(QLabel("次数:"))
        self.sched_count = QSpinBox()
        self.sched_count.setRange(1, 10000)
        self.sched_count.setValue(10)
        self.sched_count.setMinimumHeight(36)
        row3.addWidget(self.sched_count)
        row3.addStretch()
        add_task_btn = create_button("➕ 添加定时任务", COLORS['accent_amber'], COLORS['accent_amber'])
        add_task_btn.clicked.connect(self.add_scheduled_task)
        row3.addWidget(add_task_btn)
        add_layout.addLayout(row3)

        add_group.setLayout(add_layout)
        sched_layout.addWidget(add_group)

        # 任务列表
        list_group = QGroupBox("📋 定时任务列表")
        list_layout = QVBoxLayout()

        self.task_table = QTableWidget()
        self.task_table.setColumnCount(7)
        self.task_table.setHorizontalHeaderLabels(['名称', '时间', '窗口', '按键', '间隔', '次数', '状态'])
        self.task_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.task_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.task_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.task_table.setAlternatingRowColors(True)
        list_layout.addWidget(self.task_table)

        task_btn_row = QHBoxLayout()
        toggle_btn = create_button("⏯ 启用/禁用", COLORS['accent_blue'], COLORS['bg_card'])
        toggle_btn.clicked.connect(self.toggle_selected_task)
        del_btn = create_button("🗑 删除", COLORS['accent_red'], COLORS['bg_card'])
        del_btn.clicked.connect(self.delete_selected_task)
        run_btn = create_button("▶ 立即执行", COLORS['accent_green'], COLORS['accent_green'])
        run_btn.clicked.connect(self.run_selected_task_now)
        refresh_btn = create_button("🔄 刷新", COLORS['text_muted'], COLORS['bg_card'])
        refresh_btn.clicked.connect(self.refresh_task_table)

        task_btn_row.addWidget(toggle_btn)
        task_btn_row.addWidget(del_btn)
        task_btn_row.addWidget(run_btn)
        task_btn_row.addWidget(refresh_btn)
        list_layout.addLayout(task_btn_row)

        list_group.setLayout(list_layout)
        sched_layout.addWidget(list_group)

        main_layout.addWidget(tabs)

        # ── 日志 ──
        log_group = QGroupBox("📜 运行日志")
        log_layout = QVBoxLayout()
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Cascadia Code", 10))
        self.log_text.setMaximumHeight(160)
        self.log_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLORS['bg_input']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                color: {COLORS['accent_green']};
                padding: 8px;
            }}
        """)
        log_layout.addWidget(self.log_text)

        log_btn_row = QHBoxLayout()
        clear_log = create_button("🗑 清空", COLORS['text_muted'], COLORS['bg_card'])
        clear_log.clicked.connect(lambda: self.log_text.clear())
        log_btn_row.addWidget(clear_log)
        log_btn_row.addStretch()
        log_layout.addLayout(log_btn_row)

        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group)

    # ── 窗口管理 ──
    def refresh_windows(self):
        self.window_combo.clear()
        self.windows = []
        try:
            result = subprocess.run(['xdotool', 'search', '--name', ''], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                for wid in result.stdout.strip().split('\n'):
                    if not wid.strip():
                        continue
                    try:
                        name_r = subprocess.run(['xdotool', 'getwindowname', wid], capture_output=True, text=True, timeout=2)
                        name = name_r.stdout.strip() if name_r.returncode == 0 else 'Unknown'
                        geo_r = subprocess.run(['xdotool', 'getwindowgeometry', wid], capture_output=True, text=True, timeout=2)
                        geo = ''
                        if geo_r.returncode == 0:
                            for line in geo_r.stdout.split('\n'):
                                if 'Geometry:' in line:
                                    geo = line.split('Geometry:')[1].strip()
                                    break
                        if geo:
                            try:
                                w, h = geo.split('x')
                                if int(w) < 50 or int(h) < 50:
                                    continue
                            except:
                                pass
                        if name and len(name) > 1:
                            self.windows.append((wid, name, geo))
                            self.window_combo.addItem(f"[{wid}] {name} ({geo})")
                    except:
                        continue
                self.log(f"✓ 已加载 {len(self.windows)} 个窗口")
        except Exception as e:
            self.log(f"✗ 刷新失败: {e}")

    def add_window_to_list(self):
        idx = self.window_combo.currentIndex()
        if 0 <= idx < len(self.windows):
            wid, name, geo = self.windows[idx]
            text = f"[{wid}] {name} ({geo})"
            for i in range(self.window_list.count()):
                if self.window_list.item(i).text() == text:
                    self.log(f"⚠ 窗口已存在: {name}")
                    return
            self.window_list.addItem(text)
            self.log(f"✓ 已添加窗口: {name}")

    def remove_selected_window(self):
        for item in self.window_list.selectedItems():
            self.window_list.takeItem(self.window_list.row(item))

    def get_selected_window_ids(self):
        ids = []
        for i in range(self.window_list.count()):
            text = self.window_list.item(i).text()
            try:
                wid = int(text.split(']')[0].replace('[', '').strip())
                ids.append(wid)
            except:
                pass
        if not ids:
            self.log("✗ 请添加至少一个窗口")
        return ids

    # ── 按键管理 ──
    def open_capture_dialog(self):
        dialog = KeyCaptureDialog(self)
        dialog.keyCaptured.connect(self.on_key_captured)
        dialog.exec_()

    def on_key_captured(self, key_str):
        self.key_display.setText(key_str)
        self.log(f"🎯 捕获: {key_str}")

    def add_key_to_list(self):
        key_str = self.key_display.text().strip()
        if key_str:
            self.key_list.addItem(key_str)
            self.key_display.clear()
            self.log(f"✓ 已添加: {key_str}")

    def remove_selected_key(self):
        for item in self.key_list.selectedItems():
            self.key_list.takeItem(self.key_list.row(item))

    def get_content_list(self):
        keys = [self.key_list.item(i).text() for i in range(self.key_list.count())]
        if keys:
            return keys, True
        content = self.content_input.text().strip()
        if content:
            return [content], self.key_mode.isChecked()
        self.log("✗ 请捕获按键或输入内容")
        return None, None

    # ── 手动控制 ──
    def start_auto_type(self):
        window_ids = self.get_selected_window_ids()
        if not window_ids:
            return
        content_list, is_key = self.get_content_list()
        if not content_list:
            return
        interval = self.interval_spin.value()
        count = self.count_spin.value()

        content_str = ", ".join(content_list)
        reply = QMessageBox.question(
            self, '确认执行',
            f'向 {len(window_ids)} 个窗口发送:\n\n'
            f'内容: {content_str}\n间隔: {interval}秒\n'
            f'模式: {"按键" if is_key else "文本"}\n'
            f'次数: {"无限" if count == 0 else count}',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
        )
        if reply != QMessageBox.Yes:
            return

        self.log(f"▶ 开始 -> {len(window_ids)} 窗口 | {content_str} | {interval}s")
        self.worker = AutoTypeWorker("manual", window_ids, interval, content_list, is_key, count)
        self.worker.signals.log.connect(self.log)
        self.worker.signals.finished.connect(self.on_finished)
        self.worker.start()

        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.status.set_status("运行中...", COLORS['accent_green'])

    def stop_auto_type(self):
        if self.worker and self.worker.running:
            self.worker.stop()
            self.log("⏹ 正在停止...")

    def on_finished(self, task_id):
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status.set_status("已停止", COLORS['accent_amber'])
        self.log("✓ 已停止")

    # ── 定时任务 ──
    def add_scheduled_task(self):
        name = self.sched_name.text().strip() or f"任务_{datetime.now().strftime('%H%M%S')}"
        time_str = self.sched_time.time().toString("HH:mm:ss")
        window_ids = self.get_selected_window_ids()
        content_list, is_key = self.get_content_list()
        if not window_ids or not content_list:
            return
        interval = self.sched_interval.value()
        count = self.sched_count.value()

        self.schedule_mgr.add_task(name, time_str, window_ids, content_list, is_key, interval, count)
        self.log(f"⏰ 定时任务已添加: {name} @ {time_str}")
        self.refresh_task_table()

    def refresh_task_table(self):
        tasks = self.schedule_mgr.get_tasks()
        self.task_table.setRowCount(len(tasks))
        for i, t in enumerate(tasks):
            self.task_table.setItem(i, 0, QTableWidgetItem(t.get("name", "")))
            self.task_table.setItem(i, 1, QTableWidgetItem(t.get("time", "")))
            self.task_table.setItem(i, 2, QTableWidgetItem(str(len(t.get("window_ids", [])))))
            self.task_table.setItem(i, 3, QTableWidgetItem(", ".join(t.get("keys", []))))
            self.task_table.setItem(i, 4, QTableWidgetItem(str(t.get("interval", ""))))
            self.task_table.setItem(i, 5, QTableWidgetItem(str(t.get("count", ""))))
            status = "✅ 已执行" if t.get("executed") else ("⏸ 禁用" if not t.get("enabled") else "⏳ 等待中")
            self.task_table.setItem(i, 6, QTableWidgetItem(status))
            self.task_table.item(i, 0).setData(Qt.UserRole, t.get("id"))

    def get_selected_task_id(self):
        row = self.task_table.currentRow()
        if row >= 0:
            item = self.task_table.item(row, 0)
            if item:
                return item.data(Qt.UserRole)
        return None

    def toggle_selected_task(self):
        task_id = self.get_selected_task_id()
        if task_id:
            self.schedule_mgr.toggle_task(task_id)
            self.refresh_task_table()

    def delete_selected_task(self):
        task_id = self.get_selected_task_id()
        if task_id:
            self.schedule_mgr.remove_task(task_id)
            self.refresh_task_table()
            self.log(f"🗑 已删除: {task_id}")

    def run_selected_task_now(self):
        task_id = self.get_selected_task_id()
        if task_id:
            for t in self.schedule_mgr.tasks:
                if t["id"] == task_id:
                    self.log(f"▶ 立即执行: {t['name']}")
                    self.schedule_mgr.execute_task(t)
                    break

    def show_presets(self):
        presets = [
            ("回车", "Return"), ("Tab", "Tab"), ("空格", "space"),
            ("退格", "BackSpace"), ("删除", "Delete"), ("Esc", "Escape"),
            ("↑", "Up"), ("↓", "Down"), ("←", "Left"), ("→", "Right"),
            ("F5", "F5"), ("Ctrl+C", "ctrl+c"), ("Ctrl+V", "ctrl+v"),
            ("Ctrl+Z", "ctrl+z"), ("Ctrl+A", "ctrl+a"), ("Alt+Tab", "alt+Tab"),
        ]
        menu = self.sender().menu()
        if not menu:
            from PyQt5.QtWidgets import QMenu
            menu = QMenu(self)
            menu.setStyleSheet(f"""
                QMenu {{
                    background: {COLORS['bg_card']};
                    border: 1px solid {COLORS['border']};
                    border-radius: 6px;
                    padding: 4px;
                }}
                QMenu::item {{
                    padding: 8px 24px;
                    border-radius: 4px;
                }}
                QMenu::item:selected {{
                    background: {COLORS['accent_blue']};
                }}
            """)
            for name, value in presets:
                action = menu.addAction(name)
                action.setData(value)
                action.triggered.connect(lambda checked, a=action: self.key_list.addItem(a.data()))
            self.sender().setMenu(menu)
        menu.popup(self.sender().mapToGlobal(self.sender().rect().bottomLeft()))

    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        if "✓" in message or "✅" in message:
            color_msg = f'<span style="color:{COLORS["accent_green"]}">[{timestamp}] {message}</span>'
        elif "✗" in message or "⚠" in message:
            color_msg = f'<span style="color:{COLORS["accent_red"]}">[{timestamp}] {message}</span>'
        elif "⏰" in message or "▶" in message:
            color_msg = f'<span style="color:{COLORS["accent_amber"]}">[{timestamp}] {message}</span>'
        elif "🎯" in message:
            color_msg = f'<span style="color:{COLORS["accent_cyan"]}">[{timestamp}] {message}</span>'
        else:
            color_msg = f'<span style="color:{COLORS["text_secondary"]}">[{timestamp}] {message}</span>'

        self.log_text.append(color_msg)
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.log_text.setTextCursor(cursor)

    def closeEvent(self, event):
        if self.worker and self.worker.running:
            self.worker.stop()
            self.worker.join(timeout=2)
        if self.schedule_mgr:
            self.schedule_mgr.stop_all()
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    # 设置全局调色板
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(COLORS['bg_primary']))
    palette.setColor(QPalette.WindowText, QColor(COLORS['text_primary']))
    palette.setColor(QPalette.Base, QColor(COLORS['bg_input']))
    palette.setColor(QPalette.AlternateBase, QColor(COLORS['bg_card']))
    palette.setColor(QPalette.Text, QColor(COLORS['text_primary']))
    palette.setColor(QPalette.Button, QColor(COLORS['bg_card']))
    palette.setColor(QPalette.ButtonText, QColor(COLORS['text_primary']))
    palette.setColor(QPalette.Highlight, QColor(COLORS['accent_blue']))
    palette.setColor(QPalette.HighlightedText, QColor(COLORS['text_primary']))
    app.setPalette(palette)

    window = AutoTypeGUI()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
