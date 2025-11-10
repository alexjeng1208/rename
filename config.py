"""
配置和常數定義
"""

# 應用程式資訊
APP_TITLE = "檔案重新命名工具 v2.0"
APP_VERSION = "2.0.0"
WINDOW_SIZE = "1200x1000"

# 支援的檔案格式
SUPPORTED_EXTENSIONS = ['.mp4', '.jpg', '.jpeg', '.png']
SUPPORTED_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png']
SUPPORTED_VIDEO_EXTENSIONS = ['.mp4']

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

# 夢想命名規則的主題選項
THEME_OPTIONS = {
    "Hospital": ["H_Girlfriend", "H_Sister", "H_Cute", "H_Cool", "H_Motherly"],
    "BDSM": ["SM_Sister", "SM_Girlfriend"],
    "Bedroom": ["B_Cute_G", "B_Sister", "B_Cool_G", "B_M"],
    "Anime": ["A_編號"]
}

# Character 類型選項
CHARACTER_TYPES = ["Idle", "Intro", "Open"]

# 預設值
DEFAULT_CHAR_ID = "01"
DEFAULT_CHAR_TYPE = "Idle"
DEFAULT_CHAR_INDEX = "01"
DEFAULT_COLOR = "00"
DEFAULT_THEME = "Hospital"
DEFAULT_DREAM_INDEX = "01"
DEFAULT_ANIME_NUM = "01"
DEFAULT_MAX_FILES = 0

# 預覽設定
PREVIEW_IMAGE_SIZE = (300, 300)
PREVIEW_THUMBNAIL_SIZE = (200, 200)

# 設定檔案路徑
SETTINGS_FILE = "renamer_settings.json"
HISTORY_FILE = "rename_history.json"

# UI 設定
LISTBOX_HEIGHT = 10
TEXT_PREVIEW_HEIGHT = 8

# 深色模式顏色
DARK_THEME = {
    "bg": "#2b2b2b",
    "fg": "#ffffff",
    "select_bg": "#404040",
    "select_fg": "#ffffff",
    "button_bg": "#3c3c3c",
    "entry_bg": "#333333",
    "entry_fg": "#ffffff"
}

LIGHT_THEME = {
    "bg": "#ffffff",
    "fg": "#000000",
    "select_bg": "#0078d7",
    "select_fg": "#ffffff",
    "button_bg": "#f0f0f0",
    "entry_bg": "#ffffff",
    "entry_fg": "#000000"
}

# 鍵盤快捷鍵
SHORTCUTS = {
    "open_files": "<Control-o>",
    "open_folder": "<Control-Shift-o>",
    "clear": "<Control-l>",
    "delete": "<Delete>",
    "preview": "<Control-p>",
    "execute": "<Control-Return>",
    "move_up": "<Control-Up>",
    "move_down": "<Control-Down>",
    "undo": "<Control-z>",
    "search": "<Control-f>",
    "toggle_theme": "<Control-t>",
    "save_settings": "<Control-s>",
    "help": "<F1>"
}
