"""
檔案重新命名工具 v2.0
優化版本 - 模組化、功能增強、使用體驗改進
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import sys

# 導入自定義模組
from config import *
from naming_rules import NamingRuleEngine
from file_operations import FileOperationManager
from settings_manager import SettingsManager
from ui_helpers import ToolTip, ProgressDialog, SearchBar, StatusBar, center_window

# 嘗試導入可選依賴
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    HAS_DND = True
except ImportError:
    HAS_DND = False
    print("提示：未安裝tkinterdnd2，拖放功能將不可用。可使用 pip install tkinterdnd2 安裝")

try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    print("提示：未安裝Pillow，圖片預覽功能將受限。可使用 pip install Pillow 安裝")


class FileRenamerGUI:
    """檔案重新命名工具 GUI"""

    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)

        # 初始化管理器
        self.settings_manager = SettingsManager()
        self.settings_manager.load_settings()

        self.naming_engine = NamingRuleEngine()
        self.file_manager = FileOperationManager()
        self.file_manager.load_history()

        # 載入命名規則設定
        naming_rule_settings = self.settings_manager.get_naming_rule()
        if naming_rule_settings:
            self.naming_engine.load_params_dict(naming_rule_settings)

        # UI 狀態變數
        self.preview_images = {}
        self.filtered_indices = []  # 搜尋過濾後的索引
        self.current_theme = self.settings_manager.get("window.theme", "light")

        # 設置視窗大小和位置
        saved_geometry = self.settings_manager.get("window.geometry", WINDOW_SIZE)
        self.root.geometry(saved_geometry)

        # 設置 UI
        self.setup_ui()
        self.apply_theme(self.current_theme)
        self.setup_shortcuts()
        self.setup_drag_drop()

        # 綁定視窗關閉事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # 更新狀態列
        self.update_status()

    def setup_ui(self):
        """設置使用者介面"""
        # ========== 選單列 ==========
        self.create_menu_bar()

        # ========== 工具列 ==========
        toolbar = ttk.Frame(self.root)
        toolbar.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(toolbar, text="📁 選擇檔案 (Ctrl+O)",
                  command=self.select_files).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="📂 選擇資料夾 (Ctrl+Shift+O)",
                  command=self.select_folder).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🗑️ 清空列表 (Ctrl+L)",
                  command=self.clear_files).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="↩️ 撤銷重命名 (Ctrl+Z)",
                  command=self.undo_rename).pack(side=tk.LEFT, padx=2)

        # 深色模式切換按鈕
        self.theme_button = ttk.Button(toolbar, text="🌙 深色模式 (Ctrl+T)",
                                       command=self.toggle_theme)
        self.theme_button.pack(side=tk.RIGHT, padx=2)

        # ========== 檔案選擇區域 ==========
        file_frame = ttk.LabelFrame(self.root, text="檔案管理", padding=10)
        file_frame.pack(fill=tk.X, padx=10, pady=5)

        # 控制列
        control_row = ttk.Frame(file_frame)
        control_row.pack(fill=tk.X, pady=5)

        ttk.Label(control_row, text="最大選擇數量（0=無限制）:").pack(side=tk.LEFT, padx=5)
        self.max_files_var = tk.StringVar(value=str(self.settings_manager.get("max_files", 0)))
        max_files_entry = ttk.Entry(control_row, textvariable=self.max_files_var, width=10)
        max_files_entry.pack(side=tk.LEFT, padx=5)
        ToolTip(max_files_entry, "設定最多可選擇的檔案數量，0 表示無限制")

        ttk.Label(control_row, text="當前數量:").pack(side=tk.LEFT, padx=5)
        self.current_count_label = ttk.Label(control_row, text="0",
                                            foreground="blue", font=("Arial", 10, "bold"))
        self.current_count_label.pack(side=tk.LEFT, padx=5)

        ttk.Label(control_row, text="|").pack(side=tk.LEFT, padx=10)

        ttk.Button(control_row, text="🎯 定位20個人物模式",
                  command=self.setup_20_characters_mode).pack(side=tk.LEFT, padx=5)

        # 資料夾路徑輸入
        path_row = ttk.Frame(file_frame)
        path_row.pack(fill=tk.X, pady=5)

        ttk.Label(path_row, text="資料夾路徑:").pack(side=tk.LEFT, padx=5)
        self.folder_path_var = tk.StringVar(value=self.settings_manager.get("last_folder", ""))
        folder_path_entry = ttk.Entry(path_row, textvariable=self.folder_path_var, width=50)
        folder_path_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(path_row, text="導入", command=self.import_folder_path).pack(side=tk.LEFT, padx=5)
        ttk.Button(path_row, text="瀏覽", command=self.browse_folder).pack(side=tk.LEFT, padx=5)

        # ========== 搜尋列 ==========
        self.search_bar = SearchBar(file_frame, on_search=self.on_search)
        self.search_bar.pack(fill=tk.X, pady=5)
        ToolTip(self.search_bar, "輸入關鍵字搜尋檔案（支援檔名過濾）")

        # ========== 檔案列表 ==========
        list_frame = ttk.LabelFrame(self.root, text="已選擇的檔案（可多選調整順序）", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 列表控制按鈕
        list_control_frame = ttk.Frame(list_frame)
        list_control_frame.pack(fill=tk.X, pady=5)

        btn_move_up = ttk.Button(list_control_frame, text="⬆ 上移", command=self.move_up)
        btn_move_up.pack(side=tk.LEFT, padx=2)
        ToolTip(btn_move_up, "將選中的檔案向上移動 (Ctrl+↑)")

        btn_move_down = ttk.Button(list_control_frame, text="⬇ 下移", command=self.move_down)
        btn_move_down.pack(side=tk.LEFT, padx=2)
        ToolTip(btn_move_down, "將選中的檔案向下移動 (Ctrl+↓)")

        btn_remove = ttk.Button(list_control_frame, text="❌ 刪除選中", command=self.remove_selected)
        btn_remove.pack(side=tk.LEFT, padx=2)
        ToolTip(btn_remove, "刪除選中的檔案 (Delete)")

        # 僅處理選中項選項
        self.only_selected_var = tk.BooleanVar(value=False)
        chk_only_selected = ttk.Checkbutton(
            list_control_frame,
            text="僅處理選中的檔案（多選時按順序自動排序命名）",
            variable=self.only_selected_var,
            command=self.on_only_selected_change
        )
        chk_only_selected.pack(side=tk.LEFT, padx=10)
        ToolTip(chk_only_selected, "勾選後只會對選中的檔案進行重命名")

        # 列表框架
        list_container = ttk.Frame(list_frame)
        list_container.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(list_container)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.file_listbox = tk.Listbox(list_container, yscrollcommand=scrollbar.set,
                                       selectmode=tk.EXTENDED, height=LISTBOX_HEIGHT)
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.file_listbox.yview)

        # 綁定選擇事件
        self.file_listbox.bind('<<ListboxSelect>>', self.on_file_select)

        # ========== 命名規則區域 ==========
        rule_frame = ttk.LabelFrame(self.root, text="命名規則", padding=10)
        rule_frame.pack(fill=tk.X, padx=10, pady=5)

        self.rule_var = tk.StringVar(value=self.naming_engine.rule_type)
        ttk.Radiobutton(rule_frame, text="Character規則（輸出給客戶端）",
                       variable=self.rule_var, value="character",
                       command=self.on_rule_change).pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(rule_frame, text="夢想命名規則（內部規則，供員工瀏覽）",
                       variable=self.rule_var, value="dream",
                       command=self.on_rule_change).pack(side=tk.LEFT, padx=10)

        # ========== Character 規則輸入區域 ==========
        self.create_character_rule_ui()

        # ========== 夢想命名規則輸入區域 ==========
        self.create_dream_rule_ui()

        # ========== 預覽區域 ==========
        self.create_preview_ui()

        # ========== 操作按鈕 ==========
        button_frame = ttk.Frame(self.root)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        btn_preview = ttk.Button(button_frame, text="👁️ 預覽重新命名 (Ctrl+P)",
                                command=self.preview_rename)
        btn_preview.pack(side=tk.LEFT, padx=5)
        ToolTip(btn_preview, "預覽重命名結果，不會實際修改檔案")

        btn_execute = ttk.Button(button_frame, text="✅ 執行重新命名 (Ctrl+Enter)",
                                command=self.execute_rename)
        btn_execute.pack(side=tk.LEFT, padx=5)
        ToolTip(btn_execute, "執行批次重新命名操作")

        # ========== 狀態列 ==========
        self.status_bar = StatusBar(self.root)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # 拖放提示
        if HAS_DND:
            drop_hint = ttk.Label(self.root, text="💡 提示：可以直接拖放檔案或資料夾到此視窗",
                                 foreground="blue", font=("Arial", 9))
            drop_hint.pack(pady=2)

        # 初始顯示
        self.on_rule_change()

    def create_menu_bar(self):
        """創建選單列"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # 檔案選單
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="檔案", menu=file_menu)
        file_menu.add_command(label="開啟檔案... (Ctrl+O)", command=self.select_files)
        file_menu.add_command(label="開啟資料夾... (Ctrl+Shift+O)", command=self.select_folder)
        file_menu.add_separator()
        file_menu.add_command(label="儲存設定 (Ctrl+S)", command=self.save_settings)
        file_menu.add_separator()
        file_menu.add_command(label="結束", command=self.on_closing)

        # 編輯選單
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="編輯", menu=edit_menu)
        edit_menu.add_command(label="撤銷重命名 (Ctrl+Z)", command=self.undo_rename)
        edit_menu.add_command(label="清空列表 (Ctrl+L)", command=self.clear_files)
        edit_menu.add_separator()
        edit_menu.add_command(label="搜尋 (Ctrl+F)", command=lambda: self.search_bar.focus())

        # 檢視選單
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="檢視", menu=view_menu)
        view_menu.add_command(label="切換深色模式 (Ctrl+T)", command=self.toggle_theme)
        view_menu.add_separator()
        view_menu.add_command(label="預覽 (Ctrl+P)", command=self.preview_rename)

        # 工具選單
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="工具", menu=tools_menu)
        tools_menu.add_command(label="定位20個人物模式", command=self.setup_20_characters_mode)

        # 說明選單
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="說明", menu=help_menu)
        help_menu.add_command(label="快捷鍵說明 (F1)", command=self.show_shortcuts_help)
        help_menu.add_command(label="關於", command=self.show_about)

    def create_character_rule_ui(self):
        """創建 Character 規則 UI"""
        self.char_frame = ttk.LabelFrame(self.root, text="Character規則參數", padding=10)

        # 快速類型選擇
        quick_type_frame = ttk.Frame(self.char_frame)
        quick_type_frame.pack(fill=tk.X, pady=5)

        ttk.Label(quick_type_frame, text="一鍵選擇類型：",
                 font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)

        for char_type in CHARACTER_TYPES:
            btn = ttk.Button(quick_type_frame, text=f"全部設為 {char_type}",
                           command=lambda t=char_type: self.set_all_type(t))
            btn.pack(side=tk.LEFT, padx=5)
            ToolTip(btn, f"將所有檔案的類型設為 {char_type}")

        # 參數輸入
        char_input_frame = ttk.Frame(self.char_frame)
        char_input_frame.pack(fill=tk.X, pady=5)

        # 角色編號
        ttk.Label(char_input_frame, text="角色編號:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.char_id_var = tk.StringVar(value=self.naming_engine.char_params["char_id"])
        char_id_combo = ttk.Combobox(char_input_frame, textvariable=self.char_id_var,
                                    values=[f"{i:02d}" for i in range(1, 100)],
                                    state="readonly", width=10)
        char_id_combo.grid(row=0, column=1, padx=5, pady=5)
        char_id_combo.bind("<<ComboboxSelected>>", self.on_param_change)
        ToolTip(char_id_combo, "設定角色編號（01-99）")

        # 類型
        ttk.Label(char_input_frame, text="類型:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.char_type_var = tk.StringVar(value=self.naming_engine.char_params["char_type"])
        char_type_combo = ttk.Combobox(char_input_frame, textvariable=self.char_type_var,
                                      values=CHARACTER_TYPES, state="readonly", width=15)
        char_type_combo.grid(row=0, column=3, padx=5, pady=5)
        char_type_combo.bind("<<ComboboxSelected>>", self.on_char_type_change)
        ToolTip(char_type_combo, "Idle=預備演出, Intro=開獎前演出, Open=開獎演出")

        # 索引
        ttk.Label(char_input_frame, text="索引:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.char_index_var = tk.StringVar(value=self.naming_engine.char_params["char_index"])
        char_index_combo = ttk.Combobox(char_input_frame, textvariable=self.char_index_var,
                                       values=[f"{i:02d}" for i in range(1, 21)],
                                       state="readonly", width=10)
        char_index_combo.grid(row=1, column=1, padx=5, pady=5)
        char_index_combo.bind("<<ComboboxSelected>>", self.on_param_change)
        ToolTip(char_index_combo, "設定索引編號（建議不超過20）")

        # Open 類型的顏色選擇
        self.color_frame = ttk.Frame(self.char_frame)

        ttk.Label(self.color_frame, text="開獎演出顏色索引:").pack(side=tk.LEFT, padx=5)
        self.color_var = tk.StringVar(value=self.naming_engine.char_params["color"])

        for code, (chinese, english) in COLOR_MAP.items():
            rb = ttk.Radiobutton(self.color_frame, text=f"{code} - {chinese}",
                               variable=self.color_var, value=code,
                               command=self.on_param_change)
            rb.pack(side=tk.LEFT, padx=5)
            ToolTip(rb, f"顏色代碼: {code} ({chinese}/{english})")

    def create_dream_rule_ui(self):
        """創建夢想命名規則 UI"""
        self.dream_frame = ttk.LabelFrame(self.root, text="夢想命名規則參數", padding=10)

        dream_input_frame = ttk.Frame(self.dream_frame)
        dream_input_frame.pack(fill=tk.X)

        # 主題
        ttk.Label(dream_input_frame, text="主題:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.theme_var = tk.StringVar(value=self.naming_engine.dream_params["theme"])
        theme_combo = ttk.Combobox(dream_input_frame, textvariable=self.theme_var,
                                  values=list(THEME_OPTIONS.keys()),
                                  state="readonly", width=15)
        theme_combo.grid(row=0, column=1, padx=5, pady=5)
        theme_combo.bind("<<ComboboxSelected>>", self.on_theme_change)

        # 角色類型
        ttk.Label(dream_input_frame, text="角色類型:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.role_var = tk.StringVar(value=self.naming_engine.dream_params["role"])
        self.role_combo = ttk.Combobox(dream_input_frame, textvariable=self.role_var,
                                       state="readonly", width=20)
        self.role_combo.grid(row=0, column=3, padx=5, pady=5)
        self.role_combo.bind("<<ComboboxSelected>>", self.on_param_change)

        # 索引
        ttk.Label(dream_input_frame, text="索引:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.dream_index_var = tk.StringVar(value=self.naming_engine.dream_params["index"])
        dream_index_combo = ttk.Combobox(dream_input_frame, textvariable=self.dream_index_var,
                                        values=[f"{i:02d}" for i in range(1, 21)],
                                        state="readonly", width=10)
        dream_index_combo.grid(row=1, column=1, padx=5, pady=5)
        dream_index_combo.bind("<<ComboboxSelected>>", self.on_param_change)

        # Anime 主題編號
        self.anime_frame = ttk.Frame(self.dream_frame)

        ttk.Label(self.anime_frame, text="動漫主題編號 (A_編號):").pack(side=tk.LEFT, padx=5)
        self.anime_num_var = tk.StringVar(value=self.naming_engine.dream_params["anime_num"])
        anime_num_combo = ttk.Combobox(self.anime_frame, textvariable=self.anime_num_var,
                                       values=[f"{i:02d}" for i in range(1, 21)],
                                       state="readonly", width=10)
        anime_num_combo.pack(side=tk.LEFT, padx=5)
        anime_num_combo.bind("<<ComboboxSelected>>", self.on_param_change)

        # 初始化主題選項
        self.on_theme_change()

    def create_preview_ui(self):
        """創建預覽區域 UI"""
        preview_frame = ttk.LabelFrame(self.root, text="預覽", padding=10)
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 創建 Notebook 切換
        self.preview_notebook = ttk.Notebook(preview_frame)
        self.preview_notebook.pack(fill=tk.BOTH, expand=True)

        # 文字預覽
        text_preview_frame = ttk.Frame(self.preview_notebook)
        self.preview_notebook.add(text_preview_frame, text="📄 文字預覽")

        preview_scrollbar = ttk.Scrollbar(text_preview_frame)
        preview_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.preview_text = tk.Text(text_preview_frame, yscrollcommand=preview_scrollbar.set,
                                    height=TEXT_PREVIEW_HEIGHT)
        self.preview_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        preview_scrollbar.config(command=self.preview_text.yview)

        # 圖片預覽
        image_preview_frame = ttk.Frame(self.preview_notebook)
        self.preview_notebook.add(image_preview_frame, text="🖼️ 圖片/影片預覽")

        self.preview_hint_label = ttk.Label(image_preview_frame,
                                           text="💡 請在檔案列表中點選檔案以顯示預覽",
                                           font=("Arial", 10), foreground="gray")
        self.preview_hint_label.pack(pady=20)

        image_scrollbar = ttk.Scrollbar(image_preview_frame, orient=tk.VERTICAL)
        image_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.preview_canvas = tk.Canvas(image_preview_frame, yscrollcommand=image_scrollbar.set)
        self.preview_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        image_scrollbar.config(command=self.preview_canvas.yview)

    def setup_shortcuts(self):
        """設置鍵盤快捷鍵"""
        self.root.bind(SHORTCUTS["open_files"], lambda e: self.select_files())
        self.root.bind(SHORTCUTS["open_folder"], lambda e: self.select_folder())
        self.root.bind(SHORTCUTS["clear"], lambda e: self.clear_files())
        self.root.bind(SHORTCUTS["delete"], lambda e: self.remove_selected())
        self.root.bind(SHORTCUTS["preview"], lambda e: self.preview_rename())
        self.root.bind(SHORTCUTS["execute"], lambda e: self.execute_rename())
        self.root.bind(SHORTCUTS["move_up"], lambda e: self.move_up())
        self.root.bind(SHORTCUTS["move_down"], lambda e: self.move_down())
        self.root.bind(SHORTCUTS["undo"], lambda e: self.undo_rename())
        self.root.bind(SHORTCUTS["search"], lambda e: self.search_bar.focus())
        self.root.bind(SHORTCUTS["toggle_theme"], lambda e: self.toggle_theme())
        self.root.bind(SHORTCUTS["save_settings"], lambda e: self.save_settings())
        self.root.bind(SHORTCUTS["help"], lambda e: self.show_shortcuts_help())

    def setup_drag_drop(self):
        """設置拖放功能"""
        if HAS_DND:
            self.root.drop_target_register(DND_FILES)
            self.root.dnd_bind('<<Drop>>', self.on_drop)

            self.file_listbox.drop_target_register(DND_FILES)
            self.file_listbox.dnd_bind('<<Drop>>', self.on_drop)

    # ========== 檔案操作方法 ==========

    def select_files(self):
        """選擇檔案"""
        initial_dir = self.settings_manager.get("last_folder", "")
        files = filedialog.askopenfilenames(
            title="選擇檔案",
            initialdir=initial_dir,
            filetypes=[
                ("支援的檔案", "*.mp4;*.jpg;*.png;*.jpeg"),
                ("影片檔案", "*.mp4"),
                ("圖片檔案", "*.jpg;*.png;*.jpeg"),
                ("所有檔案", "*.*")
            ]
        )
        if files:
            # 更新最後使用的資料夾
            if files[0]:
                last_folder = os.path.dirname(files[0])
                self.settings_manager.update_last_folder(last_folder)
                self.folder_path_var.set(last_folder)

            # 檢查數量限制
            if not self._check_can_add_files(len(files)):
                return

            added_count = self.file_manager.add_files(list(files))
            self.update_file_list()

            if added_count > 0:
                self.status_bar.set_message(f"已添加 {added_count} 個檔案")

    def select_folder(self):
        """選擇資料夾"""
        initial_dir = self.settings_manager.get("last_folder", "")
        folder = filedialog.askdirectory(title="選擇資料夾", initialdir=initial_dir)
        if folder:
            self.settings_manager.update_last_folder(folder)
            self.folder_path_var.set(folder)
            self.import_folder_path()

    def import_folder_path(self):
        """導入資料夾路徑"""
        folder_path = self.folder_path_var.get().strip()
        if not folder_path:
            messagebox.showwarning("警告", "請輸入資料夾路徑！")
            return

        if not os.path.isdir(folder_path):
            messagebox.showerror("錯誤", f"路徑不是有效的資料夾：{folder_path}")
            return

        # 獲取資料夾中的檔案數量（估算）
        file_count = len([f for f in os.listdir(folder_path)
                         if any(f.lower().endswith(ext) for ext in SUPPORTED_EXTENSIONS)])

        if not self._check_can_add_files(file_count):
            return

        added_count = self.file_manager.add_folder(folder_path)
        self.update_file_list()

        if added_count > 0:
            self.status_bar.set_message(f"已從資料夾添加 {added_count} 個檔案")
            self.settings_manager.update_last_folder(folder_path)
        else:
            messagebox.showinfo("提示", "資料夾中沒有找到支援的檔案（支援：MP4, JPG, PNG）")

    def browse_folder(self):
        """瀏覽並選擇資料夾"""
        initial_dir = self.folder_path_var.get() or self.settings_manager.get("last_folder", "")
        folder = filedialog.askdirectory(title="選擇資料夾", initialdir=initial_dir)
        if folder:
            self.folder_path_var.set(folder)

    def clear_files(self):
        """清空檔案列表"""
        if self.file_manager.get_file_count() == 0:
            return

        result = messagebox.askyesno("確認", "確定要清空檔案列表嗎？")
        if result:
            self.file_manager.clear_files()
            self.naming_engine.clear_file_char_id_map()
            self.update_file_list()
            self.preview_text.delete(1.0, tk.END)
            self.clear_image_preview()
            self.status_bar.set_message("已清空檔案列表")

    def on_drop(self, event):
        """處理拖放事件"""
        try:
            # 處理拖放的文件列表
            if isinstance(event.data, str):
                files_str = event.data.strip('{}')
                files = [f.strip('"').strip("'") for f in files_str.split() if f.strip()]
            else:
                files = event.data

            files_to_add = []
            folders_to_process = []

            # 分類檔案和資料夾
            for file_path in files:
                file_path = file_path.strip('{}').strip('"').strip("'").strip()
                if not file_path:
                    continue

                if os.path.isfile(file_path):
                    ext = os.path.splitext(file_path)[1].lower()
                    if ext in SUPPORTED_EXTENSIONS:
                        files_to_add.append(file_path)
                elif os.path.isdir(file_path):
                    folders_to_process.append(file_path)

            total_to_add = len(files_to_add)
            # 估算資料夾中的檔案
            for folder in folders_to_process:
                total_to_add += len([f for f in os.listdir(folder)
                                    if any(f.lower().endswith(ext) for ext in SUPPORTED_EXTENSIONS)])

            if not self._check_can_add_files(total_to_add):
                return

            added_count = 0

            # 添加檔案
            if files_to_add:
                added_count += self.file_manager.add_files(files_to_add)

            # 添加資料夾
            for folder_path in folders_to_process:
                added_count += self.file_manager.add_folder(folder_path)

            if added_count > 0:
                self.update_file_list()
                self.status_bar.set_message(f"已拖放添加 {added_count} 個檔案")
            else:
                messagebox.showwarning("警告", "沒有找到支援的檔案（支援：MP4, JPG, PNG）")

        except Exception as e:
            messagebox.showerror("錯誤", f"處理拖放檔案時發生錯誤：{str(e)}")

    def _check_can_add_files(self, new_count: int) -> bool:
        """檢查是否可以添加指定數量的檔案"""
        try:
            max_files = int(self.max_files_var.get())
            if max_files <= 0:
                return True  # 無限制

            current_count = self.file_manager.get_file_count()
            if current_count + new_count > max_files:
                messagebox.showwarning("警告",
                    f"無法添加 {new_count} 個檔案！\n"
                    f"當前已有 {current_count} 個檔案，最大限制為 {max_files} 個。\n"
                    f"只能再添加 {max_files - current_count} 個檔案。")
                return False
            return True
        except ValueError:
            return True  # 輸入無效，視為無限制

    # ========== 列表操作方法 ==========

    def update_file_list(self):
        """更新檔案列表顯示"""
        self.file_listbox.delete(0, tk.END)
        files = self.file_manager.get_files()

        for file_path in files:
            self.file_listbox.insert(tk.END, os.path.basename(file_path))

        # 更新計數
        count = len(files)
        self.current_count_label.config(text=str(count))

        # 更新搜尋結果
        if self.search_bar.get_search_text():
            self.on_search(self.search_bar.get_search_text())
        else:
            self.search_bar.set_count(count, count)

        self.update_status()

    def move_up(self):
        """上移選中的檔案"""
        selected = self.file_listbox.curselection()
        if not selected:
            return

        files = self.file_manager.get_files()
        for idx in selected:
            if idx > 0:
                files[idx], files[idx-1] = files[idx-1], files[idx]

        self.file_manager.selected_files = files
        self.update_file_list()

        # 重新選中
        for idx in selected:
            if idx > 0:
                self.file_listbox.selection_set(idx-1)

    def move_down(self):
        """下移選中的檔案"""
        selected = self.file_listbox.curselection()
        if not selected:
            return

        files = self.file_manager.get_files()
        for idx in reversed(selected):
            if idx < len(files) - 1:
                files[idx], files[idx+1] = files[idx+1], files[idx]

        self.file_manager.selected_files = files
        self.update_file_list()

        # 重新選中
        for idx in selected:
            if idx < len(files) - 1:
                self.file_listbox.selection_set(idx+1)

    def remove_selected(self):
        """刪除選中的檔案"""
        selected = self.file_listbox.curselection()
        if not selected:
            return

        self.file_manager.remove_files(list(selected))
        self.update_file_list()
        self.status_bar.set_message(f"已刪除 {len(selected)} 個檔案")

    # ========== 命名規則方法 ==========

    def on_rule_change(self):
        """命名規則改變"""
        rule_type = self.rule_var.get()
        self.naming_engine.set_rule_type(rule_type)

        if rule_type == "character":
            self.char_frame.pack(fill=tk.X, padx=10, pady=5)
            self.dream_frame.pack_forget()
        else:
            self.char_frame.pack_forget()
            self.dream_frame.pack(fill=tk.X, padx=10, pady=5)

        self.preview_text.delete(1.0, tk.END)
        self.status_bar.set_message(f"已切換到 {rule_type} 規則")

    def on_char_type_change(self, event=None):
        """Character 類型改變"""
        if self.char_type_var.get() == "Open":
            self.color_frame.pack(fill=tk.X, padx=5, pady=5)
        else:
            self.color_frame.pack_forget()
        self.on_param_change()

    def on_theme_change(self, event=None):
        """主題改變"""
        theme = self.theme_var.get()
        role_options = THEME_OPTIONS.get(theme, [])

        if theme == "Anime":
            self.anime_frame.pack(fill=tk.X, padx=5, pady=5)
        else:
            self.anime_frame.pack_forget()

        self.role_combo['values'] = role_options
        if role_options:
            self.role_var.set(role_options[0])

        self.on_param_change()

    def on_param_change(self, event=None):
        """參數改變"""
        # 更新命名引擎參數
        self.naming_engine.set_char_params(
            char_id=self.char_id_var.get(),
            char_type=self.char_type_var.get(),
            char_index=self.char_index_var.get(),
            color=self.color_var.get()
        )

        self.naming_engine.set_dream_params(
            theme=self.theme_var.get(),
            role=self.role_var.get(),
            index=self.dream_index_var.get(),
            anime_num=self.anime_num_var.get()
        )

        # 更新預覽
        selected_indices = self.file_listbox.curselection()
        if selected_indices:
            self.on_file_select()

    def set_all_type(self, char_type: str):
        """一鍵設置所有檔案的類型"""
        self.char_type_var.set(char_type)
        self.on_char_type_change()
        self.status_bar.set_message(f"已將類型設為 {char_type}")

    # ========== 搜尋方法 ==========

    def on_search(self, search_text: str):
        """處理搜尋"""
        files = self.file_manager.get_files()

        if not search_text:
            # 顯示所有項目
            self.filtered_indices = list(range(len(files)))
            self.search_bar.set_count(len(files), len(files))
            return

        # 過濾檔案
        search_lower = search_text.lower()
        self.filtered_indices = [
            i for i, f in enumerate(files)
            if search_lower in os.path.basename(f).lower()
        ]

        self.search_bar.set_count(len(self.filtered_indices), len(files))

        # 高亮顯示搜尋結果（簡化版：僅更新計數）
        # TODO: 可以在列表中高亮或僅顯示過濾後的項目

    # ========== 預覽方法 ==========

    def on_file_select(self, event=None):
        """檔案選擇事件"""
        selected_indices = self.file_listbox.curselection()
        if not selected_indices:
            self.clear_image_preview()
            return

        # 顯示第一個選中檔案的預覽
        selected_index = selected_indices[0]
        files = self.get_files_to_process()

        if 0 <= selected_index < len(self.file_manager.get_files()):
            file_path = self.file_manager.get_files()[selected_index]

            # 計算在處理列表中的索引
            if file_path in files:
                process_index = files.index(file_path)
                self.show_single_file_preview(file_path, process_index)
            else:
                self.show_single_file_preview(file_path, selected_index)

    def show_single_file_preview(self, file_path: str, index: int):
        """顯示單個檔案的預覽"""
        # 隱藏提示標籤
        self.preview_hint_label.pack_forget()

        # 清除 Canvas
        self.preview_canvas.delete("all")
        self.preview_images.clear()

        new_name = self.naming_engine.generate_filename(file_path, index)
        old_name = os.path.basename(file_path)
        ext = os.path.splitext(file_path)[1].lower()

        # 載入預覽圖片
        preview_img = self.load_preview_image(file_path, PREVIEW_IMAGE_SIZE)

        # 計算居中位置
        canvas_width = self.preview_canvas.winfo_width()
        if canvas_width < 10:
            canvas_width = 400

        center_x = canvas_width // 2

        if preview_img:
            # 顯示預覽圖片
            img_width = preview_img.width()
            img_height = preview_img.height()
            img_x = center_x - img_width // 2

            img_id = self.preview_canvas.create_image(img_x, 20, anchor=tk.NW, image=preview_img)
            self.preview_images[img_id] = preview_img

            # 如果是影片，顯示影片標記
            if ext == '.mp4':
                self.preview_canvas.create_text(center_x, 20 + img_height // 2, anchor=tk.CENTER,
                                              text="🎬 影片", font=("Arial", 16, "bold"),
                                              fill="white")

            text_y = 20 + img_height + 20
        else:
            # 無法載入預覽
            file_type = "圖片" if ext in SUPPORTED_IMAGE_EXTENSIONS else "影片"
            box_size = 300
            box_x = center_x - box_size // 2
            self.preview_canvas.create_rectangle(box_x, 20, box_x + box_size, 20 + box_size,
                                                outline="gray", fill="lightgray", width=2)
            self.preview_canvas.create_text(center_x, 20 + box_size // 2, anchor=tk.CENTER,
                                            text=f"📄 {file_type}", font=("Arial", 16))
            text_y = 20 + box_size + 20

        # 顯示檔案名稱
        self.preview_canvas.create_text(center_x, text_y, anchor=tk.CENTER,
                                      text=f"原檔名: {old_name}", font=("Arial", 11))
        self.preview_canvas.create_text(center_x, text_y + 25, anchor=tk.CENTER,
                                      text=f"新檔名: {new_name}", font=("Arial", 11, "bold"),
                                      fill="blue")

        # 更新滾動區域
        self.preview_canvas.update_idletasks()
        self.preview_canvas.config(scrollregion=self.preview_canvas.bbox("all"))

    def clear_image_preview(self):
        """清除圖片預覽"""
        self.preview_canvas.delete("all")
        self.preview_images.clear()
        self.preview_hint_label.pack(pady=20)

    def load_preview_image(self, file_path: str, max_size: tuple):
        """載入預覽圖片"""
        try:
            ext = os.path.splitext(file_path)[1].lower()

            if ext in SUPPORTED_IMAGE_EXTENSIONS:
                if HAS_PIL:
                    img = Image.open(file_path)
                    img.thumbnail(max_size, Image.Resampling.LANCZOS)
                    return ImageTk.PhotoImage(img)
            elif ext == '.mp4':
                if HAS_PIL:
                    # 創建影片圖標
                    img = Image.new('RGB', max_size, color='#2d2d2d')
                    return ImageTk.PhotoImage(img)
        except Exception as e:
            print(f"載入預覽圖片失敗: {str(e)}")

        return None

    def preview_rename(self):
        """預覽重新命名"""
        files_to_process = self.get_files_to_process()
        if not files_to_process:
            if self.only_selected_var.get():
                messagebox.showwarning("警告", "請先選擇要處理的檔案！")
            else:
                messagebox.showwarning("警告", "請先選擇檔案！")
            return

        # 驗證參數
        is_valid, message = self.naming_engine.validate_params()
        if not is_valid:
            messagebox.showerror("錯誤", message)
            return
        elif message:  # 警告訊息
            messagebox.showwarning("警告", message)

        # 文字預覽
        self.preview_text.delete(1.0, tk.END)

        for i, file_path in enumerate(files_to_process):
            new_name = self.naming_engine.generate_filename(file_path, i)
            old_name = os.path.basename(file_path)
            dir_path = os.path.dirname(file_path)
            new_path = os.path.join(dir_path, new_name)

            self.preview_text.insert(tk.END, f"原檔名: {old_name}\n")
            self.preview_text.insert(tk.END, f"新檔名: {new_name}\n")
            self.preview_text.insert(tk.END, f"完整路徑: {new_path}\n")
            self.preview_text.insert(tk.END, "-" * 60 + "\n")

        self.status_bar.set_message(f"已預覽 {len(files_to_process)} 個檔案的重命名結果")

        # 切換到文字預覽標籤頁
        self.preview_notebook.select(0)

    # ========== 執行重命名方法 ==========

    def execute_rename(self):
        """執行重新命名"""
        files_to_process = self.get_files_to_process()
        if not files_to_process:
            if self.only_selected_var.get():
                messagebox.showwarning("警告", "請先選擇要處理的檔案！")
            else:
                messagebox.showwarning("警告", "請先選擇檔案！")
            return

        # 驗證參數
        is_valid, message = self.naming_engine.validate_params()
        if not is_valid:
            messagebox.showerror("錯誤", message)
            return

        # 生成重命名列表
        rename_list = []
        for i, file_path in enumerate(files_to_process):
            new_name = self.naming_engine.generate_filename(file_path, i)
            dir_path = os.path.dirname(file_path)
            new_path = os.path.join(dir_path, new_name)
            rename_list.append((file_path, new_path))

        # 檢查衝突
        conflicts = self.file_manager.check_conflicts(rename_list)
        if conflicts:
            conflict_names = "\n".join([f"- {os.path.basename(new)}" for old, new in conflicts[:5]])
            if len(conflicts) > 5:
                conflict_names += f"\n...還有 {len(conflicts)-5} 個衝突"

            result = messagebox.askyesnocancel("檔案衝突",
                f"發現 {len(conflicts)} 個檔案名稱衝突：\n\n{conflict_names}\n\n"
                "選擇操作：\n"
                "「是」- 覆蓋現有檔案\n"
                "「否」- 跳過衝突檔案\n"
                "「取消」- 取消操作")

            if result is None:  # 取消
                return
            elif result is False:  # 跳過衝突
                rename_list = [(old, new) for old, new in rename_list if (old, new) not in conflicts]

        if not rename_list:
            messagebox.showinfo("提示", "沒有需要重新命名的檔案")
            return

        # 確認對話框
        if self.settings_manager.get("ui_preferences.confirm_before_rename", True):
            result = messagebox.askyesno("確認", f"確定要重新命名 {len(rename_list)} 個檔案嗎？")
            if not result:
                return

        # 執行重新命名
        success_count, error_count, errors = self.file_manager.execute_rename(rename_list)

        # 顯示結果
        message = f"重新命名完成！\n成功: {success_count} 個\n失敗: {error_count} 個"
        if error_count > 0:
            error_details = "\n".join(errors[:5])
            if len(errors) > 5:
                error_details += f"\n...還有 {len(errors)-5} 個錯誤"
            messagebox.showwarning("完成", f"{message}\n\n錯誤詳情：\n{error_details}")
        else:
            messagebox.showinfo("完成", message)

        self.status_bar.set_message(f"重新命名完成：成功 {success_count} 個，失敗 {error_count} 個")

        # 清空列表
        self.clear_files()

    def undo_rename(self):
        """撤銷重命名"""
        if not self.file_manager.can_undo():
            messagebox.showinfo("提示", "沒有可撤銷的操作")
            return

        result = messagebox.askyesno("確認", "確定要撤銷上次的重新命名操作嗎？")
        if not result:
            return

        success, message = self.file_manager.undo_last_rename()

        if success:
            messagebox.showinfo("完成", message)
            self.status_bar.set_message("已撤銷上次的重新命名操作")
        else:
            messagebox.showwarning("警告", message)

    # ========== 輔助方法 ==========

    def get_files_to_process(self):
        """獲取要處理的檔案列表"""
        if self.only_selected_var.get():
            selected_indices = self.file_listbox.curselection()
            if not selected_indices:
                return []
            files = self.file_manager.get_files()
            return [files[i] for i in selected_indices]
        else:
            return self.file_manager.get_files()

    def on_only_selected_change(self):
        """僅處理選中項選項改變"""
        self.on_file_select()

    def setup_20_characters_mode(self):
        """定位20個人物模式"""
        files = self.file_manager.get_files()
        if len(files) < 20:
            result = messagebox.askyesno("定位20個人物模式",
                f"目前只有 {len(files)} 個檔案，少於20個。\n是否繼續設定？")
            if not result:
                return

        # 創建設定視窗
        setup_window = tk.Toplevel(self.root)
        setup_window.title("定位20個人物模式")
        setup_window.geometry("600x500")
        center_window(setup_window, 600, 500)

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

        # 儲存設定
        char_settings = {}

        # 為每個檔案創建輸入框
        for i, file_path in enumerate(files[:20]):
            frame = ttk.Frame(scrollable_frame)
            frame.pack(fill=tk.X, padx=10, pady=5)

            file_name = os.path.basename(file_path)
            display_name = file_name[:40] + "..." if len(file_name) > 40 else file_name
            ttk.Label(frame, text=f"{i+1:02d}. {display_name}", width=40).pack(side=tk.LEFT, padx=5)

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
                        char_id_int = int(char_id)
                        if 1 <= char_id_int <= 99:
                            self.naming_engine.set_file_char_id(file_path, char_id)
                        else:
                            messagebox.showwarning("警告",
                                f"角色編號 {char_id} 超出範圍（1-99），已跳過")
                    except ValueError:
                        messagebox.showwarning("警告",
                            f"角色編號 {char_id} 不是有效數字，已跳過")

            messagebox.showinfo("完成",
                f"已為 {len(char_settings)} 個檔案設定角色編號！\n請在預覽中確認結果。")
            setup_window.destroy()

        ttk.Button(setup_window, text="應用設定", command=apply_settings).pack(pady=10)

    # ========== 主題和設定方法 ==========

    def toggle_theme(self):
        """切換深色/淺色主題"""
        new_theme = self.settings_manager.toggle_theme()
        self.current_theme = new_theme
        self.apply_theme(new_theme)
        self.status_bar.set_message(f"已切換到{'深色' if new_theme == 'dark' else '淺色'}模式")

    def apply_theme(self, theme: str):
        """應用主題"""
        if theme == "dark":
            # 深色主題暫時簡化處理（完整實作需要使用 ttkthemes 或自定義樣式）
            self.theme_button.config(text="☀️ 淺色模式 (Ctrl+T)")
            self.status_bar.set_message("深色模式（基礎支援）")
        else:
            self.theme_button.config(text="🌙 深色模式 (Ctrl+T)")

    def save_settings(self):
        """保存設定"""
        # 更新設定
        self.settings_manager.update_window_geometry(self.root.geometry())
        self.settings_manager.set("max_files", int(self.max_files_var.get() or 0))

        # 更新命名規則設定
        naming_params = self.naming_engine.get_params_dict()
        self.settings_manager.update_naming_rule(naming_params)

        # 保存到檔案
        if self.settings_manager.save_settings():
            self.status_bar.set_message("設定已保存")
        else:
            messagebox.showerror("錯誤", "保存設定失敗")

    def update_status(self):
        """更新狀態列"""
        file_count = self.file_manager.get_file_count()
        history_count = self.file_manager.get_history_count()

        info = f"檔案: {file_count}"
        if history_count > 0:
            info += f" | 可撤銷: {history_count}"

        self.status_bar.set_info(info)

    def on_closing(self):
        """視窗關閉事件"""
        # 自動保存設定
        self.settings_manager.update_window_geometry(self.root.geometry())
        self.settings_manager.set("max_files", int(self.max_files_var.get() or 0))

        naming_params = self.naming_engine.get_params_dict()
        self.settings_manager.update_naming_rule(naming_params)

        self.settings_manager.save_settings()

        self.root.destroy()

    # ========== 說明方法 ==========

    def show_shortcuts_help(self):
        """顯示快捷鍵說明"""
        help_text = """
鍵盤快捷鍵說明：

檔案操作：
  Ctrl + O              選擇檔案
  Ctrl + Shift + O      選擇資料夾
  Ctrl + L              清空列表
  Delete                刪除選中的檔案

編輯操作：
  Ctrl + Z              撤銷上次重新命名
  Ctrl + F              搜尋檔案
  Ctrl + ↑              上移選中的檔案
  Ctrl + ↓              下移選中的檔案

檢視操作：
  Ctrl + P              預覽重新命名
  Ctrl + T              切換深色/淺色模式

其他：
  Ctrl + S              保存設定
  Ctrl + Enter          執行重新命名
  F1                    顯示此說明
        """

        messagebox.showinfo("快捷鍵說明", help_text)

    def show_about(self):
        """顯示關於資訊"""
        about_text = f"""
{APP_TITLE}

版本：{APP_VERSION}

功能特點：
• 支援 Character 和夢想兩種命名規則
• 圖片和影片預覽功能
• 批次重新命名
• 撤銷功能
• 檔案搜尋過濾
• 拖放支援
• 鍵盤快捷鍵
• 深色模式
• 設定記憶

支援格式：MP4, JPG, PNG

© 2024 版權所有
        """

        messagebox.showinfo("關於", about_text)


def main():
    """主程式入口"""
    # 檢查 tkinter 是否可用
    try:
        import tkinter
    except ImportError:
        print("錯誤：此系統未安裝tkinter，請安裝Python時選擇包含tkinter的選項")
        sys.exit(1)

    # 創建視窗
    if HAS_DND:
        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()

    # 創建應用程式
    app = FileRenamerGUI(root)

    # 啟動主迴圈
    root.mainloop()


if __name__ == "__main__":
    main()
