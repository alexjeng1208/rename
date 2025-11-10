"""
設定管理器
"""
import json
import os
from typing import Dict, Any, Optional
from config import SETTINGS_FILE


class SettingsManager:
    """設定管理器，用於保存和載入用戶設定"""

    def __init__(self):
        self.settings = self._get_default_settings()

    def _get_default_settings(self) -> Dict[str, Any]:
        """獲取預設設定"""
        return {
            "window": {
                "geometry": "1200x1000",
                "theme": "light"  # light or dark
            },
            "last_folder": "",
            "max_files": 0,
            "naming_rule": {
                "rule_type": "character",
                "char_params": {
                    "char_id": "01",
                    "char_type": "Idle",
                    "char_index": "01",
                    "color": "00"
                },
                "dream_params": {
                    "theme": "Hospital",
                    "role": "H_Girlfriend",
                    "index": "01",
                    "anime_num": "01"
                }
            },
            "ui_preferences": {
                "show_tooltips": True,
                "auto_preview": True,
                "confirm_before_rename": True
            }
        }

    def load_settings(self) -> bool:
        """
        從檔案載入設定

        Returns:
            是否成功載入
        """
        try:
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                    # 合併載入的設定和預設設定
                    self._merge_settings(loaded_settings)
                return True
            return False
        except Exception as e:
            print(f"載入設定失敗: {str(e)}")
            return False

    def save_settings(self) -> bool:
        """
        保存設定到檔案

        Returns:
            是否成功保存
        """
        try:
            with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存設定失敗: {str(e)}")
            return False

    def _merge_settings(self, loaded_settings: Dict[str, Any]):
        """合併載入的設定和預設設定"""
        def merge_dict(default: dict, loaded: dict):
            """遞迴合併字典"""
            for key, value in loaded.items():
                if key in default and isinstance(default[key], dict) and isinstance(value, dict):
                    merge_dict(default[key], value)
                else:
                    default[key] = value

        merge_dict(self.settings, loaded_settings)

    def get(self, key: str, default: Any = None) -> Any:
        """
        獲取設定值（支援點號分隔的路徑）

        Args:
            key: 設定鍵（例如 "window.geometry"）
            default: 預設值

        Returns:
            設定值
        """
        keys = key.split('.')
        value = self.settings
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any):
        """
        設置設定值（支援點號分隔的路徑）

        Args:
            key: 設定鍵（例如 "window.geometry"）
            value: 設定值
        """
        keys = key.split('.')
        target = self.settings
        for k in keys[:-1]:
            if k not in target:
                target[k] = {}
            target = target[k]
        target[keys[-1]] = value

    def get_all(self) -> Dict[str, Any]:
        """獲取所有設定"""
        return self.settings.copy()

    def reset_to_default(self):
        """重置為預設設定"""
        self.settings = self._get_default_settings()

    def update_window_geometry(self, geometry: str):
        """更新視窗大小和位置"""
        self.set("window.geometry", geometry)

    def update_last_folder(self, folder: str):
        """更新最後使用的資料夾"""
        self.set("last_folder", folder)

    def update_naming_rule(self, rule_params: Dict[str, Any]):
        """更新命名規則參數"""
        for key, value in rule_params.items():
            self.set(f"naming_rule.{key}", value)

    def get_naming_rule(self) -> Dict[str, Any]:
        """獲取命名規則設定"""
        return self.get("naming_rule", {})

    def toggle_theme(self) -> str:
        """
        切換主題

        Returns:
            新的主題名稱
        """
        current_theme = self.get("window.theme", "light")
        new_theme = "dark" if current_theme == "light" else "light"
        self.set("window.theme", new_theme)
        return new_theme
