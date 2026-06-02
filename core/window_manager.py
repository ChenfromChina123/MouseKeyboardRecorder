"""
窗口管理模块
负责窗口枚举、查找、激活和坐标转换
"""

import ctypes
from dataclasses import dataclass
from typing import Optional

import win32gui
import win32con


@dataclass
class WindowInfo:
    """窗口信息"""
    hwnd: int  # 窗口句柄
    title: str  # 窗口标题
    class_name: str  # 窗口类名
    rect: tuple  # 窗口矩形 (left, top, right, bottom)
    is_visible: bool  # 是否可见

    def __str__(self):
        return f"{self.title} [{self.class_name}]"


class WindowManager:
    """窗口管理器：枚举、选择、坐标转换"""

    @staticmethod
    def enum_visible_windows() -> list:
        """
        枚举所有可见窗口
        返回 WindowInfo 列表
        """
        windows = []

        def callback(hwnd, _):
            if not win32gui.IsWindowVisible(hwnd):
                return True
            title = win32gui.GetWindowText(hwnd)
            if not title or not title.strip():
                return True
            try:
                class_name = win32gui.GetClassName(hwnd)
            except Exception:
                class_name = ""
            try:
                rect = win32gui.GetWindowRect(hwnd)
            except Exception:
                rect = (0, 0, 0, 0)
            windows.append(WindowInfo(
                hwnd=hwnd,
                title=title,
                class_name=class_name,
                rect=rect,
                is_visible=True
            ))
            return True

        win32gui.EnumWindows(callback, None)
        return windows

    @staticmethod
    def find_window(title: str) -> Optional[int]:
        """
        根据标题模糊查找窗口
        返回窗口句柄，未找到返回 None
        """
        windows = WindowManager.enum_visible_windows()
        title_lower = title.lower()
        for w in windows:
            if title_lower in w.title.lower():
                return w.hwnd
        return None

    @staticmethod
    def get_window_by_hwnd(hwnd: int) -> Optional[WindowInfo]:
        """根据句柄获取窗口信息"""
        if not win32gui.IsWindow(hwnd):
            return None
        try:
            title = win32gui.GetWindowText(hwnd)
            class_name = win32gui.GetClassName(hwnd)
            rect = win32gui.GetWindowRect(hwnd)
            return WindowInfo(
                hwnd=hwnd,
                title=title,
                class_name=class_name,
                rect=rect,
                is_visible=win32gui.IsWindowVisible(hwnd)
            )
        except Exception:
            return None

    @staticmethod
    def screen_to_client(hwnd: int, screen_x: int, screen_y: int) -> tuple:
        """屏幕坐标转窗口客户区坐标"""
        return win32gui.ScreenToClient(hwnd, (screen_x, screen_y))

    @staticmethod
    def client_to_screen(hwnd: int, client_x: int, client_y: int) -> tuple:
        """窗口客户区坐标转屏幕坐标"""
        return win32gui.ClientToScreen(hwnd, (client_x, client_y))

    @staticmethod
    def activate_window(hwnd: int) -> bool:
        """
        激活窗口（使其获得焦点）
        返回是否成功
        """
        try:
            if not win32gui.IsWindow(hwnd):
                return False
            # 如果窗口最小化，先恢复
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(hwnd)
            return True
        except Exception:
            # SetForegroundWindow 可能因前台锁定失败
            # 使用备用方案：AttachThreadInput
            try:
                foreground = win32gui.GetForegroundWindow()
                foreground_tid = ctypes.windll.user32.GetWindowThreadProcessId(foreground, None)
                current_tid = ctypes.windll.kernel32.GetCurrentThreadId()
                ctypes.windll.user32.AttachThreadInput(current_tid, foreground_tid, True)
                win32gui.SetForegroundWindow(hwnd)
                ctypes.windll.user32.AttachThreadInput(current_tid, foreground_tid, False)
                return True
            except Exception:
                return False

    @staticmethod
    def get_window_rect(hwnd: int) -> Optional[tuple]:
        """获取窗口矩形 (left, top, right, bottom)"""
        try:
            if win32gui.IsWindow(hwnd):
                return win32gui.GetWindowRect(hwnd)
        except Exception:
            pass
        return None
