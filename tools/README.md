# Auto-Type 自动键盘输入工具

多窗口自动键盘输入工具，支持按键捕获、多窗口同时发送、定时任务。

## 功能特性

- 🎯 **按键捕获** - 直接按下键盘按键自动识别
- 📡 **多窗口支持** - 同时向多个窗口发送按键
- ⏰ **定时任务** - 设置时间自动执行
- 🎮 **手动控制** - 实时控制发送
- 🌑 **赛博朋克风格** - 暗黑霓虹界面

## 安装依赖

```bash
sudo apt install xdotool python3-pyqt5
```

## 使用方法

### GUI 界面
```bash
python3 tools/auto-type-gui.py
```

### 命令行
```bash
# 列出窗口
./tools/auto-type.sh list

# 向窗口输入
./tools/auto-type.sh type "窗口名" "内容"

# 发送按键
./tools/auto-type.sh key "Firefox" "ctrl+t"
```

## 快捷操作

1. 点击「🎯 捕获按键」→ 按下键盘按键
2. 点击「➕ 添加」加入队列
3. 选择目标窗口
4. 点击「▶ 开始执行」

## 定时任务

1. 切换到「⏰ 定时任务」标签
2. 设置任务名和触发时间
3. 点击「➕ 添加定时任务」
4. 任务会在指定时间自动执行

## 配置文件

定时任务保存在 `tools/scheduled_tasks.json`
