@echo off
chcp 65001 >nul
echo ========================================
echo 文件重命名工具 - 壓力測試
echo ========================================
echo.

echo [1/2] 運行壓力測試...
python stress_test.py
echo.

echo [2/2] 運行用戶錯誤操作模擬...
python user_error_simulation.py
echo.

echo ========================================
echo 所有測試完成
echo ========================================
pause

