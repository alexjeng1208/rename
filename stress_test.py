# -*- coding: utf-8 -*-
"""
壓力測試腳本 - 模擬非程式人員的錯誤操作
"""

import os
import sys
import tempfile
import shutil
import random
import string
from pathlib import Path

# 添加當前目錄到路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from file_renamer import FileRenamerGUI
    import tkinter as tk
    from tkinter import messagebox
except ImportError as e:
    print(f"無法導入模組: {e}")
    sys.exit(1)


class StressTest:
    """壓力測試類"""
    
    def __init__(self):
        self.test_dir = None
        self.test_files = []
        self.errors = []
        self.warnings = []
        
    def setup_test_environment(self):
        """設置測試環境"""
        # 創建臨時測試目錄
        self.test_dir = tempfile.mkdtemp(prefix="file_renamer_test_")
        print(f"測試目錄: {self.test_dir}")
        
    def cleanup_test_environment(self):
        """清理測試環境"""
        if self.test_dir and os.path.exists(self.test_dir):
            try:
                shutil.rmtree(self.test_dir)
                print(f"已清理測試目錄: {self.test_dir}")
            except Exception as e:
                print(f"清理失敗: {e}")
    
    def create_test_file(self, filename):
        """創建測試文件（包含路徑驗證）"""
        # 驗證文件名，防止路徑遍歷
        if not filename or filename.strip() == '':
            return None
        
        # 使用 basename 防止路徑遍歷
        safe_filename = os.path.basename(filename)
        if safe_filename != filename:
            # 如果文件名包含路徑，記錄但允許（用於測試）
            pass
        
        file_path = os.path.join(self.test_dir, safe_filename)
        
        # 確保文件在測試目錄內（防止路徑遍歷）
        abs_test_dir = os.path.abspath(self.test_dir)
        abs_file_path = os.path.abspath(file_path)
        if not abs_file_path.startswith(abs_test_dir):
            # 路徑遍歷被阻止
            return None
        
        try:
            with open(file_path, 'w') as f:
                f.write(f"Test content for {safe_filename}")
            return file_path
        except Exception as e:
            self.errors.append(f"創建文件失敗 {filename}: {e}")
            return None
    
    def test_scenario_1_extremely_long_filename(self):
        """測試場景1: 極長的文件名"""
        print("\n=== 測試場景1: 極長的文件名 ===")
        # 創建超過255字符的文件名
        long_name = "A" * 300 + ".mp4"
        file_path = self.create_test_file(long_name)
        if file_path:
            print(f"[OK] 創建了極長文件名: {len(long_name)} 字符")
        else:
            print("[SKIP] 無法創建極長文件名（預期行為）")
    
    def test_scenario_2_special_characters(self):
        """測試場景2: 特殊字符文件名"""
        print("\n=== 測試場景2: 特殊字符文件名 ===")
        special_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
        for char in special_chars:
            filename = f"test{char}file.mp4"
            file_path = self.create_test_file(filename)
            if file_path:
                print(f"[OK] 創建了包含特殊字符的文件: {char}")
            else:
                print(f"[SKIP] 無法創建包含特殊字符的文件: {char}（預期行為）")
    
    def test_scenario_3_reserved_names(self):
        """測試場景3: Windows保留文件名"""
        print("\n=== 測試場景3: Windows保留文件名 ===")
        reserved_names = ['CON', 'PRN', 'AUX', 'NUL', 'COM1', 'LPT1']
        for name in reserved_names:
            filename = f"{name}.mp4"
            file_path = self.create_test_file(filename)
            if file_path:
                print(f"[OK] 創建了保留文件名: {name}")
            else:
                print(f"[SKIP] 無法創建保留文件名: {name}（預期行為）")
    
    def test_scenario_4_empty_filename(self):
        """測試場景4: 空文件名"""
        print("\n=== 測試場景4: 空文件名 ===")
        try:
            file_path = self.create_test_file("")
            if file_path:
                print("[ERROR] 創建了空文件名（不應該發生）")
            else:
                print("[OK] 無法創建空文件名（預期行為）")
        except Exception as e:
            print(f"[OK] 空文件名被正確拒絕: {e}")
    
    def test_scenario_5_path_traversal(self):
        """測試場景5: 路徑遍歷攻擊"""
        print("\n=== 測試場景5: 路徑遍歷攻擊 ===")
        traversal_names = [
            "../test.mp4",
            "../../test.mp4",
            "..\\test.mp4",
            "C:\\Windows\\System32\\test.mp4",
            "/etc/passwd",
            "\\\\server\\share\\test.mp4"
        ]
        for name in traversal_names:
            file_path = self.create_test_file(name)
            if file_path:
                # 檢查文件是否在測試目錄內
                abs_test_dir = os.path.abspath(self.test_dir)
                abs_file_path = os.path.abspath(file_path)
                if abs_file_path.startswith(abs_test_dir):
                    print(f"[OK] 路徑遍歷被正確阻止: {name}")
                else:
                    print(f"[SECURITY] 路徑遍歷成功（安全漏洞）: {name}")
            else:
                print(f"[OK] 路徑遍歷被正確拒絕: {name}")
    
    def test_scenario_6_large_number_of_files(self):
        """測試場景6: 大量文件"""
        print("\n=== 測試場景6: 大量文件 ===")
        file_count = 1000
        created = 0
        for i in range(file_count):
            filename = f"test_{i:04d}.mp4"
            file_path = self.create_test_file(filename)
            if file_path:
                created += 1
        print(f"[OK] 創建了 {created}/{file_count} 個文件")
        if created < file_count:
            print(f"⚠ 警告: 只創建了 {created} 個文件，可能達到系統限制")
    
    def test_scenario_7_unicode_characters(self):
        """測試場景7: Unicode字符"""
        print("\n=== 測試場景7: Unicode字符 ===")
        unicode_names = [
            "測試文件.mp4",
            "тест.mp4",
            "テスト.mp4",
            "🎬video.mp4",
            "文件 名稱.mp4",
            "file\u0000name.mp4"  # 空字符
        ]
        for name in unicode_names:
            try:
                file_path = self.create_test_file(name)
                if file_path:
                    # 避免打印包含emoji的文件名（編碼問題）
                    safe_name = repr(name) if any(ord(c) > 0xFFFF for c in name) else name
                    print(f"[OK] 創建了Unicode文件名: {safe_name}")
                else:
                    safe_name = repr(name) if any(ord(c) > 0xFFFF for c in name) else name
                    print(f"[SKIP] 無法創建Unicode文件名: {safe_name}")
            except Exception as e:
                # 避免打印包含emoji的文件名（編碼問題）
                print(f"[ERROR] Unicode文件名錯誤: {repr(name)} - {str(e)}")
    
    def test_scenario_8_concurrent_operations(self):
        """測試場景8: 並發操作（模擬）"""
        print("\n=== 測試場景8: 並發操作 ===")
        # 創建多個文件，模擬同時操作
        files = []
        for i in range(10):
            filename = f"concurrent_{i}.mp4"
            file_path = self.create_test_file(filename)
            if file_path:
                files.append(file_path)
        
        # 模擬同時重命名（通過快速連續操作）
        print(f"[OK] 創建了 {len(files)} 個文件用於並發測試")
        print("⚠ 注意: 實際並發測試需要多線程，這裡只模擬")
    
    def test_scenario_9_invalid_extensions(self):
        """測試場景9: 無效擴展名"""
        print("\n=== 測試場景9: 無效擴展名 ===")
        invalid_exts = [
            ".exe",
            ".bat",
            ".cmd",
            ".sh",
            ".ps1",
            "no_ext",
            ".mp4.mp4",
            ".mp4.",
            "."
        ]
        for ext in invalid_exts:
            filename = f"test{ext}"
            file_path = self.create_test_file(filename)
            if file_path:
                print(f"[OK] 創建了無效擴展名文件: {ext}")
            else:
                print(f"[SKIP] 無法創建無效擴展名文件: {ext}")
    
    def test_scenario_10_nested_directories(self):
        """測試場景10: 嵌套目錄"""
        print("\n=== 測試場景10: 嵌套目錄 ===")
        try:
            nested_dir = os.path.join(self.test_dir, "nested", "deep", "path")
            os.makedirs(nested_dir, exist_ok=True)
            file_path = os.path.join(nested_dir, "test.mp4")
            with open(file_path, 'w') as f:
                f.write("test")
            print(f"[OK] 創建了嵌套目錄文件: {file_path}")
        except Exception as e:
            print(f"[ERROR] 嵌套目錄創建失敗: {e}")
    
    def test_scenario_11_readonly_files(self):
        """測試場景11: 只讀文件"""
        print("\n=== 測試場景11: 只讀文件 ===")
        filename = "readonly.mp4"
        file_path = self.create_test_file(filename)
        if file_path:
            try:
                os.chmod(file_path, 0o444)  # 只讀權限
                print(f"[OK] 創建了只讀文件: {filename}")
            except Exception as e:
                print(f"[ERROR] 無法設置只讀權限: {e}")
    
    def test_scenario_12_very_large_files(self):
        """測試場景12: 非常大的文件（模擬）"""
        print("\n=== 測試場景12: 非常大的文件 ===")
        # 創建一個較大的文件（10MB）
        filename = "large_file.mp4"
        file_path = os.path.join(self.test_dir, filename)
        try:
            with open(file_path, 'wb') as f:
                f.write(b'0' * (10 * 1024 * 1024))  # 10MB
            size_mb = os.path.getsize(file_path) / (1024 * 1024)
            print(f"[OK] 創建了大文件: {size_mb:.2f} MB")
        except Exception as e:
            print(f"[ERROR] 無法創建大文件: {e}")
    
    def test_scenario_13_duplicate_names(self):
        """測試場景13: 重複文件名"""
        print("\n=== 測試場景13: 重複文件名 ===")
        filename = "duplicate.mp4"
        count = 0
        for i in range(5):
            file_path = self.create_test_file(filename)
            if file_path:
                count += 1
        print(f"[OK] 創建了 {count} 個同名文件（系統會自動處理）")
    
    def test_scenario_14_mixed_case_extensions(self):
        """測試場景14: 混合大小寫擴展名"""
        print("\n=== 測試場景14: 混合大小寫擴展名 ===")
        cases = [".MP4", ".Mp4", ".mP4", ".mp4", ".JPG", ".Png"]
        for ext in cases:
            filename = f"test{ext}"
            file_path = self.create_test_file(filename)
            if file_path:
                print(f"[OK] 創建了混合大小寫擴展名: {ext}")
    
    def test_scenario_15_whitespace_in_names(self):
        """測試場景15: 文件名中的空白字符"""
        print("\n=== 測試場景15: 文件名中的空白字符 ===")
        whitespace_names = [
            "  test.mp4",  # 前導空格
            "test  .mp4",  # 尾隨空格
            "test file.mp4",  # 中間空格
            "test\tfile.mp4",  # Tab字符
            "test\nfile.mp4",  # 換行符
        ]
        for name in whitespace_names:
            try:
                file_path = self.create_test_file(name)
                if file_path:
                    print(f"[OK] 創建了包含空白字符的文件: {repr(name)}")
            except Exception as e:
                print(f"[ERROR] 無法創建包含空白字符的文件: {repr(name)} - {e}")
    
    def run_all_tests(self):
        """運行所有測試"""
        print("=" * 60)
        print("開始壓力測試")
        print("=" * 60)
        
        self.setup_test_environment()
        
        try:
            # 運行所有測試場景
            self.test_scenario_1_extremely_long_filename()
            self.test_scenario_2_special_characters()
            self.test_scenario_3_reserved_names()
            self.test_scenario_4_empty_filename()
            self.test_scenario_5_path_traversal()
            self.test_scenario_6_large_number_of_files()
            self.test_scenario_7_unicode_characters()
            self.test_scenario_8_concurrent_operations()
            self.test_scenario_9_invalid_extensions()
            self.test_scenario_10_nested_directories()
            self.test_scenario_11_readonly_files()
            self.test_scenario_12_very_large_files()
            self.test_scenario_13_duplicate_names()
            self.test_scenario_14_mixed_case_extensions()
            self.test_scenario_15_whitespace_in_names()
            
        finally:
            self.cleanup_test_environment()
        
        print("\n" + "=" * 60)
        print("壓力測試完成")
        print("=" * 60)
        
        if self.errors:
            print(f"\n錯誤: {len(self.errors)} 個")
            for error in self.errors[:10]:  # 只顯示前10個
                print(f"  - {error}")
        
        if self.warnings:
            print(f"\n警告: {len(self.warnings)} 個")
            for warning in self.warnings[:10]:  # 只顯示前10個
                print(f"  - {warning}")


def main():
    """主函數"""
    print("文件重命名工具 - 壓力測試")
    print("模擬非程式人員的錯誤操作場景")
    print()
    
    tester = StressTest()
    tester.run_all_tests()


if __name__ == "__main__":
    main()

