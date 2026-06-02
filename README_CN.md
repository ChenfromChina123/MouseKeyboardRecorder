# MouseKeyboardRecorder

[English](README.md) | 中文

<p align="center">
  <img width="800" alt="MouseKeyboardRecorder" src="https://github.com/user-attachments/assets/9d3c8935-3bea-4b4a-9add-fb1884d28914" />
</p>

一款 Windows 桌面自动化工具，支持录制鼠标键盘操作并按时间精确回放。基于 Python + PySide6 开发。

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

## 环境要求

- Windows 10/11
- Python 3.8+

## 安装

```bash
# 克隆仓库
git clone https://github.com/ChenfromChina123/MouseKeyboardRecorder.git
cd MouseKeyboardRecorder

# 安装依赖
pip install -r requirements.txt
```

## 使用方式

### 直接运行

```bash
python main.py
```

### 打包成可执行文件

```bash
build.bat
```

打包完成后，独立可执行文件生成在 `dist/MouseKeyboardRecorder.exe`。

## 操作指南

### 录制

1. （可选）选择录制模式：鼠标+键盘、仅鼠标、仅键盘
2. （可选）在"目标窗口"区域添加目标窗口
3. 点击"录制"按钮开始录制，执行需要录制的操作，点击"停止"结束
4. 所有事件会显示在事件预览表格中，包含时间戳

### 回放

1. 按需调整回放速度和重复次数
2. 选择回放模式：
   - **全局模式**：在原始屏幕坐标位置回放
   - **窗口模式**：添加目标窗口后，点击"回放选中窗口"或"轮流回放全部"
3. 点击"回放"开始，点击"暂停"暂停/继续，按 Esc 停止

### 配置管理

1. 调整所有设置（录制模式、速度、重复次数、窗口列表等）
2. 点击"保存配置"，输入名称，整个配置将被持久化保存
3. 从下拉列表选择已保存的配置，点击"加载配置"恢复所有设置
4. 配置文件以 JSON 格式存储在 `configs/` 目录

## 快捷键

| 快捷键 | 功能 |
|--------|------|
| Ctrl+S | 保存录制 |
| Ctrl+O | 加载录制 |
| Ctrl+N | 清空重置 |
| Esc    | 停止回放 |
| Alt+F4 | 退出程序 |

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
├── configs/                   # 已保存的配置文件
├── recordings/                # 已保存的录制文件
├── logs/                      # 运行日志
├── build.bat                  # PyInstaller 打包脚本
└── requirements.txt           # Python 依赖
```

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

## 注意事项

- 以管理员权限运行的程序，本工具也需要以管理员身份运行才能录制
- 全屏 DirectX 应用和游戏可能不兼容
- 中文输入法的回放使用 Unicode 模式，兼容性较好
- 录制文件为纯 JSON 格式，可手动编辑
