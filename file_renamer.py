import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
from pathlib import Path
import sys
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


# 檢查tkinter是否可用
try:
    import tkinter
except ImportError:
    print("錯誤：此系統未安裝tkinter，請安裝Python時選擇包含tkinter的選項")
    sys.exit(1)


class FileRenamerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("檔案重新命名工具")
        self.root.geometry("1200x1000")
        
        self.selected_files = []
        self.file_char_id_map = {}  # 儲存每個檔案的角色編號設定
        self.preview_images = {}  # 儲存預覽圖片
        self.color_map = {
            "00": ("沒穿", "nude"),
            "01": ("黑色", "black"),
            "02": ("白色", "white"),
            "03": ("綠色", "green"),
            "04": ("紅色", "red"),
            "05": ("黃色", "yellow"),
            "06": ("藍色", "blue")
        }
        self.setup_ui()
        self.setup_drag_drop()
    
    def setup_ui(self):
        # 選擇檔案區域
        file_frame = ttk.LabelFrame(self.root, text="選擇檔案", padding=10)
        file_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 第一行：按鈕
        button_row = ttk.Frame(file_frame)
        button_row.pack(fill=tk.X, pady=5)
        
        ttk.Button(button_row, text="選擇檔案", command=self.select_files).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_row, text="選擇資料夾", command=self.select_folder).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_row, text="清空列表", command=self.clear_files).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_row, text="定位20個人物模式", command=self.setup_20_characters_mode).pack(side=tk.LEFT, padx=5)
        
        # 第二行：限制數量設定和資料夾路徑輸入
        control_row = ttk.Frame(file_frame)
        control_row.pack(fill=tk.X, pady=5)
        
        ttk.Label(control_row, text="最大選擇數量（0=無限制）:").pack(side=tk.LEFT, padx=5)
        self.max_files_var = tk.StringVar(value="0")
        max_files_entry = ttk.Entry(control_row, textvariable=self.max_files_var, width=10)
        max_files_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(control_row, text="當前數量:").pack(side=tk.LEFT, padx=5)
        self.current_count_label = ttk.Label(control_row, text="0", foreground="blue", font=("Arial", 10, "bold"))
        self.current_count_label.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(control_row, text="|").pack(side=tk.LEFT, padx=10)
        
        ttk.Label(control_row, text="資料夾路徑:").pack(side=tk.LEFT, padx=5)
        self.folder_path_var = tk.StringVar()
        folder_path_entry = ttk.Entry(control_row, textvariable=self.folder_path_var, width=40)
        folder_path_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(control_row, text="導入", command=self.import_folder_path).pack(side=tk.LEFT, padx=5)
        
        # 檔案列表（支援多選和調整順序）
        list_frame = ttk.LabelFrame(self.root, text="已選擇的檔案（可多選調整順序）", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 列表控制按鈕
        list_control_frame = ttk.Frame(list_frame)
        list_control_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(list_control_frame, text="上移", command=self.move_up).pack(side=tk.LEFT, padx=2)
        ttk.Button(list_control_frame, text="下移", command=self.move_down).pack(side=tk.LEFT, padx=2)
        ttk.Button(list_control_frame, text="刪除選中", command=self.remove_selected).pack(side=tk.LEFT, padx=2)
        
        # 添加"僅處理選中項"選項
        self.only_selected_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(list_control_frame, text="僅處理選中的檔案（多選時按順序自動排序命名）", 
                       variable=self.only_selected_var,
                       command=self.on_only_selected_change).pack(side=tk.LEFT, padx=10)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.file_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, 
                                       selectmode=tk.EXTENDED, height=10)
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.file_listbox.yview)
        
        # 綁定選擇事件，點選時顯示預覽
        self.file_listbox.bind('<<ListboxSelect>>', self.on_file_select)
        
        # 命名規則選擇
        rule_frame = ttk.LabelFrame(self.root, text="命名規則", padding=10)
        rule_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.rule_var = tk.StringVar(value="character")
        ttk.Radiobutton(rule_frame, text="Character規則（輸出給客戶端）", 
                       variable=self.rule_var, value="character", 
                       command=self.on_rule_change).pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(rule_frame, text="夢想命名規則（內部規則，供員工瀏覽）", 
                       variable=self.rule_var, value="dream", 
                       command=self.on_rule_change).pack(side=tk.LEFT, padx=10)
        
        # Character規則輸入區域
        self.char_frame = ttk.LabelFrame(self.root, text="Character規則參數", padding=10)
        self.char_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 一鍵選擇類型選單
        quick_type_frame = ttk.Frame(self.char_frame)
        quick_type_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(quick_type_frame, text="一鍵選擇類型：", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
        ttk.Button(quick_type_frame, text="全部設為Idle", 
                  command=lambda: self.set_all_type("Idle")).pack(side=tk.LEFT, padx=5)
        ttk.Button(quick_type_frame, text="全部設為Intro", 
                  command=lambda: self.set_all_type("Intro")).pack(side=tk.LEFT, padx=5)
        ttk.Button(quick_type_frame, text="全部設為Open", 
                  command=lambda: self.set_all_type("Open")).pack(side=tk.LEFT, padx=5)
        
        char_input_frame = ttk.Frame(self.char_frame)
        char_input_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(char_input_frame, text="角色編號:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.char_id_var = tk.StringVar(value="01")
        char_id_combo = ttk.Combobox(char_input_frame, textvariable=self.char_id_var, 
                                    values=[f"{i:02d}" for i in range(1, 100)], 
                                    state="readonly", width=10)
        char_id_combo.grid(row=0, column=1, padx=5, pady=5)
        char_id_combo.bind("<<ComboboxSelected>>", self.on_index_change)
        
        ttk.Label(char_input_frame, text="類型:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.char_type_var = tk.StringVar(value="Idle")
        char_type_combo = ttk.Combobox(char_input_frame, textvariable=self.char_type_var, 
                                      values=["Idle", "Intro", "Open"], state="readonly", width=15)
        char_type_combo.grid(row=0, column=3, padx=5, pady=5)
        char_type_combo.bind("<<ComboboxSelected>>", lambda e: (self.on_char_type_change(e), self.on_index_change(e)))
        
        ttk.Label(char_input_frame, text="索引:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.char_index_var = tk.StringVar(value="01")
        char_index_combo = ttk.Combobox(char_input_frame, textvariable=self.char_index_var, 
                                       values=[f"{i:02d}" for i in range(1, 21)], 
                                       state="readonly", width=10)
        char_index_combo.grid(row=1, column=1, padx=5, pady=5)
        char_index_combo.bind("<<ComboboxSelected>>", self.on_index_change)
        
        # Open類型的顏色選擇（顯示中文）
        self.color_frame = ttk.Frame(self.char_frame)
        self.color_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(self.color_frame, text="開獎演出顏色索引（顯示中文，儲存為對應編號）:").pack(side=tk.LEFT, padx=5)
        self.color_var = tk.StringVar(value="00")
        for code, (chinese, english) in self.color_map.items():
            color_radio = ttk.Radiobutton(self.color_frame, text=f"{code} - {chinese}", 
                          variable=self.color_var, value=code, command=self.on_index_change)
            color_radio.pack(side=tk.LEFT, padx=5)
        
        
        # 夢想命名規則輸入區域
        self.dream_frame = ttk.LabelFrame(self.root, text="夢想命名規則參數", padding=10)
        self.dream_frame.pack(fill=tk.X, padx=10, pady=5)
        
        dream_input_frame = ttk.Frame(self.dream_frame)
        dream_input_frame.pack(fill=tk.X)
        
        ttk.Label(dream_input_frame, text="主題:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.theme_var = tk.StringVar(value="Hospital")
        theme_combo = ttk.Combobox(dream_input_frame, textvariable=self.theme_var,
                                  values=["Hospital", "BDSM", "Bedroom", "Anime"], 
                                  state="readonly", width=15)
        theme_combo.grid(row=0, column=1, padx=5, pady=5)
        theme_combo.bind("<<ComboboxSelected>>", lambda e: (self.on_theme_change(e), self.on_index_change(e)))
        
        ttk.Label(dream_input_frame, text="角色類型:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.role_var = tk.StringVar()
        self.role_combo = ttk.Combobox(dream_input_frame, textvariable=self.role_var, 
                                       state="readonly", width=20)
        self.role_combo.grid(row=0, column=3, padx=5, pady=5)
        self.role_combo.bind("<<ComboboxSelected>>", self.on_index_change)
        
        ttk.Label(dream_input_frame, text="索引:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.dream_index_var = tk.StringVar(value="01")
        dream_index_combo = ttk.Combobox(dream_input_frame, textvariable=self.dream_index_var, 
                                        values=[f"{i:02d}" for i in range(1, 21)], 
                                        state="readonly", width=10)
        dream_index_combo.grid(row=1, column=1, padx=5, pady=5)
        dream_index_combo.bind("<<ComboboxSelected>>", self.on_index_change)
        
        # Anime主題的編號
        self.anime_frame = ttk.Frame(self.dream_frame)
        self.anime_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(self.anime_frame, text="動漫主題編號 (A_編號):").pack(side=tk.LEFT, padx=5)
        self.anime_num_var = tk.StringVar(value="01")
        anime_num_combo = ttk.Combobox(self.anime_frame, textvariable=self.anime_num_var, 
                                       values=[f"{i:02d}" for i in range(1, 21)], 
                                       state="readonly", width=10)
        anime_num_combo.pack(side=tk.LEFT, padx=5)
        anime_num_combo.bind("<<ComboboxSelected>>", self.on_index_change)
        
        # 初始化主題選項
        self.on_theme_change()
        
        # 預覽區域（分為文字預覽和圖片預覽）
        preview_frame = ttk.LabelFrame(self.root, text="預覽", padding=10)
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
            drop_hint = ttk.Label(self.root, text="💡 提示：可以直接拖放檔案到此視窗", 
                                 foreground="blue", font=("Arial", 9))
            drop_hint.pack(pady=5)
        
        # 按鈕區域
        button_frame = ttk.Frame(self.root)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="預覽重新命名", command=self.preview_rename).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="執行重新命名", command=self.execute_rename).pack(side=tk.LEFT, padx=5)
        
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
        files = filedialog.askopenfilenames(
            title="選擇檔案",
            filetypes=[
                ("支援的檔案", "*.mp4;*.jpg;*.png"),
                ("影片檔案", "*.mp4"),
                ("圖片檔案", "*.jpg;*.png"),
                ("所有檔案", "*.*")
            ]
        )
        if files:
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
    
    def select_folder(self):
        folder = filedialog.askdirectory(title="選擇資料夾")
        if folder:
            self.add_files_from_folder(folder)
    
    def clear_files(self):
        self.selected_files = []
        self.file_char_id_map = {}
        self.update_file_list()
        self.preview_text.delete(1.0, tk.END)
        self.clear_image_preview()
    
    def update_file_list(self):
        self.file_listbox.delete(0, tk.END)
        for file_path in self.selected_files:
            self.file_listbox.insert(tk.END, os.path.basename(file_path))
        # 更新當前數量顯示
        self.current_count_label.config(text=str(len(self.selected_files)))
    
    def check_max_files_limit(self, new_files_count):
        """檢查是否超過最大選擇數量限制"""
        try:
            max_files = int(self.max_files_var.get())
            if max_files <= 0:
                return True, None  # 無限制
            
            current_count = len(self.selected_files)
            if current_count + new_files_count > max_files:
                return False, max_files
            return True, None
        except ValueError:
            return True, None  # 如果輸入無效，視為無限制
    
    def add_files_from_folder(self, folder_path):
        """從資料夾添加檔案"""
        if not os.path.isdir(folder_path):
            messagebox.showerror("錯誤", f"路徑不是有效的資料夾：{folder_path}")
            return 0
        
        extensions = ['*.mp4', '*.jpg', '*.jpeg', '*.png']
        files_to_add = []
        
        for ext in extensions:
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
        """導入資料夾路徑"""
        folder_path = self.folder_path_var.get().strip()
        if not folder_path:
            messagebox.showwarning("警告", "請輸入資料夾路徑！")
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
        """清除圖片預覽"""
        self.preview_canvas.delete("all")
        self.preview_images.clear()
        self.preview_hint_label.pack(pady=20)
    
    def show_single_file_preview(self, file_path, index):
        """顯示單個檔案的預覽"""
        # 隱藏提示標籤
        self.preview_hint_label.pack_forget()
        
        # 清除Canvas
        self.preview_canvas.delete("all")
        self.preview_images.clear()
        
        new_name = self.generate_new_filename(file_path, index)
        old_name = os.path.basename(file_path)
        ext = os.path.splitext(file_path)[1].lower()
        
        # 載入預覽圖片
        preview_img = self.load_preview_image(file_path, max_size=(300, 300))
        
        # 計算居中位置
        canvas_width = self.preview_canvas.winfo_width()
        if canvas_width < 10:  # 如果Canvas還沒初始化，使用預設值
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
        
        # 顯示檔案名稱
        self.preview_canvas.create_text(center_x, text_y, anchor=tk.CENTER, 
                                      text=f"原檔名: {old_name}", font=("Arial", 11))
        self.preview_canvas.create_text(center_x, text_y + 25, anchor=tk.CENTER, 
                                      text=f"新檔名: {new_name}", font=("Arial", 11, "bold"), 
                                      fill="blue")
        
        # 更新滾動區域
        self.preview_canvas.update_idletasks()
        self.preview_canvas.config(scrollregion=self.preview_canvas.bbox("all"))
    
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
        if self.rule_var.get() == "character":
            self.char_frame.pack(fill=tk.X, padx=10, pady=5)
            self.dream_frame.pack_forget()
        else:
            self.char_frame.pack_forget()
            self.dream_frame.pack(fill=tk.X, padx=10, pady=5)
        self.preview_text.delete(1.0, tk.END)
    
    def on_char_type_change(self, event=None):
        if self.char_type_var.get() == "Open":
            self.color_frame.pack(fill=tk.X, padx=5, pady=5)
        else:
            self.color_frame.pack_forget()
        self.on_index_change()
    
    def on_index_change(self, event=None):
        """當索引選項改變時，刷新預覽"""
        # 如果當前有選中的檔案，更新預覽
        selected_indices = self.file_listbox.curselection()
        if selected_indices:
            selected_index = selected_indices[0]
            if 0 <= selected_index < len(self.selected_files):
                file_path = self.selected_files[selected_index]
                self.show_single_file_preview(file_path, selected_index)
    
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
        """生成新檔名"""
        original_name = os.path.basename(original_path)
        name, ext = os.path.splitext(original_name)
        
        if self.rule_var.get() == "character":
            # 如果該檔案有設定角色編號，使用設定的編號，否則使用預設值
            if original_path in self.file_char_id_map:
                char_id = self.file_char_id_map[original_path].zfill(2)
            else:
                char_id = self.char_id_var.get().zfill(2)
            
            char_type = self.char_type_var.get()
            
            if char_type == "Open":
                # Open類型使用顏色索引
                char_index = self.color_var.get()
            else:
                # Idle和Intro使用輸入的索引
                char_index = self.char_index_var.get().zfill(2)
            
            new_name = f"Character_{char_id}_{char_type}_{char_index}{ext}"
        else:  # dream rule
            theme = self.theme_var.get()
            dream_index = self.dream_index_var.get().zfill(2)
            
            if theme == "Anime":
                anime_num = self.anime_num_var.get().zfill(2)
                new_name = f"A_{anime_num}{ext}"
            else:
                role = self.role_var.get()
                new_name = f"{role}_{dream_index}{ext}"
        
        return new_name
    
    def load_preview_image(self, file_path, max_size=(200, 200)):
        """載入預覽圖片"""
        try:
            ext = os.path.splitext(file_path)[1].lower()
            
            if ext in ['.jpg', '.jpeg', '.png']:
                if HAS_PIL:
                    img = Image.open(file_path)
                    img.thumbnail(max_size, Image.Resampling.LANCZOS)
                    return ImageTk.PhotoImage(img)
                else:
                    return None
            elif ext == '.mp4':
                # 對於影片，創建一個帶有播放圖標的預覽
                if HAS_PIL:
                    # 創建一個深色背景的影片圖標
                    img = Image.new('RGB', max_size, color='#2d2d2d')
                    # 可以在這裡添加播放圖標，但為了簡化，先使用純色背景
                    return ImageTk.PhotoImage(img)
                else:
                    return None
        except Exception as e:
            print(f"載入預覽圖片失敗: {str(e)}")
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
        # 同時刷新文字預覽（不顯示警告）
        files_to_process = self.get_files_to_process()
        if files_to_process:
            # 文字預覽
            self.preview_text.delete(1.0, tk.END)
            for i, file_path in enumerate(files_to_process):
                new_name = self.generate_new_filename(file_path, i)
                old_name = os.path.basename(file_path)
                dir_path = os.path.dirname(file_path)
                new_path = os.path.join(dir_path, new_name)
                
                self.preview_text.insert(tk.END, f"原檔名: {old_name}\n")
                self.preview_text.insert(tk.END, f"新檔名: {new_name}\n")
                self.preview_text.insert(tk.END, f"完整路徑: {new_path}\n")
                self.preview_text.insert(tk.END, "-" * 60 + "\n")
    
    def preview_rename(self):
        """預覽重新命名結果"""
        files_to_process = self.get_files_to_process()
        if not files_to_process:
            if self.only_selected_var.get():
                messagebox.showwarning("警告", "請先選擇要處理的檔案！")
            else:
                messagebox.showwarning("警告", "請先選擇檔案！")
            return
        
        # 文字預覽
        self.preview_text.delete(1.0, tk.END)
        
        for i, file_path in enumerate(files_to_process):
            new_name = self.generate_new_filename(file_path, i)
            old_name = os.path.basename(file_path)
            dir_path = os.path.dirname(file_path)
            new_path = os.path.join(dir_path, new_name)
            
            self.preview_text.insert(tk.END, f"原檔名: {old_name}\n")
            self.preview_text.insert(tk.END, f"新檔名: {new_name}\n")
            self.preview_text.insert(tk.END, f"完整路徑: {new_path}\n")
            self.preview_text.insert(tk.END, "-" * 60 + "\n")
        
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
                os.remove(new_path)  # 刪除現有檔案
                os.rename(old_path, new_path)
                return "success"
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
        
        for i, file_path in enumerate(files_to_process):
            new_name = self.generate_new_filename(file_path, i)
            dir_path = os.path.dirname(file_path)
            new_path = os.path.join(dir_path, new_name)
            
            # 檢查新檔名是否已存在
            if os.path.exists(new_path) and new_path != file_path:
                conflicts.append((file_path, new_path))
            else:
                rename_list.append((file_path, new_path))
        
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
        
        # 執行重新命名
        success_count = 0
        error_count = 0
        errors = []
        
        for old_path, new_path in rename_list:
            try:
                if os.path.exists(new_path) and new_path != old_path:
                    # 如果目標檔案存在且不是同一個檔案，跳過（應該已經處理過了）
                    continue
                os.rename(old_path, new_path)
                success_count += 1
            except Exception as e:
                error_count += 1
                errors.append(f"{os.path.basename(old_path)}: {str(e)}")
        
        # 顯示結果
        message = f"重新命名完成！\n成功: {success_count} 個\n失敗: {error_count} 個"
        if error_count > 0:
            error_details = "\n".join(errors[:5])  # 只顯示前5個錯誤
            if len(errors) > 5:
                error_details += f"\n...還有 {len(errors)-5} 個錯誤"
            messagebox.showwarning("完成", f"{message}\n\n錯誤詳情：\n{error_details}")
        else:
            messagebox.showinfo("完成", message)
        
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


def main():
    if HAS_DND:
        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()
    app = FileRenamerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
