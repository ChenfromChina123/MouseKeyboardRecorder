@echo off
chcp 65001 >nul
echo ========================================
echo   鼠标键盘录制回放器 - 打包脚本
echo ========================================
echo.

:: 检查 Python 环境
echo [1/4] 检查 Python 环境...
python --version
if errorlevel 1 (
    echo 错误: 未找到 Python，请确保已安装 Python 3.8+
    pause
    exit /b 1
)

:: 安装依赖
echo.
echo [2/4] 安装依赖...
pip install PySide6 pynput PyAutoGUI pywin32 keyboard pyinstaller -q

:: 清理旧构建
echo.
echo [3/4] 清理旧构建...
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build
if exist "*.spec" del /q "*.spec"

:: 打包
echo.
echo [4/4] 正在打包...
pyinstaller --onefile --windowed ^
    --name "MouseKeyboardRecorder" ^
    --add-data "recordings;recordings" ^
    --noconfirm ^
    --clean ^
    main.py

if errorlevel 1 (
    echo.
    echo 打包失败！请检查错误信息。
    pause
    exit /b 1
)

echo.
echo ========================================
echo   打包完成！
echo   可执行文件: dist\MouseKeyboardRecorder.exe
echo ========================================
echo.
echo 提示: 将 exe 复制到桌面即可双击运行
pause
