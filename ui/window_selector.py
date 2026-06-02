"""
窗口选择对话框
显示所有可见窗口列表，让用户选择目标窗口
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget,
    QPushButton, QLabel, QLineEdit, QGroupBox
)
from PySide6.QtCore import Qt

from core.window_manager import WindowManager, WindowInfo


class WindowSelectorDialog(QDialog):
    """窗口选择对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("选择目标窗口")
        self.setMinimumSize(550, 420)
        self.selected_window: WindowInfo = None

        self._setup_ui()
        self._refresh_list()

    def _setup_ui(self):
        """构建界面"""
        layout = QVBoxLayout(self)

        # 搜索栏
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("搜索:"))
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("输入窗口标题关键字过滤...")
        self.txt_search.textChanged.connect(self._filter_list)
        search_layout.addWidget(self.txt_search)
        layout.addLayout(search_layout)

        # 窗口列表
        self.list_widget = QListWidget()
        self.list_widget.setAlternatingRowColors(True)
        self.list_widget.doubleClicked.connect(self._on_double_click)
        layout.addWidget(self.list_widget)

        # 信息显示
        self.lbl_info = QLabel("双击或选中后点击确定")
        layout.addWidget(self.lbl_info)

        # 按钮行
        btn_layout = QHBoxLayout()
        self.btn_refresh = QPushButton("刷新列表")
        self.btn_ok = QPushButton("确定")
        self.btn_cancel = QPushButton("取消")

        self.btn_refresh.clicked.connect(self._refresh_list)
        self.btn_ok.clicked.connect(self._on_ok)
        self.btn_cancel.clicked.connect(self.reject)

        btn_layout.addWidget(self.btn_refresh)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_ok)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)

    def _refresh_list(self):
        """刷新窗口列表"""
        self.list_widget.clear()
        self._all_windows = WindowManager.enum_visible_windows()
        for w in self._all_windows:
            self.list_widget.addItem(f"{w.title}  [{w.class_name}]  hwnd={w.hwnd}")
        self.lbl_info.setText(f"共 {len(self._all_windows)} 个可见窗口")

    def _filter_list(self, text: str):
        """根据搜索文本过滤列表"""
        self.list_widget.clear()
        text_lower = text.lower()
        self._filtered_windows = []
        for w in self._all_windows:
            if text_lower in w.title.lower() or text_lower in w.class_name.lower():
                self.list_widget.addItem(f"{w.title}  [{w.class_name}]  hwnd={w.hwnd}")
                self._filtered_windows.append(w)
        self.lbl_info.setText(f"显示 {len(self._filtered_windows)} / {len(self._all_windows)} 个窗口")

    def _on_double_click(self, index):
        """双击选中"""
        self._on_ok()

    def _on_ok(self):
        """确定按钮"""
        row = self.list_widget.currentRow()
        if row < 0:
            return
        # 获取选中的窗口
        search_text = self.txt_search.text().strip()
        if search_text:
            windows = getattr(self, '_filtered_windows', self._all_windows)
        else:
            windows = self._all_windows
        if 0 <= row < len(windows):
            self.selected_window = windows[row]
            self.accept()
