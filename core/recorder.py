"""
录制模块
使用 pynput 全局 Hook 监听鼠标键盘事件，记录精确时间戳
"""

import threading
import time
from datetime import datetime

from pynput import mouse, keyboard

from core.event_model import ActionEvent, EventType, RecordingSession


class Recorder:
    """鼠标键盘录制器"""

    def __init__(self):
        self._session: RecordingSession = None
        self._start_time: float = 0.0
        self._mouse_listener: mouse.Listener = None
        self._keyboard_listener: keyboard.Listener = None
        self._is_recording: bool = False
        self._is_replaying: bool = False  # 标记是否正在回放，用于过滤回放事件
        self._lock = threading.Lock()
        self._last_move_ts: float = 0.0  # 鼠标移动节流

        # 回调：通知 UI
        self.on_status_changed = None  # callable(str)
        self.on_event_recorded = None  # callable(ActionEvent)

    @property
    def is_recording(self) -> bool:
        return self._is_recording

    def set_replaying(self, replaying: bool):
        """设置回放状态标记，回放期间不录制"""
        self._is_replaying = replaying

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
        self._is_recording = True

        self._mouse_listener = mouse.Listener(
            on_move=self._on_mouse_move,
            on_click=self._on_mouse_click,
            on_scroll=self._on_mouse_scroll
        )
        self._keyboard_listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release
        )

        self._mouse_listener.start()
        self._keyboard_listener.start()

        if self.on_status_changed:
            self.on_status_changed("录制中...")

    def stop_recording(self) -> RecordingSession:
        """停止录制，返回录制会话"""
        if not self._is_recording:
            return None

        self._is_recording = False

        if self._mouse_listener:
            self._mouse_listener.stop()
            self._mouse_listener = None
        if self._keyboard_listener:
            self._keyboard_listener.stop()
            self._keyboard_listener = None

        self._session.duration = time.perf_counter() - self._start_time

        if self.on_status_changed:
            self.on_status_changed("录制已停止")

        return self._session

    def get_current_session(self) -> RecordingSession:
        """获取当前录制会话"""
        return self._session

    def _on_mouse_move(self, x, y, injected=False):
        """鼠标移动回调（带节流）"""
        if injected or self._is_replaying:
            return
        now = time.perf_counter() - self._start_time
        # 节流：至少间隔 16ms（约60fps）
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
        self._add_event(ActionEvent(
            event_type=EventType.MOUSE_CLICK,
            timestamp=time.perf_counter() - self._start_time,
            x=x, y=y,
            button=button.name,  # "left", "right", "middle"
            pressed=pressed
        ))

    def _on_mouse_scroll(self, x, y, dx, dy, injected=False):
        """鼠标滚轮回调"""
        if injected or self._is_replaying:
            return
        self._add_event(ActionEvent(
            event_type=EventType.MOUSE_SCROLL,
            timestamp=time.perf_counter() - self._start_time,
            x=x, y=y, dx=dx, dy=dy
        ))

    def _on_key_press(self, key, injected=False):
        """按键按下回调"""
        if injected or self._is_replaying:
            return
        event = self._key_to_event(key, True)
        if event:
            self._add_event(event)

    def _on_key_release(self, key, injected=False):
        """按键释放回调"""
        if injected or self._is_replaying:
            return
        event = self._key_to_event(key, False)
        if event:
            self._add_event(event)

    def _key_to_event(self, key, pressed: bool):
        """将 pynput key 对象转换为 ActionEvent"""
        timestamp = time.perf_counter() - self._start_time

        if hasattr(key, 'vk') and key.vk is not None:
            # 特殊键（ctrl, shift, alt, 功能键等）或普通字母键
            vk = key.vk
            key_name = key.name if hasattr(key, 'name') else str(key)
            return ActionEvent(
                event_type=EventType.KEY_PRESS if pressed else EventType.KEY_RELEASE,
                timestamp=timestamp,
                key=key_name, vk=vk, pressed=pressed
            )
        elif hasattr(key, 'char') and key.char is not None:
            # 普通字符键（可能无 vk）
            return ActionEvent(
                event_type=EventType.KEY_PRESS if pressed else EventType.KEY_RELEASE,
                timestamp=timestamp,
                key=key.char, vk=getattr(key, 'vk', None), pressed=pressed
            )
        return None

    def _add_event(self, event: ActionEvent):
        """线程安全地添加事件"""
        with self._lock:
            if self._session:
                self._session.events.append(event)
                if self.on_event_recorded:
                    self.on_event_recorded(event)
