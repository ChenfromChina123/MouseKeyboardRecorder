"""
配置管理模块
支持保存、加载、删除、重命名多个命名配置
配置文件存储在 configs/ 目录，每个配置一个 JSON 文件
"""

import json
import os
from datetime import datetime

# 配置文件目录（相对于项目根目录）
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_DIR = os.path.join(_BASE_DIR, "configs")


def _ensure_dir():
    """确保配置目录存在"""
    os.makedirs(CONFIG_DIR, exist_ok=True)


def _config_path(name: str) -> str:
    """获取配置文件路径"""
    safe_name = "".join(c for c in name if c.isalnum() or c in " _-")
    return os.path.join(CONFIG_DIR, f"{safe_name}.json")


def save_config(name: str, settings: dict):
    """
    保存配置到文件
    name: 配置名称
    settings: 配置数据字典
    """
    _ensure_dir()
    data = {
        "name": name,
        "created_at": datetime.now().isoformat(),
        **settings
    }
    path = _config_path(name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_config(name: str) -> dict:
    """
    加载指定名称的配置
    返回配置数据字典，不存在则返回 None
    """
    path = _config_path(name)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def list_configs() -> list:
    """
    列出所有已保存的配置名称
    返回名称列表
    """
    _ensure_dir()
    configs = []
    for fname in os.listdir(CONFIG_DIR):
        if fname.endswith(".json"):
            configs.append(fname[:-5])
    return sorted(configs)


def delete_config(name: str) -> bool:
    """
    删除指定配置
    返回是否成功
    """
    path = _config_path(name)
    if os.path.exists(path):
        os.remove(path)
        return True
    return False


def rename_config(old_name: str, new_name: str) -> bool:
    """
    重命名配置
    返回是否成功
    """
    old_path = _config_path(old_name)
    new_path = _config_path(new_name)
    if os.path.exists(old_path) and not os.path.exists(new_path):
        os.rename(old_path, new_path)
        return True
    return False
