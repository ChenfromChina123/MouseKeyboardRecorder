# MouseKeyboardRecorder

[English](README.md) | 中文

<p align="center">
  <img width="400" alt="MouseKeyboardRecorder" src="https://github.com/user-attachments/assets/9d3c8935-3bea-4b4a-9add-fb1884d28914" />
</p>

一款桌面自动化工具，支持录制鼠标键盘操作并按时间精确回放。基于 Python + PySide6 开发。

---

## 📋 目录

- [功能特性](#功能特性)
- [安装依赖](#安装依赖)
- [使用方式](#使用方式)
- [Auto-Type 自动键盘输入工具](#auto-type-自动键盘输入工具)
- [快捷键](#快捷键)
- [项目架构](#项目架构)
- [技术细节](#技术细节)
- [注意事项](#注意事项)

---

## 功能特性

- **完整事件捕获**：录制鼠标移动、点击、滚轮和全部键盘按键，时间戳精确到微秒
- **精确时间回放**：按录制时的时间间隔精确复现所有操作，采用混合等待策略（sleep + spin-wait，精度 <1ms）
- **指定窗口回放**：可选择一个或多个窗口作为回放目标，操作直接发送到焦点窗口
- **多窗口轮流回放**：添加多个窗口后，每个回放周期自动切换到下一个窗口
- **录制模式筛选**：支持仅鼠标、仅键盘、鼠标+键盘三种录制模式
- **速度调节**：支持 0.1x ~ 5.0x 回放速度
- **重复与循环**：支持设置重复次数（1 ~ 999,999 次）或无限循环
- **配置持久化**：支持保存和加载多个命名配置，包含所有设置、已选窗口和录制事件
- **保存/加载录制**：可将录制结果导出为 JSON 文件，随时加载回放
- **紧急停止**：按 Esc 键或鼠标移到屏幕左上角即可立即停止回放
- **彩色事件表格**：不同事件类型使用不同颜色高亮，便于区分

---

## 环境要求

### 原始项目（Windows）
- Windows 10/11
- Python 3.8+

### Auto-Type 工具（Linux/Kali）
- Linux 系统（推荐 Kali）
- Python 3.6+
- X11 图形环境

---

## 安装

### 原始项目（Windows）

```bash
# 克隆仓库
git clone https://github.com/ChenfromChina123/MouseKeyboardRecorder.git
cd MouseKeyboardRecorder

# 安装依赖
pip install -r requirements.txt
```

### Auto-Type 工具（Linux/Kali）

```bash
# 克隆仓库
git clone https://github.com/ChenfromChina123/MouseKeyboardRecorder.git
cd MouseKeyboardRecorder

# 安装系统依赖
sudo apt install xdotool python3-pyqt5
```

---

## 使用方式

### 原始项目

#### 直接运行

```bash
python main.py
```

#### 打包成可执行文件

```bash
build.bat
```

打包完成后，独立可执行文件生成在 `dist/MouseKeyboardRecorder.exe`。

#### 录制

1. （可选）选择录制模式：鼠标+键盘、仅鼠标、仅键盘
2. （可选）在"目标窗口"区域添加目标窗口
3. 点击"录制"按钮开始录制，执行需要录制的操作，点击"停止"结束
4. 所有事件会显示在事件预览表格中，包含时间戳

#### 回放

1. 按需调整回放速度和重复次数
2. 选择回放模式：
   - **全局模式**：在原始屏幕坐标位置回放
   - **窗口模式**：添加目标窗口后，点击"回放选中窗口"或"轮流回放全部"
3. 点击"回放"开始，点击"暂停"暂停/继续，按 Esc 停止

#### 配置管理

1. 调整所有设置（录制模式、速度、重复次数、窗口列表等）
2. 点击"保存配置"，输入名称，整个配置将被持久化保存
3. 从下拉列表选择已保存的配置，点击"加载配置"恢复所有设置
4. 配置文件以 JSON 格式存储在 `configs/` 目录

---

## Auto-Type 自动键盘输入工具

### 🎯 功能简介

Auto-Type 是一款轻量级多窗口自动键盘输入工具，专为 Linux/Kali 系统设计。

#### 核心功能

| 功能 | 说明 |
|------|------|
| 🎯 按键捕获 | 直接按下键盘按键，自动识别并填入键名 |
| 📡 多窗口支持 | 同时向多个窗口发送按键 |
| ⏰ 定时任务 | 设置时间自动执行任务 |
| 🎮 手动控制 | 实时控制发送 |
| 🌑 赛博朋克风格 | 暗黑霓虹界面 |

### 🚀 快速开始

#### 启动 GUI 界面

```bash
python3 tools/auto-type-gui.py
```

#### 命令行使用

```bash
# 列出所有可见窗口
./tools/auto-type.sh list

# 向指定窗口输入文本
./tools/auto-type.sh type "窗口名" "要输入的内容"

# 发送按键
./tools/auto-type.sh key "Firefox" "ctrl+t"

# 每隔 5 秒发送一次回车
./tools/auto-type.sh terminal 5 Return
```

### 📖 详细使用说明

#### 1. 启动程序

```bash
python3 tools/auto-type-gui.py
```

#### 2. 选择目标窗口

- 点击「🔄 刷新」加载所有可见窗口
- 从下拉菜单选择窗口
- 点击「➕ 添加」将窗口加入目标列表
- 可添加多个窗口同时操作

#### 3. 捕获按键

- 点击「🎯 捕获按键」打开捕获窗口
- 直接在键盘上按下想要的按键（回车、Tab、F5等）
- 支持组合键：先按住 Ctrl/Alt/Shift，再按其他键
- 500ms 自动确认，或点击 OK 确认
- 点击「➕ 添加」将按键加入队列

#### 4. 设置参数

- **间隔(秒)**：每次发送的间隔时间
- **次数(0=无限)**：执行次数，0 表示无限循环

#### 5. 开始执行

- 点击「▶ 开始执行」启动
- 点击「⏹ 停止」停止
- 日志区域显示实时状态

### ⏰ 定时任务

#### 添加定时任务

1. 切换到「⏰ 定时任务」标签
2. 输入任务名称
3. 设置触发时间（精确到秒）
4. 设置间隔和次数
5. 点击「➕ 添加定时任务」

#### 管理任务

| 操作 | 说明 |
|------|------|
| ⏯ 启用/禁用 | 切换任务状态 |
| 🗑 删除 | 删除任务 |
| ▶ 立即执行 | 立即执行选中的任务 |
| 🔄 刷新 | 刷新任务列表 |

#### 配置文件

定时任务保存在 `tools/scheduled_tasks.json`，可手动编辑或通过界面保存/加载。

### 🎨 界面预览

```
┌─────────────────────────────────────────────────────────────┐
│ ⌨ AUTO-TYPE CONSOLE                                    ● 就绪 │
├─────────────────────────────────────────────────────────────┤
│ [🎮 手动控制] [⏰ 定时任务]                                    │
├─────────────────────────────────────────────────────────────┤
│ 📡 目标窗口（支持多选）                                        │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ [下拉菜单选择窗口...]              [🔄 刷新] [➕ 添加]    │ │
│ └─────────────────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ [96468999] ✳ Scan APK file on server (640x480)          │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ ⌨ 按键设置                                                  │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ [捕获的按键显示...]        [🎯 捕获按键] [➕ 添加]        │ │
│ └─────────────────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Return                                                   │ │
│ │ Tab                                                      │ │
│ │ ctrl+c                                                   │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ ⚙ 执行参数                                                  │
│ 间隔(秒): [2] 次数(0=无限): [0]                              │
│                                                             │
│ [▶ 开始执行]                    [⏹ 停止]                     │
├─────────────────────────────────────────────────────────────┤
│ 📜 运行日志                                                  │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ [21:31:44] ✓ 已添加窗口: ✳ Scan APK file on server       │ │
│ │ [21:31:46] 🎯 捕获: Return                               │ │
│ │ [21:31:48] ✓ 已添加: Return                              │ │
│ │ [21:31:50] ▶ 开始 -> 1 窗口 | Return | 2s                │ │
│ │ [21:31:52] ✓ → 96468999: Return                          │ │
│ └─────────────────────────────────────────────────────────┘ │
│ [🗑 清空]                                                    │
└─────────────────────────────────────────────────────────────┘
```

### 🔧 命令行工具详解

#### auto-type.sh

```bash
# 用法
./tools/auto-type.sh <窗口名> <间隔秒数> <内容> [次数]

# 示例
./tools/auto-type.sh terminal 10 Return        # 每10秒按回车
./tools/auto-type.sh Firefox 5 "hello" 20      # 每5秒输入hello，共20次
./tools/auto-type.sh "Scan APK" 2 Return       # 每2秒按回车
```

#### multi-window-typing.sh

```bash
# 列出窗口
./tools/multi-window-typing.sh list

# 向窗口输入
./tools/multi-window-typing.sh type "窗口名" "内容"

# 批量任务
./tools/multi-window-typing.sh batch tasks.txt
```

#### 批量任务配置文件格式

```bash
# tasks.txt
# 格式: 窗口名|内容|动作(type/key)|延迟(ms)
terminal|ls -la|type|50
Firefox|ctrl+t|key|
```

### 💡 使用技巧

#### 组合键示例

| 按键 | xdotool 格式 |
|------|--------------|
| 回车 | `Return` |
| Tab | `Tab` |
| 空格 | `space` |
| 退格 | `BackSpace` |
| 删除 | `Delete` |
| Esc | `Escape` |
| 方向键 | `Up` `Down` `Left` `Right` |
| F1-F12 | `F1` `F2` ... `F12` |
| Ctrl+C | `ctrl+c` |
| Ctrl+V | `ctrl+v` |
| Ctrl+Z | `ctrl+z` |
| Alt+Tab | `alt+Tab` |
| Ctrl+Alt+T | `ctrl+alt+t` |

#### 常见应用场景

1. **批量执行命令**
   - 添加终端窗口
   - 捕获 `Return` 键
   - 设置间隔 2 秒
   - 开始执行

2. **自动刷新页面**
   - 添加 Firefox 窗口
   - 捕获 `F5` 键
   - 设置间隔 30 秒
   - 开始执行

3. **多窗口轮换操作**
   - 添加多个窗口
   - 设置按键队列
   - 系统会按顺序循环发送

---

## 快捷键

| 快捷键 | 功能 |
|--------|------|
| Ctrl+S | 保存录制 |
| Ctrl+O | 加载录制 |
| Ctrl+N | 清空重置 |
| Esc    | 停止回放 |
| Alt+F4 | 退出程序 |

---

## 项目架构

```
MouseKeyboardRecorder/
├── main.py                    # 程序入口
├── core/
│   ├── event_model.py         # 事件数据结构（ActionEvent、RecordingSession）
│   ├── recorder.py            # 录制引擎（pynput 鼠标 Hook + GetAsyncKeyState 键盘轮询）
│   ├── replayer.py            # 回放引擎（SendInput + 混合等待策略）
│   ├── window_manager.py      # 窗口枚举、激活、坐标转换
│   └── config_manager.py      # 配置持久化管理
├── ui/
│   ├── main_window.py         # 主窗口（所有 UI 组件）
│   └── window_selector.py     # 窗口选择对话框
├── tools/                     # Auto-Type 工具（Linux/Kali）
│   ├── auto-type-gui.py       # GUI 界面（赛博朋克风格）
│   ├── auto-type.sh           # 命令行工具
│   ├── multi-window-typing.sh # 多窗口输入脚本
│   ├── scheduled_tasks.json   # 定时任务配置
│   └── README.md              # 工具说明
├── configs/                   # 已保存的配置文件
├── recordings/                # 已保存的录制文件
├── logs/                      # 运行日志
├── build.bat                  # PyInstaller 打包脚本
└── requirements.txt           # Python 依赖
```

---

## 技术细节

| 组件 | 实现方式 |
|------|---------|
| 鼠标捕获 | pynput `mouse.Listener` 全局 Hook |
| 键盘捕获 | `GetAsyncKeyState` 通过 QTimer 在主线程轮询 |
| 键盘模拟 | `SendInput` ctypes（VK 码 + Unicode 双模式） |
| 鼠标模拟 | 全局模式使用 `SendInput`；窗口模式使用 `PostMessage` |
| 回放计时 | `time.perf_counter()` + 混合 sleep/spin-wait（精度 <1ms） |
| 注入过滤 | pynput `injected` 参数过滤回放自身产生的事件 |
| 窗口定位 | `SetForegroundWindow` 激活窗口 + `SendInput` 发送到焦点窗口 |
| X11 自动化 | xdotool（Linux/Kali 系统） |

---

## 注意事项

- 以管理员权限运行的程序，本工具也需要以管理员身份运行才能录制
- 全屏 DirectX 应用和游戏可能不兼容
- 中文输入法的回放使用 Unicode 模式，兼容性较好
- 录制文件为纯 JSON 格式，可手动编辑
- Auto-Type 工具仅支持 Linux/Kali 系统（需要 X11）
- 定时任务精度为秒级

---

## 许可证

MIT License

---

## 贡献

欢迎提交 Issue 和 Pull Request！

---

## 作者

ChenfromChina123
