"""
鼠标键盘录制回放器 - 主程序入口
功能：录制鼠标键盘操作，按时间精确复现，支持指定窗口回放
"""

import sys
import os

# 确保项目根目录在 Python 路径中
if getattr(sys, 'frozen', False):
    # PyInstaller 打包后的路径
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

from ui.main_window import MainWindow


def main():
    """程序主入口"""
    # 确保 UTF-8 编码
    if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass

    # 创建应用
    app = QApplication(sys.argv)

    # 设置应用风格（Fusion 在 Windows 上中文显示较好）
    app.setStyle("Fusion")

    # 设置应用信息
    app.setApplicationName("鼠标键盘录制回放器")
    app.setApplicationVersion("1.0.0")

    # 创建并显示主窗口
    window = MainWindow()
    window.show()

    # 注册 Esc 全局热键停止回放
    try:
        import keyboard
        keyboard.add_hotkey('esc', lambda: _esc_handler(window))
    except Exception:
        pass  # keyboard 模块可能需要管理员权限

    sys.exit(app.exec())


def _esc_handler(window: MainWindow):
    """Esc 热键处理：停止回放"""
    from PySide6.QtCore import QTimer
    # keyboard 回调在非主线程，需要通过 QTimer 在主线程执行
    QTimer.singleShot(0, lambda: window._on_stop())


if __name__ == '__main__':
    main()
