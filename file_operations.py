"""
檔案操作邏輯處理
"""
import os
import json
from pathlib import Path
from typing import List, Tuple, Optional, Dict
from config import SUPPORTED_EXTENSIONS, HISTORY_FILE


class FileOperationManager:
    """檔案操作管理器"""

    def __init__(self):
        self.selected_files = []
        self.rename_history = []

    def add_files(self, files: List[str]) -> int:
        """
        添加檔案到列表

        Args:
            files: 檔案路徑列表

        Returns:
            成功添加的檔案數量
        """
        added_count = 0
        for file_path in files:
            if self._is_valid_file(file_path) and file_path not in self.selected_files:
                self.selected_files.append(file_path)
                added_count += 1
        return added_count

    def add_folder(self, folder_path: str) -> int:
        """
        從資料夾添加檔案

        Args:
            folder_path: 資料夾路徑

        Returns:
            成功添加的檔案數量
        """
        if not os.path.isdir(folder_path):
            return 0

        files_to_add = []
        for ext in SUPPORTED_EXTENSIONS:
            # 移除開頭的點，因為 glob 需要 *.ext 格式
            pattern = f"*{ext}"
            for file_path in Path(folder_path).glob(pattern):
                file_str = str(file_path)
                if file_str not in self.selected_files:
                    files_to_add.append(file_str)

        return self.add_files(files_to_add)

    def remove_files(self, indices: List[int]) -> int:
        """
        移除指定索引的檔案

        Args:
            indices: 要移除的檔案索引列表

        Returns:
            移除的檔案數量
        """
        # 從後往前刪除，避免索引變化
        for idx in sorted(indices, reverse=True):
            if 0 <= idx < len(self.selected_files):
                del self.selected_files[idx]
        return len(indices)

    def clear_files(self):
        """清空檔案列表"""
        self.selected_files.clear()

    def move_file(self, index: int, direction: int) -> bool:
        """
        移動檔案位置

        Args:
            index: 檔案索引
            direction: 移動方向（-1=上移，1=下移）

        Returns:
            是否成功移動
        """
        new_index = index + direction
        if 0 <= new_index < len(self.selected_files):
            self.selected_files[index], self.selected_files[new_index] = \
                self.selected_files[new_index], self.selected_files[index]
            return True
        return False

    def get_files(self) -> List[str]:
        """獲取所有檔案列表"""
        return self.selected_files.copy()

    def get_file_count(self) -> int:
        """獲取檔案數量"""
        return len(self.selected_files)

    def _is_valid_file(self, file_path: str) -> bool:
        """檢查檔案是否有效"""
        if not os.path.isfile(file_path):
            return False
        ext = os.path.splitext(file_path)[1].lower()
        return ext in SUPPORTED_EXTENSIONS

    def execute_rename(self, rename_list: List[Tuple[str, str]]) -> Tuple[int, int, List[str]]:
        """
        執行批次重新命名

        Args:
            rename_list: (舊路徑, 新路徑) 的列表

        Returns:
            (成功數量, 失敗數量, 錯誤訊息列表)
        """
        success_count = 0
        error_count = 0
        errors = []

        # 記錄到歷史（用於撤銷）
        batch_history = {
            "timestamp": self._get_timestamp(),
            "operations": []
        }

        for old_path, new_path in rename_list:
            try:
                # 檢查目標檔案是否存在且不是同一個檔案
                if os.path.exists(new_path) and new_path != old_path:
                    error_count += 1
                    errors.append(f"{os.path.basename(old_path)}: 目標檔案已存在")
                    continue

                os.rename(old_path, new_path)
                success_count += 1

                # 記錄操作
                batch_history["operations"].append({
                    "old_path": old_path,
                    "new_path": new_path
                })

            except Exception as e:
                error_count += 1
                errors.append(f"{os.path.basename(old_path)}: {str(e)}")

        # 保存歷史記錄
        if batch_history["operations"]:
            self.rename_history.append(batch_history)
            self._save_history()

        return success_count, error_count, errors

    def can_undo(self) -> bool:
        """檢查是否可以撤銷"""
        return len(self.rename_history) > 0

    def undo_last_rename(self) -> Tuple[bool, str]:
        """
        撤銷上次重新命名操作

        Returns:
            (是否成功, 訊息)
        """
        if not self.rename_history:
            return False, "沒有可撤銷的操作"

        last_batch = self.rename_history.pop()
        success_count = 0
        error_count = 0
        errors = []

        # 反向執行操作
        for operation in reversed(last_batch["operations"]):
            old_path = operation["old_path"]
            new_path = operation["new_path"]

            try:
                # 檢查新路徑是否存在
                if not os.path.exists(new_path):
                    error_count += 1
                    errors.append(f"{os.path.basename(new_path)}: 檔案不存在，可能已被移動或刪除")
                    continue

                # 檢查舊路徑是否已存在其他檔案
                if os.path.exists(old_path):
                    error_count += 1
                    errors.append(f"{os.path.basename(old_path)}: 原檔名已被其他檔案佔用")
                    continue

                os.rename(new_path, old_path)
                success_count += 1

            except Exception as e:
                error_count += 1
                errors.append(f"{os.path.basename(new_path)}: {str(e)}")

        self._save_history()

        if error_count > 0:
            error_msg = "\n".join(errors[:5])
            if len(errors) > 5:
                error_msg += f"\n...還有 {len(errors)-5} 個錯誤"
            return False, f"撤銷部分成功（成功：{success_count}，失敗：{error_count}）\n\n錯誤：\n{error_msg}"

        return True, f"成功撤銷 {success_count} 個檔案的重新命名"

    def get_history_count(self) -> int:
        """獲取歷史記錄數量"""
        return len(self.rename_history)

    def _get_timestamp(self) -> str:
        """獲取當前時間戳"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _save_history(self):
        """保存歷史記錄到檔案"""
        try:
            with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.rename_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存歷史記錄失敗: {str(e)}")

    def load_history(self):
        """從檔案載入歷史記錄"""
        try:
            if os.path.exists(HISTORY_FILE):
                with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                    self.rename_history = json.load(f)
        except Exception as e:
            print(f"載入歷史記錄失敗: {str(e)}")
            self.rename_history = []

    def check_conflicts(self, rename_list: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
        """
        檢查重新命名衝突

        Args:
            rename_list: (舊路徑, 新路徑) 的列表

        Returns:
            衝突的檔案列表
        """
        conflicts = []
        for old_path, new_path in rename_list:
            if os.path.exists(new_path) and new_path != old_path:
                conflicts.append((old_path, new_path))
        return conflicts
