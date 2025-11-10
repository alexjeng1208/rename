import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
from pathlib import Path
import sys
from threading import Thread
from datetime import datetime

# 檢測是否在打包後的EXE中運行
IN_EXE = getattr(sys, 'frozen', False)

# 匯入配置和工具模組
try:
    from config import (
        config_manager, COLOR_MAP, THEMES,
        SUPPORTED_EXTENSIONS,
        APP_NAME, DEFAULT_WINDOW_SIZE
    )
    from utils import HistoryManager, format_file_size
    from ui_theme import ModernTheme
    from security_utils import (
        sanitize_filename, validate_file_path, safe_join_path,
        validate_and_sanitize_new_filename, safe_rename,
        validate_game_engine_filename
    )
    from filename_validator import (
        validate_character_filename, generate_character_filename
    )
except ImportError:
    # 如果模組匯入失敗，使用預設值（確保能打包成EXE）
    # 注意：打包成EXE時不應有print輸出，但這裡保留以便調試
    try:
        import sys
        if hasattr(sys, 'frozen'):  # 如果是打包後的EXE
            pass  # 不輸出，避免控制台窗口
        else:
            print("警告：無法匯入配置模組，使用預設配置")
    except:
        pass
    COLOR_MAP = {
        "00": ("沒穿", "nude"), "01": ("黑色", "black"), "02": ("白色", "white"),
        "03": ("綠色", "green"), "04": ("紅色", "red"), "05": ("黃色", "yellow"),
        "06": ("藍色", "blue")
    }
    THEMES = {
        "Hospital": ["H_Girlfriend", "H_Sister", "H_Cute", "H_Cool", "H_Motherly"],
        "BDSM": ["SM_Sister", "SM_Girlfriend"],
        "Bedroom": ["B_Cute_G", "B_Sister", "B_Cool_G", "B_M"],
        "Anime": ["A_編號"]
    }
    SUPPORTED_EXTENSIONS = ['.mp4', '.jpg', '.jpeg', '.png']
    APP_NAME = "檔案重新命名工具"
    DEFAULT_WINDOW_SIZE = "1200x1000"
    config_manager = None
    HistoryManager = None
    ModernTheme = None
    # 安全工具函數的備用實現
    def sanitize_filename(filename):
        return filename.replace('/', '').replace('\\', '').replace(':', '').replace('*', '').replace('?', '').replace('"', '').replace('<', '').replace('>', '').replace('|', '')
    def validate_file_path(file_path):
        return True, None
    def safe_join_path(dir_path, filename):
        return os.path.join(dir_path, sanitize_filename(filename))
    def validate_and_sanitize_new_filename(original_path, new_name, game_engine_mode=True):
        return sanitize_filename(new_name, game_engine_mode=game_engine_mode), None
    def validate_game_engine_filename(filename):
        return True, None
    def validate_character_filename(filename):
        return True, None, None
    def generate_character_filename(char_id, char_type, char_index, ext=''):
        if ext and not ext.startswith('.'):
            ext = '.' + ext
        return f"Character_{str(int(char_id)).zfill(2)}_{char_type}_{str(int(char_index)).zfill(2)}{ext.lower() if ext else ''}"
    def safe_rename(old_path, new_path):
        try:
            os.rename(old_path, new_path)
            return True, None
        except Exception as e:
            return False, str(e)

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    HAS_DND = True
except ImportError:
    HAS_DND = False
    # 打包成EXE時不輸出提示
    try:
        import sys
        if not hasattr(sys, 'frozen'):
            print("提示：未安裝tkinterdnd2，拖放功能將不可用。可使用 pip install tkinterdnd2 安裝")
    except:
        pass

try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    # 打包成EXE時不輸出提示
    try:
        import sys
        if not hasattr(sys, 'frozen'):
            print("提示：未安裝Pillow，圖片預覽功能將受限。可使用 pip install Pillow 安裝")
    except:
        pass

# tkinter已在第一行導入，無需重複檢查


class FileRenamerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_NAME)
        
        # 載入儲存的視窗大小和位置
        if config_manager:
            saved_geometry = config_manager.get("window_geometry", DEFAULT_WINDOW_SIZE)
            self.root.geometry(saved_geometry)
        else:
            self.root.geometry(DEFAULT_WINDOW_SIZE)
        
        self.selected_files = []
        self.file_char_id_map = {}  # 儲存每個檔案的角色編號設定
        self.preview_images = {}  # 儲存預覽圖片
        self.color_map = COLOR_MAP
        self.rename_history = []  # 重命名歷史，用於撤銷
        self.dark_mode = False
        
        # 初始化UI主題
        if ModernTheme:
            self.theme = ModernTheme()
        else:
            self.theme = None
        
        # 初始化歷史管理器
        if HistoryManager:
            self.history_manager = HistoryManager()
        else:
            self.history_manager = None
        
        # 預覽刷新防抖（避免過於頻繁的刷新）
        self.preview_update_pending = False
        
        # 狀態追蹤
        self.current_preview_file = None
        self.current_preview_index = None
        
        self.setup_ui()
        self.setup_drag_drop()
        self.setup_keyboard_shortcuts()
        self.load_saved_settings()
        
        # 綁定視窗關閉事件，儲存設定
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_ui(self):
        """設置現代化UI"""
        # 應用現代化樣式
        self.apply_modern_style()
        
        # 創建主滾動框架
        # 創建 Canvas 和 Scrollbar 用於整個窗口滾動
        main_canvas_frame = ttk.Frame(self.root)
        main_canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        # 創建垂直滾動條
        main_scrollbar = ttk.Scrollbar(main_canvas_frame, orient=tk.VERTICAL)
        main_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 創建 Canvas
        self.main_canvas = tk.Canvas(main_canvas_frame, yscrollcommand=main_scrollbar.set)
        self.main_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        main_scrollbar.config(command=self.main_canvas.yview)
        
        # 創建內容框架（所有內容都放在這裡）
        self.content_frame = ttk.Frame(self.main_canvas)
        self.main_canvas_window = self.main_canvas.create_window((0, 0), window=self.content_frame, anchor=tk.NW)
        
        # 綁定 Canvas 大小變化事件
        def on_canvas_configure(event):
            # 設置內容框架寬度等於 Canvas 寬度
            canvas_width = event.width
            self.main_canvas.itemconfig(self.main_canvas_window, width=canvas_width)
            # 更新 Canvas 滾動區域
            self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all"))
        
        self.main_canvas.bind('<Configure>', on_canvas_configure)
        
        # 綁定鼠標滾輪事件
        def on_mousewheel(event):
            # 檢查鼠標是否在 Canvas 上
            if self.main_canvas.winfo_containing(event.x_root, event.y_root):
                self.main_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        self.main_canvas.bind_all("<MouseWheel>", on_mousewheel)
        
        # 綁定內容框架大小變化事件
        def on_content_configure(event):
            # 更新 Canvas 滾動區域
            self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all"))
        
        self.content_frame.bind('<Configure>', on_content_configure)
        
        # 在設置完所有內容後，更新一次滾動區域
        def update_scroll_region():
            self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all"))
        
        self.root.after(100, update_scroll_region)
        
        # 選擇檔案區域（現代化卡片）
        file_frame = self.create_modern_card(self.content_frame, "📁 選擇檔案", padding=16)
        file_frame.pack(fill=tk.X, padx=12, pady=8)
        
        # 第一行：按鈕（現代化樣式）
        button_row = ttk.Frame(file_frame)
        button_row.pack(fill=tk.X, pady=(0, 12))
        
        self.create_modern_button(button_row, "📄 選擇檔案", self.select_files, 'primary').pack(side=tk.LEFT, padx=(0, 8))
        self.create_modern_button(button_row, "📁 選擇資料夾", self.select_folder, 'primary').pack(side=tk.LEFT, padx=(0, 8))
        self.create_modern_button(button_row, "🗑️ 清空列表", self.clear_files, 'secondary').pack(side=tk.LEFT, padx=(0, 8))
        self.create_modern_button(button_row, "👥 定位20個人物模式", self.setup_20_characters_mode, 'secondary').pack(side=tk.LEFT, padx=(0, 8))
        
        # 第二行：限制數量設定和資料夾路徑輸入（現代化樣式）
        control_row = ttk.Frame(file_frame)
        control_row.pack(fill=tk.X, pady=(0, 8))
        
        # 左側：數量控制
        count_frame = ttk.Frame(control_row)
        count_frame.pack(side=tk.LEFT, padx=(0, 16))
        
        ttk.Label(count_frame, text="最大選擇數量（0=無限制）:", 
                 font=self.theme.get_font('body') if self.theme else ('Arial', 10)).pack(side=tk.LEFT, padx=(0, 8))
        self.max_files_var = tk.StringVar(value="0")
        max_files_entry = ttk.Entry(count_frame, textvariable=self.max_files_var, width=10, style='Modern.TEntry')
        max_files_entry.pack(side=tk.LEFT, padx=(0, 12))
        
        ttk.Label(count_frame, text="當前數量:", 
                 font=self.theme.get_font('body') if self.theme else ('Arial', 10)).pack(side=tk.LEFT, padx=(0, 8))
        theme_colors = self.theme.get_theme(self.dark_mode) if self.theme else {}
        count_color = theme_colors.get('primary', '#2196F3')
        self.current_count_label = ttk.Label(count_frame, text="0", 
                                            foreground=count_color, 
                                            font=self.theme.get_font('subheading') if self.theme else ('Arial', 10, 'bold'))
        self.current_count_label.pack(side=tk.LEFT)
        
        # 右側：資料夾路徑
        path_frame = ttk.Frame(control_row)
        path_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Label(path_frame, text="📂 資料夾路徑:", 
                 font=self.theme.get_font('body') if self.theme else ('Arial', 10)).pack(side=tk.LEFT, padx=(0, 8))
        self.folder_path_var = tk.StringVar()
        folder_path_entry = ttk.Entry(path_frame, textvariable=self.folder_path_var, width=40, style='Modern.TEntry')
        folder_path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        self.create_modern_button(path_frame, "導入", self.import_folder_path, 'secondary').pack(side=tk.LEFT)
        
        # 檔案列表（支援多選和調整順序）- 現代化卡片
        list_frame = self.create_modern_card(self.content_frame, "📋 已選擇的檔案（可多選調整順序）", padding=16)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)
        
        # 列表控制按鈕（現代化樣式）
        list_control_frame = ttk.Frame(list_frame)
        list_control_frame.pack(fill=tk.X, pady=(0, 12))
        
        self.create_modern_button(list_control_frame, "⬆️ 上移", self.move_up, 'secondary').pack(side=tk.LEFT, padx=(0, 6))
        self.create_modern_button(list_control_frame, "⬇️ 下移", self.move_down, 'secondary').pack(side=tk.LEFT, padx=(0, 6))
        self.create_modern_button(list_control_frame, "🗑️ 刪除選中", self.remove_selected, 'secondary').pack(side=tk.LEFT, padx=(0, 12))
        
        # 添加"僅處理選中項"選項
        self.only_selected_var = tk.BooleanVar(value=False)
        only_selected_check = ttk.Checkbutton(list_control_frame, 
                       text="✓ 僅處理選中的檔案（多選時按順序自動排序命名）", 
                       variable=self.only_selected_var,
                       command=self.on_only_selected_change)
        only_selected_check.pack(side=tk.LEFT, padx=(0, 0))
        
        # 搜索框（現代化樣式）
        search_frame = ttk.Frame(list_frame)
        search_frame.pack(fill=tk.X, pady=(0, 12))
        ttk.Label(search_frame, text="🔍 搜尋:", 
                 font=self.theme.get_font('body') if self.theme else ('Arial', 10)).pack(side=tk.LEFT, padx=(0, 8))
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self.filter_file_list())
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30, style='Modern.TEntry')
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        self.create_modern_button(search_frame, "清除", lambda: self.search_var.set(""), 'secondary').pack(side=tk.LEFT)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.file_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, 
                                       selectmode=tk.EXTENDED, height=10)
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.file_listbox.yview)
        
        # 綁定選擇事件，點選時顯示預覽
        self.file_listbox.bind('<<ListboxSelect>>', self.on_file_select)
        
        # 命名規則選擇（現代化卡片）
        rule_frame = self.create_modern_card(self.content_frame, "⚙️ 命名規則", padding=16)
        rule_frame.pack(fill=tk.X, padx=12, pady=8)
        
        self.rule_var = tk.StringVar(value="character")
        ttk.Radiobutton(rule_frame, text="Character規則（輸出給客戶端）", 
                       variable=self.rule_var, value="character", 
                       command=lambda: (self.on_rule_change(), self.on_index_change())).pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(rule_frame, text="夢想命名規則（內部規則，供員工瀏覽）", 
                       variable=self.rule_var, value="dream", 
                       command=lambda: (self.on_rule_change(), self.on_index_change())).pack(side=tk.LEFT, padx=10)
        
        # Character規則輸入區域（現代化卡片）
        self.char_frame = self.create_modern_card(self.content_frame, "🎭 Character規則參數", padding=16)
        self.char_frame.pack(fill=tk.X, padx=12, pady=8)
        
        # 一鍵選擇類型選單（現代化樣式）
        quick_type_frame = ttk.Frame(self.char_frame)
        quick_type_frame.pack(fill=tk.X, pady=(0, 12))
        
        ttk.Label(quick_type_frame, text="⚡ 一鍵選擇類型：", 
                 font=self.theme.get_font('subheading') if self.theme else ('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=(0, 12))
        self.create_modern_button(quick_type_frame, "Idle", 
                  lambda: self.set_all_type("Idle"), 'secondary').pack(side=tk.LEFT, padx=(0, 6))
        self.create_modern_button(quick_type_frame, "Intro", 
                  lambda: self.set_all_type("Intro"), 'secondary').pack(side=tk.LEFT, padx=(0, 6))
        self.create_modern_button(quick_type_frame, "Open", 
                  lambda: self.set_all_type("Open"), 'secondary').pack(side=tk.LEFT, padx=(0, 6))
        
        char_input_frame = ttk.Frame(self.char_frame)
        char_input_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(char_input_frame, text="角色編號:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.char_id_var = tk.StringVar(value="01")
        char_id_combo = ttk.Combobox(char_input_frame, textvariable=self.char_id_var, 
                                    values=[f"{i:02d}" for i in range(1, 100)], 
                                    state="readonly", width=10, style='Modern.TCombobox')
        char_id_combo.grid(row=0, column=1, padx=5, pady=5)
        char_id_combo.bind("<<ComboboxSelected>>", self.on_index_change)
        
        ttk.Label(char_input_frame, text="類型:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.char_type_var = tk.StringVar(value="Idle")
        char_type_combo = ttk.Combobox(char_input_frame, textvariable=self.char_type_var, 
                                      values=["Idle", "Intro", "Open"], state="readonly", width=15, style='Modern.TCombobox')
        char_type_combo.grid(row=0, column=3, padx=5, pady=5)
        char_type_combo.bind("<<ComboboxSelected>>", lambda e: (self.on_char_type_change(e), self.on_index_change(e)))
        
        ttk.Label(char_input_frame, text="索引:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        # 創建帶顏色提示的索引選項（顯示：01 - 沒穿，但值還是01）
        # 索引01對應顏色00（沒穿），索引02對應顏色01（黑色），以此類推
        # 顏色索引只有00-06這7個，所以索引只顯示01-07
        index_values = []
        for i in range(1, 8):  # 只顯示01-07，對應顏色00-06
            index_str = f"{i:02d}"
            color_code = f"{i-1:02d}"
            color_name = self.color_map.get(color_code, ("", ""))[0]
            if color_name:
                index_values.append(f"{index_str} - {color_name}")
            else:
                index_values.append(index_str)
        # 初始值設為帶顏色提示的格式
        initial_value = index_values[0] if index_values else "01"
        self.char_index_var = tk.StringVar(value=initial_value)
        char_index_combo = ttk.Combobox(char_input_frame, textvariable=self.char_index_var, 
                                       values=index_values, 
                                       state="readonly", width=15, style='Modern.TCombobox')
        char_index_combo.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        char_index_combo.bind("<<ComboboxSelected>>", lambda e: self.on_index_combo_change(e, self.char_index_var))
        # 保存原始值映射
        self.char_index_combo = char_index_combo
        
        # Open類型的顏色選擇（顯示中文）
        # 初始時不顯示，避免界面飄移，等類型為Open時再顯示
        self.color_frame = ttk.Frame(self.char_frame)
        # 不立即pack，等類型為Open時再顯示
        
        ttk.Label(self.color_frame, text="開獎演出顏色索引（顯示中文，儲存為對應編號）:").pack(side=tk.LEFT, padx=5)
        self.color_var = tk.StringVar(value="00")
        for code, (chinese, english) in self.color_map.items():
            color_radio = ttk.Radiobutton(self.color_frame, text=f"{code} - {chinese}", 
                          variable=self.color_var, value=code, 
                          command=lambda c=code: (self.color_var.set(c), self.on_index_change()))
            color_radio.pack(side=tk.LEFT, padx=5)
        
        # 如果初始類型是Open，顯示顏色框架
        if self.char_type_var.get() == "Open":
            self.color_frame.pack(fill=tk.X, padx=5, pady=5)
        
        
        # 夢想命名規則輸入區域
        self.dream_frame = ttk.LabelFrame(self.content_frame, text="夢想命名規則參數", padding=10)
        self.dream_frame.pack(fill=tk.X, padx=10, pady=5)
        
        dream_input_frame = ttk.Frame(self.dream_frame)
        dream_input_frame.pack(fill=tk.X)
        
        ttk.Label(dream_input_frame, text="主題:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.theme_var = tk.StringVar(value="Hospital")
        theme_combo = ttk.Combobox(dream_input_frame, textvariable=self.theme_var, style='Modern.TCombobox',
                                  values=["Hospital", "BDSM", "Bedroom", "Anime"], 
                                  state="readonly", width=15)
        theme_combo.grid(row=0, column=1, padx=5, pady=5)
        theme_combo.bind("<<ComboboxSelected>>", lambda e: (self.on_theme_change(e), self.on_index_change(e)))
        
        ttk.Label(dream_input_frame, text="角色類型:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.role_var = tk.StringVar()
        self.role_combo = ttk.Combobox(dream_input_frame, textvariable=self.role_var, style='Modern.TCombobox', 
                                       state="readonly", width=20)
        self.role_combo.grid(row=0, column=3, padx=5, pady=5)
        self.role_combo.bind("<<ComboboxSelected>>", self.on_index_change)
        
        ttk.Label(dream_input_frame, text="索引:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.dream_index_var = tk.StringVar(value="01")
        dream_index_combo = ttk.Combobox(dream_input_frame, textvariable=self.dream_index_var, style='Modern.TCombobox', 
                                        values=[f"{i:02d}" for i in range(1, 21)], 
                                        state="readonly", width=10)
        dream_index_combo.grid(row=1, column=1, padx=5, pady=5)
        dream_index_combo.bind("<<ComboboxSelected>>", self.on_index_change)
        
        # Anime主題的編號
        self.anime_frame = ttk.Frame(self.dream_frame)
        self.anime_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(self.anime_frame, text="動漫主題編號 (A_編號):").pack(side=tk.LEFT, padx=5)
        self.anime_num_var = tk.StringVar(value="01")
        anime_num_combo = ttk.Combobox(self.anime_frame, textvariable=self.anime_num_var, style='Modern.TCombobox', 
                                       values=[f"{i:02d}" for i in range(1, 21)], 
                                       state="readonly", width=10)
        anime_num_combo.pack(side=tk.LEFT, padx=5)
        anime_num_combo.bind("<<ComboboxSelected>>", self.on_index_change)
        
        # 初始化主題選項
        self.on_theme_change()
        
        # 預覽區域（分為文字預覽和圖片預覽）
        preview_frame = ttk.LabelFrame(self.content_frame, text="預覽", padding=10)
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 創建Notebook來切換文字和圖片預覽
        self.preview_notebook = ttk.Notebook(preview_frame)
        self.preview_notebook.pack(fill=tk.BOTH, expand=True)
        
        # 文字預覽標籤頁
        text_preview_frame = ttk.Frame(self.preview_notebook)
        self.preview_notebook.add(text_preview_frame, text="文字預覽")
        
        preview_scrollbar = ttk.Scrollbar(text_preview_frame)
        preview_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.preview_text = tk.Text(text_preview_frame, yscrollcommand=preview_scrollbar.set, height=8)
        self.preview_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        preview_scrollbar.config(command=self.preview_text.yview)
        
        # 配置文字樣式標籤（用於顯示錯誤和成功）
        self.preview_text.tag_config("error", foreground="red", font=("Arial", 9, "bold"))
        self.preview_text.tag_config("success", foreground="green", font=("Arial", 9, "bold"))
        
        # 圖片預覽標籤頁
        image_preview_frame = ttk.Frame(self.preview_notebook)
        self.preview_notebook.add(image_preview_frame, text="圖片/影片預覽")
        
        # 提示標籤
        self.preview_hint_label = ttk.Label(image_preview_frame, 
                                           text="💡 請在檔案列表中點選檔案以顯示預覽", 
                                           font=("Arial", 10), foreground="gray")
        self.preview_hint_label.pack(pady=20)
        
        # 創建Canvas用於顯示預覽
        image_canvas_frame = ttk.Frame(image_preview_frame)
        image_canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        image_scrollbar = ttk.Scrollbar(image_preview_frame, orient=tk.VERTICAL)
        image_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.preview_canvas = tk.Canvas(image_preview_frame, yscrollcommand=image_scrollbar.set)
        self.preview_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        image_scrollbar.config(command=self.preview_canvas.yview)
        
        # 拖放提示
        if HAS_DND:
            drop_hint = ttk.Label(self.content_frame, text="💡 提示：可以直接拖放檔案到此視窗", 
                                 foreground="blue", font=("Arial", 9))
            drop_hint.pack(pady=5)
        
        # 按鈕區域
        button_frame = ttk.Frame(self.content_frame)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        preview_btn = ttk.Button(button_frame, text="預覽重新命名 (Ctrl+R)", command=self.preview_rename)
        preview_btn.pack(side=tk.LEFT, padx=5)
        self.create_tooltip(preview_btn, "預覽重新命名結果 (快捷鍵: Ctrl+R)")
        
        execute_btn = ttk.Button(button_frame, text="執行重新命名 (Ctrl+Enter)", command=self.execute_rename)
        execute_btn.pack(side=tk.LEFT, padx=5)
        self.create_tooltip(execute_btn, "執行重新命名操作 (快捷鍵: Ctrl+Enter)")
        
        undo_btn = ttk.Button(button_frame, text="撤銷 (Ctrl+Z)", command=self.undo_rename)
        undo_btn.pack(side=tk.LEFT, padx=5)
        self.create_tooltip(undo_btn, "撤銷最後一次重命名操作 (快捷鍵: Ctrl+Z)")
        
        dark_mode_btn = ttk.Button(button_frame, text="深色模式 (Ctrl+T)", command=self.toggle_dark_mode)
        dark_mode_btn.pack(side=tk.LEFT, padx=5)
        self.create_tooltip(dark_mode_btn, "切換深色/淺色模式 (快捷鍵: Ctrl+T)")
        
        # 批量操作按鈕
        batch_btn = ttk.Button(button_frame, text="批量設定角色編號", command=self.batch_set_char_id)
        batch_btn.pack(side=tk.LEFT, padx=5)
        self.create_tooltip(batch_btn, "批量為選中的檔案設定角色編號")
        
        # 狀態欄
        status_frame = ttk.Frame(self.content_frame)
        status_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.status_label = ttk.Label(status_frame, text="就緒", relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=2)
        
        # 統計資訊標籤
        self.stats_label = ttk.Label(status_frame, text="", relief=tk.SUNKEN, anchor=tk.E)
        self.stats_label.pack(side=tk.RIGHT, padx=5, pady=2)
        
        # 初始顯示
        self.on_rule_change()
    
    def setup_drag_drop(self):
        """設置拖放功能"""
        if HAS_DND:
            # 為整個視窗啟用拖放
            self.root.drop_target_register(DND_FILES)
            self.root.dnd_bind('<<Drop>>', self.on_drop)
            
            # 為檔案列表啟用拖放
            self.file_listbox.drop_target_register(DND_FILES)
            self.file_listbox.dnd_bind('<<Drop>>', self.on_drop)
    
    def on_drop(self, event):
        """處理拖放事件（支援檔案和資料夾）"""
        try:
            # 處理拖放的文件列表
            # tkinterdnd2在Windows上可能返回字符串或列表
            if isinstance(event.data, str):
                # Windows路徑可能用大括號包圍，需要處理
                files_str = event.data.strip('{}')
                # 分割多個檔案（可能用空格或換行分隔）
                files = [f.strip('"').strip("'") for f in files_str.split() if f.strip()]
            else:
                files = event.data
            
            valid_extensions = ['.mp4', '.jpg', '.jpeg', '.png']
            files_to_add = []
            folders_to_process = []
            
            # 分類檔案和資料夾
            for file_path in files:
                # 清理路徑
                file_path = file_path.strip('{}').strip('"').strip("'").strip()
                if not file_path:
                    continue
                
                if os.path.isfile(file_path):
                    ext = os.path.splitext(file_path)[1].lower()
                    if ext in valid_extensions:
                        if file_path not in self.selected_files:
                            files_to_add.append(file_path)
                elif os.path.isdir(file_path):
                    folders_to_process.append(file_path)
            
            added_count = 0
            
            # 先處理檔案
            if files_to_add:
                # 檢查數量限制
                can_add, max_files = self.check_max_files_limit(len(files_to_add))
                if not can_add:
                    messagebox.showwarning("警告", 
                        f"無法添加 {len(files_to_add)} 個檔案！\n"
                        f"當前已有 {len(self.selected_files)} 個檔案，最大限制為 {max_files} 個。\n"
                        f"只能再添加 {max_files - len(self.selected_files)} 個檔案。")
                    # 只添加允許的數量
                    allowed_count = max_files - len(self.selected_files)
                    if allowed_count > 0:
                        files_to_add = files_to_add[:allowed_count]
                    else:
                        files_to_add = []
                
                for file_path in files_to_add:
                    if file_path not in self.selected_files:
                        self.selected_files.append(file_path)
                        added_count += 1
            
            # 再處理資料夾
            for folder_path in folders_to_process:
                folder_added = self.add_files_from_folder(folder_path)
                added_count += folder_added
            
            if added_count > 0:
                self.update_file_list()
                # 不顯示訊息框，避免打斷用戶操作
                # messagebox.showinfo("成功", f"已添加 {added_count} 個檔案")
            elif len(files) > 0:
                messagebox.showwarning("警告", "沒有找到支援的檔案或資料夾（支援：MP4, JPG, PNG）")
        except Exception as e:
            messagebox.showerror("錯誤", f"處理拖放檔案時發生錯誤：{str(e)}")
    
    def select_files(self):
        """選擇檔案"""
        # 使用上次的資料夾（如果有的話）
        initial_dir = None
        if config_manager:
            last_folder = config_manager.get("last_folder", "")
            if last_folder and os.path.isdir(last_folder):
                initial_dir = last_folder
        
        files = filedialog.askopenfilenames(
            title="選擇檔案",
            initialdir=initial_dir,
            filetypes=[
                ("支援的檔案", "*.mp4;*.jpg;*.png"),
                ("影片檔案", "*.mp4"),
                ("圖片檔案", "*.jpg;*.png"),
                ("所有檔案", "*.*")
            ]
        )
        if files:
            # 記錄最後使用的資料夾
            if config_manager and files:
                last_folder = os.path.dirname(files[0])
                if os.path.isdir(last_folder):
                    config_manager.set("last_folder", last_folder)
            
            files_to_add = [f for f in files if f not in self.selected_files]
            
            if files_to_add:
                # 檢查數量限制
                can_add, max_files = self.check_max_files_limit(len(files_to_add))
                if not can_add:
                    messagebox.showwarning("警告", 
                        f"無法添加 {len(files_to_add)} 個檔案！\n"
                        f"當前已有 {len(self.selected_files)} 個檔案，最大限制為 {max_files} 個。\n"
                        f"只能再添加 {max_files - len(self.selected_files)} 個檔案。")
                    # 只添加允許的數量
                    allowed_count = max_files - len(self.selected_files)
                    if allowed_count > 0:
                        files_to_add = files_to_add[:allowed_count]
                    else:
                        files_to_add = []
                
                for f in files_to_add:
                    if f not in self.selected_files:
                        self.selected_files.append(f)
                self.update_file_list()
                # 更新狀態
                self.update_status(f"已添加 {len(files_to_add)} 個檔案")
    
    def select_folder(self):
        """選擇資料夾"""
        # 使用上次的資料夾（如果有的話）
        initial_dir = None
        if config_manager:
            last_folder = config_manager.get("last_folder", "")
            if last_folder and os.path.isdir(last_folder):
                initial_dir = last_folder
        
        folder = filedialog.askdirectory(title="選擇資料夾", initialdir=initial_dir)
        if folder:
            # 記錄最後使用的資料夾
            if config_manager:
                config_manager.set("last_folder", folder)
            added_count = self.add_files_from_folder(folder)
            if added_count > 0:
                self.update_status(f"從資料夾添加了 {added_count} 個檔案")
    
    def clear_files(self):
        self.selected_files = []
        self.file_char_id_map = {}
        self.update_file_list()
        self.preview_text.delete(1.0, tk.END)
        self.clear_image_preview()
    
    def filter_file_list(self):
        """根據搜尋過濾檔案列表"""
        search_text = self.search_var.get().lower() if hasattr(self, 'search_var') else ""
        self.file_listbox.delete(0, tk.END)
        filtered_count = 0
        for file_path in self.selected_files:
            file_name = os.path.basename(file_path).lower()
            if not search_text or search_text in file_name:
                self.file_listbox.insert(tk.END, os.path.basename(file_path))
                filtered_count += 1
        # 更新當前數量顯示
        if hasattr(self, 'current_count_label'):
            self.current_count_label.config(text=f"{filtered_count}/{len(self.selected_files)}")
    
    def update_file_list(self):
        """更新檔案列表"""
        self.filter_file_list()
        # 更新統計資訊
        self.update_statistics()
    
    def update_statistics(self):
        """更新統計資訊"""
        if not hasattr(self, 'stats_label'):
            return
        
        total_files = len(self.selected_files)
        if total_files == 0:
            self.stats_label.config(text="")
            return
        
        # 統計檔案類型
        file_types = {}
        total_size = 0
        for file_path in self.selected_files:
            ext = os.path.splitext(file_path)[1].lower()
            file_types[ext] = file_types.get(ext, 0) + 1
            try:
                total_size += os.path.getsize(file_path)
            except:
                pass
        
        # 格式化統計資訊
        type_info = ", ".join([f"{ext.upper()}: {count}" for ext, count in sorted(file_types.items())])
        try:
            from utils import format_file_size
            size_info = format_file_size(total_size)
        except:
            size_info = f"{total_size / 1024 / 1024:.2f} MB"
        stats_text = f"總數: {total_files} | {type_info} | 大小: {size_info}"
        self.stats_label.config(text=stats_text)
    
    def update_status(self, message):
        """更新狀態欄訊息"""
        if hasattr(self, 'status_label'):
            self.status_label.config(text=message)
            # 3秒後恢復為"就緒"
            self.root.after(3000, lambda: self.status_label.config(text="就緒") if hasattr(self, 'status_label') else None)
    
    def check_max_files_limit(self, new_files_count):
        """檢查是否超過最大選擇數量限制"""
        try:
            max_files = int(self.max_files_var.get())
            # 限制範圍在 0-10000（防止過大值）
            max_files = max(0, min(10000, max_files))
            if max_files <= 0:
                return True, None  # 無限制
            
            current_count = len(self.selected_files)
            if current_count + new_files_count > max_files:
                return False, max_files
            return True, None
        except ValueError:
            return True, None  # 如果輸入無效，視為無限制
    
    def add_files_from_folder(self, folder_path):
        """從資料夾添加檔案（包含安全驗證）"""
        # 驗證路徑
        is_valid, error = validate_file_path(folder_path)
        if not is_valid:
            messagebox.showerror("錯誤", f"路徑無效: {error}")
            return 0
        
        if not os.path.isdir(folder_path):
            messagebox.showerror("錯誤", f"路徑不是有效的資料夾：{folder_path}")
            return 0
        
        files_to_add = []
        for ext in ['*.mp4', '*.jpg', '*.jpeg', '*.png']:
            for file_path in Path(folder_path).glob(ext):
                file_str = str(file_path)
                if file_str not in self.selected_files:
                    files_to_add.append(file_str)
        
        if not files_to_add:
            messagebox.showinfo("提示", "資料夾中沒有找到支援的檔案（支援：MP4, JPG, PNG）")
            return 0
        
        # 檢查數量限制
        original_files_count = len(files_to_add)
        can_add, max_files = self.check_max_files_limit(original_files_count)
        if not can_add:
            messagebox.showwarning("警告", 
                f"無法添加 {original_files_count} 個檔案！\n"
                f"當前已有 {len(self.selected_files)} 個檔案，最大限制為 {max_files} 個。\n"
                f"只能再添加 {max_files - len(self.selected_files)} 個檔案。")
            # 只添加允許的數量
            allowed_count = max_files - len(self.selected_files)
            if allowed_count > 0:
                files_to_add = files_to_add[:allowed_count]
            else:
                return 0
        
        added_count = 0
        for file_path in files_to_add:
            if file_path not in self.selected_files:
                self.selected_files.append(file_path)
                added_count += 1
        
        if added_count > 0:
            self.update_file_list()
            # 如果因為限制而沒有添加所有檔案，顯示提示
            if not can_add and added_count < original_files_count:
                messagebox.showinfo("提示", f"已添加 {added_count} 個檔案（已達最大限制 {max_files} 個）")
        
        return added_count
    
    def import_folder_path(self):
        """導入資料夾路徑（包含安全驗證）"""
        folder_path = self.folder_path_var.get().strip()
        if not folder_path:
            messagebox.showwarning("警告", "請輸入資料夾路徑！")
            return
        
        # 驗證路徑
        is_valid, error = validate_file_path(folder_path)
        if not is_valid:
            messagebox.showerror("錯誤", f"路徑無效: {error}")
            return
        
        self.add_files_from_folder(folder_path)
    
    def on_file_select(self, event=None):
        """當檔案列表中的項目被選中時，顯示預覽"""
        selected_indices = self.file_listbox.curselection()
        if not selected_indices:
            # 如果沒有選中任何項目，清除預覽
            self.clear_image_preview()
            return
        
        # 只顯示第一個選中檔案的預覽（如果多選，顯示第一個）
        selected_index = selected_indices[0]
        if 0 <= selected_index < len(self.selected_files):
            file_path = self.selected_files[selected_index]
            # 如果啟用了"僅處理選中項"，使用在處理列表中的索引
            if self.only_selected_var.get():
                files_to_process = self.get_files_to_process()
                if file_path in files_to_process:
                    process_index = files_to_process.index(file_path)
                    self.show_single_file_preview(file_path, process_index)
                else:
                    # 如果文件不在處理列表中，使用原始索引
                    self.show_single_file_preview(file_path, selected_index)
            else:
                self.show_single_file_preview(file_path, selected_index)
    
    def clear_image_preview(self):
        """清除圖片預覽（包含資源清理）"""
        # 清除Canvas內容
        self.preview_canvas.delete("all")
        
        # 清理圖片引用以釋放內存
        for img_id, img in list(self.preview_images.items()):
            try:
                del img
            except:
                pass
        
        # 清空圖片字典
        self.preview_images.clear()
        
        # 顯示提示標籤
        self.preview_hint_label.pack(pady=20)
    
    def show_single_file_preview(self, file_path, index):
        """顯示單個檔案的預覽（完全重新加載，確保穩定性）"""
        # 記錄當前預覽的檔案和索引
        self.current_preview_file = file_path
        self.current_preview_index = index
        
        # 立即清除舊的預覽，確保及時刷新（包含資源清理）
        self.preview_canvas.delete("all")
        
        # 清理舊的圖片引用以釋放內存
        for img_id, img in list(self.preview_images.items()):
            try:
                del img
            except:
                pass
        
        self.preview_images.clear()
        
        # 隱藏提示標籤
        self.preview_hint_label.pack_forget()
        
        # 立即更新視窗，確保清除操作生效
        self.root.update_idletasks()
        
        # 獲取擴展名
        old_name = os.path.basename(file_path)
        ext = os.path.splitext(file_path)[1].lower()
        
        # 載入預覽圖片（異步載入，避免阻塞UI）
        # 不傳遞 new_name，讓 _display_preview 實時生成
        self._load_preview_image_async(file_path, old_name, ext, index)
    
    def _load_preview_image_async(self, file_path, old_name, ext, index):
        """異步載入預覽圖片（增強穩定性，防止並發問題）"""
        # 生成唯一的加載ID，用於追踪
        import time
        load_id = f"{file_path}_{index}_{time.time()}"
        self.current_load_id = load_id
        
        def load_and_display():
            try:
                preview_img = self.load_preview_image(file_path, max_size=(300, 300))
                # 在主線程中更新UI，並檢查是否仍然是當前請求
                self.root.after(0, lambda: self._display_preview(preview_img, old_name, ext, file_path, index, load_id))
            except Exception as e:
                # 如果加載失敗，顯示錯誤信息
                if not IN_EXE:
                    print(f"預覽加載錯誤: {e}")
                self.root.after(0, lambda: self._display_preview(None, old_name, ext, file_path, index, load_id))
        
        # 在後台線程中載入圖片
        thread = Thread(target=load_and_display, daemon=True)
        thread.start()
        
        # 先顯示載入中提示
        try:
            center_x = self.preview_canvas.winfo_width()
            if center_x < 10:
                center_x = 400
            else:
                center_x = center_x // 2
            
            self.preview_canvas.create_text(center_x, 200, anchor=tk.CENTER, 
                                          text="載入中...", font=("Arial", 12), tags="loading")
        except Exception as e:
            if not IN_EXE:
                print(f"顯示載入提示錯誤: {e}")
    
    def _display_preview(self, preview_img, old_name, ext, file_path, index, load_id):
        """顯示預覽內容（增強穩定性，實時生成文件名）"""
        try:
            # 檢查這是否仍然是當前請求的預覽
            if not hasattr(self, 'current_load_id') or self.current_load_id != load_id:
                # 這是一個過時的請求，忽略它
                if not IN_EXE:
                    print(f"忽略過時的預覽請求: {file_path}")
                return
            
            # 檢查當前預覽的檔案是否仍然是這個檔案
            if self.current_preview_file != file_path:
                # 用戶已經切換到其他檔案了，忽略這個預覽
                if not IN_EXE:
                    print(f"忽略過時的預覽請求（檔案已改變）: {file_path}")
                return
            
            # 實時生成新檔名（使用當前最新的參數設定）
            new_name = self.generate_new_filename(file_path, index)
            
            if not IN_EXE:
                print(f"顯示預覽: {old_name} -> {new_name}")
            
            # 清除載入中提示和所有舊內容
            self.preview_canvas.delete("all")
            
            # 計算居中位置
            canvas_width = self.preview_canvas.winfo_width()
            if canvas_width < 10:
                canvas_width = 400
            center_x = canvas_width // 2
            
            if preview_img:
                # 顯示預覽圖片（居中）
                img_width = preview_img.width()
                img_height = preview_img.height()
                img_x = center_x - img_width // 2
                
                img_id = self.preview_canvas.create_image(img_x, 20, anchor=tk.NW, image=preview_img)
                self.preview_images[img_id] = preview_img  # 保持引用
                
                # 如果是影片，顯示影片標記
                if ext == '.mp4':
                    self.preview_canvas.create_text(center_x, 20 + img_height // 2, anchor=tk.CENTER, 
                                                  text="🎬 影片", font=("Arial", 16, "bold"), 
                                                  fill="white")
                
                # 顯示檔案名稱（在圖片下方）
                text_y = 20 + img_height + 20
            else:
                # 如果無法載入預覽，顯示檔案類型標記
                file_type = "圖片" if ext in ['.jpg', '.jpeg', '.png'] else "影片" if ext == '.mp4' else "檔案"
                box_size = 300
                box_x = center_x - box_size // 2
                self.preview_canvas.create_rectangle(box_x, 20, box_x + box_size, 20 + box_size, 
                                                    outline="gray", fill="lightgray", width=2)
                self.preview_canvas.create_text(center_x, 20 + box_size // 2, anchor=tk.CENTER, 
                                                text=f"📄 {file_type}", font=("Arial", 16))
                text_y = 20 + box_size + 20
            
            # 顯示檔案名稱（使用標籤以便後續更新）
            self.preview_canvas.create_text(center_x, text_y, anchor=tk.CENTER, 
                                          text=f"原檔名: {old_name}", 
                                          font=("Arial", 11), 
                                          tags="filename_old")
            self.preview_canvas.create_text(center_x, text_y + 25, anchor=tk.CENTER, 
                                          text=f"新檔名: {new_name}", 
                                          font=("Arial", 11, "bold"), 
                                          fill="blue", 
                                          tags="filename_new")
            
            # 更新滾動區域
            self.preview_canvas.update_idletasks()
            self.preview_canvas.config(scrollregion=self.preview_canvas.bbox("all"))
            
        except Exception as e:
            if not IN_EXE:
                print(f"顯示預覽錯誤: {e}")
                import traceback
                traceback.print_exc()
            # 發生錯誤時，至少顯示檔案名稱
            try:
                # 嘗試生成新檔名
                try:
                    new_name = self.generate_new_filename(file_path, index)
                except:
                    new_name = "生成失敗"
                
                self.preview_canvas.delete("all")
                center_x = 200
                self.preview_canvas.create_text(center_x, 100, anchor=tk.CENTER, 
                                              text=f"原檔名: {old_name}", font=("Arial", 11))
                self.preview_canvas.create_text(center_x, 125, anchor=tk.CENTER, 
                                              text=f"新檔名: {new_name}", 
                                              font=("Arial", 11, "bold"), fill="blue")
            except:
                pass
    
    def move_up(self):
        selected = self.file_listbox.curselection()
        if not selected:
            return
        for idx in selected:
            if idx > 0:
                self.selected_files[idx], self.selected_files[idx-1] = \
                    self.selected_files[idx-1], self.selected_files[idx]
        self.update_file_list()
        # 重新選中移動後的項目
        for idx in selected:
            if idx > 0:
                self.file_listbox.selection_set(idx-1)
    
    def move_down(self):
        selected = self.file_listbox.curselection()
        if not selected:
            return
        # 從後往前處理，避免索引變化問題
        for idx in reversed(selected):
            if idx < len(self.selected_files) - 1:
                self.selected_files[idx], self.selected_files[idx+1] = \
                    self.selected_files[idx+1], self.selected_files[idx]
        self.update_file_list()
        # 重新選中移動後的項目
        for idx in selected:
            if idx < len(self.selected_files) - 1:
                self.file_listbox.selection_set(idx+1)
    
    def remove_selected(self):
        selected = self.file_listbox.curselection()
        if not selected:
            return
        # 從後往前刪除，避免索引變化
        for idx in reversed(selected):
            del self.selected_files[idx]
        self.update_file_list()
    
    def set_all_type(self, file_type):
        """一鍵設置所有選中檔案的類型"""
        self.char_type_var.set(file_type)
        self.on_char_type_change()
    
    def on_rule_change(self):
        # 使用grid或固定位置，避免界面飄移
        if self.rule_var.get() == "character":
            # 确保 Character 规则参数显示，使用正确的 padx 和 pady
            if not self.char_frame.winfo_viewable():
                self.char_frame.pack(fill=tk.X, padx=12, pady=8, before=self.dream_frame if self.dream_frame.winfo_viewable() else None)
            if self.dream_frame.winfo_viewable():
                self.dream_frame.pack_forget()
        else:
            if self.char_frame.winfo_viewable():
                self.char_frame.pack_forget()
            # 确保梦想规则参数显示
            if not self.dream_frame.winfo_viewable():
                self.dream_frame.pack(fill=tk.X, padx=10, pady=5)
        self.preview_text.delete(1.0, tk.END)
    
    def on_char_type_change(self, event=None):
        # 固定顏色框架的位置，避免界面飄移
        if self.char_type_var.get() == "Open":
            if not self.color_frame.winfo_viewable():
                # 找到char_frame中最後一個可見的子元件，在其前面插入
                children = [w for w in self.char_frame.winfo_children() if w.winfo_viewable()]
                if children:
                    self.color_frame.pack(fill=tk.X, padx=5, pady=5, before=children[-1])
                else:
                    self.color_frame.pack(fill=tk.X, padx=5, pady=5)
        else:
            if self.color_frame.winfo_viewable():
                self.color_frame.pack_forget()
        self.on_index_change()
    
    def on_index_combo_change(self, event, var):
        """當索引下拉框改變時，提取數字部分並更新變數"""
        selected_value = var.get()
        # 如果包含" - "，提取前面的數字部分，但不改變顯示值
        # 保持顯示 "01 - 沒穿" 這樣的格式
        if " - " in selected_value:
            numeric_value = selected_value.split(" - ")[0]
            # 不改變 var.set()，保持顯示格式
            # 只在內部使用數字值
            pass
        # 調用預覽更新（不清除預覽狀態，讓異步加載機制自行管理）
        self.on_index_change()
    
    def on_index_change(self, event=None):
        """當任何選項改變時，刷新預覽（包括角色編號、類型、索引、命名規則等）"""
        # 使用防抖機制，避免過於頻繁的刷新
        if self.preview_update_pending:
            return
        
        self.preview_update_pending = True
        self.root.after(100, self._do_index_change)  # 100ms後執行
    
    def _do_index_change(self):
        """實際執行預覽更新"""
        self.preview_update_pending = False
        
        # 如果當前有選中的檔案，更新圖片預覽
        selected_indices = self.file_listbox.curselection()
        if selected_indices:
            selected_index = selected_indices[0]
            if 0 <= selected_index < len(self.selected_files):
                file_path = self.selected_files[selected_index]
                # 如果啟用了"僅處理選中項"，使用在處理列表中的索引
                if self.only_selected_var.get():
                    files_to_process = self.get_files_to_process()
                    if file_path in files_to_process:
                        process_index = files_to_process.index(file_path)
                        self.show_single_file_preview(file_path, process_index)
                    else:
                        # 如果文件不在處理列表中，使用原始索引
                        self.show_single_file_preview(file_path, selected_index)
                else:
                    self.show_single_file_preview(file_path, selected_index)
        
        # 同時更新文字預覽（如果檔案列表不為空）
        if self.selected_files:
            self.update_text_preview()
        
        # 更新統計資訊
        self.update_statistics()
    
    def on_theme_change(self, event=None):
        theme = self.theme_var.get()
        role_options = []
        
        if theme == "Hospital":
            role_options = ["H_Girlfriend", "H_Sister", "H_Cute", "H_Cool", "H_Motherly"]
        elif theme == "BDSM":
            role_options = ["SM_Sister", "SM_Girlfriend"]
        elif theme == "Bedroom":
            role_options = ["B_Cute_G", "B_Sister", "B_Cool_G", "B_M"]
        elif theme == "Anime":
            role_options = ["A_編號"]
            self.anime_frame.pack(fill=tk.X, padx=5, pady=5)
        else:
            self.anime_frame.pack_forget()
        
        if theme != "Anime":
            self.anime_frame.pack_forget()
        
        self.role_combo['values'] = role_options
        if role_options:
            self.role_var.set(role_options[0])
    
    def generate_new_filename(self, original_path, index):
        """生成新檔名（完全符合對外格式要求：Character_{角色編號}_{類型}_{索引}.ext）"""
        try:
            # 獲取原始檔案的擴展名（保留原始格式，重點是前面的格式）
            original_ext = os.path.splitext(original_path)[1]
            if original_ext:
                original_ext = original_ext.lower()  # 擴展名轉為小寫
            else:
                # 如果沒有擴展名，不添加擴展名（重點是前面的格式）
                original_ext = ''
            
            if self.rule_var.get() == "character":
                # 對外模式：Character_{角色編號}_{類型}_{索引}.ext
                
                # 1. 角色編號：確保為兩位數字（01-99）
                if original_path in self.file_char_id_map:
                    char_id_raw = str(self.file_char_id_map[original_path])
                else:
                    char_id_raw = str(self.char_id_var.get())
                
                # 提取數字部分並補零（添加異常處理）
                try:
                    char_id_digits = ''.join(filter(str.isdigit, char_id_raw))
                    char_id_num = int(char_id_digits) if char_id_digits else 1
                    # 限制範圍在 1-99
                    char_id_num = max(1, min(99, char_id_num))
                    char_id = f"{char_id_num:02d}"  # 確保兩位數字
                except (ValueError, TypeError):
                    # 如果轉換失敗，使用預設值
                    char_id = "01"
                
                # 2. 類型：確保為 Idle, Intro, Open（大小写敏感）
                char_type_raw = str(self.char_type_var.get())
                valid_types = ['Idle', 'Intro', 'Open']
                if char_type_raw in valid_types:
                    char_type = char_type_raw
                else:
                    # 如果類型無效，使用預設值
                    char_type = 'Idle'
                
                # 3. 索引：根據類型決定
                if char_type == "Open":
                    # Open類型使用顏色索引（00-06）
                    color_raw = str(self.color_var.get())
                    try:
                        color_digits = ''.join(filter(str.isdigit, color_raw))
                        char_index_num = int(color_digits) if color_digits else 0
                        # 限制範圍在 0-6
                        char_index_num = max(0, min(6, char_index_num))
                        char_index = f"{char_index_num:02d}"  # 確保兩位數字，範圍00-06
                    except (ValueError, TypeError):
                        # 如果轉換失敗，使用預設值
                        char_index = "00"
                else:
                    # Idle和Intro使用輸入的索引（01-20）
                    index_value = str(self.char_index_var.get())
                    # 如果包含" - "，提取前面的數字部分
                    if " - " in index_value:
                        index_value = index_value.split(" - ")[0]
                    # 提取數字部分並補零（添加異常處理）
                    try:
                        index_digits = ''.join(filter(str.isdigit, index_value))
                        char_index_num = int(index_digits) if index_digits else 1
                        # 限制範圍在 1-20
                        char_index_num = max(1, min(20, char_index_num))
                        char_index = f"{char_index_num:02d}"  # 確保兩位數字，範圍01-20
                    except (ValueError, TypeError):
                        # 如果轉換失敗，使用預設值
                        char_index = "01"
                
                # 使用專用的生成函數確保格式完全精確
                new_name = generate_character_filename(
                    char_id=char_id,
                    char_type=char_type,
                    char_index=char_index,
                    ext=original_ext
                )
                
                # 驗證生成的文件名是否符合Character格式
                is_valid, validation_error, parsed_data = validate_character_filename(new_name)
                if not is_valid:
                    # 如果驗證失敗，記錄錯誤但繼續使用生成的文件名
                    # 因為generate_character_filename已經確保了格式正確
                    # 打包成EXE時不輸出調試信息
                    try:
                        import sys
                        if not hasattr(sys, 'frozen'):
                            print(f"警告：文件名驗證失敗: {validation_error}")
                    except:
                        pass
                
                # Character規則不需要額外清理（因為格式已經完全精確）
                return new_name
            else:  # dream rule
                theme = str(self.theme_var.get())
                dream_index = str(self.dream_index_var.get()).zfill(2)
                
                if theme == "Anime":
                    anime_num = str(self.anime_num_var.get()).zfill(2)
                    # 確保格式精確：A_XX.ext
                    new_name = f"A_{anime_num}{original_ext}"
                else:
                    role = str(self.role_var.get())
                    # 確保格式精確：Role_XX.ext
                    new_name = f"{role}_{dream_index}{original_ext}"
            
            # 使用遊戲引擎模式驗證和清理檔案名
            sanitized_name, error = validate_and_sanitize_new_filename(
                original_path, new_name, game_engine_mode=True
            )
            
            if error:
                # 如果清理失敗，使用安全的備用名稱
                safe_name = sanitize_filename(new_name, game_engine_mode=True)
                if safe_name and safe_name != "unnamed":
                    return safe_name
                # 最終備用名稱
                return f"renamed_{index:04d}{original_ext}"
            
            # 最終驗證：確保文件名完全符合遊戲引擎標準
            is_valid, validation_error = validate_game_engine_filename(sanitized_name)
            if not is_valid:
                # 如果驗證失敗，使用備用名稱
                return f"renamed_{index:04d}{original_ext}"
            
            return sanitized_name
        except Exception as e:
            # 如果生成失敗，返回安全的備用名稱
            ext = os.path.splitext(original_path)[1].lower()
            return f"renamed_{index:04d}{ext}"
    
    def load_preview_image(self, file_path, max_size=(200, 200)):
        """載入預覽圖片（包含資源管理）"""
        try:
            # 驗證檔案路徑
            is_valid, error = validate_file_path(file_path)
            if not is_valid:
                return None
            
            # 檢查檔案是否存在
            if not os.path.exists(file_path) or not os.path.isfile(file_path):
                return None
            
            ext = os.path.splitext(file_path)[1].lower()
            
            if ext in ['.jpg', '.jpeg', '.png']:
                if HAS_PIL:
                    try:
                        img = Image.open(file_path)
                        img.thumbnail(max_size, Image.Resampling.LANCZOS)
                        photo = ImageTk.PhotoImage(img)
                        # 關閉原始圖片以釋放資源
                        img.close()
                        return photo
                    except Exception:
                        return None
                else:
                    return None
            elif ext == '.mp4':
                # 對於影片，創建一個帶有播放圖標的預覽
                if HAS_PIL:
                    try:
                        # 創建一個深色背景的影片圖標
                        img = Image.new('RGB', max_size, color='#2d2d2d')
                        photo = ImageTk.PhotoImage(img)
                        # 關閉圖片以釋放資源
                        img.close()
                        return photo
                    except Exception:
                        return None
                else:
                    return None
        except Exception:
            return None
    
    def get_files_to_process(self):
        """獲取要處理的檔案列表（根據是否僅處理選中項）"""
        if self.only_selected_var.get():
            # 僅處理選中的檔案，按照選中順序
            selected_indices = self.file_listbox.curselection()
            if not selected_indices:
                return []
            # 按照選中順序排列
            files_to_process = [self.selected_files[i] for i in selected_indices]
            return files_to_process
        else:
            # 處理所有檔案
            return self.selected_files
    
    def update_text_preview(self):
        """更新文字預覽"""
        files_to_process = self.get_files_to_process()
        if not files_to_process:
            self.preview_text.delete(1.0, tk.END)
            return
        
        # 文字預覽（包含遊戲引擎標準驗證）
        self.preview_text.delete(1.0, tk.END)
        validation_errors = []
        
        for i, file_path in enumerate(files_to_process):
            new_name = self.generate_new_filename(file_path, i)
            old_name = os.path.basename(file_path)
            dir_path = os.path.dirname(file_path)
            new_path = safe_join_path(dir_path, new_name)
            
            # 驗證文件名（Character規則使用專用驗證）
            if self.rule_var.get() == "character":
                is_valid, error, parsed = validate_character_filename(new_name)
                if is_valid:
                    validation_status = "✓"
                    # 顯示解析的詳細信息
                    self.preview_text.insert(tk.END, f"原檔名: {old_name}\n")
                    self.preview_text.insert(tk.END, f"新檔名: {new_name} {validation_status}\n", "success")
                    self.preview_text.insert(tk.END, 
                        f"  角色編號: {parsed['char_id']}, 類型: {parsed['char_type']}, "
                        f"索引: {parsed['char_index']}, 擴展名: {parsed['ext']}\n")
                else:
                    validation_status = "✗"
                    self.preview_text.insert(tk.END, f"原檔名: {old_name}\n")
                    self.preview_text.insert(tk.END, f"新檔名: {new_name} {validation_status}\n")
                    self.preview_text.insert(tk.END, f"  ⚠️ 格式驗證失敗: {error}\n", "error")
                    validation_errors.append(f"{old_name}: {error}")
            else:
                # 夢想規則使用遊戲引擎標準驗證
                is_valid, error = validate_game_engine_filename(new_name)
                validation_status = "✓" if is_valid else "✗"
                self.preview_text.insert(tk.END, f"原檔名: {old_name}\n")
                self.preview_text.insert(tk.END, f"新檔名: {new_name} {validation_status}\n")
                if not is_valid:
                    self.preview_text.insert(tk.END, f"  ⚠️ 驗證失敗: {error}\n", "error")
                    validation_errors.append(f"{old_name}: {error}")
            
            self.preview_text.insert(tk.END, f"完整路徑: {new_path}\n")
            self.preview_text.insert(tk.END, "-" * 60 + "\n")
    
    def on_only_selected_change(self):
        """當"僅處理選中項"選項改變時，刷新預覽"""
        # 如果當前有選中的檔案，更新預覽
        selected_indices = self.file_listbox.curselection()
        if selected_indices:
            selected_index = selected_indices[0]
            if 0 <= selected_index < len(self.selected_files):
                file_path = self.selected_files[selected_index]
                # 如果啟用了"僅處理選中項"，使用在處理列表中的索引
                if self.only_selected_var.get():
                    files_to_process = self.get_files_to_process()
                    if file_path in files_to_process:
                        process_index = files_to_process.index(file_path)
                        self.show_single_file_preview(file_path, process_index)
                    else:
                        # 如果文件不在處理列表中，使用原始索引
                        self.show_single_file_preview(file_path, selected_index)
                else:
                    self.show_single_file_preview(file_path, selected_index)
        # 同時刷新文字預覽
        self.update_text_preview()
    
    def preview_rename(self):
        """預覽重新命名結果"""
        files_to_process = self.get_files_to_process()
        if not files_to_process:
            if self.only_selected_var.get():
                messagebox.showwarning("警告", "請先選擇要處理的檔案！")
            else:
                messagebox.showwarning("警告", "請先選擇檔案！")
            return
        
        # 更新文字預覽
        self.update_text_preview()
        
        # 如果當前有選中的檔案，更新圖片預覽
        selected_indices = self.file_listbox.curselection()
        if selected_indices:
            selected_index = selected_indices[0]
            if 0 <= selected_index < len(self.selected_files):
                file_path = self.selected_files[selected_index]
                # 計算在處理列表中的索引
                files_to_process = self.get_files_to_process()
                if file_path in files_to_process:
                    process_index = files_to_process.index(file_path)
                    self.show_single_file_preview(file_path, process_index)
                else:
                    self.show_single_file_preview(file_path, selected_index)
    
    def handle_rename_conflict(self, old_path, new_path):
        """處理重新命名衝突，讓用戶選擇"""
        old_name = os.path.basename(old_path)
        new_name = os.path.basename(new_path)
        
        result = messagebox.askyesnocancel(
            "檔案衝突",
            f"目標檔案已存在：\n{new_name}\n\n"
            f"原檔案：{old_name}\n\n"
            f"選擇操作：\n"
            f"「是」- 覆蓋現有檔案\n"
            f"「否」- 跳過此檔案\n"
            f"「取消」- 取消所有操作"
        )
        
        if result is True:  # 覆蓋
            try:
                # 驗證路徑
                is_valid, error = validate_file_path(old_path)
                if not is_valid:
                    messagebox.showerror("錯誤", f"原始路徑無效: {error}")
                    return "error"
                
                is_valid, error = validate_file_path(new_path)
                if not is_valid:
                    messagebox.showerror("錯誤", f"目標路徑無效: {error}")
                    return "error"
                
                # 檢查原始檔案是否存在
                if not os.path.exists(old_path):
                    messagebox.showerror("錯誤", "原始檔案不存在")
                    return "error"
                
                # 使用安全的重命名（safe_rename 內部會處理衝突）
                # 注意：safe_rename 會檢查目標文件是否存在，這裡不需要單獨刪除
                # 避免競態條件：在檢查和刪除之間，文件可能被修改
                success, error_msg = safe_rename(old_path, new_path)
                if success:
                    return "success"
                else:
                    messagebox.showerror("錯誤", f"覆蓋失敗：{error_msg or '未知錯誤'}")
                    return "error"
            except Exception as e:
                messagebox.showerror("錯誤", f"覆蓋失敗：{str(e)}")
                return "error"
        elif result is False:  # 跳過
            return "skip"
        else:  # 取消
            return "cancel"
    
    def execute_rename(self):
        """執行重新命名"""
        files_to_process = self.get_files_to_process()
        if not files_to_process:
            if self.only_selected_var.get():
                messagebox.showwarning("警告", "請先選擇要處理的檔案！")
            else:
                messagebox.showwarning("警告", "請先選擇檔案！")
            return
        
        # 先預覽，確認無誤
        rename_list = []
        conflicts = []
        errors = []  # 預先定義errors列表
        
        for i, file_path in enumerate(files_to_process):
            try:
                # 驗證原始檔案路徑
                is_valid, error = validate_file_path(file_path)
                if not is_valid:
                    errors.append(f"{os.path.basename(file_path)}: {error}")
                    continue
                
                # 檢查檔案是否存在
                if not os.path.exists(file_path):
                    errors.append(f"{os.path.basename(file_path)}: 檔案不存在")
                    continue
                
                # 檢查是否為檔案（不是目錄）
                if not os.path.isfile(file_path):
                    errors.append(f"{os.path.basename(file_path)}: 不是檔案")
                    continue
                
                new_name = self.generate_new_filename(file_path, i)
                dir_path = os.path.dirname(file_path)
                
                # 使用安全的路徑連接
                new_path = safe_join_path(dir_path, new_name)
                
                # 檢查新檔名是否已存在
                if os.path.exists(new_path) and os.path.abspath(new_path) != os.path.abspath(file_path):
                    conflicts.append((file_path, new_path))
                else:
                    rename_list.append((file_path, new_path))
            except Exception as e:
                errors.append(f"{os.path.basename(file_path)}: {str(e)}")
        
        # 如果有錯誤，顯示錯誤訊息
        if errors:
            error_details = "\n".join(errors[:5])
            if len(errors) > 5:
                error_details += f"\n...還有 {len(errors)-5} 個錯誤"
            messagebox.showwarning("警告", f"以下檔案無法處理：\n{error_details}")
        
        # 如果有衝突，先處理衝突
        if conflicts:
            for old_path, new_path in conflicts:
                result = self.handle_rename_conflict(old_path, new_path)
                if result == "cancel":
                    return
                elif result == "success":
                    rename_list.append((old_path, new_path))
                # skip的情況不加入列表
        
        if not rename_list:
            messagebox.showinfo("提示", "沒有需要重新命名的檔案")
            return
        
        # 確認對話框
        result = messagebox.askyesno("確認", f"確定要重新命名 {len(rename_list)} 個檔案嗎？")
        if not result:
            return
        
        # 建立進度視窗
        progress_window = tk.Toplevel(self.root)
        progress_window.title("正在重新命名...")
        progress_window.geometry("400x100")
        progress_window.transient(self.root)
        progress_window.grab_set()
        
        progress_label = ttk.Label(progress_window, text="正在處理...")
        progress_label.pack(pady=10)
        
        progress_bar = ttk.Progressbar(progress_window, length=350, mode='determinate')
        progress_bar.pack(pady=10)
        progress_bar['maximum'] = len(rename_list)
        
        # 執行重新命名
        success_count = 0
        error_count = 0
        errors = []
        
        for i, (old_path, new_path) in enumerate(rename_list):
            try:
                # 使用安全的重命名函數
                success, error_msg = safe_rename(old_path, new_path)
                
                if success:
                    success_count += 1
                    
                    # 記錄歷史
                    self.rename_history.append({
                        'old_path': old_path,
                        'new_path': new_path,
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    # 更新歷史管理器
                    if self.history_manager:
                        self.history_manager.add_record(old_path, new_path)
                else:
                    error_count += 1
                    errors.append(f"{os.path.basename(old_path)}: {error_msg or '重命名失敗'}")
                
            except Exception as e:
                error_count += 1
                errors.append(f"{os.path.basename(old_path)}: {str(e)}")
            
            # 更新進度條
            progress_bar['value'] = i + 1
            progress_label.config(text=f"正在處理 {i+1}/{len(rename_list)}... ({os.path.basename(old_path)})")
            progress_window.update()
            # 更新狀態欄
            if hasattr(self, 'status_label'):
                self.status_label.config(text=f"正在處理: {os.path.basename(old_path)}")
        
        # 關閉進度視窗
        progress_window.destroy()
        
        # 顯示結果
        message = f"重新命名完成！\n成功: {success_count} 個\n失敗: {error_count} 個"
        if error_count > 0:
            error_details = "\n".join(errors[:5])  # 只顯示前5個錯誤
            if len(errors) > 5:
                error_details += f"\n...還有 {len(errors)-5} 個錯誤"
            messagebox.showwarning("完成", f"{message}\n\n錯誤詳情：\n{error_details}")
        else:
            messagebox.showinfo("完成", message)
        
        # 更新狀態欄
        self.update_status(f"重新命名完成：成功 {success_count} 個，失敗 {error_count} 個")
        
        # 清空列表
        self.clear_files()
    
    def setup_20_characters_mode(self):
        """定位20個人物模式"""
        if len(self.selected_files) < 20:
            result = messagebox.askyesno(
                "定位20個人物模式",
                f"目前只有 {len(self.selected_files)} 個檔案，少於20個。\n"
                f"是否繼續設定？"
            )
            if not result:
                return
        
        # 創建新視窗設定20個人物
        setup_window = tk.Toplevel(self.root)
        setup_window.title("定位20個人物模式")
        setup_window.geometry("600x500")
        
        ttk.Label(setup_window, text="為每個檔案設定角色編號（01-20）", 
                 font=("Arial", 12, "bold")).pack(pady=10)
        
        # 創建滾動框架
        canvas = tk.Canvas(setup_window)
        scrollbar = ttk.Scrollbar(setup_window, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 儲存每個檔案的設定
        char_settings = {}
        
        # 為每個檔案創建輸入框
        for i, file_path in enumerate(self.selected_files[:20]):
            frame = ttk.Frame(scrollable_frame)
            frame.pack(fill=tk.X, padx=10, pady=5)
            
            file_name = os.path.basename(file_path)
            ttk.Label(frame, text=f"{i+1:02d}. {file_name[:40]}...", width=40).pack(side=tk.LEFT, padx=5)
            
            char_id_var = tk.StringVar(value=f"{i+1:02d}")
            entry = ttk.Entry(frame, textvariable=char_id_var, width=5)
            entry.pack(side=tk.LEFT, padx=5)
            
            char_settings[file_path] = char_id_var
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        def apply_settings():
            """應用設定"""
            for file_path, char_id_var in char_settings.items():
                char_id = char_id_var.get().strip()
                if char_id:
                    try:
                        # 驗證輸入是否為有效數字
                        char_id_int = int(char_id)
                        if 1 <= char_id_int <= 99:
                            self.file_char_id_map[file_path] = char_id
                        else:
                            messagebox.showwarning("警告", f"角色編號 {char_id} 超出範圍（1-99），已跳過")
                    except ValueError:
                        messagebox.showwarning("警告", f"角色編號 {char_id} 不是有效數字，已跳過")
            
            messagebox.showinfo("完成", f"已為 {len(self.file_char_id_map)} 個檔案設定角色編號！\n請在預覽中確認結果。")
            setup_window.destroy()
        
        ttk.Button(setup_window, text="應用設定", command=apply_settings).pack(pady=10)
    
    def batch_set_char_id(self):
        """批量設定角色編號"""
        selected_indices = self.file_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("警告", "請先選擇要設定的檔案！")
            return
        
        # 創建批量設定視窗
        batch_window = tk.Toplevel(self.root)
        batch_window.title("批量設定角色編號")
        batch_window.geometry("400x200")
        batch_window.transient(self.root)
        batch_window.grab_set()
        
        ttk.Label(batch_window, text=f"為 {len(selected_indices)} 個選中的檔案設定角色編號", 
                 font=("Arial", 10, "bold")).pack(pady=10)
        
        input_frame = ttk.Frame(batch_window)
        input_frame.pack(pady=10)
        
        ttk.Label(input_frame, text="角色編號:").pack(side=tk.LEFT, padx=5)
        batch_char_id_var = tk.StringVar(value="01")
        batch_char_id_combo = ttk.Combobox(input_frame, textvariable=batch_char_id_var, style='Modern.TCombobox', 
                                          values=[f"{i:02d}" for i in range(1, 100)], 
                                          state="readonly", width=10)
        batch_char_id_combo.pack(side=tk.LEFT, padx=5)
        
        def apply_batch_settings():
            char_id = batch_char_id_var.get()
            for idx in selected_indices:
                if 0 <= idx < len(self.selected_files):
                    file_path = self.selected_files[idx]
                    self.file_char_id_map[file_path] = char_id
            messagebox.showinfo("完成", f"已為 {len(selected_indices)} 個檔案設定角色編號：{char_id}")
            batch_window.destroy()
            # 刷新預覽
            self.on_index_change()
            self.update_status(f"已批量設定 {len(selected_indices)} 個檔案的角色編號")
        
        button_frame = ttk.Frame(batch_window)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="應用", command=apply_batch_settings).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="取消", command=batch_window.destroy).pack(side=tk.LEFT, padx=5)
    
    def setup_keyboard_shortcuts(self):
        """設定鍵盤快捷鍵"""
        # Ctrl+O: 選擇檔案
        self.root.bind('<Control-o>', lambda e: self.select_files())
        # Ctrl+D: 選擇資料夾
        self.root.bind('<Control-d>', lambda e: self.select_folder())
        # Delete: 刪除選中
        self.root.bind('<Delete>', lambda e: self.remove_selected())
        # Ctrl+F: 搜尋
        self.root.bind('<Control-f>', lambda e: self.focus_search())
        # Ctrl+Z: 撤銷
        self.root.bind('<Control-z>', lambda e: self.undo_rename())
        # Ctrl+R: 預覽重命名
        self.root.bind('<Control-r>', lambda e: self.preview_rename())
        # Ctrl+Enter: 執行重命名
        self.root.bind('<Control-Return>', lambda e: self.execute_rename())
        # Ctrl+T: 切換深色模式
        self.root.bind('<Control-t>', lambda e: self.toggle_dark_mode())
    
    def load_saved_settings(self):
        """載入儲存的設定"""
        if not config_manager:
            return
        
        # 載入命名規則設定
        last_rule = config_manager.get("last_rule", "character")
        if last_rule:
            self.rule_var.set(last_rule)
            self.on_rule_change()
        
        # 載入Character規則設定
        if hasattr(self, 'char_id_var'):
            self.char_id_var.set(config_manager.get("last_char_id", "01"))
            self.char_type_var.set(config_manager.get("last_char_type", "Idle"))
            # 載入索引時，需要更新下拉框顯示值（帶顏色提示）
            saved_index = config_manager.get("last_char_index", "01")
            # 更新下拉框顯示值（帶顏色提示）
            if hasattr(self, 'char_index_combo'):
                index_values = self.char_index_combo['values']
                for val in index_values:
                    if val.startswith(saved_index + " - "):
                        self.char_index_var.set(val)
                        break
                else:
                    # 如果找不到匹配的，使用純數字
                    self.char_index_var.set(saved_index)
            else:
                self.char_index_var.set(saved_index)
            self.color_var.set(config_manager.get("last_color", "00"))
        
        # 載入夢想規則設定
        if hasattr(self, 'theme_var'):
            self.theme_var.set(config_manager.get("last_theme", "Hospital"))
            self.on_theme_change()
            self.dream_index_var.set(config_manager.get("last_dream_index", "01"))
            self.anime_num_var.set(config_manager.get("last_anime_num", "01"))
        
        # 載入最大檔案數限制
        if hasattr(self, 'max_files_var'):
            self.max_files_var.set(config_manager.get("max_files", "0"))
        
        # 載入深色模式
        dark_mode = config_manager.get("dark_mode", False)
        if dark_mode:
            self.toggle_dark_mode()
    
    def save_settings(self):
        """儲存當前設定"""
        if not config_manager:
            return
        
        # 儲存視窗大小和位置
        config_manager.set("window_geometry", self.root.geometry())
        
        # 儲存命名規則設定
        config_manager.set("last_rule", self.rule_var.get())
        
        # 儲存Character規則設定
        if hasattr(self, 'char_id_var'):
            config_manager.set("last_char_id", self.char_id_var.get())
            config_manager.set("last_char_type", self.char_type_var.get())
            # 儲存索引時，只儲存數字部分（不包含顏色提示）
            index_value = self.char_index_var.get()
            if " - " in index_value:
                numeric_index = index_value.split(" - ")[0]
            else:
                numeric_index = index_value
            config_manager.set("last_char_index", numeric_index)
            config_manager.set("last_color", self.color_var.get())
        
        # 儲存夢想規則設定
        if hasattr(self, 'theme_var'):
            config_manager.set("last_theme", self.theme_var.get())
            config_manager.set("last_role", self.role_var.get() if hasattr(self, 'role_var') else "")
            config_manager.set("last_dream_index", self.dream_index_var.get() if hasattr(self, 'dream_index_var') else "01")
            config_manager.set("last_anime_num", self.anime_num_var.get() if hasattr(self, 'anime_num_var') else "01")
        
        # 儲存最大檔案數限制
        if hasattr(self, 'max_files_var'):
            config_manager.set("max_files", self.max_files_var.get())
        
        # 儲存深色模式
        config_manager.set("dark_mode", self.dark_mode)
        
        config_manager.save_config()
    
    def on_closing(self):
        """視窗關閉時的處理（包含資源清理）"""
        try:
            # 清理圖片資源
            if hasattr(self, 'preview_images'):
                for img_id, img in list(self.preview_images.items()):
                    try:
                        del img
                    except:
                        pass
                self.preview_images.clear()
            
            # 保存設定
            self.save_settings()
            
            # 銷毀視窗
            self.root.destroy()
        except Exception:
            # 即使清理失敗，也要關閉視窗
            try:
                self.root.destroy()
            except:
                pass
    
    def undo_rename(self):
        """撤銷最後一次重命名操作"""
        if not self.rename_history:
            messagebox.showinfo("提示", "沒有可撤銷的操作")
            return
        
        # 獲取最後一次重命名記錄
        last_rename = self.rename_history.pop()
        old_path = last_rename['new_path']
        new_path = last_rename['old_path']
        
        try:
            # 使用安全的重命名函數
            success, error_msg = safe_rename(old_path, new_path)
            
            if success:
                self.update_status(f"已撤銷重命名：{os.path.basename(old_path)} -> {os.path.basename(new_path)}")
                messagebox.showinfo("成功", f"已撤銷重命名：\n{os.path.basename(old_path)} -> {os.path.basename(new_path)}")
                # 更新歷史記錄
                if self.history_manager:
                    self.history_manager.add_record(old_path, new_path)
                # 重新整理檔案列表
                self.update_file_list()
            else:
                error_msg = error_msg or "撤銷失敗"
                self.update_status(f"撤銷失敗：{error_msg}")
                messagebox.showerror("錯誤", f"撤銷失敗：{error_msg}")
        except Exception as e:
            self.update_status(f"撤銷失敗：{str(e)}")
            messagebox.showerror("錯誤", f"撤銷失敗：{str(e)}")
    
    def focus_search(self):
        """聚焦到搜尋框"""
        if hasattr(self, 'search_entry'):
            self.search_entry.focus()
    
    def apply_modern_style(self):
        """應用現代化樣式"""
        if not self.theme:
            return
        
        theme_colors = self.theme.get_theme(self.dark_mode)
        
        # 設置主視窗背景
        self.root.configure(bg=theme_colors['bg_secondary'])
        
        # 配置ttk樣式
        style = ttk.Style()
        
        # 配置主題
        style.theme_use('clam')
        
        # 配置LabelFrame樣式（卡片效果）
        style.configure('Card.TLabelframe',
                      background=theme_colors['card_bg'],
                      borderwidth=1,
                      relief='flat',
                      bordercolor=theme_colors['divider'])
        style.configure('Card.TLabelframe.Label',
                      background=theme_colors['card_bg'],
                      foreground=theme_colors['text_primary'],
                      font=self.theme.get_font('subheading'))
        
        # 配置按鈕樣式
        style.configure('Primary.TButton',
                      background=theme_colors['button_bg'],
                      foreground=theme_colors['button_text'],
                      borderwidth=0,
                      focuscolor='none',
                      padding=(16, 8),
                      font=self.theme.get_font('button'))
        style.map('Primary.TButton',
                 background=[('active', theme_colors['button_hover']),
                           ('pressed', theme_colors['primary_dark'])])
        
        style.configure('Secondary.TButton',
                      background=theme_colors['button_secondary_bg'],
                      foreground=theme_colors['button_secondary_text'],
                      borderwidth=0,
                      focuscolor='none',
                      padding=(12, 6),
                      font=self.theme.get_font('body'))
        style.map('Secondary.TButton',
                 background=[('active', theme_colors['button_secondary_hover'])])
        
        # 配置Entry樣式
        style.configure('Modern.TEntry',
                      fieldbackground=theme_colors['bg_primary'],
                      foreground=theme_colors['text_primary'],
                      borderwidth=1,
                      relief='solid',
                      padding=8,
                      bordercolor=theme_colors['border'])
        style.map('Modern.TEntry',
                 bordercolor=[('focus', theme_colors['primary'])])
        
        # 配置Combobox樣式
        style.configure('Modern.TCombobox',
                      fieldbackground=theme_colors['bg_primary'],
                      foreground=theme_colors['text_primary'],
                      borderwidth=1,
                      relief='solid',
                      padding=6,
                      bordercolor=theme_colors['border'],
                      arrowcolor=theme_colors['text_primary'])
        style.map('Modern.TCombobox',
                 bordercolor=[('focus', theme_colors['primary'])],
                 fieldbackground=[('readonly', theme_colors['bg_primary'])])
    
    def create_modern_card(self, parent, title, padding=16):
        """創建現代化卡片容器"""
        card = ttk.LabelFrame(parent, text=title, padding=padding, style='Card.TLabelframe')
        return card
    
    def create_modern_button(self, parent, text, command, style_type='primary', **kwargs):
        """創建現代化按鈕"""
        style_name = 'Primary.TButton' if style_type == 'primary' else 'Secondary.TButton'
        btn = ttk.Button(parent, text=text, command=command, style=style_name, **kwargs)
        return btn
    
    def toggle_dark_mode(self):
        """切換深色模式"""
        self.dark_mode = not self.dark_mode
        
        # 重新應用樣式
        self.apply_modern_style()
        
        # 更新所有UI元素
        if not self.theme:
            return
        
        theme_colors = self.theme.get_theme(self.dark_mode)
        
        # 更新主視窗背景
        self.root.configure(bg=theme_colors['bg_secondary'])
        
        # 更新Listbox樣式
        if hasattr(self, 'file_listbox'):
            self.file_listbox.configure(
                bg=theme_colors['bg_primary'],
                fg=theme_colors['text_primary'],
                selectbackground=theme_colors['primary'],
                selectforeground=theme_colors['button_text'],
                font=self.theme.get_font('body')
            )
        
        # 更新Text元件樣式
        if hasattr(self, 'preview_text'):
            self.preview_text.configure(
                bg=theme_colors['bg_primary'],
                fg=theme_colors['text_primary'],
                insertbackground=theme_colors['primary']
            )
        
        # 更新Canvas背景
        if hasattr(self, 'preview_canvas'):
            self.preview_canvas.configure(bg=theme_colors['bg_primary'])
        
        # 儲存設定
        if config_manager:
            config_manager.set("dark_mode", self.dark_mode)
            config_manager.save_config()
        
        # 更新狀態
        self.update_status(f"已切換到{'深色' if self.dark_mode else '淺色'}模式")
    
    def create_tooltip(self, widget, text):
        """建立工具提示"""
        def on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            label = tk.Label(tooltip, text=text, background="#ffffe0", 
                           relief=tk.SOLID, borderwidth=1, font=("Arial", 9))
            label.pack()
            widget.tooltip = tooltip
        
        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip
        
        widget.bind('<Enter>', on_enter)
        widget.bind('<Leave>', on_leave)


def main():
    if HAS_DND:
        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()
    app = FileRenamerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
