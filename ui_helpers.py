"""
UI 輔助工具
"""
import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable


class ToolTip:
    """工具提示類"""

    def __init__(self, widget, text: str, delay: int = 500):
        """
        Args:
            widget: 要添加工具提示的控件
            text: 提示文字
            delay: 延遲顯示時間（毫秒）
        """
        self.widget = widget
        self.text = text
        self.delay = delay
        self.tooltip_window = None
        self.schedule_id = None

        # 綁定事件
        self.widget.bind('<Enter>', self.on_enter)
        self.widget.bind('<Leave>', self.on_leave)
        self.widget.bind('<Button-1>', self.on_leave)

    def on_enter(self, event=None):
        """滑鼠進入時"""
        self.schedule_id = self.widget.after(self.delay, self.show_tooltip)

    def on_leave(self, event=None):
        """滑鼠離開時"""
        if self.schedule_id:
            self.widget.after_cancel(self.schedule_id)
            self.schedule_id = None
        self.hide_tooltip()

    def show_tooltip(self):
        """顯示工具提示"""
        if self.tooltip_window or not self.text:
            return

        # 獲取控件的位置
        x, y, _, _ = self.widget.bbox("insert") if hasattr(self.widget, 'bbox') else (0, 0, 0, 0)
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25

        # 創建工具提示視窗
        self.tooltip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)  # 移除視窗邊框
        tw.wm_geometry(f"+{x}+{y}")

        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                        background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                        font=("微軟正黑體", 9))
        label.pack()

    def hide_tooltip(self):
        """隱藏工具提示"""
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None


class ProgressDialog:
    """進度對話框"""

    def __init__(self, parent, title: str = "處理中", message: str = "正在處理，請稍候..."):
        """
        Args:
            parent: 父視窗
            title: 對話框標題
            message: 顯示訊息
        """
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("400x150")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # 居中顯示
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (150 // 2)
        self.dialog.geometry(f"+{x}+{y}")

        # 訊息標籤
        self.message_label = ttk.Label(self.dialog, text=message, font=("微軟正黑體", 10))
        self.message_label.pack(pady=20)

        # 進度條
        self.progress = ttk.Progressbar(self.dialog, mode='indeterminate', length=300)
        self.progress.pack(pady=10)
        self.progress.start(10)

        # 詳細資訊標籤
        self.detail_label = ttk.Label(self.dialog, text="", font=("微軟正黑體", 9))
        self.detail_label.pack(pady=5)

    def update_message(self, message: str):
        """更新訊息"""
        self.message_label.config(text=message)
        self.dialog.update()

    def update_detail(self, detail: str):
        """更新詳細資訊"""
        self.detail_label.config(text=detail)
        self.dialog.update()

    def close(self):
        """關閉對話框"""
        self.progress.stop()
        self.dialog.destroy()


class SearchBar(ttk.Frame):
    """搜尋列控件"""

    def __init__(self, parent, on_search: Optional[Callable] = None, **kwargs):
        """
        Args:
            parent: 父控件
            on_search: 搜尋回調函數
        """
        super().__init__(parent, **kwargs)

        self.on_search = on_search

        # 搜尋圖標標籤
        ttk.Label(self, text="🔍").pack(side=tk.LEFT, padx=5)

        # 搜尋輸入框
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(self, textvariable=self.search_var, width=30)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        self.search_entry.bind('<KeyRelease>', self._on_key_release)

        # 清除按鈕
        self.clear_button = ttk.Button(self, text="✕", width=3, command=self.clear_search)
        self.clear_button.pack(side=tk.LEFT, padx=2)

        # 計數標籤
        self.count_label = ttk.Label(self, text="")
        self.count_label.pack(side=tk.LEFT, padx=10)

    def _on_key_release(self, event):
        """按鍵釋放時觸發搜尋"""
        if self.on_search:
            search_text = self.search_var.get()
            self.on_search(search_text)

    def clear_search(self):
        """清除搜尋"""
        self.search_var.set("")
        if self.on_search:
            self.on_search("")

    def get_search_text(self) -> str:
        """獲取搜尋文字"""
        return self.search_var.get()

    def set_count(self, count: int, total: int):
        """設置計數顯示"""
        if count == total:
            self.count_label.config(text=f"共 {total} 項")
        else:
            self.count_label.config(text=f"找到 {count}/{total} 項")

    def focus(self):
        """讓搜尋框獲得焦點"""
        self.search_entry.focus()


class StatusBar(ttk.Frame):
    """狀態列控件"""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

        # 左側狀態訊息
        self.message_label = ttk.Label(self, text="就緒", relief=tk.SUNKEN, anchor=tk.W)
        self.message_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2, pady=2)

        # 右側資訊標籤
        self.info_label = ttk.Label(self, text="", relief=tk.SUNKEN, anchor=tk.E, width=30)
        self.info_label.pack(side=tk.RIGHT, padx=2, pady=2)

    def set_message(self, message: str):
        """設置狀態訊息"""
        self.message_label.config(text=message)

    def set_info(self, info: str):
        """設置右側資訊"""
        self.info_label.config(text=info)

    def clear(self):
        """清除狀態列"""
        self.message_label.config(text="就緒")
        self.info_label.config(text="")


def create_scrollable_frame(parent) -> tuple:
    """
    創建可滾動的框架

    Args:
        parent: 父控件

    Returns:
        (容器框架, 可滾動框架, 垂直滾動條)
    """
    # 容器框架
    container = ttk.Frame(parent)

    # 創建Canvas
    canvas = tk.Canvas(container)
    scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)

    # 可滾動框架
    scrollable_frame = ttk.Frame(canvas)

    # 配置滾動
    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    # 綁定滾輪事件
    def on_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    canvas.bind_all("<MouseWheel>", on_mousewheel)

    # 佈局
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    return container, scrollable_frame, scrollbar


def center_window(window, width: int = 0, height: int = 0):
    """
    將視窗居中顯示

    Args:
        window: Tkinter 視窗
        width: 視窗寬度（0 表示使用當前寬度）
        height: 視窗高度（0 表示使用當前高度）
    """
    window.update_idletasks()

    if width == 0:
        width = window.winfo_width()
    if height == 0:
        height = window.winfo_height()

    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()

    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)

    window.geometry(f"{width}x{height}+{x}+{y}")
