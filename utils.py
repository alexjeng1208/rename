# -*- coding: utf-8 -*-
"""
工具函數
"""

import os
import json
from pathlib import Path
from datetime import datetime
from config import HISTORY_FILE, CONFIG_DIR

class HistoryManager:
    """歷史記錄管理器"""
    
    def __init__(self):
        self.history = []
        self.load_history()
    
    def load_history(self):
        """載入歷史記錄"""
        try:
            if HISTORY_FILE.exists():
                with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
        except Exception as e:
            print(f"載入歷史記錄失敗: {e}")
            self.history = []
    
    def save_history(self):
        """儲存歷史記錄"""
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"儲存歷史記錄失敗: {e}")
    
    def add_record(self, old_path, new_path, timestamp=None):
        """新增歷史記錄"""
        if timestamp is None:
            timestamp = datetime.now().isoformat()
        
        record = {
            "timestamp": timestamp,
            "old_path": old_path,
            "new_path": new_path,
            "old_name": os.path.basename(old_path),
            "new_name": os.path.basename(new_path)
        }
        self.history.append(record)
        # 只保留最近1000筆記錄
        if len(self.history) > 1000:
            self.history = self.history[-1000:]
        self.save_history()
    
    def get_recent(self, limit=50):
        """獲取最近的歷史記錄"""
        return self.history[-limit:] if len(self.history) > limit else self.history
    
    def clear_history(self):
        """清空歷史記錄"""
        self.history = []
        self.save_history()

def format_file_size(size_bytes):
    """格式化檔案大小"""
    if size_bytes == 0:
        return "0 B"
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    return f"{size_bytes:.2f} {size_names[i]}"

def get_file_info(file_path):
    """獲取檔案資訊"""
    try:
        stat = os.stat(file_path)
        return {
            "size": stat.st_size,
            "size_formatted": format_file_size(stat.st_size),
            "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        return {
            "size": 0,
            "size_formatted": "0 B",
            "modified": "未知"
        }

