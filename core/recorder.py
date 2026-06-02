"""
录制模块
鼠标使用 pynput Hook 监听，键盘使用 GetAsyncKeyState 在主线程 QTimer 轮询
"""

import ctypes
import threading
import time
from datetime import datetime

from pynput import mouse

from core.event_model import ActionEvent, EventType, RecordingSession

# Windows API
user32 = ctypes.windll.user32

# 虚拟键码到名称的映射（常用键）
VK_NAMES = {
    0x08: 'backspace', 0x09: 'tab', 0x0D: 'enter', 0x10: 'shift',
    0x11: 'ctrl', 0x12: 'alt', 0x13: 'pause', 0x14: 'caps_lock',
    0x1B: 'esc', 0x20: 'space', 0x21: 'page_up', 0x22: 'page_down',
    0x23: 'end', 0x24: 'home', 0x25: 'left', 0x26: 'up',
    0x27: 'right', 0x28: 'down', 0x2C: 'print_screen', 0x2D: 'insert',
    0x2E: 'delete', 0x5B: 'win_l', 0x5C: 'win_r', 0x5D: 'apps',
    0x60: 'num_0', 0x61: 'num_1', 0x62: 'num_2', 0x63: 'num_3',
    0x64: 'num_4', 0x65: 'num_5', 0x66: 'num_6', 0x67: 'num_7',
    0x68: 'num_8', 0x69: 'num_9', 0x6A: 'num_multiply',
    0x6B: 'num_add', 0x6C: 'num_separator', 0x6D: 'num_subtract',
    0x6E: 'num_decimal', 0x6F: 'num_divide',
    0x70: 'f1', 0x71: 'f2', 0x72: 'f3', 0x73: 'f4', 0x74: 'f5',
    0x75: 'f6', 0x76: 'f7', 0x77: 'f8', 0x78: 'f9', 0x79: 'f10',
    0x7A: 'f11', 0x7B: 'f12',
    0x90: 'num_lock', 0x91: 'scroll_lock',
    0xA0: 'shift_l', 0xA1: 'shift_r', 0xA2: 'ctrl_l', 0xA3: 'ctrl_r',
    0xA4: 'alt_l', 0xA5: 'alt_r',
}

# 需要轮询的键码范围
VK_SCAN_RANGES = list(range(0x08, 0x97))


# 录制模式
RECORD_MODE_BOTH = "both"
RECORD_MODE_MOUSE = "mouse_only"
RECORD_MODE_KEYBOARD = "keyboard_only"


class Recorder:
    """鼠标键盘录制器"""

    def __init__(self):
        self._session: RecordingSession = None
        self._start_time: float = 0.0
        self._mouse_listener: mouse.Listener = None
        self._is_recording: bool = False
        self._is_replaying: bool = False
        self._lock = threading.Lock()
        self._last_move_ts: float = 0.0
        self._key_states: dict = {}
        self._record_mode: str = RECORD_MODE_BOTH  # 默认同时录制鼠标和键盘

        # QTimer 引用（由外部设置）
        self._keyboard_timer = None

        # 回调
        self.on_status_changed = None
        self.on_event_recorded = None

    @property
    def is_recording(self) -> bool:
        return self._is_recording

    def set_replaying(self, replaying: bool):
        """设置回放状态标记"""
        self._is_replaying = replaying

    def set_keyboard_timer(self, timer):
        """设置 QTimer 用于主线程键盘轮询"""
        self._keyboard_timer = timer

    def set_record_mode(self, mode: str):
        """设置录制模式：RECORD_MODE_BOTH / RECORD_MODE_MOUSE / RECORD_MODE_KEYBOARD"""
        self._record_mode = mode

    def start_recording(self, target_window: str = None, target_window_rect: tuple = None):
        """开始录制"""
        if self._is_recording:
            return

        self._session = RecordingSession(
            name=f"录制_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            created_at=datetime.now().isoformat(),
            target_window=target_window,
            target_window_rect=target_window_rect
        )
        self._start_time = time.perf_counter()
        self._last_move_ts = 0.0
        self._key_states.clear()
        self._is_recording = True

        # 鼠标使用 pynput Hook
        self._mouse_listener = mouse.Listener(
            on_move=self._on_mouse_move,
            on_click=self._on_mouse_click,
            on_scroll=self._on_mouse_scroll
        )
        self._mouse_listener.start()

        # 键盘使用 QTimer 在主线程轮询
        if self._keyboard_timer:
            self._keyboard_timer.start(10)  # 10ms 间隔

        if self.on_status_changed:
            self.on_status_changed("录制中...")

    def stop_recording(self) -> RecordingSession:
        """停止录制"""
        if not self._is_recording:
            return None

        self._is_recording = False

        if self._mouse_listener:
            self._mouse_listener.stop()
            self._mouse_listener = None

        if self._keyboard_timer:
            self._keyboard_timer.stop()

        self._session.duration = time.perf_counter() - self._start_time

        if self.on_status_changed:
            self.on_status_changed("录制已停止")

        return self._session

    def get_current_session(self) -> RecordingSession:
        """获取当前录制会话"""
        return self._session

    def poll_keyboard(self):
        """键盘轮询（由 QTimer 在主线程调用）"""
        if not self._is_recording or self._is_replaying:
            return
        if self._record_mode == RECORD_MODE_MOUSE:
            return  # 仅鼠标模式下跳过键盘录制

        now = time.perf_counter() - self._start_time
        for vk in VK_SCAN_RANGES:
            state = user32.GetAsyncKeyState(vk)
            was_just_pressed = (state & 1) != 0
            is_held = (state & 0x8000) != 0
            was_pressed = self._key_states.get(vk, False)

            if was_just_pressed and not was_pressed:
                self._key_states[vk] = True
                key_name = VK_NAMES.get(vk, f'vk_{vk}')
                self._add_event(ActionEvent(
                    event_type=EventType.KEY_PRESS,
                    timestamp=now,
                    key=key_name, vk=vk, pressed=True
                ))
            elif not is_held and was_pressed:
                self._key_states[vk] = False
                key_name = VK_NAMES.get(vk, f'vk_{vk}')
                self._add_event(ActionEvent(
                    event_type=EventType.KEY_RELEASE,
                    timestamp=now,
                    key=key_name, vk=vk, pressed=False
                ))

    # ========== 鼠标回调 ==========

    def _on_mouse_move(self, x, y, injected=False):
        """鼠标移动回调（带节流）"""
        if injected or self._is_replaying:
            return
        if self._record_mode == RECORD_MODE_KEYBOARD:
            return  # 仅键盘模式下跳过鼠标录制
        now = time.perf_counter() - self._start_time
        if (now - self._last_move_ts) < 0.016:
            return
        self._last_move_ts = now
        self._add_event(ActionEvent(
            event_type=EventType.MOUSE_MOVE,
            timestamp=now, x=x, y=y
        ))

    def _on_mouse_click(self, x, y, button, pressed, injected=False):
        """鼠标点击回调"""
        if injected or self._is_replaying:
            return
        if self._record_mode == RECORD_MODE_KEYBOARD:
            return
        self._add_event(ActionEvent(
            event_type=EventType.MOUSE_CLICK,
            timestamp=time.perf_counter() - self._start_time,
            x=x, y=y,
            button=button.name,
            pressed=pressed
        ))

    def _on_mouse_scroll(self, x, y, dx, dy, injected=False):
        """鼠标滚轮回调"""
        if injected or self._is_replaying:
            return
        if self._record_mode == RECORD_MODE_KEYBOARD:
            return
        self._add_event(ActionEvent(
            event_type=EventType.MOUSE_SCROLL,
            timestamp=time.perf_counter() - self._start_time,
            x=x, y=y, dx=dx, dy=dy
        ))

    # ========== 事件管理 ==========

    def _add_event(self, event: ActionEvent):
        """线程安全地添加事件"""
        with self._lock:
            if self._session:
                self._session.events.append(event)
                if self.on_event_recorded:
                    self.on_event_recorded(event)
