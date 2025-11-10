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
echo 正在打包成EXE...
echo.

pyinstaller --name="檔案重新命名工具" ^
    --onefile ^
    --windowed ^
    --icon=NONE ^
    --add-data "file_renamer.py;." ^
    --add-data "config.py;." ^
    --add-data "utils.py;." ^
    --add-data "ui_theme.py;." ^
    --add-data "security_utils.py;." ^
    --add-data "filename_validator.py;." ^
    --hidden-import=tkinterdnd2 ^
    --hidden-import=PIL ^
    --hidden-import=PIL.Image ^
    --hidden-import=PIL.ImageTk ^
    --hidden-import=config ^
    --hidden-import=utils ^
    --hidden-import=ui_theme ^
    --hidden-import=security_utils ^
    --hidden-import=filename_validator ^
    --collect-all tkinterdnd2 ^
    --collect-all PIL ^
    file_renamer.py

if errorlevel 1 (
    echo.
    echo 打包失敗！請檢查錯誤訊息。
    pause
    exit /b 1
)

echo.
echo ========================================
echo 打包完成！
echo EXE檔案位置：dist\檔案重新命名工具.exe
echo ========================================
echo.
pause

