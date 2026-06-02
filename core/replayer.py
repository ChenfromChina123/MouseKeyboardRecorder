"""
回放模块
按事件时间戳精确重放鼠标键盘操作，支持全局模式和窗口指定模式
"""

import ctypes
import threading
import time
from ctypes import wintypes
from typing import Callable

import pyautogui
import win32gui
import win32con
import win32api

from core.event_model import ActionEvent, EventType, RecordingSession
from core.window_manager import WindowManager

# 关闭 PyAutoGUI 的安全暂停，保留 FAILSAFE
pyautogui.PAUSE = 0
pyautogui.FAILSAFE = True

# ========== SendInput ctypes 定义 ==========

INPUT_MOUSE = 0
INPUT_KEYBOARD = 1

KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004
KEYEVENTF_EXTENDEDKEY = 0x0001

MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040
MOUSEEVENTF_WHEEL = 0x0800
MOUSEEVENTF_HWHEEL = 0x1000
MOUSEEVENTF_ABSOLUTE = 0x8000

WHEEL_DELTA = 120


class KEYBDINPUT(ctypes.Structure):
    """键盘输入结构体"""
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class MOUSEINPUT(ctypes.Structure):
    """鼠标输入结构体"""
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class _INPUT_UNION(ctypes.Union):
    _fields_ = [("ki", KEYBDINPUT), ("mi", MOUSEINPUT)]


class INPUT(ctypes.Structure):
    """通用输入结构体"""
    _fields_ = [
        ("type", wintypes.DWORD),
        ("union", _INPUT_UNION),
    ]


# Windows API 函数
SendInput = ctypes.windll.user32.SendInput
MapVirtualKey = ctypes.windll.user32.MapVirtualKeyW
GetSystemMetrics = ctypes.windll.user32.GetSystemMetrics


def _send_key_event(vk: int, is_press: bool, scan_code: int = None):
    """使用 SendInput 发送键盘事件"""
    if scan_code is None:
        scan_code = MapVirtualKey(vk, 0)  # MAPVK_VK_TO_VSC
    flags = 0 if is_press else KEYEVENTF_KEYUP
    # 扩展键标志
    if vk in (0x25, 0x26, 0x27, 0x28,  # 方向键
              0x2D, 0x2E,  # Insert, Delete
              0x21, 0x22,  # PageUp, PageDown
              0x23, 0x24,  # End, Home
              0x5B, 0x5C,  # 左右 Win
              0xA2, 0xA3,  # 左右 Ctrl
              0xA4, 0xA5,  # 左右 Alt
              0x2C,  # PrintScreen
              ):
        flags |= KEYEVENTF_EXTENDEDKEY
    inp = INPUT(type=INPUT_KEYBOARD)
    inp.union.ki = KEYBDINPUT(wVk=vk, wScan=scan_code, dwFlags=flags, time=0)
    SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))


def _send_unicode_char(char: str, is_press: bool):
    """使用 SendInput 的 Unicode 模式发送字符"""
    code = ord(char)
    flags = KEYEVENTF_UNICODE
    if not is_press:
        flags |= KEYEVENTF_KEYUP
    inp = INPUT(type=INPUT_KEYBOARD)
    inp.union.ki = KEYBDINPUT(wVk=0, wScan=code, dwFlags=flags, time=0)
    SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))


def _send_mouse_event(x: int, y: int, flags: int, data: int = 0):
    """使用 SendInput 发送鼠标事件"""
    # 转换为绝对坐标（0-65535 范围）
    screen_w = GetSystemMetrics(0)  # SM_CXSCREEN
    screen_h = GetSystemMetrics(1)  # SM_CYSCREEN
    abs_x = int(x * 65535 / screen_w)
    abs_y = int(y * 65535 / screen_h)
    inp = INPUT(type=INPUT_MOUSE)
    inp.union.mi = MOUSEINPUT(
        dx=abs_x, dy=abs_y,
        mouseData=data,
        dwFlags=flags | MOUSEEVENTF_ABSOLUTE,
        time=0
    )
    SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))


class Replayer:
    """操作回放器"""

    def __init__(self):
        self._is_replaying: bool = False
        self._replay_thread: threading.Thread = None
        self._stop_event: threading.Event = threading.Event()
        self._pause_event: threading.Event = threading.Event()
        self._pause_event.set()  # 初始不暂停
        self._speed: float = 1.0
        self._target_hwnd: int = None
        self._is_paused: bool = False

        # 回调
        self.on_status_changed: Callable[[str], None] = None
        self.on_progress: Callable[[int, int], None] = None
        self.on_finished: Callable[[], None] = None

    @property
    def is_replaying(self) -> bool:
        return self._is_replaying

    @property
    def is_paused(self) -> bool:
        return self._is_paused

    def set_speed(self, speed: float):
        """设置回放速度（0.1x ~ 10.0x）"""
        self._speed = max(0.1, min(10.0, speed))

    def set_target_window(self, hwnd: int):
        """指定目标窗口句柄"""
        self._target_hwnd = hwnd

    def clear_target_window(self):
        """清除目标窗口（使用全局模式）"""
        self._target_hwnd = None

    def start_replay(self, session: RecordingSession, repeat: int = 1):
        """开始回放"""
        if self._is_replaying:
            return
        if not session or not session.events:
            return

        self._stop_event.clear()
        self._pause_event.set()
        self._is_paused = False
        self._replay_thread = threading.Thread(
            target=self._replay_worker,
            args=(session, repeat),
            daemon=True
        )
        self._is_replaying = True
        self._replay_thread.start()

    def stop_replay(self):
        """停止回放"""
        self._stop_event.set()
        self._pause_event.set()  # 解除暂停以便线程退出

    def pause_replay(self):
        """暂停/继续回放"""
        if not self._is_replaying:
            return
        if self._is_paused:
            self._pause_event.set()
            self._is_paused = False
            if self.on_status_changed:
                self.on_status_changed("回放中...")
        else:
            self._pause_event.clear()
            self._is_paused = True
            if self.on_status_changed:
                self.on_status_changed("已暂停")

    def _replay_worker(self, session: RecordingSession, repeat: int):
        """回放工作线程"""
        try:
            if self.on_status_changed:
                self.on_status_changed("回放中...")

            events = session.events
            total = len(events)

            # 如果指定了窗口，先激活它
            if self._target_hwnd:
                WindowManager.activate_window(self._target_hwnd)
                time.sleep(0.3)  # 等待窗口激活

            for rep in range(repeat):
                if self._stop_event.is_set():
                    break

                replay_start = time.perf_counter()

                for i, event in enumerate(events):
                    if self._stop_event.is_set():
                        break

                    # 暂停等待
                    self._pause_event.wait()

                    # 等待到事件应该发生的时刻
                    target_time = event.timestamp / self._speed
                    elapsed = time.perf_counter() - replay_start
                    wait_time = target_time - elapsed

                    if wait_time > 0:
                        if wait_time > 0.005:
                            # 长等待：先 sleep 让出 CPU
                            time.sleep(wait_time - 0.002)
                        # 精确等待：spin-wait
                        while time.perf_counter() - replay_start < target_time:
                            if self._stop_event.is_set():
                                break
                            pass

                    if self._stop_event.is_set():
                        break

                    # 执行事件
                    self._execute_event(event)

                    if self.on_progress:
                        self.on_progress(i + 1, total)

        finally:
            self._is_replaying = False
            self._is_paused = False
            if self.on_status_changed:
                self.on_status_changed("回放完成")
            if self.on_finished:
                self.on_finished()

    def _execute_event(self, event: ActionEvent):
        """执行单个事件"""
        if event.event_type == EventType.MOUSE_MOVE:
            self._execute_mouse_move(event)
        elif event.event_type == EventType.MOUSE_CLICK:
            self._execute_mouse_click(event)
        elif event.event_type == EventType.MOUSE_SCROLL:
            self._execute_mouse_scroll(event)
        elif event.event_type == EventType.KEY_PRESS:
            self._execute_key(event, is_press=True)
        elif event.event_type == EventType.KEY_RELEASE:
            self._execute_key(event, is_press=False)

    def _execute_mouse_move(self, event: ActionEvent):
        """执行鼠标移动"""
        x, y = self._transform_coords(event.x, event.y)
        if self._target_hwnd:
            self._send_mouse_to_window(x, y, 'move')
        else:
            _send_mouse_event(x, y, MOUSEEVENTF_MOVE)

    def _execute_mouse_click(self, event: ActionEvent):
        """执行鼠标点击"""
        x, y = self._transform_coords(event.x, event.y)
        if self._target_hwnd:
            self._send_mouse_to_window(x, y, 'click', event.button, event.pressed)
        else:
            if event.button == 'left':
                flags = MOUSEEVENTF_LEFTDOWN if event.pressed else MOUSEEVENTF_LEFTUP
            elif event.button == 'right':
                flags = MOUSEEVENTF_RIGHTDOWN if event.pressed else MOUSEEVENTF_RIGHTUP
            elif event.button == 'middle':
                flags = MOUSEEVENTF_MIDDLEDOWN if event.pressed else MOUSEEVENTF_MIDDLEUP
            else:
                return
            _send_mouse_event(x, y, flags)

    def _execute_mouse_scroll(self, event: ActionEvent):
        """执行鼠标滚轮"""
        x, y = self._transform_coords(event.x, event.y)
        if self._target_hwnd:
            self._send_mouse_to_window(x, y, 'scroll', dx=event.dx, dy=event.dy)
        else:
            if event.dy:
                _send_mouse_event(x, y, MOUSEEVENTF_WHEEL, event.dy * WHEEL_DELTA)
            if event.dx:
                _send_mouse_event(x, y, MOUSEEVENTF_HWHEEL, event.dx * WHEEL_DELTA)

    def _execute_key(self, event: ActionEvent, is_press: bool):
        """执行键盘事件"""
        if self._target_hwnd:
            self._send_key_to_window(event, is_press)
        else:
            if event.vk is not None:
                _send_key_event(event.vk, is_press, event.scan_code)
            elif event.key:
                _send_unicode_char(event.key, is_press)

    def _transform_coords(self, x: int, y: int) -> tuple:
        """坐标变换：录制坐标 -> 回放坐标"""
        if self._target_hwnd and hasattr(self, '_session_window_rect') and self._session_window_rect:
            # 窗口指定模式：坐标偏移法
            rect = self._session_window_rect
            current_rect = WindowManager.get_window_rect(self._target_hwnd)
            if current_rect:
                dx = current_rect[0] - rect[0]
                dy = current_rect[1] - rect[1]
                return x + dx, y + dy
        return x, y

    def set_session_window_rect(self, rect: tuple):
        """设置录制时的窗口矩形，用于坐标偏移计算"""
        self._session_window_rect = rect

    def _send_mouse_to_window(self, x: int, y: int, action: str, button: str = None, pressed: bool = None, dx: int = None, dy: int = None):
        """向指定窗口发送鼠标事件"""
        try:
            client_x, client_y = win32gui.ScreenToClient(self._target_hwnd, (x, y))
            lparam = win32api.MAKELONG(client_x, client_y)

            if action == 'move':
                win32gui.PostMessage(self._target_hwnd, win32con.WM_MOUSEMOVE, 0, lparam)
            elif action == 'click':
                if button == 'left':
                    msg = win32con.WM_LBUTTONDOWN if pressed else win32con.WM_LBUTTONUP
                    wparam = win32con.MK_LBUTTON if pressed else 0
                elif button == 'right':
                    msg = win32con.WM_RBUTTONDOWN if pressed else win32con.WM_RBUTTONUP
                    wparam = win32con.MK_RBUTTON if pressed else 0
                elif button == 'middle':
                    msg = win32con.WM_MBUTTONDOWN if pressed else win32con.WM_MBUTTONUP
                    wparam = win32con.MK_MBUTTON if pressed else 0
                else:
                    return
                win32gui.PostMessage(self._target_hwnd, msg, wparam, lparam)
            elif action == 'scroll':
                if dy:
                    wparam = win32api.MAKELONG(0, dy * WHEEL_DELTA)
                    win32gui.PostMessage(self._target_hwnd, win32con.WM_MOUSEWHEEL, wparam, lparam)
                if dx:
                    wparam = win32api.MAKELONG(dx * WHEEL_DELTA, 0)
                    win32gui.PostMessage(self._target_hwnd, win32con.WM_MOUSEHWHEEL, wparam, lparam)
        except Exception:
            pass  # 窗口可能已关闭

    def _send_key_to_window(self, event: ActionEvent, is_press: bool):
        """向指定窗口发送键盘事件"""
        try:
            msg = win32con.WM_KEYDOWN if is_press else win32con.WM_KEYUP
            wparam = event.vk if event.vk else (ord(event.key) if event.key and len(event.key) == 1 else 0)
            if wparam == 0:
                return
            scan = event.scan_code if event.scan_code else MapVirtualKey(wparam, 0)
            lparam = (scan << 16) | 1
            if not is_press:
                lparam |= 0xC0000000
            win32gui.PostMessage(self._target_hwnd, msg, wparam, lparam)
        except Exception:
            pass
