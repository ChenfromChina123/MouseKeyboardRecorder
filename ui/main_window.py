"""
主窗口模块
包含录制控制、回放设置、事件预览表格、状态栏等所有 UI 组件
支持多窗口选择、无限回放、颜色区分、配置持久化
"""

import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QSlider, QLabel, QTableWidget, QTableWidgetItem,
    QSpinBox, QStatusBar, QFileDialog, QMessageBox,
    QHeaderView, QGroupBox, QCheckBox, QListWidget, QAbstractItemView,
    QComboBox, QInputDialog
)
from PySide6.QtCore import Qt, Signal, Slot, QTimer
from PySide6.QtGui import QAction, QColor, QFont

from core.event_model import ActionEvent, EventType, RecordingSession, EVENT_TYPE_NAMES
from core.recorder import Recorder
from core.replayer import Replayer
from core.window_manager import WindowManager, WindowInfo
from core.config_manager import save_config, load_config, list_configs, delete_config
from ui.window_selector import WindowSelectorDialog


# 事件类型对应的颜色（更鲜明的区分）
EVENT_COLORS = {
    EventType.MOUSE_MOVE: QColor(200, 230, 255),    # 浅蓝色
    EventType.MOUSE_CLICK: QColor(255, 210, 180),    # 橙色
    EventType.MOUSE_SCROLL: QColor(220, 200, 255),   # 紫色
    EventType.KEY_PRESS: QColor(180, 255, 200),      # 绿色
    EventType.KEY_RELEASE: QColor(235, 235, 235),    # 灰色
}

# 事件类型对应的文字颜色
EVENT_TEXT_COLORS = {
    EventType.MOUSE_MOVE: QColor(0, 80, 160),        # 深蓝
    EventType.MOUSE_CLICK: QColor(160, 60, 0),       # 深橙
    EventType.MOUSE_SCROLL: QColor(100, 0, 160),     # 深紫
    EventType.KEY_PRESS: QColor(0, 120, 40),         # 深绿
    EventType.KEY_RELEASE: QColor(100, 100, 100),    # 深灰
}


class MainWindow(QMainWindow):
    """主窗口"""

    # 跨线程通信信号
    status_signal = Signal(str)
    progress_signal = Signal(int, int)
    event_signal = Signal(object)  # ActionEvent
    finished_signal = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("鼠标键盘录制回放器")
        self.setMinimumSize(800, 620)
        self.resize(850, 680)

        # 核心模块
        self.recorder = Recorder()
        self.replayer = Replayer()
        self.window_mgr = WindowManager()

        # 键盘轮询 QTimer
        self._keyboard_timer = QTimer(self)
        self._keyboard_timer.timeout.connect(self.recorder.poll_keyboard)
        self.recorder.set_keyboard_timer(self._keyboard_timer)

        # 当前录制会话
        self.current_session: RecordingSession = None
        # 已选择的窗口列表 [{hwnd, title, rect}]
        self.selected_windows: list = []

        self._setup_ui()
        self._setup_menu()
        self._setup_status_bar()
        self._connect_signals()
        self._refresh_window_list()
        self._refresh_config_list()

    def _setup_ui(self):
        """构建主界面"""
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(6)

        # === 录制控制区 ===
        ctrl_group = QGroupBox("录制控制")
        ctrl_layout = QHBoxLayout()

        self.btn_record = QPushButton("● 录制")
        self.btn_stop = QPushButton("■ 停止")
        self.btn_replay = QPushButton("▶ 回放")
        self.btn_pause = QPushButton("❚❚ 暂停")
        self.btn_clear = QPushButton("✖ 清空重置")

        # 录制模式选择
        ctrl_layout.addWidget(QLabel("录制范围:"))
        self.combo_record_mode = QComboBox()
        self.combo_record_mode.addItem("鼠标 + 键盘", "both")
        self.combo_record_mode.addItem("仅鼠标", "mouse_only")
        self.combo_record_mode.addItem("仅键盘", "keyboard_only")
        self.combo_record_mode.setMinimumWidth(120)

        self.btn_record.setStyleSheet(
            "QPushButton { background-color: #e03030; color: white; font-weight: bold; padding: 8px 16px; border-radius: 4px; }"
            "QPushButton:hover { background-color: #c02020; }"
        )
        self.btn_stop.setStyleSheet(
            "QPushButton { background-color: #777777; color: white; font-weight: bold; padding: 8px 16px; border-radius: 4px; }"
            "QPushButton:hover { background-color: #606060; }"
        )
        self.btn_replay.setStyleSheet(
            "QPushButton { background-color: #2eaa2e; color: white; font-weight: bold; padding: 8px 16px; border-radius: 4px; }"
            "QPushButton:hover { background-color: #208020; }"
        )
        self.btn_pause.setStyleSheet(
            "QPushButton { background-color: #3377cc; color: white; font-weight: bold; padding: 8px 16px; border-radius: 4px; }"
            "QPushButton:hover { background-color: #2260aa; }"
        )
        self.btn_clear.setStyleSheet(
            "QPushButton { background-color: #cc6633; color: white; font-weight: bold; padding: 8px 16px; border-radius: 4px; }"
            "QPushButton:hover { background-color: #aa5020; }"
        )

        self.btn_stop.setEnabled(False)
        self.btn_replay.setEnabled(False)
        self.btn_pause.setEnabled(False)

        ctrl_layout.addWidget(self.combo_record_mode)
        ctrl_layout.addWidget(self.btn_record)
        ctrl_layout.addWidget(self.btn_stop)
        ctrl_layout.addWidget(self.btn_replay)
        ctrl_layout.addWidget(self.btn_pause)
        ctrl_layout.addWidget(self.btn_clear)
        ctrl_group.setLayout(ctrl_layout)

        # === 回放设置区 ===
        settings_group = QGroupBox("回放设置")
        settings_layout = QHBoxLayout()

        settings_layout.addWidget(QLabel("回放速度:"))
        self.slider_speed = QSlider(Qt.Horizontal)
        self.slider_speed.setRange(1, 50)  # 0.1x ~ 5.0x
        self.slider_speed.setValue(10)
        self.slider_speed.setTickPosition(QSlider.TicksBelow)
        self.slider_speed.setTickInterval(5)
        self.lbl_speed = QLabel("1.0x")
        self.lbl_speed.setMinimumWidth(40)
        settings_layout.addWidget(self.slider_speed)
        settings_layout.addWidget(self.lbl_speed)

        settings_layout.addWidget(QLabel("  重复:"))
        self.spin_repeat = QSpinBox()
        self.spin_repeat.setRange(1, 999999)
        self.spin_repeat.setValue(1)
        self.spin_repeat.setMinimumWidth(70)
        settings_layout.addWidget(self.spin_repeat)
        settings_layout.addWidget(QLabel("次"))
        self.chk_infinite = QCheckBox("无限循环")
        self.chk_infinite.toggled.connect(self._on_infinite_toggled)
        settings_layout.addWidget(self.chk_infinite)
        settings_layout.addStretch()

        settings_group.setLayout(settings_layout)

        # === 目标窗口区 ===
        window_group = QGroupBox("目标窗口（可选，不指定则全局回放）")
        window_main_layout = QVBoxLayout()

        # 第一行：窗口选择控件
        window_select_layout = QHBoxLayout()
        self.combo_window = QComboBox()
        self.combo_window.setMinimumWidth(260)
        self.btn_refresh_windows = QPushButton("刷新")
        self.btn_add_window = QPushButton("添加到列表")
        self.btn_remove_window = QPushButton("移除选中")
        self.chk_no_window = QCheckBox("全局模式")

        window_select_layout.addWidget(self.combo_window)
        window_select_layout.addWidget(self.btn_refresh_windows)
        window_select_layout.addWidget(self.btn_add_window)
        window_select_layout.addWidget(self.btn_remove_window)
        window_select_layout.addWidget(self.chk_no_window)
        window_main_layout.addLayout(window_select_layout)

        # 第二行：已选窗口列表 + 操作按钮
        window_list_layout = QHBoxLayout()
        self.list_selected_windows = QListWidget()
        self.list_selected_windows.setMaximumHeight(100)
        self.list_selected_windows.setAlternatingRowColors(True)
        self.list_selected_windows.setSelectionMode(QListWidget.SingleSelection)

        # 右侧操作按钮
        btn_list_layout = QVBoxLayout()
        self.btn_replay_selected = QPushButton("回放选中窗口")
        self.btn_replay_all = QPushButton("轮流回放全部")
        self.btn_replay_selected.setStyleSheet(
            "QPushButton { background-color: #2eaa2e; color: white; padding: 6px; border-radius: 3px; }"
            "QPushButton:hover { background-color: #208020; }"
            "QPushButton:disabled { background-color: #aaaaaa; }"
        )
        self.btn_replay_all.setStyleSheet(
            "QPushButton { background-color: #3377cc; color: white; padding: 6px; border-radius: 3px; }"
            "QPushButton:hover { background-color: #2260aa; }"
            "QPushButton:disabled { background-color: #aaaaaa; }"
        )
        self.btn_replay_selected.setEnabled(False)
        self.btn_replay_all.setEnabled(False)

        btn_list_layout.addWidget(self.btn_replay_selected)
        btn_list_layout.addWidget(self.btn_replay_all)
        btn_list_layout.addStretch()

        window_list_layout.addWidget(self.list_selected_windows)
        window_list_layout.addLayout(btn_list_layout)
        window_main_layout.addLayout(window_list_layout)

        window_group.setLayout(window_main_layout)

        # === 事件预览表格 ===
        table_group = QGroupBox("事件预览")
        table_layout = QVBoxLayout()

        self.event_table = QTableWidget()
        self.event_table.setColumnCount(4)
        self.event_table.setHorizontalHeaderLabels(["时间", "类型", "详情", "坐标"])
        self.event_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.event_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.event_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.event_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.event_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.event_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.event_table.setAlternatingRowColors(False)  # 使用自定义颜色
        self.event_table.verticalHeader().setVisible(False)
        # 设置行高
        self.event_table.verticalHeader().setDefaultSectionSize(24)

        table_layout.addWidget(self.event_table)
        table_group.setLayout(table_layout)

        # === 配置管理区 ===
        config_group = QGroupBox("配置管理")
        config_layout = QHBoxLayout()

        self.combo_config = QComboBox()
        self.combo_config.setMinimumWidth(200)
        self.btn_config_load = QPushButton("加载配置")
        self.btn_config_save = QPushButton("保存配置")
        self.btn_config_delete = QPushButton("删除配置")

        self.btn_config_load.setStyleSheet(
            "QPushButton { background-color: #2eaa2e; color: white; padding: 6px 12px; border-radius: 3px; }"
            "QPushButton:hover { background-color: #208020; }"
        )
        self.btn_config_save.setStyleSheet(
            "QPushButton { background-color: #3377cc; color: white; padding: 6px 12px; border-radius: 3px; }"
            "QPushButton:hover { background-color: #2260aa; }"
        )
        self.btn_config_delete.setStyleSheet(
            "QPushButton { background-color: #cc3333; color: white; padding: 6px 12px; border-radius: 3px; }"
            "QPushButton:hover { background-color: #aa2020; }"
        )

        config_layout.addWidget(QLabel("配置:"))
        config_layout.addWidget(self.combo_config)
        config_layout.addWidget(self.btn_config_load)
        config_layout.addWidget(self.btn_config_save)
        config_layout.addWidget(self.btn_config_delete)
        config_layout.addStretch()
        config_group.setLayout(config_layout)

        # 添加到主布局
        main_layout.addWidget(ctrl_group)
        main_layout.addWidget(settings_group)
        main_layout.addWidget(window_group)
        main_layout.addWidget(config_group)
        main_layout.addWidget(table_group, 1)

    def _setup_menu(self):
        """构建菜单栏"""
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("文件(&F)")
        self.action_save = QAction("保存录制(&S)", self)
        self.action_save.setShortcut("Ctrl+S")
        self.action_load = QAction("加载录制(&L)", self)
        self.action_load.setShortcut("Ctrl+O")
        self.action_clear = QAction("清空重置(&N)", self)
        self.action_clear.setShortcut("Ctrl+N")
        self.action_exit = QAction("退出(&X)", self)
        self.action_exit.setShortcut("Alt+F4")
        file_menu.addAction(self.action_save)
        file_menu.addAction(self.action_load)
        file_menu.addSeparator()
        file_menu.addAction(self.action_clear)
        file_menu.addSeparator()
        file_menu.addAction(self.action_exit)

        help_menu = menu_bar.addMenu("帮助(&H)")
        self.action_about = QAction("关于(&A)", self)
        help_menu.addAction(self.action_about)

    def _setup_status_bar(self):
        """构建状态栏"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.lbl_status = QLabel("就绪")
        self.lbl_event_count = QLabel("事件数: 0")
        self.lbl_duration = QLabel("时长: 0.0s")
        self.lbl_progress = QLabel("")
        self.status_bar.addWidget(self.lbl_status)
        self.status_bar.addWidget(self.lbl_progress)
        self.status_bar.addPermanentWidget(self.lbl_event_count)
        self.status_bar.addPermanentWidget(self.lbl_duration)

    def _connect_signals(self):
        """连接信号槽"""
        self.btn_record.clicked.connect(self._on_record)
        self.btn_stop.clicked.connect(self._on_stop)
        self.btn_replay.clicked.connect(self._on_replay)
        self.btn_pause.clicked.connect(self._on_pause)
        self.btn_clear.clicked.connect(self._on_clear)

        self.btn_refresh_windows.clicked.connect(self._refresh_window_list)
        self.btn_add_window.clicked.connect(self._on_add_window)
        self.btn_remove_window.clicked.connect(self._on_remove_window)
        self.chk_no_window.toggled.connect(self._on_global_mode_toggled)
        self.btn_replay_selected.clicked.connect(self._on_replay_selected_window)
        self.btn_replay_all.clicked.connect(self._on_replay_all_windows)
        self.list_selected_windows.currentRowChanged.connect(self._on_selected_window_changed)

        self.btn_config_save.clicked.connect(self._on_save_config)
        self.btn_config_load.clicked.connect(self._on_load_config)
        self.btn_config_delete.clicked.connect(self._on_delete_config)

        self.slider_speed.valueChanged.connect(self._on_speed_changed)

        self.action_save.triggered.connect(self._on_save)
        self.action_load.triggered.connect(self._on_load)
        self.action_clear.triggered.connect(self._on_clear)
        self.action_exit.triggered.connect(self.close)
        self.action_about.triggered.connect(self._on_about)

        self.status_signal.connect(self._update_status)
        self.progress_signal.connect(self._update_progress)
        self.event_signal.connect(self._add_event_to_table)
        self.finished_signal.connect(self._on_replay_finished)

        self.recorder.on_status_changed = lambda s: self.status_signal.emit(s)
        self.recorder.on_event_recorded = lambda e: self.event_signal.emit(e)

        self.replayer.on_status_changed = lambda s: self.status_signal.emit(s)
        self.replayer.on_progress = lambda c, t: self.progress_signal.emit(c, t)
        self.replayer.on_finished = lambda: self.finished_signal.emit()

    # ========== 无限循环 ==========

    def _on_infinite_toggled(self, checked):
        """无限循环切换"""
        self.spin_repeat.setEnabled(not checked)

    # ========== 录制控制 ==========

    def _on_record(self):
        """开始录制"""
        target_title = None
        target_rect = None
        if not self.chk_no_window.isChecked() and self.selected_windows:
            first = self.selected_windows[0]
            target_title = first['title']
            target_rect = first['rect']

        # 设置录制模式
        mode = self.combo_record_mode.currentData()
        self.recorder.set_record_mode(mode)

        self.event_table.setRowCount(0)
        self.recorder.start_recording(target_title, target_rect)
        self._set_ui_recording_state()

    def _on_stop(self):
        """停止录制或回放"""
        if self.recorder.is_recording:
            session = self.recorder.stop_recording()
            if session:
                self.current_session = session
                self._update_session_info()
                self._set_ui_idle_state()
        if self.replayer.is_replaying:
            self.replayer.stop_replay()

    def _on_replay(self):
        """开始回放"""
        if not self.current_session or not self.current_session.events:
            QMessageBox.warning(self, "提示", "没有可回放的录制数据，请先录制或加载。")
            return

        speed = self.slider_speed.value() / 10.0
        self.replayer.set_speed(speed)

        # 确定回放模式
        if self.chk_no_window.isChecked() or not self.selected_windows:
            # 全局模式
            self.replayer.clear_target_window()
            hwnd_list = None
        else:
            # 窗口模式：传入已选窗口列表
            hwnd_list = [w['hwnd'] for w in self.selected_windows]
            self.replayer.set_target_windows(hwnd_list)
            if self.current_session.target_window_rect:
                self.replayer.set_session_window_rect(self.current_session.target_window_rect)

        self.recorder.set_replaying(True)

        # 确定重复次数
        if self.chk_infinite.isChecked():
            repeat = 0  # 0 表示无限
        else:
            repeat = self.spin_repeat.value()

        self.replayer.start_replay(self.current_session, repeat)
        self._set_ui_replay_state()

    def _on_pause(self):
        """暂停/继续回放"""
        self.replayer.pause_replay()
        if self.replayer.is_paused:
            self.btn_pause.setText("▶ 继续")
        else:
            self.btn_pause.setText("❚❚ 暂停")

    def _on_clear(self):
        """清空重置"""
        if self.recorder.is_recording:
            self.recorder.stop_recording()
        if self.replayer.is_replaying:
            self.replayer.stop_replay()
        self.current_session = None
        self.event_table.setRowCount(0)
        self.lbl_status.setText("就绪")
        self.lbl_event_count.setText("事件数: 0")
        self.lbl_duration.setText("时长: 0.0s")
        self.lbl_progress.setText("")
        self._set_ui_idle_state()

    # ========== 窗口选择（多窗口） ==========

    def _refresh_window_list(self):
        """刷新窗口下拉列表"""
        self.combo_window.clear()
        windows = self.window_mgr.enum_visible_windows()
        for w in windows:
            self.combo_window.addItem(f"{w.title}", {'hwnd': w.hwnd, 'title': w.title, 'rect': w.rect})

    def _on_add_window(self):
        """添加窗口到已选列表"""
        if self.chk_no_window.isChecked():
            return

        # 从下拉框获取选中的窗口
        data = self.combo_window.currentData()
        if not data:
            return

        # 检查是否已存在
        for w in self.selected_windows:
            if w['hwnd'] == data['hwnd']:
                return

        self.selected_windows.append(data)
        self._update_selected_windows_list()

    def _on_remove_window(self):
        """从已选列表移除选中的窗口"""
        row = self.list_selected_windows.currentRow()
        if row >= 0 and row < len(self.selected_windows):
            self.selected_windows.pop(row)
            self._update_selected_windows_list()

    def _update_selected_windows_list(self):
        """更新已选窗口列表显示"""
        self.list_selected_windows.clear()
        for w in self.selected_windows:
            self.list_selected_windows.addItem(f"{w['title']}  (hwnd={w['hwnd']})")

    def _on_global_mode_toggled(self, checked):
        """全局模式切换"""
        self.combo_window.setEnabled(not checked)
        self.btn_add_window.setEnabled(not checked)
        self.btn_remove_window.setEnabled(not checked)
        if checked:
            self.selected_windows.clear()
            self._update_selected_windows_list()
        self._update_window_action_buttons()

    def _on_selected_window_changed(self, row):
        """已选窗口列表选择变化"""
        self._update_window_action_buttons()

    def _update_window_action_buttons(self):
        """更新窗口操作按钮状态"""
        has_selected = self.list_selected_windows.currentRow() >= 0
        has_windows = len(self.selected_windows) > 0
        has_data = self.current_session is not None and len(self.current_session.events) > 0

        self.btn_replay_selected.setEnabled(has_selected and has_data and not self.replayer.is_replaying)
        self.btn_replay_all.setEnabled(has_windows and has_data and not self.replayer.is_replaying)

    def _on_replay_selected_window(self):
        """回放选中的单个窗口"""
        row = self.list_selected_windows.currentRow()
        if row < 0 or row >= len(self.selected_windows):
            return
        self._start_window_replay([self.selected_windows[row]])

    def _on_replay_all_windows(self):
        """轮流回放所有已选窗口"""
        if not self.selected_windows:
            return
        self._start_window_replay(self.selected_windows)

    def _start_window_replay(self, windows: list):
        """启动指定窗口的回放"""
        if not self.current_session or not self.current_session.events:
            QMessageBox.warning(self, "提示", "没有可回放的录制数据。")
            return

        speed = self.slider_speed.value() / 10.0
        self.replayer.set_speed(speed)

        hwnd_list = [w['hwnd'] for w in windows]
        self.replayer.set_target_windows(hwnd_list)
        if self.current_session.target_window_rect:
            self.replayer.set_session_window_rect(self.current_session.target_window_rect)

        self.recorder.set_replaying(True)

        if self.chk_infinite.isChecked():
            repeat = 0
        else:
            repeat = self.spin_repeat.value()

        self.replayer.start_replay(self.current_session, repeat)
        self._set_ui_replay_state()

    def _on_speed_changed(self, value):
        """速度滑块变化"""
        speed = value / 10.0
        self.lbl_speed.setText(f"{speed:.1f}x")
        self.replayer.set_speed(speed)

    # ========== 事件表格 ==========

    def _add_event_to_table(self, event: ActionEvent):
        """向表格添加事件（跨线程安全）"""
        row = self.event_table.rowCount()
        self.event_table.insertRow(row)

        # 时间
        time_item = QTableWidgetItem(f"{event.timestamp:.3f}s")
        time_item.setTextAlignment(Qt.AlignCenter)
        self.event_table.setItem(row, 0, time_item)

        # 类型
        type_name = EVENT_TYPE_NAMES.get(event.event_type, event.event_type.value)
        type_item = QTableWidgetItem(type_name)
        type_item.setTextAlignment(Qt.AlignCenter)
        self.event_table.setItem(row, 1, type_item)

        # 详情
        detail_item = QTableWidgetItem(event.get_detail_text())
        self.event_table.setItem(row, 2, detail_item)

        # 坐标
        pos_item = QTableWidgetItem(event.get_position_text())
        pos_item.setTextAlignment(Qt.AlignCenter)
        self.event_table.setItem(row, 3, pos_item)

        # 背景色 + 文字颜色
        bg_color = EVENT_COLORS.get(event.event_type, QColor(255, 255, 255))
        text_color = EVENT_TEXT_COLORS.get(event.event_type, QColor(0, 0, 0))
        font = QFont()
        font.setBold(event.event_type in (EventType.MOUSE_CLICK, EventType.KEY_PRESS))
        for col in range(4):
            item = self.event_table.item(row, col)
            item.setBackground(bg_color)
            item.setForeground(text_color)
            item.setFont(font)

        self.event_table.scrollToBottom()

        count = self.event_table.rowCount()
        self.lbl_event_count.setText(f"事件数: {count}")

    def _load_events_to_table(self, session: RecordingSession):
        """将整个会话的事件加载到表格"""
        self.event_table.setRowCount(0)
        for event in session.events:
            self._add_event_to_table(event)
        self._update_session_info()

    def _update_session_info(self):
        """更新会话信息显示"""
        if self.current_session:
            count = self.current_session.get_event_count()
            duration = self.current_session.duration
            self.lbl_event_count.setText(f"事件数: {count}")
            self.lbl_duration.setText(f"时长: {duration:.1f}s")

    # ========== 状态更新 ==========

    @Slot(str)
    def _update_status(self, text: str):
        self.lbl_status.setText(text)

    @Slot(int, int)
    def _update_progress(self, current: int, total: int):
        if self.chk_infinite.isChecked():
            self.lbl_progress.setText(f"进度: {current}/{total} (无限循环中...)")
        else:
            self.lbl_progress.setText(f"进度: {current}/{total}")

    @Slot()
    def _on_replay_finished(self):
        self.recorder.set_replaying(False)
        self.lbl_progress.setText("")
        self._set_ui_idle_state()

    # ========== UI 状态切换 ==========

    def _set_ui_recording_state(self):
        self.btn_record.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.btn_replay.setEnabled(False)
        self.btn_pause.setEnabled(False)
        self.btn_record.setText("● 录制中...")
        self.combo_record_mode.setEnabled(False)
        self.btn_replay_selected.setEnabled(False)
        self.btn_replay_all.setEnabled(False)

    def _set_ui_replay_state(self):
        self.btn_record.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.btn_replay.setEnabled(False)
        self.btn_pause.setEnabled(True)
        self.btn_pause.setText("❚❚ 暂停")
        self._update_window_action_buttons()

    def _set_ui_idle_state(self):
        self.btn_record.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.btn_replay.setEnabled(self.current_session is not None and len(self.current_session.events) > 0)
        self.btn_pause.setEnabled(False)
        self.btn_record.setText("● 录制")
        self.btn_pause.setText("❚❚ 暂停")
        self.combo_record_mode.setEnabled(True)
        self._update_window_action_buttons()

    # ========== 文件操作 ==========

    def _on_save(self):
        if not self.current_session or not self.current_session.events:
            QMessageBox.warning(self, "提示", "没有可保存的录制数据。")
            return
        filepath, _ = QFileDialog.getSaveFileName(
            self, "保存录制", "recordings/", "JSON 文件 (*.json)"
        )
        if filepath:
            try:
                self.current_session.save_to_file(filepath)
                self.status_signal.emit(f"已保存: {filepath}")
                QMessageBox.information(self, "成功", f"录制已保存到:\n{filepath}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败:\n{e}")

    def _on_load(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "加载录制", "recordings/", "JSON 文件 (*.json)"
        )
        if filepath:
            try:
                session = RecordingSession.load_from_file(filepath)
                self.current_session = session
                self._load_events_to_table(session)
                self._set_ui_idle_state()
                self.status_signal.emit(f"已加载: {session.name} ({session.get_event_count()} 个事件)")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"加载失败:\n{e}")

    def _on_about(self):
        QMessageBox.about(
            self, "关于",
            "<h3>鼠标键盘录制回放器</h3>"
            "<p>版本: 1.1.0</p>"
            "<p>功能: 录制鼠标键盘操作并按时间精确复现</p>"
            "<p>支持全局模式和多窗口指定模式</p>"
            "<br><p>快捷键:</p>"
            "<p>Ctrl+S - 保存录制</p>"
            "<p>Ctrl+O - 加载录制</p>"
            "<p>Ctrl+N - 清空重置</p>"
            "<p>Esc - 停止回放</p>"
        )

    # ========== 配置管理 ==========

    def _refresh_config_list(self):
        """刷新配置下拉列表"""
        self.combo_config.clear()
        configs = list_configs()
        for name in configs:
            self.combo_config.addItem(name)

    def _collect_settings(self) -> dict:
        """收集当前 UI 状态为配置字典"""
        settings = {
            "record_mode": self.combo_record_mode.currentData(),
            "speed": self.slider_speed.value() / 10.0,
            "repeat_count": self.spin_repeat.value(),
            "infinite_loop": self.chk_infinite.isChecked(),
            "global_mode": self.chk_no_window.isChecked(),
            "selected_windows": [
                {"hwnd": w["hwnd"], "title": w["title"], "rect": list(w["rect"])}
                for w in self.selected_windows
            ],
            "session_file": None
        }
        # 保存当前会话事件
        if self.current_session and self.current_session.events:
            from datetime import datetime
            session_name = f"config_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            session_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "recordings", f"{session_name}.json"
            )
            os.makedirs(os.path.dirname(session_path), exist_ok=True)
            self.current_session.save_to_file(session_path)
            settings["session_file"] = session_path
        return settings

    def _apply_settings(self, settings: dict):
        """将配置字典应用到 UI"""
        # 录制模式
        mode = settings.get("record_mode", "both")
        for i in range(self.combo_record_mode.count()):
            if self.combo_record_mode.itemData(i) == mode:
                self.combo_record_mode.setCurrentIndex(i)
                break

        # 速度
        speed = settings.get("speed", 1.0)
        self.slider_speed.setValue(int(speed * 10))

        # 重复次数
        repeat = settings.get("repeat_count", 1)
        self.spin_repeat.setValue(repeat)

        # 无限循环
        infinite = settings.get("infinite_loop", False)
        self.chk_infinite.setChecked(infinite)

        # 全局模式
        global_mode = settings.get("global_mode", True)
        self.chk_no_window.setChecked(global_mode)

        # 已选窗口
        self.selected_windows.clear()
        for w in settings.get("selected_windows", []):
            rect = w.get("rect")
            if isinstance(rect, list):
                rect = tuple(rect)
            self.selected_windows.append({
                "hwnd": w["hwnd"],
                "title": w["title"],
                "rect": rect
            })
        self._update_selected_windows_list()

        # 加载录制事件
        session_file = settings.get("session_file")
        if session_file and os.path.exists(session_file):
            try:
                session = RecordingSession.load_from_file(session_file)
                self.current_session = session
                self._load_events_to_table(session)
                self._set_ui_idle_state()
            except Exception:
                pass

    def _on_save_config(self):
        """保存当前配置"""
        name, ok = QInputDialog.getText(self, "保存配置", "请输入配置名称:")
        if not ok or not name.strip():
            return
        name = name.strip()
        settings = self._collect_settings()
        save_config(name, settings)
        self._refresh_config_list()
        # 选中刚保存的配置
        idx = self.combo_config.findText(name)
        if idx >= 0:
            self.combo_config.setCurrentIndex(idx)
        self.status_signal.emit(f"配置已保存: {name}")

    def _on_load_config(self):
        """加载选中的配置"""
        name = self.combo_config.currentText()
        if not name:
            QMessageBox.warning(self, "提示", "请先选择一个配置。")
            return
        settings = load_config(name)
        if not settings:
            QMessageBox.warning(self, "提示", f"配置 '{name}' 不存在。")
            return
        self._apply_settings(settings)
        self.status_signal.emit(f"配置已加载: {name}")

    def _on_delete_config(self):
        """删除选中的配置"""
        name = self.combo_config.currentText()
        if not name:
            return
        reply = QMessageBox.question(
            self, "确认删除", f"确定要删除配置 '{name}' 吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            delete_config(name)
            self._refresh_config_list()
            self.status_signal.emit(f"配置已删除: {name}")

    def closeEvent(self, event):
        if self.recorder.is_recording:
            self.recorder.stop_recording()
        if self.replayer.is_replaying:
            self.replayer.stop_replay()
        event.accept()
