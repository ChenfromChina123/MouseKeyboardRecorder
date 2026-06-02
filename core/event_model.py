"""
事件数据结构模块
定义录制事件模型和会话模型，支持 JSON 序列化/反序列化
"""

import json
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional


class EventType(Enum):
    """事件类型枚举"""
    MOUSE_MOVE = "mouse_move"
    MOUSE_CLICK = "mouse_click"
    MOUSE_SCROLL = "mouse_scroll"
    KEY_PRESS = "key_press"
    KEY_RELEASE = "key_release"


# 事件类型中文映射
EVENT_TYPE_NAMES = {
    EventType.MOUSE_MOVE: "鼠标移动",
    EventType.MOUSE_CLICK: "鼠标点击",
    EventType.MOUSE_SCROLL: "鼠标滚轮",
    EventType.KEY_PRESS: "按键按下",
    EventType.KEY_RELEASE: "按键释放",
}


@dataclass
class ActionEvent:
    """单个操作事件"""
    event_type: EventType
    timestamp: float  # 相对于录制开始的时间偏移（秒）
    x: Optional[int] = None  # 鼠标 X 坐标（屏幕绝对坐标）
    y: Optional[int] = None  # 鼠标 Y 坐标
    button: Optional[str] = None  # 鼠标按键: "left", "right", "middle"
    pressed: Optional[bool] = None  # 按下(True)/释放(False)
    dx: Optional[int] = None  # 水平滚动量
    dy: Optional[int] = None  # 垂直滚动量
    key: Optional[str] = None  # 按键标识（字符或特殊键名称）
    vk: Optional[int] = None  # 虚拟键码（Windows VK code）
    scan_code: Optional[int] = None  # 扫描码

    def to_dict(self) -> dict:
        """转换为可序列化的字典"""
        d = asdict(self)
        d['event_type'] = self.event_type.value
        return d

    @classmethod
    def from_dict(cls, d: dict) -> 'ActionEvent':
        """从字典反序列化"""
        d = dict(d)
        d['event_type'] = EventType(d['event_type'])
        return cls(**d)

    def get_detail_text(self) -> str:
        """获取事件详情的中文描述"""
        if self.event_type == EventType.MOUSE_MOVE:
            return f"移动到 ({self.x}, {self.y})"
        elif self.event_type == EventType.MOUSE_CLICK:
            btn = {"left": "左键", "right": "右键", "middle": "中键"}.get(self.button, self.button)
            action = "按下" if self.pressed else "释放"
            return f"{btn}{action} ({self.x}, {self.y})"
        elif self.event_type == EventType.MOUSE_SCROLL:
            return f"滚动 dx={self.dx}, dy={self.dy} ({self.x}, {self.y})"
        elif self.event_type in (EventType.KEY_PRESS, EventType.KEY_RELEASE):
            action = "按下" if self.event_type == EventType.KEY_PRESS else "释放"
            key_name = self.key or f"VK_{self.vk}"
            return f"{action} [{key_name}]"
        return ""

    def get_position_text(self) -> str:
        """获取坐标文本"""
        if self.x is not None and self.y is not None:
            return f"({self.x}, {self.y})"
        return ""


@dataclass
class RecordingSession:
    """一次录制会话"""
    name: str = "未命名录制"
    created_at: str = ""
    duration: float = 0.0
    target_window: Optional[str] = None
    target_window_rect: Optional[tuple] = None
    events: list = field(default_factory=list)

    def save_to_file(self, filepath: str):
        """保存到 JSON 文件"""
        data = {
            'name': self.name,
            'created_at': self.created_at,
            'duration': self.duration,
            'target_window': self.target_window,
            'target_window_rect': list(self.target_window_rect) if self.target_window_rect else None,
            'events': [e.to_dict() for e in self.events]
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @classmethod
    def load_from_file(cls, filepath: str) -> 'RecordingSession':
        """从 JSON 文件加载"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        rect = data.get('target_window_rect')
        session = cls(
            name=data['name'],
            created_at=data['created_at'],
            duration=data['duration'],
            target_window=data.get('target_window'),
            target_window_rect=tuple(rect) if rect else None,
            events=[ActionEvent.from_dict(e) for e in data['events']]
        )
        return session

    def get_event_count(self) -> int:
        """获取事件总数"""
        return len(self.events)
