"""
回放模块
按事件时间戳精确重放鼠标键盘操作，支持全局模式和多窗口指定模式
"""

import ctypes
import logging
import os
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

# 日志配置
_log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
os.makedirs(_log_dir, exist_ok=True)
_logger = logging.getLogger("replayer")
_logger.setLevel(logging.DEBUG)
_fh = logging.FileHandler(os.path.join(_log_dir, "replayer.log"), encoding="utf-8", mode="w")
_fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
_logger.addHandler(_fh)

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
        scan_code = MapVirtualKey(vk, 0)
    flags = 0 if is_press else KEYEVENTF_KEYUP
    if vk in (0x25, 0x26, 0x27, 0x28, 0x2D, 0x2E, 0x21, 0x22, 0x23, 0x24,
              0x5B, 0x5C, 0xA2, 0xA3, 0xA4, 0xA5, 0x2C):
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
    screen_w = GetSystemMetrics(0)
    screen_h = GetSystemMetrics(1)
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
        self._pause_event.set()
        self._speed: float = 1.0
        self._target_hwnds: list = []  # 目标窗口列表
        self._current_target_hwnd: int = None  # 当前回放的目标窗口
        self._is_paused: bool = False
        self._session_window_rect: tuple = None
        self._edit_hwnd_cache: dict = {}  # 缓存窗口对应的编辑控件句柄

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
        """设置回放速度"""
        self._speed = max(0.1, min(10.0, speed))

    def set_target_windows(self, hwnd_list: list):
        """设置目标窗口列表"""
        self._target_hwnds = list(hwnd_list)
        self._edit_hwnd_cache.clear()
        if hwnd_list:
            self._current_target_hwnd = hwnd_list[0]
        else:
            self._current_target_hwnd = None

    def set_target_window(self, hwnd: int):
        """设置单个目标窗口（兼容旧接口）"""
        self.set_target_windows([hwnd] if hwnd else [])

    def clear_target_window(self):
        """清除目标窗口（全局模式）"""
        self._target_hwnds = []
        self._current_target_hwnd = None

    def set_session_window_rect(self, rect: tuple):
        """设置录制时的窗口矩形"""
        self._session_window_rect = rect

    def start_replay(self, session: RecordingSession, repeat: int = 1):
        """开始回放。repeat=0 表示无限循环"""
        _logger.info(f"start_replay 被调用: 事件数={len(session.events) if session else 0}, repeat={repeat}")
        _logger.info(f"目标窗口列表: {self._target_hwnds}")
        _logger.info(f"当前目标窗口: {self._current_target_hwnd}")
        _logger.info(f"速度: {self._speed}")
        if self._is_replaying:
            _logger.warning("已在回放中，忽略")
            return
        if not session or not session.events:
            _logger.warning("无会话或无事件，忽略")
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
        _logger.info("启动回放线程")
        self._replay_thread.start()

    def stop_replay(self):
        """停止回放"""
        self._stop_event.set()
        self._pause_event.set()

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
        """回放工作线程。repeat=0 表示无限循环"""
        _logger.info(f"回放线程启动: 事件数={len(session.events)}, repeat={repeat}, 有窗口={bool(self._target_hwnds)}")
        try:
            if self.on_status_changed:
                self.on_status_changed("回放中...")

            events = session.events
            total = len(events)
            has_windows = bool(self._target_hwnds)

            rep = 0
            while True:
                if self._stop_event.is_set():
                    _logger.info("收到停止信号，退出循环")
                    break

                # 无限循环检查：repeat=0 表示无限
                if repeat > 0 and rep >= repeat:
                    _logger.info(f"重复次数已到: rep={rep}, repeat={repeat}")
                    break

                # 如果有多窗口，每个循环切换到下一个窗口
                if has_windows:
                    hwnd_idx = rep % len(self._target_hwnds)
                    self._current_target_hwnd = self._target_hwnds[hwnd_idx]
                    _logger.info(f"第{rep+1}轮 -> 窗口 hwnd={self._current_target_hwnd}")
                    WindowManager.activate_window(self._current_target_hwnd)
                    time.sleep(0.3)

                _logger.info(f"开始第{rep+1}轮回放, 目标hwnd={self._current_target_hwnd}")
                replay_start = time.perf_counter()

                for i, event in enumerate(events):
                    if self._stop_event.is_set():
                        break

                    self._pause_event.wait()

                    target_time = event.timestamp / self._speed
                    elapsed = time.perf_counter() - replay_start
                    wait_time = target_time - elapsed

                    if wait_time > 0:
                        if wait_time > 0.005:
                            time.sleep(wait_time - 0.002)
                        while time.perf_counter() - replay_start < target_time:
                            if self._stop_event.is_set():
                                break
                            pass

                    if self._stop_event.is_set():
                        break

                    self._execute_event(event)

                    if self.on_progress:
                        self.on_progress(i + 1, total)

                rep += 1

        finally:
            self._is_replaying = False
            self._is_paused = False
            if not self._stop_event.is_set():
                if self.on_status_changed:
                    self.on_status_changed("回放完成")
            else:
                if self.on_status_changed:
                    self.on_status_changed("已停止")
            if self.on_finished:
                self.on_finished()

    def _execute_event(self, event: ActionEvent):
        """执行单个事件"""
        if event.event_type == EventType.KEY_PRESS:
            _logger.debug(f"KEY_PRESS: key={event.key}, vk={event.vk}, hwnd={self._current_target_hwnd}")
        elif event.event_type == EventType.KEY_RELEASE:
            _logger.debug(f"KEY_RELEASE: key={event.key}, vk={event.vk}")

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
        x, y = self._transform_coords(event.x, event.y)
        if self._current_target_hwnd:
            self._send_mouse_to_window(self._current_target_hwnd, x, y, 'move')
        else:
            _send_mouse_event(x, y, MOUSEEVENTF_MOVE)

    def _execute_mouse_click(self, event: ActionEvent):
        x, y = self._transform_coords(event.x, event.y)
        if self._current_target_hwnd:
            self._send_mouse_to_window(self._current_target_hwnd, x, y, 'click', event.button, event.pressed)
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
        x, y = self._transform_coords(event.x, event.y)
        if self._current_target_hwnd:
            self._send_mouse_to_window(self._current_target_hwnd, x, y, 'scroll', dx=event.dx, dy=event.dy)
        else:
            if event.dy:
                _send_mouse_event(x, y, MOUSEEVENTF_WHEEL, event.dy * WHEEL_DELTA)
            if event.dx:
                _send_mouse_event(x, y, MOUSEEVENTF_HWHEEL, event.dx * WHEEL_DELTA)

    def _execute_key(self, event: ActionEvent, is_press: bool):
        if self._current_target_hwnd:
            _logger.debug(f"窗口模式: key={event.key}, vk={event.vk}, pressed={is_press}, target_hwnd={self._current_target_hwnd}")
            self._send_key_to_window(self._current_target_hwnd, event, is_press)
        else:
            _logger.debug(f"全局模式: key={event.key}, vk={event.vk}, pressed={is_press}")
            if event.vk is not None:
                _send_key_event(event.vk, is_press, event.scan_code)
            elif event.key:
                _send_unicode_char(event.key, is_press)

    def _transform_coords(self, x: int, y: int) -> tuple:
        """坐标变换"""
        hwnd = self._current_target_hwnd
        if hwnd and self._session_window_rect:
            current_rect = WindowManager.get_window_rect(hwnd)
            if current_rect:
                dx = current_rect[0] - self._session_window_rect[0]
                dy = current_rect[1] - self._session_window_rect[1]
                return x + dx, y + dy
        return x, y

    def _send_mouse_to_window(self, hwnd, x, y, action, button=None, pressed=None, dx=None, dy=None):
        """向指定窗口发送鼠标事件"""
        try:
            client_x, client_y = win32gui.ScreenToClient(hwnd, (x, y))
            lparam = win32api.MAKELONG(client_x, client_y)

            if action == 'move':
                win32gui.PostMessage(hwnd, win32con.WM_MOUSEMOVE, 0, lparam)
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
                win32gui.PostMessage(hwnd, msg, wparam, lparam)
            elif action == 'scroll':
                if dy:
                    wparam = win32api.MAKELONG(0, dy * WHEEL_DELTA)
                    win32gui.PostMessage(hwnd, win32con.WM_MOUSEWHEEL, wparam, lparam)
                if dx:
                    wparam = win32api.MAKELONG(dx * WHEEL_DELTA, 0)
                    win32gui.PostMessage(hwnd, win32con.WM_MOUSEHWHEEL, wparam, lparam)
        except Exception:
            pass

    def _find_edit_control(self, hwnd) -> int:
        """查找窗口内的编辑控件（Edit/RichEdit/Scintilla 等）"""
        EDIT_CLASSES = {"Edit", "RichEdit", "RichEditD2DPT", "Scintilla",
                        "RICHEDIT", "NotepadTextBox"}
        result = [None]

        def enum_child(child_hwnd, _):
            try:
                cls = win32gui.GetClassName(child_hwnd)
                if cls in EDIT_CLASSES:
                    result[0] = child_hwnd
                    _logger.info(f"找到编辑控件: hwnd={child_hwnd}, class={cls}")
                    return False  # 停止枚举
            except Exception:
                pass
            return True

        try:
            win32gui.EnumChildWindows(hwnd, enum_child, None)
        except Exception:
            pass
        if not result[0]:
            _logger.warning(f"未找到编辑控件, 父窗口 hwnd={hwnd}")
        return result[0]

    def _get_target_hwnd(self, hwnd) -> int:
        """获取实际接收键盘消息的窗口句柄（优先使用子控件，带缓存）"""
        if hwnd in self._edit_hwnd_cache:
            cached = self._edit_hwnd_cache[hwnd]
            if win32gui.IsWindow(cached):
                return cached
            del self._edit_hwnd_cache[hwnd]
        edit = self._find_edit_control(hwnd)
        if edit:
            self._edit_hwnd_cache[hwnd] = edit
            return edit
        return hwnd

    def _send_key_to_window(self, hwnd, event, is_press):
        """向指定窗口发送键盘事件（WM_KEYDOWN + WM_CHAR）"""
        try:
            target = self._get_target_hwnd(hwnd)
            wparam = event.vk if event.vk else (ord(event.key) if event.key and len(event.key) == 1 else 0)
            if wparam == 0:
                _logger.warning(f"wparam=0, 跳过: key={event.key}, vk={event.vk}")
                return
            scan = event.scan_code if event.scan_code else MapVirtualKey(wparam, 0)
            lparam = (scan << 16) | 1

            if is_press:
                _logger.debug(f"  -> PostMessage WM_KEYDOWN to hwnd={target}, vk={wparam:#06x}, scan={scan:#06x}")
                win32gui.PostMessage(target, win32con.WM_KEYDOWN, wparam, lparam)
                # WM_CHAR（对可打印字符，让记事本等应用正确接收文字输入）
                if event.key and len(event.key) == 1 and event.key.isprintable():
                    char_code = ord(event.key)
                    _logger.debug(f"  -> PostMessage WM_CHAR to hwnd={target}, char='{event.key}' ({char_code:#06x})")
                    win32gui.PostMessage(target, win32con.WM_CHAR, char_code, lparam)
            else:
                lparam |= 0xC0000000
                _logger.debug(f"  -> PostMessage WM_KEYUP to hwnd={target}, vk={wparam:#06x}")
                win32gui.PostMessage(target, win32con.WM_KEYUP, wparam, lparam)
        except Exception as e:
            _logger.error(f"_send_key_to_window 异常: {e}", exc_info=True)
