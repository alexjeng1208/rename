# -*- coding: utf-8 -*-
"""
配置檔案和常數定義
"""

import os
import json
from pathlib import Path

# 應用配置
APP_NAME = "檔案重新命名工具"
APP_VERSION = "2.0.0"
DEFAULT_WINDOW_SIZE = "1200x1000"

# 支援的檔案擴展名
SUPPORTED_EXTENSIONS = ['.mp4', '.jpg', '.jpeg', '.png']
VALID_EXTENSIONS_PATTERNS = ['*.mp4', '*.jpg', '*.jpeg', '*.png']

# 顏色映射
COLOR_MAP = {
    "00": ("沒穿", "nude"),
    "01": ("黑色", "black"),
    "02": ("白色", "white"),
    "03": ("綠色", "green"),
    "04": ("紅色", "red"),
    "05": ("黃色", "yellow"),
    "06": ("藍色", "blue")
}

# 角色類型
CHAR_TYPES = ["Idle", "Intro", "Open"]

# 主題選項
THEMES = {
    "Hospital": ["H_Girlfriend", "H_Sister", "H_Cute", "H_Cool", "H_Motherly"],
    "BDSM": ["SM_Sister", "SM_Girlfriend"],
    "Bedroom": ["B_Cute_G", "B_Sister", "B_Cool_G", "B_M"],
    "Anime": ["A_編號"]
}

# 配置檔案路徑
CONFIG_DIR = Path.home() / ".file_renamer"
CONFIG_FILE = CONFIG_DIR / "config.json"
HISTORY_FILE = CONFIG_DIR / "history.json"

# 預設配置
DEFAULT_CONFIG = {
    "last_folder": "",
    "last_rule": "character",
    "last_char_id": "01",
    "last_char_type": "Idle",
    "last_char_index": "01",
    "last_theme": "Hospital",
    "last_role": "",
    "last_dream_index": "01",
    "last_anime_num": "01",
    "last_color": "00",
    "max_files": "0",
    "dark_mode": False,
    "window_geometry": DEFAULT_WINDOW_SIZE,
    "remember_settings": True
}

class ConfigManager:
    """配置管理器"""
    
    def __init__(self):
        self.config = DEFAULT_CONFIG.copy()
        self.load_config()
    
    def load_config(self):
        """載入配置"""
        try:
            if CONFIG_FILE.exists():
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    self.config.update(loaded_config)
        except Exception as e:
            print(f"載入配置失敗: {e}")
    
    def save_config(self):
        """儲存配置"""
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"儲存配置失敗: {e}")
    
    def get(self, key, default=None):
        """獲取配置值"""
        return self.config.get(key, default)
    
    def set(self, key, value):
        """設定配置值"""
        self.config[key] = value
    
    def reset(self):
        """重置為預設配置"""
        self.config = DEFAULT_CONFIG.copy()
        self.save_config()

# 全域配置管理器實例
config_manager = ConfigManager()

