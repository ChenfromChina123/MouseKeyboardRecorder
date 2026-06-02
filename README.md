# MouseKeyboardRecorder

English | [中文](README_CN.md)

<p align="center">
  <img width="800" alt="MouseKeyboardRecorder" src="https://github.com/user-attachments/assets/9d3c8935-3bea-4b4a-9add-fb1884d28914" />
</p>

A Windows desktop automation tool that records mouse and keyboard operations and replays them with microsecond precision. Built with Python + PySide6.

## Features

- **Full Event Capture**: Records mouse movement, clicks, scroll wheel, and all keyboard keys with precise timestamps
- **Precise Replay**: Replays all operations following the original timing intervals using a hybrid wait strategy (sleep + spin-wait)
- **Window-Targeted Replay**: Select one or multiple windows as replay targets; operations are sent directly to the focused window
- **Multi-Window Rotation**: Add multiple windows and replay across them in sequence, one per cycle
- **Recording Mode Filter**: Choose to record mouse only, keyboard only, or both simultaneously
- **Speed Control**: Adjustable replay speed from 0.1x to 5.0x
- **Repeat & Loop**: Set repeat count (1 to 999,999) or enable infinite looping
- **Configuration Profiles**: Save and load multiple named configurations, including all settings, selected windows, and recorded events
- **Save/Load Recordings**: Export recordings as JSON files for later use
- **Emergency Stop**: Press Esc or move the mouse to the top-left corner to stop replay immediately
- **Color-Coded Event Table**: Different event types are highlighted with distinct colors for easy identification

## Requirements

- Windows 10/11
- Python 3.8+

## Installation

```bash
# Clone the repository
git clone https://github.com/ChenfromChina123/MouseKeyboardRecorder.git
cd MouseKeyboardRecorder

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Run directly

```bash
python main.py
```

### Build executable

```bash
build.bat
```

The standalone executable will be generated at `dist/MouseKeyboardRecorder.exe`.

## How It Works

### Recording

1. (Optional) Select recording mode: Mouse + Keyboard, Mouse Only, or Keyboard Only
2. (Optional) Add target windows in the "Target Windows" section
3. Click "Record" to start, perform your operations, click "Stop" when done
4. All events appear in the event preview table with timestamps

### Replaying

1. Adjust replay speed and repeat count as needed
2. Choose replay mode:
   - **Global mode**: Replay at the original screen coordinates
   - **Window mode**: Add target windows, then click "Replay Selected Window" or "Replay All Windows"
3. Click "Replay" to start; press "Pause" to pause/resume; press "Esc" to stop

### Configuration Profiles

1. Adjust all settings (recording mode, speed, repeat, windows, etc.)
2. Click "Save Config", enter a name, and the entire configuration is persisted
3. Select a saved config from the dropdown and click "Load Config" to restore
4. Configurations are stored as JSON files in the `configs/` directory

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+S   | Save recording |
| Ctrl+O   | Load recording |
| Ctrl+N   | Clear and reset |
| Esc      | Stop replay |
| Alt+F4   | Exit |

## Architecture

```
MouseKeyboardRecorder/
├── main.py                    # Application entry point
├── core/
│   ├── event_model.py         # Event data structures (ActionEvent, RecordingSession)
│   ├── recorder.py            # Recording engine (pynput mouse hook + GetAsyncKeyState polling)
│   ├── replayer.py            # Replay engine (SendInput + mixed wait strategy)
│   ├── window_manager.py      # Window enumeration, activation, coordinate transforms
│   └── config_manager.py      # Configuration persistence
├── ui/
│   ├── main_window.py         # Main window with all UI components
│   └── window_selector.py     # Window selection dialog
├── configs/                   # Saved configuration profiles
├── recordings/                # Saved recording files
├── logs/                      # Runtime logs
├── build.bat                  # PyInstaller build script
└── requirements.txt           # Python dependencies
```

## Technical Details

| Component | Implementation |
|-----------|---------------|
| Mouse capture | pynput `mouse.Listener` global hook |
| Keyboard capture | `GetAsyncKeyState` polling via QTimer on main thread |
| Keyboard simulation | `SendInput` ctypes (VK code + Unicode dual mode) |
| Mouse simulation | `SendInput` for global mode; `PostMessage` for window-targeted mode |
| Replay timing | `time.perf_counter()` + hybrid sleep/spin-wait (<1ms accuracy) |
| Injection filtering | pynput `injected` parameter rejects replay-generated events |
| Window targeting | `SetForegroundWindow` activation + `SendInput` to focused window |

## Notes

- Programs running as administrator may require this tool to also run as administrator for recording to work
- Fullscreen DirectX applications and games may not be compatible
- Chinese IME input replay uses Unicode mode for better compatibility
- Recording files are plain JSON and can be manually edited
