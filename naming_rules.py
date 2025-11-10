"""
命名規則邏輯處理
"""
import os
from typing import Dict, Any
from config import COLOR_MAP


class NamingRuleEngine:
    """命名規則引擎"""

    def __init__(self):
        self.rule_type = "character"
        self.char_params = {
            "char_id": "01",
            "char_type": "Idle",
            "char_index": "01",
            "color": "00"
        }
        self.dream_params = {
            "theme": "Hospital",
            "role": "H_Girlfriend",
            "index": "01",
            "anime_num": "01"
        }
        self.file_char_id_map = {}  # 儲存每個檔案的角色編號設定

    def set_rule_type(self, rule_type: str):
        """設置命名規則類型"""
        self.rule_type = rule_type

    def set_char_params(self, **kwargs):
        """設置 Character 規則參數"""
        self.char_params.update(kwargs)

    def set_dream_params(self, **kwargs):
        """設置夢想命名規則參數"""
        self.dream_params.update(kwargs)

    def set_file_char_id(self, file_path: str, char_id: str):
        """為特定檔案設定角色編號"""
        self.file_char_id_map[file_path] = char_id

    def get_file_char_id(self, file_path: str) -> str:
        """獲取檔案的角色編號"""
        return self.file_char_id_map.get(file_path, self.char_params["char_id"])

    def clear_file_char_id_map(self):
        """清空檔案角色編號映射"""
        self.file_char_id_map.clear()

    def generate_filename(self, original_path: str, index: int = 0) -> str:
        """
        根據規則生成新檔名

        Args:
            original_path: 原始檔案路徑
            index: 檔案索引（用於批次處理）

        Returns:
            新檔名（不含路徑）
        """
        _, ext = os.path.splitext(original_path)

        if self.rule_type == "character":
            return self._generate_character_filename(original_path, ext)
        else:
            return self._generate_dream_filename(ext)

    def _generate_character_filename(self, original_path: str, ext: str) -> str:
        """生成 Character 規則檔名"""
        # 如果該檔案有設定角色編號，使用設定的編號
        char_id = self.get_file_char_id(original_path).zfill(2)
        char_type = self.char_params["char_type"]

        if char_type == "Open":
            # Open 類型使用顏色索引
            char_index = self.char_params["color"]
        else:
            # Idle 和 Intro 使用輸入的索引
            char_index = self.char_params["char_index"].zfill(2)

        return f"Character_{char_id}_{char_type}_{char_index}{ext}"

    def _generate_dream_filename(self, ext: str) -> str:
        """生成夢想命名規則檔名"""
        theme = self.dream_params["theme"]
        index = self.dream_params["index"].zfill(2)

        if theme == "Anime":
            anime_num = self.dream_params["anime_num"].zfill(2)
            return f"A_{anime_num}{ext}"
        else:
            role = self.dream_params["role"]
            return f"{role}_{index}{ext}"

    def validate_params(self) -> tuple[bool, str]:
        """
        驗證參數是否有效

        Returns:
            (是否有效, 錯誤訊息)
        """
        if self.rule_type == "character":
            return self._validate_character_params()
        else:
            return self._validate_dream_params()

    def _validate_character_params(self) -> tuple[bool, str]:
        """驗證 Character 規則參數"""
        try:
            char_id = int(self.char_params["char_id"])
            if not (1 <= char_id <= 99):
                return False, "角色編號必須在 1-99 之間"

            if self.char_params["char_type"] not in ["Idle", "Intro", "Open"]:
                return False, "無效的類型選擇"

            if self.char_params["char_type"] != "Open":
                char_index = int(self.char_params["char_index"])
                if char_index > 20:
                    return True, f"警告：索引 {char_index} 超過 20，請確認是否正確"
            else:
                if self.char_params["color"] not in COLOR_MAP:
                    return False, "無效的顏色選擇"

            return True, ""
        except ValueError as e:
            return False, f"參數格式錯誤：{str(e)}"

    def _validate_dream_params(self) -> tuple[bool, str]:
        """驗證夢想命名規則參數"""
        try:
            if not self.dream_params["theme"]:
                return False, "請選擇主題"

            if not self.dream_params["role"]:
                return False, "請選擇角色類型"

            index = int(self.dream_params["index"])
            if not (1 <= index <= 99):
                return False, "索引必須在 1-99 之間"

            if self.dream_params["theme"] == "Anime":
                anime_num = int(self.dream_params["anime_num"])
                if not (1 <= anime_num <= 99):
                    return False, "動漫主題編號必須在 1-99 之間"

            return True, ""
        except ValueError as e:
            return False, f"參數格式錯誤：{str(e)}"

    def get_params_dict(self) -> Dict[str, Any]:
        """獲取當前參數字典（用於保存設定）"""
        return {
            "rule_type": self.rule_type,
            "char_params": self.char_params.copy(),
            "dream_params": self.dream_params.copy(),
            "file_char_id_map": self.file_char_id_map.copy()
        }

    def load_params_dict(self, params: Dict[str, Any]):
        """從字典加載參數（用於讀取設定）"""
        self.rule_type = params.get("rule_type", "character")
        self.char_params.update(params.get("char_params", {}))
        self.dream_params.update(params.get("dream_params", {}))
        self.file_char_id_map = params.get("file_char_id_map", {})
