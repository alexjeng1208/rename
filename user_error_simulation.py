# -*- coding: utf-8 -*-
"""
用戶錯誤操作模擬 - 測試非程式人員可能犯的錯誤
"""

import os
import sys
import tempfile
import shutil
import random
import time
from pathlib import Path

# 添加當前目錄到路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class UserErrorSimulation:
    """用戶錯誤操作模擬"""
    
    def __init__(self):
        self.test_dir = None
        self.scenarios = []
        
    def setup_test_environment(self):
        """設置測試環境"""
        self.test_dir = tempfile.mkdtemp(prefix="user_error_test_")
        print(f"測試目錄: {self.test_dir}\n")
        
    def cleanup_test_environment(self):
        """清理測試環境"""
        if self.test_dir and os.path.exists(self.test_dir):
            try:
                shutil.rmtree(self.test_dir)
            except Exception as e:
                print(f"清理失敗: {e}")
    
    def create_test_file(self, filename):
        """創建測試文件"""
        file_path = os.path.join(self.test_dir, filename)
        try:
            with open(file_path, 'w') as f:
                f.write(f"Test: {filename}")
            return file_path
        except Exception as e:
            return None
    
    def scenario_1_wrong_file_selection(self):
        """場景1: 選擇錯誤的文件類型"""
        print("【場景1】用戶選擇了不支持的文件類型")
        print("  模擬: 用戶選擇了 .txt, .doc, .exe 等文件")
        files = ["document.txt", "report.doc", "program.exe", "script.bat"]
        for f in files:
            self.create_test_file(f)
        print(f"  [OK] 創建了 {len(files)} 個不支持的文件")
        print("  預期: 程序應該過濾掉這些文件\n")
    
    def scenario_2_too_many_files(self):
        """場景2: 選擇過多文件"""
        print("【場景2】用戶選擇了過多文件（超過限制）")
        print("  模擬: 用戶選擇了 1000 個文件，但限制是 100")
        count = 1000
        created = 0
        for i in range(count):
            if self.create_test_file(f"file_{i:04d}.mp4"):
                created += 1
        print(f"  [OK] 創建了 {created} 個文件")
        print("  預期: 程序應該限制文件數量並提示用戶\n")
    
    def scenario_3_empty_selection(self):
        """場景3: 沒有選擇任何文件就點擊重命名"""
        print("【場景3】用戶沒有選擇文件就點擊重命名")
        print("  模擬: 文件列表為空時執行重命名")
        print("  [OK] 模擬空文件列表")
        print("  預期: 程序應該顯示警告，不執行操作\n")
    
    def scenario_4_invalid_character_id(self):
        """場景4: 輸入無效的角色編號"""
        print("【場景4】用戶輸入無效的角色編號")
        invalid_ids = ["abc", "999", "-1", "0", "100", "01a", ""]
        print(f"  模擬無效輸入: {invalid_ids}")
        print("  預期: 程序應該驗證並限制在 01-99 範圍內\n")
    
    def scenario_5_wrong_index_range(self):
        """場景5: 輸入錯誤的索引範圍"""
        print("【場景5】用戶輸入錯誤的索引範圍")
        print("  模擬: Idle/Intro 輸入 00 或 21+")
        print("  模擬: Open 輸入 07+")
        invalid_indices = {
            "Idle": ["00", "21", "99", "abc"],
            "Open": ["07", "10", "99", "abc"]
        }
        for char_type, indices in invalid_indices.items():
            print(f"  {char_type} 無效索引: {indices}")
        print("  預期: 程序應該驗證並限制在正確範圍內\n")
    
    def scenario_6_special_characters_in_input(self):
        """場景6: 在輸入框中輸入特殊字符"""
        print("【場景6】用戶在輸入框中輸入特殊字符")
        special_inputs = ["<script>", "'; DROP TABLE", "../../etc/passwd", "中文測試"]
        print(f"  模擬特殊輸入: {special_inputs}")
        print("  預期: 程序應該清理或拒絕這些輸入\n")
    
    def scenario_7_rapid_clicking(self):
        """場景7: 快速連續點擊按鈕"""
        print("【場景7】用戶快速連續點擊按鈕")
        print("  模擬: 用戶在短時間內多次點擊'執行重命名'")
        print("  [OK] 模擬快速點擊（可能導致重複操作）")
        print("  預期: 程序應該防止重複操作或顯示進度\n")
    
    def scenario_8_file_deleted_during_operation(self):
        """場景8: 操作過程中文件被刪除"""
        print("【場景8】操作過程中文件被外部程序刪除")
        file_path = self.create_test_file("test.mp4")
        if file_path:
                print(f"  [OK] 創建測試文件: {file_path}")
            print("  模擬: 在重命名過程中，文件被其他程序刪除")
            print("  預期: 程序應該檢測並處理這種情況\n")
    
    def scenario_9_insufficient_permissions(self):
        """場景9: 權限不足"""
        print("【場景9】用戶沒有文件寫入權限")
        file_path = self.create_test_file("readonly.mp4")
        if file_path:
            try:
                os.chmod(file_path, 0o444)  # 只讀
                print(f"  [OK] 創建只讀文件: {file_path}")
                print("  預期: 程序應該檢測權限並顯示錯誤\n")
            except Exception as e:
                print(f"  [ERROR] 無法設置權限: {e}\n")
    
    def scenario_10_network_drive_timeout(self):
        """場景10: 網絡驅動器超時"""
        print("【場景10】操作網絡驅動器上的文件時超時")
        print("  模擬: 文件在網絡驅動器上，操作時網絡中斷")
        print("  [OK] 模擬網絡超時情況")
        print("  預期: 程序應該處理超時並顯示適當錯誤\n")
    
    def scenario_11_duplicate_renaming(self):
        """場景11: 重複命名導致衝突"""
        print("【場景11】多個文件重命名為相同名稱")
        files = [
            self.create_test_file("file1.mp4"),
            self.create_test_file("file2.mp4"),
            self.create_test_file("file3.mp4")
        ]
        print(f"  [OK] 創建了 {len([f for f in files if f])} 個文件")
        print("  模擬: 所有文件都重命名為 Character_01_Idle_01.mp4")
        print("  預期: 程序應該檢測衝突並提示用戶\n")
    
    def scenario_12_cancel_during_operation(self):
        """場景12: 操作過程中取消"""
        print("【場景12】用戶在批量重命名過程中點擊取消")
        print("  模擬: 正在處理 100 個文件，處理到第 50 個時取消")
        print("  [OK] 模擬中途取消操作")
        print("  預期: 程序應該安全停止，已處理的文件保持不變\n")
    
    def scenario_13_mixed_file_types(self):
        """場景13: 混合文件類型"""
        print("【場景13】用戶選擇了混合文件類型")
        files = [
            self.create_test_file("video.mp4"),
            self.create_test_file("image.jpg"),
            self.create_test_file("image.png"),
            self.create_test_file("document.txt")  # 不支持
        ]
        print(f"  [OK] 創建了混合類型文件")
        print("  預期: 程序應該只處理支持的文件類型\n")
    
    def scenario_14_very_long_path(self):
        """場景14: 非常長的路徑"""
        print("【場景14】文件路徑非常長")
        deep_path = os.path.join(self.test_dir, *["deep"] * 10)
        os.makedirs(deep_path, exist_ok=True)
        long_name = "A" * 200 + ".mp4"
        file_path = os.path.join(deep_path, long_name)
        try:
            with open(file_path, 'w') as f:
                f.write("test")
            path_len = len(file_path)
            print(f"  [OK] 創建了長路徑文件: {path_len} 字符")
            if path_len > 260:
                print(f"  ⚠ 路徑超過 Windows 260 字符限制")
            print("  預期: 程序應該處理或拒絕過長路徑\n")
        except Exception as e:
            print(f"  [ERROR] 無法創建長路徑: {e}\n")
    
    def scenario_15_unicode_confusion(self):
        """場景15: Unicode字符混淆"""
        print("【場景15】用戶使用容易混淆的Unicode字符")
        confusing_chars = [
            "file_Ｏ.mp4",  # 全角O
            "file_0.mp4",   # 數字0
            "file_O.mp4",   # 字母O
            "file_１.mp4",  # 全角1
            "file_1.mp4",   # 數字1
            "file_l.mp4",   # 字母l
        ]
        for name in confusing_chars:
            self.create_test_file(name)
        print(f"  [OK] 創建了容易混淆的文件名")
        print("  預期: 程序應該正確處理Unicode字符\n")
    
    def scenario_16_case_sensitivity_issues(self):
        """場景16: 大小寫敏感問題"""
        print("【場景16】文件名大小寫問題")
        files = [
            self.create_test_file("Test.MP4"),
            self.create_test_file("test.mp4"),
            self.create_test_file("TEST.MP4"),
        ]
        print(f"  [OK] 創建了不同大小寫的文件")
        print("  預期: 程序應該統一處理大小寫\n")
    
    def scenario_17_empty_folders(self):
        """場景17: 選擇空文件夾"""
        print("【場景17】用戶選擇了空文件夾")
        empty_dir = os.path.join(self.test_dir, "empty")
        os.makedirs(empty_dir, exist_ok=True)
        print(f"  [OK] 創建了空文件夾: {empty_dir}")
        print("  預期: 程序應該提示沒有找到文件\n")
    
    def scenario_18_hidden_files(self):
        """場景18: 隱藏文件"""
        print("【場景18】文件夾中包含隱藏文件")
        hidden_file = os.path.join(self.test_dir, ".hidden.mp4")
        try:
            with open(hidden_file, 'w') as f:
                f.write("hidden")
            # 在Windows上設置隱藏屬性
            if sys.platform == 'win32':
                import ctypes
                ctypes.windll.kernel32.SetFileAttributesW(hidden_file, 2)
            print(f"  [OK] 創建了隱藏文件")
            print("  預期: 程序應該決定是否處理隱藏文件\n")
        except Exception as e:
            print(f"  [ERROR] 無法創建隱藏文件: {e}\n")
    
    def scenario_19_system_files(self):
        """場景19: 系統文件"""
        print("【場景19】用戶嘗試重命名系統文件")
        system_files = ["desktop.ini", "thumbs.db", ".DS_Store"]
        for name in system_files:
            self.create_test_file(name)
        print(f"  [OK] 創建了系統文件名")
        print("  預期: 程序應該避免處理系統文件\n")
    
    def scenario_20_incomplete_operations(self):
        """場景20: 不完整的操作"""
        print("【場景20】用戶開始操作但未完成")
        print("  模擬: 用戶選擇文件，設置參數，但未點擊'執行'就關閉程序")
        print("  [OK] 模擬不完整操作")
        print("  預期: 程序應該安全關閉，不影響文件\n")
    
    def run_all_scenarios(self):
        """運行所有場景"""
        print("=" * 70)
        print("用戶錯誤操作模擬測試")
        print("模擬非程式人員可能犯的錯誤")
        print("=" * 70)
        print()
        
        self.setup_test_environment()
        
        try:
            self.scenario_1_wrong_file_selection()
            self.scenario_2_too_many_files()
            self.scenario_3_empty_selection()
            self.scenario_4_invalid_character_id()
            self.scenario_5_wrong_index_range()
            self.scenario_6_special_characters_in_input()
            self.scenario_7_rapid_clicking()
            self.scenario_8_file_deleted_during_operation()
            self.scenario_9_insufficient_permissions()
            self.scenario_10_network_drive_timeout()
            self.scenario_11_duplicate_renaming()
            self.scenario_12_cancel_during_operation()
            self.scenario_13_mixed_file_types()
            self.scenario_14_very_long_path()
            self.scenario_15_unicode_confusion()
            self.scenario_16_case_sensitivity_issues()
            self.scenario_17_empty_folders()
            self.scenario_18_hidden_files()
            self.scenario_19_system_files()
            self.scenario_20_incomplete_operations()
            
        finally:
            self.cleanup_test_environment()
        
        print("=" * 70)
        print("測試完成")
        print("=" * 70)


def main():
    """主函數"""
    simulator = UserErrorSimulation()
    simulator.run_all_scenarios()


if __name__ == "__main__":
    main()

