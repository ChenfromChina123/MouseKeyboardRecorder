"""
主窗口模块
包含录制控制、回放设置、事件预览表格、状态栏等所有 UI 组件
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QSlider, QLabel, QTableWidget, QTableWidgetItem,
    QSpinBox, QStatusBar, QFileDialog, QMessageBox,
    QHeaderView, QGroupBox, QCheckBox, QComboBox, QAbstractItemView
)
from PySide6.QtCore import Qt, Signal, Slot, QTimer
from PySide6.QtGui import QAction, QColor, QFont

from core.event_model import ActionEvent, EventType, RecordingSession, EVENT_TYPE_NAMES
from core.recorder import Recorder
from core.replayer import Replayer
from core.window_manager import WindowManager
from ui.window_selector import WindowSelectorDialog


# 事件类型对应的颜色
EVENT_COLORS = {
    EventType.MOUSE_MOVE: QColor(220, 240, 255),
    EventType.MOUSE_CLICK: QColor(255, 240, 220),
    EventType.MOUSE_SCROLL: QColor(240, 220, 255),
    EventType.KEY_PRESS: QColor(220, 255, 220),
    EventType.KEY_RELEASE: QColor(240, 240, 240),
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
        self.setMinimumSize(750, 580)
        self.resize(800, 650)

        # 核心模块
        self.recorder = Recorder()
        self.replayer = Replayer()
        self.window_mgr = WindowManager()

        # 当前录制会话
        self.current_session: RecordingSession = None
        # 目标窗口信息
        self.target_hwnd: int = None
        self.target_window_title: str = ""

        self._setup_ui()
        self._setup_menu()
        self._setup_status_bar()
        self._connect_signals()
        self._refresh_window_list()

    def _setup_ui(self):
        """构建主界面"""
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(8)

        # === 录制控制区 ===
        ctrl_group = QGroupBox("录制控制")
        ctrl_layout = QHBoxLayout()

        self.btn_record = QPushButton("● 录制")
        self.btn_stop = QPushButton("■ 停止")
        self.btn_replay = QPushButton("▶ 回放")
        self.btn_pause = QPushButton("❚❚ 暂停")

        self.btn_record.setStyleSheet("QPushButton { background-color: #ff4444; color: white; font-weight: bold; padding: 8px 16px; }")
        self.btn_stop.setStyleSheet("QPushButton { background-color: #888888; color: white; font-weight: bold; padding: 8px 16px; }")
        self.btn_replay.setStyleSheet("QPushButton { background-color: #44aa44; color: white; font-weight: bold; padding: 8px 16px; }")
        self.btn_pause.setStyleSheet("QPushButton { background-color: #4488cc; color: white; font-weight: bold; padding: 8px 16px; }")

        self.btn_stop.setEnabled(False)
        self.btn_replay.setEnabled(False)
        self.btn_pause.setEnabled(False)

        ctrl_layout.addWidget(self.btn_record)
        ctrl_layout.addWidget(self.btn_stop)
        ctrl_layout.addWidget(self.btn_replay)
        ctrl_layout.addWidget(self.btn_pause)
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
        self.spin_repeat.setRange(1, 9999)
        self.spin_repeat.setMinimumWidth(60)
        settings_layout.addWidget(self.spin_repeat)
        settings_layout.addWidget(QLabel("次"))

        settings_group.setLayout(settings_layout)

        # === 目标窗口区 ===
        window_group = QGroupBox("目标窗口（可选，不指定则全局回放）")
        window_layout = QHBoxLayout()

        self.combo_window = QComboBox()
        self.combo_window.setMinimumWidth(300)
        self.btn_refresh_windows = QPushButton("刷新")
        self.btn_select_window = QPushButton("选择窗口...")
        self.chk_no_window = QCheckBox("全局模式")
        self.chk_no_window.setChecked(True)

        window_layout.addWidget(self.combo_window)
        window_layout.addWidget(self.btn_refresh_windows)
        window_layout.addWidget(self.btn_select_window)
        window_layout.addWidget(self.chk_no_window)
        window_group.setLayout(window_layout)

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
        self.event_table.setAlternatingRowColors(True)
        self.event_table.verticalHeader().setVisible(False)

        table_layout.addWidget(self.event_table)
        table_group.setLayout(table_layout)

        # 添加到主布局
        main_layout.addWidget(ctrl_group)
        main_layout.addWidget(settings_group)
        main_layout.addWidget(window_group)
        main_layout.addWidget(table_group, 1)

    def _setup_menu(self):
        """构建菜单栏"""
        menu_bar = self.menuBar()

        # 文件菜单
        file_menu = menu_bar.addMenu("文件(&F)")
        self.action_save = QAction("保存录制(&S)", self)
        self.action_save.setShortcut("Ctrl+S")
        self.action_load = QAction("加载录制(&L)", self)
        self.action_load.setShortcut("Ctrl+O")
        self.action_exit = QAction("退出(&X)", self)
        self.action_exit.setShortcut("Alt+F4")
        file_menu.addAction(self.action_save)
        file_menu.addAction(self.action_load)
        file_menu.addSeparator()
        file_menu.addAction(self.action_exit)

        # 帮助菜单
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
        # UI 按钮
        self.btn_record.clicked.connect(self._on_record)
        self.btn_stop.clicked.connect(self._on_stop)
        self.btn_replay.clicked.connect(self._on_replay)
        self.btn_pause.clicked.connect(self._on_pause)

        # 窗口选择
        self.btn_refresh_windows.clicked.connect(self._refresh_window_list)
        self.btn_select_window.clicked.connect(self._on_select_window)
        self.chk_no_window.toggled.connect(self._on_global_mode_toggled)

        # 速度滑块
        self.slider_speed.valueChanged.connect(self._on_speed_changed)

        # 菜单
        self.action_save.triggered.connect(self._on_save)
        self.action_load.triggered.connect(self._on_load)
        self.action_exit.triggered.connect(self.close)
        self.action_about.triggered.connect(self._on_about)

        # 跨线程信号
        self.status_signal.connect(self._update_status)
        self.progress_signal.connect(self._update_progress)
        self.event_signal.connect(self._add_event_to_table)
        self.finished_signal.connect(self._on_replay_finished)

        # 录制器回调
        self.recorder.on_status_changed = lambda s: self.status_signal.emit(s)
        self.recorder.on_event_recorded = lambda e: self.event_signal.emit(e)

        # 回放器回调
        self.replayer.on_status_changed = lambda s: self.status_signal.emit(s)
        self.replayer.on_progress = lambda c, t: self.progress_signal.emit(c, t)
        self.replayer.on_finished = lambda: self.finished_signal.emit()

    # ========== 录制控制 ==========

    def _on_record(self):
        """开始录制"""
        # 获取目标窗口信息
        target_title = None
        target_rect = None
        if not self.chk_no_window.isChecked() and self.target_hwnd:
            target_title = self.target_window_title
            target_rect = WindowManager.get_window_rect(self.target_hwnd)

        # 清空表格
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

        # 设置回放速度
        speed = self.slider_speed.value() / 10.0
        self.replayer.set_speed(speed)

        # 设置目标窗口
        if not self.chk_no_window.isChecked() and self.target_hwnd:
            self.replayer.set_target_window(self.target_hwnd)
            if self.current_session.target_window_rect:
                self.replayer.set_session_window_rect(self.current_session.target_window_rect)
        else:
            self.replayer.clear_target_window()

        # 通知录制器进入回放模式（过滤回放事件）
        self.recorder.set_replaying(True)

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

    # ========== 窗口选择 ==========

    def _refresh_window_list(self):
        """刷新窗口下拉列表"""
        self.combo_window.clear()
        self.combo_window.addItem("-- 不指定窗口（全局模式）--", None)
        windows = self.window_mgr.enum_visible_windows()
        for w in windows:
            self.combo_window.addItem(f"{w.title}", w.hwnd)

    def _on_select_window(self):
        """打开窗口选择对话框"""
        dialog = WindowSelectorDialog(self)
        if dialog.exec() == WindowSelectorDialog.Accepted and dialog.selected_window:
            w = dialog.selected_window
            self.target_hwnd = w.hwnd
            self.target_window_title = w.title
            self.chk_no_window.setChecked(False)
            self._update_window_display()

    def _on_global_mode_toggled(self, checked):
        """全局模式切换"""
        if checked:
            self.target_hwnd = None
            self.target_window_title = ""
            self.combo_window.setCurrentIndex(0)
        else:
            # 从下拉列表选择
            hwnd = self.combo_window.currentData()
            if hwnd:
                self.target_hwnd = hwnd
                self.target_window_title = self.combo_window.currentText()
            else:
                self.chk_no_window.setChecked(True)

    def _on_speed_changed(self, value):
        """速度滑块变化"""
        speed = value / 10.0
        self.lbl_speed.setText(f"{speed:.1f}x")
        self.replayer.set_speed(speed)

    def _update_window_display(self):
        """更新窗口选择显示"""
        for i in range(self.combo_window.count()):
            if self.combo_window.itemData(i) == self.target_hwnd:
                self.combo_window.setCurrentIndex(i)
                break

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

        # 背景色
        color = EVENT_COLORS.get(event.event_type, QColor(255, 255, 255))
        for col in range(4):
            self.event_table.item(row, col).setBackground(color)

        # 自动滚动到最新行
        self.event_table.scrollToBottom()

        # 更新事件计数
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
        """更新状态栏文本"""
        self.lbl_status.setText(text)

    @Slot(int, int)
    def _update_progress(self, current: int, total: int):
        """更新回放进度"""
        self.lbl_progress.setText(f"进度: {current}/{total}")

    @Slot()
    def _on_replay_finished(self):
        """回放完成"""
        self.recorder.set_replaying(False)
        self.lbl_progress.setText("")
        self._set_ui_idle_state()

    # ========== UI 状态切换 ==========

    def _set_ui_recording_state(self):
        """设置录制中的 UI 状态"""
        self.btn_record.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.btn_replay.setEnabled(False)
        self.btn_pause.setEnabled(False)
        self.btn_record.setText("● 录制中...")

    def _set_ui_replay_state(self):
        """设置回放中的 UI 状态"""
        self.btn_record.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.btn_replay.setEnabled(False)
        self.btn_pause.setEnabled(True)
        self.btn_pause.setText("❚❚ 暂停")

    def _set_ui_idle_state(self):
        """设置空闲状态"""
        self.btn_record.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.btn_replay.setEnabled(self.current_session is not None and len(self.current_session.events) > 0)
        self.btn_pause.setEnabled(False)
        self.btn_record.setText("● 录制")
        self.btn_pause.setText("❚❚ 暂停")

    # ========== 文件操作 ==========

    def _on_save(self):
        """保存录制"""
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
        """加载录制"""
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
        """关于对话框"""
        QMessageBox.about(
            self, "关于",
            "<h3>鼠标键盘录制回放器</h3>"
            "<p>版本: 1.0.0</p>"
            "<p>功能: 录制鼠标键盘操作并按时间精确复现</p>"
            "<p>支持全局模式和指定窗口模式</p>"
            "<br><p>快捷键:</p>"
            "<p>Ctrl+S - 保存录制</p>"
            "<p>Ctrl+O - 加载录制</p>"
            "<p>Esc - 停止回放</p>"
        )

    # ========== 窗口关闭 ==========

    def closeEvent(self, event):
        """窗口关闭事件"""
        if self.recorder.is_recording:
            self.recorder.stop_recording()
        if self.replayer.is_replaying:
            self.replayer.stop_replay()
        event.accept()
