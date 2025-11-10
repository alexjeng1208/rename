@echo off
chcp 65001 >nul
echo ========================================
echo 檔案重新命名工具 - 打包成EXE
echo ========================================
echo.

echo 正在檢查依賴套件...
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo 正在安裝 PyInstaller...
    pip install pyinstaller
)

pip show tkinterdnd2 >nul 2>&1
if errorlevel 1 (
    echo 正在安裝 tkinterdnd2...
    pip install tkinterdnd2
)

pip show Pillow >nul 2>&1
if errorlevel 1 (
    echo 正在安裝 Pillow...
    pip install Pillow
)

echo.
echo 正在打包成EXE（v2.0 優化版）...
echo.

REM 打包新版本（v2.0）
pyinstaller --name="檔案重新命名工具_v2" ^
    --onefile ^
    --windowed ^
    --icon=NONE ^
    --hidden-import=tkinterdnd2 ^
    --hidden-import=PIL ^
    --hidden-import=PIL.Image ^
    --hidden-import=PIL.ImageTk ^
    --hidden-import=config ^
    --hidden-import=naming_rules ^
    --hidden-import=file_operations ^
    --hidden-import=settings_manager ^
    --hidden-import=ui_helpers ^
    --collect-all tkinterdnd2 ^
    --collect-all PIL ^
    file_renamer_v2.py

if errorlevel 1 (
    echo.
    echo v2.0 打包失敗，嘗試打包原版本...
    echo.

    REM 備用：打包原版本（v1.0）
    pyinstaller --name="檔案重新命名工具" ^
        --onefile ^
        --windowed ^
        --icon=NONE ^
        --add-data "file_renamer.py;." ^
        --hidden-import=tkinterdnd2 ^
        --hidden-import=PIL ^
        --hidden-import=PIL.Image ^
        --hidden-import=PIL.ImageTk ^
        --collect-all tkinterdnd2 ^
        --collect-all PIL ^
        file_renamer.py
)

if errorlevel 1 (
    echo.
    echo 打包失敗！請檢查錯誤訊息。
    pause
    exit /b 1
)

echo.
echo ========================================
echo 打包完成！
echo.
echo v2.0 優化版：dist\檔案重新命名工具_v2.exe
echo v1.0 原版本：dist\檔案重新命名工具.exe （如果有）
echo.
echo 建議使用 v2.0 版本，功能更強大！
echo ========================================
echo.
pause

