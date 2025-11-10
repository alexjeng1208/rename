@echo off
chcp 65001 >nul
echo ========================================
echo 安裝依賴套件
echo ========================================
echo.

echo 正在安裝 tkinterdnd2（拖放功能）...
pip install tkinterdnd2

echo.
echo 正在安裝 Pillow（圖片預覽功能）...
pip install Pillow

echo.
echo ========================================
echo 安裝完成！
echo ========================================
echo.
pause

