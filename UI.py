import logging
import os
import queue
import re
import subprocess
import threading
from typing import Callable, Optional

import ttkbootstrap as tb
from ttkbootstrap.dialogs.dialogs import Messagebox
from tkinter import filedialog as fd
import tkinter as tk

from Custom_Struc import *
from Init_Settings import *
from Iwara_Login import il
from Logger import get_logger
logger: logging.Logger = get_logger("⭐Iwaratown⭐")
from Search_Engine import Search_Engine
from Settings_Manager import sm, cm
from Channel import channel_manager

class Window_AuthorSelection(tb.Toplevel):
    """A modal window to select an author from a list."""
    def __init__(self, master: tb.Window, authors: list[str], callback: Callable[[str], None]) -> None:
        super().__init__()
        self.master = master
        self.authors = authors
        self.callback = callback
        self.selection: Optional[str] = None

        self.title("选择作者")
        self.geometry("400x500")
        self.create_widgets()

        # Make window modal
        self.transient(self.master)
        self.grab_set()
        self.wait_window()

    def create_widgets(self) -> None:
        """Creates the widgets for the author selection window."""
        tb.Label(self, text="找到多位作者 请选择一位(双击选定)").pack(pady=10, padx=10, anchor=tk.W)

        frame_list = tb.Frame(self)
        frame_list.pack(pady=5, padx=10, fill=tk.BOTH, expand=True)

        self.tree = tb.Treeview(frame_list, columns=("author"), show='headings', height=15)
        self.tree.heading("author", text="作者")
        self.tree.column("author", stretch=True)

        vsb = tb.Scrollbar(frame_list, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        
        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        frame_list.grid_rowconfigure(0, weight=1)
        frame_list.grid_columnconfigure(0, weight=1)

        for author in self.authors:
            self.tree.insert("", "end", values=(author,))

        self.tree.bind("<Double-1>", self.on_select)

    def on_select(self, event: Optional[tk.Event] = None) -> None:
        """Handles author selection and closes the window."""
        selected_item = self.tree.selection()
        if not selected_item:
            self.master.after(0, lambda: Messagebox.show_warning("请选择一位作者", "提示", parent=self))
            return
        
        self.selection = self.tree.item(selected_item[0], "values")[0]
        self.on_close()

    def on_close(self) -> None:
        """Calls the callback with the selection before closing."""
        self.callback(self.selection) if self.selection else None
        self.destroy()

class Window_Settings(tb.Toplevel):
    """The application settings window."""
    def __init__(self, master: tb.Window) -> None:
        super().__init__() # --- Modified Code: Correctly initialize Toplevel ---
        self.master = master
        self.title("设置")
        self.geometry("800x450")
        self.create_widgets()
        self.fill_entry()

    def create_widgets(self) -> None:
        """Creates the widgets for the settings window."""
        frame_xpv_hostname = tb.Frame(self)
        frame_xpv_hostname.pack(anchor=tk.NW, pady=5, padx=10)
        tb.Label(frame_xpv_hostname, text="Xpv主机名:").pack(side='left')
        self.entry_xpv_hostname = tb.Entry(frame_xpv_hostname, width=50)
        self.entry_xpv_hostname.pack(side='left', padx=5)

        frame_iwara_hostname = tb.Frame(self)
        frame_iwara_hostname.pack(anchor=tk.NW, pady=5, padx=10)
        tb.Label(frame_iwara_hostname, text="Iwara主机名:").pack(side='left')
        self.entry_iwara_hostname = tb.Entry(frame_iwara_hostname, width=50)
        self.entry_iwara_hostname.pack(side='left', padx=5)

        frame_hanime1_hostname = tb.Frame(self)
        frame_hanime1_hostname.pack(anchor=tk.NW, pady=5, padx=10)
        tb.Label(frame_hanime1_hostname, text="Hanime1主机名:").pack(side='left')
        self.entry_hanime1_hostname = tb.Entry(frame_hanime1_hostname, width=50)
        self.entry_hanime1_hostname.pack(side='left', padx=5)
        
        frame_xpv_path = tb.Frame(self)
        frame_xpv_path.pack(anchor=tk.NW, pady=5, padx=10)
        tb.Label(frame_xpv_path, text="Xpv下载路径:").pack(side='left')
        self.entry_xpv_path = tb.Entry(frame_xpv_path, width=80)
        self.entry_xpv_path.pack(side='left', padx=5)
        tb.Button(frame_xpv_path, text="浏览", command=lambda: self.browse_directory(self.entry_xpv_path)).pack(side='left')

        frame_iwara_path = tb.Frame(self)
        frame_iwara_path.pack(anchor=tk.NW, pady=5, padx=10)
        tb.Label(frame_iwara_path, text="Iwara下载路径:").pack(side='left')
        self.entry_iwara_path = tb.Entry(frame_iwara_path, width=80)
        self.entry_iwara_path.pack(side='left', padx=5)
        tb.Button(frame_iwara_path, text="浏览", command=lambda: self.browse_directory(self.entry_iwara_path)).pack(side='left')

        frame_hanime1_path = tb.Frame(self)
        frame_hanime1_path.pack(anchor=tk.NW, pady=5, padx=10)
        tb.Label(frame_hanime1_path, text="Hanime1下载路径:").pack(side='left')
        self.entry_hanime1_path = tb.Entry(frame_hanime1_path, width=80)
        self.entry_hanime1_path.pack(side='left', padx=5)
        tb.Button(frame_hanime1_path, text="浏览", command=lambda: self.browse_directory(self.entry_hanime1_path)).pack(side='left')

        frame_custom_path = tb.Frame(self)
        frame_custom_path.pack(anchor=tk.NW, pady=5, padx=10)
        tb.Label(frame_custom_path, text="自定义下载路径:").pack(side='left')
        self.entry_custom_path = tb.Entry(frame_custom_path, width=80)
        self.entry_custom_path.pack(side='left', padx=5)
        tb.Button(frame_custom_path, text="浏览", command=lambda: self.browse_directory(self.entry_custom_path)).pack(side='left')
        
        frame_max_threads = tb.Frame(self)
        frame_max_threads.pack(anchor=tk.NW, pady=5, padx=10)
        tb.Label(frame_max_threads, text="最大线程数:").pack(side='left')
        self.entry_max_threads = tb.Entry(frame_max_threads, width=5)
        self.entry_max_threads.pack(side='left', padx=5)

        frame_check_cert = tb.Frame(self)
        frame_check_cert.pack(anchor=tk.NW, pady=5, padx=10)
        self.check_cert_var = tb.BooleanVar()
        tb.Checkbutton(frame_check_cert, text="检查证书", variable=self.check_cert_var).pack(side='left')

        tb.Button(self, text="保存", command=self.on_close).pack(anchor=tk.NW, padx=5, pady=10)

    def browse_directory(self, entry: tb.Entry) -> None:
        """Opens a dialog to select a directory."""
        logger.debug("打开目录选择对话框")
        selected_dir = fd.askdirectory()
        if selected_dir:
            entry.delete(0, tk.END)
            entry.insert(0, selected_dir)
            logger.info(f"选择的目录: {selected_dir}")
        self.focus_set()

    def fill_entry(self) -> None:
        self.entry_xpv_hostname.insert(0, sm.settings.get("Xpv_Hostname", DEFAULT_SETTINGS["Xpv_Hostname"]))
        self.entry_iwara_hostname.insert(0, sm.settings.get("Iwara_Hostname", DEFAULT_SETTINGS["Iwara_Hostname"]))
        self.entry_hanime1_hostname.insert(0, sm.settings.get("Hanime1_Hostname", DEFAULT_SETTINGS["Hanime1_Hostname"]))
        self.entry_xpv_path.insert(0, sm.settings.get("Xpv_Download_Path", DEFAULT_SETTINGS["Xpv_Download_Path"]))
        self.entry_iwara_path.insert(0, sm.settings.get("Iwara_Download_Path", DEFAULT_SETTINGS["Iwara_Download_Path"]))
        self.entry_hanime1_path.insert(0, sm.settings.get("Hanime1_Download_Path", DEFAULT_SETTINGS["Hanime1_Download_Path"]))
        self.entry_custom_path.insert(0, sm.settings.get("Custom_Download_Path", DEFAULT_SETTINGS["Custom_Download_Path"]))
        self.entry_max_threads.insert(0, str(sm.settings.get("Max_Threads", DEFAULT_SETTINGS["Max_Threads"])))
        self.check_cert_var.set(sm.settings.get("Check_Cert", DEFAULT_SETTINGS["Check_Cert"]))

    def on_close(self) -> None:
        sm.settings["Xpv_Hostname"] = self.entry_xpv_hostname.get().strip()
        sm.settings["Iwara_Hostname"] = self.entry_iwara_hostname.get().strip()
        sm.settings["Hanime1_Hostname"] = self.entry_hanime1_hostname.get().strip()
        sm.settings["Xpv_Download_Path"] = self.entry_xpv_path.get().strip()
        sm.settings["Iwara_Download_Path"] = self.entry_iwara_path.get().strip()
        sm.settings["Hanime1_Download_Path"] = self.entry_hanime1_path.get().strip()
        sm.settings["Custom_Download_Path"] = self.entry_custom_path.get().strip()
        sm.settings["Check_Cert"] = self.check_cert_var.get()

        try:
            max_threads = int(self.entry_max_threads.get())
            if not 1 <= max_threads <= 32:
                raise ValueError("线程数必须在 1-32 之间")
            sm.settings["Max_Threads"] = max_threads
            sm.save_settings()
            self.destroy()
        except ValueError as e:
            logger.error(f"无效的线程数输入: {e}")

class Window_CheckUpdate(tb.Toplevel):
    """检查更新窗口，用于显示未下载的新视频"""
    def __init__(self, master: "Win_Main", new_videos: list[stru_xpv_video]) -> None:
        super().__init__()
        self.master: "Win_Main" = master  # pyright: ignore[reportIncompatibleVariableOverride]
        self.new_videos = new_videos
        self.sorted_videos: list[stru_xpv_video] = []  # 添加排序后的视频列表
        self.title("检查更新结果")
        self.geometry("1000x600")
        self.create_widgets()

    def create_widgets(self) -> None:
        """创建窗口组件"""
        # 创建tree组件
        frame_tree = tb.Frame(self)
        frame_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.tree = tb.Treeview(frame_tree, columns=(
            "author",
            "title",
            "date",
            "link"
        ), show='headings', height=20)
        self.tree.heading("author", text="作者", anchor=tk.W)
        self.tree.heading("title", text="标题", anchor=tk.W)
        self.tree.heading("date", text="日期", anchor=tk.W)
        self.tree.heading("link", text="链接", anchor=tk.W)
        
        # 设置列宽
        self.tree.column("author", width=150, stretch=False)
        self.tree.column("title", width=400, stretch=True)
        self.tree.column("date", width=120, stretch=False)
        self.tree.column("link", width=100, stretch=False)

        # 添加滚动条
        vsb = tb.Scrollbar(frame_tree, orient="vertical", command=self.tree.yview)
        hsb = tb.Scrollbar(frame_tree, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # 布局
        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        frame_tree.grid_rowconfigure(0, weight=1)
        frame_tree.grid_columnconfigure(0, weight=1)

        # 绑定事件
        self.tree.bind("<MouseWheel>", lambda e: self.tree.yview_scroll(int(-1 * (e.delta / 120) * 2), "units"))
        self.tree.bind("<Button-1>", self.on_tree_click)

        # 创建按钮区域
        frame_buttons = tb.Frame(self)
        frame_buttons.pack(fill=tk.X, padx=10, pady=5)

        self.btn_download = tb.Button(frame_buttons, text="下载选中的视频", command=self.download_selected)
        self.btn_download.pack(side='right', padx=5)

        # 填充数据
        self.fill_tree()

    def fill_tree(self) -> None:
        """填充tree组件的数据"""
        # 清空现有数据
        self.tree.delete(*self.tree.get_children())

        # 按照作者正序，日期倒序排序
        self.sorted_videos = sorted(self.new_videos, key=lambda v: (v.author, v.get_updatedAt_timestamp()), reverse=True)

        # 插入数据
        video: stru_xpv_video
        for video in self.sorted_videos:
            self.tree.insert('', 'end', values=(
                video.author,
                video.title,
                video.updatedAt,
                "打开链接"
            ))

    def on_tree_click(self, event) -> None:
        """处理tree组件的点击事件"""
        col = self.tree.identify_column(event.x)
        row = self.tree.identify_row(event.y)

        # 如果点击了链接列
        if col == "#4" and row:
            # 获取视频索引
            video_index = int(self.tree.index(row))
            if video_index < len(self.sorted_videos):
                # 打开视频链接
                video = self.sorted_videos[video_index]
                self.master.open_edge_private(video.url)

    def download_selected(self) -> None:
        """下载选中的视频"""
        selected_items = self.tree.selection()
        if not selected_items:
            Messagebox.show_warning("请先选择要下载的视频", "提示", parent=self)
            return

        # 获取选中的视频索引
        selected_indices = [int(self.tree.index(item)) for item in selected_items]

        # 调用主窗口的下载函数
        if isinstance(self.master, Win_Main):
            # 直接使用已排序的视频列表
            selected_videos = [self.sorted_videos[i] for i in selected_indices]

            # 将选中的视频添加到队列中
            self.master.progressbar.configure(maximum=len(selected_videos), value=0)
            for video in selected_videos:
                self.master.download_queue.put(video)

            logger.info(f"已将 {len(selected_videos)} 个视频添加到下载队列")
            Messagebox.show_info(f"已将 {len(selected_videos)} 个视频添加到下载队列", "提示", parent=self)

            # 关闭窗口
            self.destroy()

class Window_Login(tb.Toplevel):
    """登录窗口类，用于用户登录Iwara平台"""
    def __init__(self, master: tb.Window) -> None:
        super().__init__()
        self.master = master
        self.title("登录Iwara")
        self.geometry("450x350")
        self.login_manager = il
        
        # 创建并配置界面组件
        self.create_widgets()
        
        # 设置窗口为模态
        self.transient(self.master)
        self.grab_set()
        
    def create_widgets(self) -> None:
        """创建登录窗口的UI组件"""
        # 创建容器框架
        frame_main = tb.Frame(self, padding=20)
        frame_main.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        tb.Label(frame_main, text="Iwara 账号登录", font=("Microsoft YaHei", 12, "bold")).pack(pady=10)
        
        # 邮箱输入框
        frame_email = tb.Frame(frame_main)
        frame_email.pack(fill=tk.X, pady=5)
        tb.Label(frame_email, text="邮箱:", width=8).pack(side=tk.LEFT)
        self.entry_email = tb.Entry(frame_email)
        self.entry_email.pack(fill=tk.X, side=tk.LEFT, expand=True)
        
        # 密码输入框
        frame_password = tb.Frame(frame_main)
        frame_password.pack(fill=tk.X, pady=5)
        tb.Label(frame_password, text="密码:", width=8).pack(side=tk.LEFT)
        self.entry_password = tb.Entry(frame_password, show="*")
        self.entry_password.pack(fill=tk.X, side=tk.LEFT, expand=True)
        
        # 错误提示标签
        self.label_error = tb.Label(frame_main, text="", foreground="red", wraplength=300)
        self.label_error.pack(pady=10)
        
        # 按钮区域
        frame_buttons = tb.Frame(frame_main)
        frame_buttons.pack(pady=10)
        
        # 登录按钮
        self.btn_login = tb.Button(frame_buttons, text="登录", width=12, command=self.on_login)
        self.btn_login.pack(side=tk.LEFT, padx=5)
        
        # 取消按钮
        self.btn_cancel = tb.Button(frame_buttons, text="取消", width=12, command=self.destroy)
        self.btn_cancel.pack(side=tk.LEFT, padx=5)
    
    def on_login(self) -> None:
        """处理登录按钮点击事件"""
        # 获取用户输入
        email = self.entry_email.get().strip()
        password = self.entry_password.get().strip()
        
        # 简单验证
        if not email:
            self.show_error("请输入邮箱")
            return
        if not password:
            self.show_error("请输入密码")
            return
            
        # 验证邮箱格式
        if not self._is_valid_email(email):
            self.show_error("请输入有效的邮箱地址")
            return
        
        # 禁用按钮防止重复点击
        self.btn_login.config(state=tk.DISABLED)
        self.btn_cancel.config(state=tk.DISABLED)
        self.label_error.config(text="正在登录...")
        
        # 在后台线程中执行登录操作
        self.update()
        threading.Thread(target=self._login_thread, args=(email, password)).start()
    
    def _login_thread(self, email: str, password: str) -> None:
        """登录操作的后台线程"""
        # 执行登录
        success, message, token = self.login_manager.login(email, password)
        
        # 在主线程中更新UI
        self.after(0, lambda: self._handle_login_result(success, message, token))
    
    def _handle_login_result(self, success: bool, message: str, token: str) -> None:
        """处理登录结果"""
        # 重新启用按钮
        self.btn_login.config(state=tk.NORMAL)
        self.btn_cancel.config(state=tk.NORMAL)
        
        if success:
            # 登录成功，保存token到设置中
            sm.settings["Iwara_Token"] = token
            sm.save_settings()
            
            # 更新UI状态，显示登录成功信息
            self.label_error.config(text="登录成功！", foreground="green")
            logger.info(f"用户登录成功")
            
            # 更新主窗口的登录按钮文本
            if isinstance(self.master, Win_Main):
                self.master.update_login_status(True)
            
            # 延迟关闭窗口
            self.after(1000, self.destroy)
        else:
            # 登录失败，显示错误信息
            logger.error(f"登录失败: {message}")
            self.show_error(message)
    
    def show_error(self, message: str) -> None:
        """显示错误信息"""
        self.label_error.config(text=message, foreground="red")
    
    @staticmethod
    def _is_valid_email(email: str) -> bool:
        """验证邮箱格式"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

class Window_Favor(tb.Toplevel):
    def __init__(self, master: tb.Window) -> None:
        super().__init__()
        self.master = master
        self.title("收藏夹")
        self.geometry("600x700")

        self.favor_data: dict = sm.settings.get("Favor", {"xpv": [], "iwara": [], "hanime1": []})
        self.current_channel = "xpv"  # 默认渠道

        self.create_widgets()
    
    def create_widgets(self) -> None:
        """Creates the widgets for the main window."""
        frame_toolbar = tb.Frame(self)
        frame_toolbar.pack(fill=tk.X, pady=5, padx=5)
        tb.Button(frame_toolbar, text="编辑", command=lambda: [
            logger.debug("打开收藏夹编辑窗口"),
            self.edit_favor()
        ]).pack(side='left', padx=5)

        # 创建Notebook用于显示不同渠道的收藏列表
        self.notebook = tb.Notebook(self)
        self.notebook.pack(pady=5, padx=10, fill=tk.BOTH, expand=True)
        
        self.frame_xpv: tb.Frame = tb.Frame(self.notebook)
        self.notebook.add(self.frame_xpv, text="Xpv")
        self.frame_iwara: tb.Frame = tb.Frame(self.notebook)
        self.notebook.add(self.frame_iwara, text="Iwara")
        self.frame_hanime1: tb.Frame = tb.Frame(self.notebook)
        self.notebook.add(self.frame_hanime1, text="Hanime1")
        
        # 为Xpv标签页创建列表
        self.tree_xpv = tb.Treeview(self.frame_xpv, columns=("author"), show='headings', height=15)
        self.tree_xpv.heading("author", text="作者")
        self.tree_xpv.column("author", stretch=True)
        
        vsb_xpv = tb.Scrollbar(self.frame_xpv, orient="vertical", command=self.tree_xpv.yview)
        self.tree_xpv.configure(yscrollcommand=vsb_xpv.set)
        self.tree_xpv.bind("<MouseWheel>", lambda e: self.tree_xpv.yview_scroll(int(-1 * (e.delta / 120) * 2), "units"))
        
        self.tree_xpv.grid(row=0, column=0, sticky='nsew')
        vsb_xpv.grid(row=0, column=1, sticky='ns')
        self.frame_xpv.grid_rowconfigure(0, weight=1)
        self.frame_xpv.grid_columnconfigure(0, weight=1)
        
        # 为Iwara标签页创建列表
        self.tree_iwara = tb.Treeview(self.frame_iwara, columns=("author"), show='headings', height=15)
        self.tree_iwara.heading("author", text="作者")
        self.tree_iwara.column("author", stretch=True)
        
        vsb_iwara = tb.Scrollbar(self.frame_iwara, orient="vertical", command=self.tree_iwara.yview)
        self.tree_iwara.configure(yscrollcommand=vsb_iwara.set)
        self.tree_iwara.bind("<MouseWheel>", lambda e: self.tree_iwara.yview_scroll(int(-1 * (e.delta / 120) * 2), "units"))
        
        self.tree_iwara.grid(row=0, column=0, sticky='nsew')
        vsb_iwara.grid(row=0, column=1, sticky='ns')
        self.frame_iwara.grid_rowconfigure(0, weight=1)
        self.frame_iwara.grid_columnconfigure(0, weight=1)

        
        # 为Hanime1标签页创建列表
        self.tree_hanime1 = tb.Treeview(self.frame_hanime1, columns=("author"), show='headings', height=15)
        self.tree_hanime1.heading("author", text="作者")
        self.tree_hanime1.column("author", stretch=True)
        
        vsb_hanime1 = tb.Scrollbar(self.frame_hanime1, orient="vertical", command=self.tree_hanime1.yview)
        self.tree_hanime1.configure(yscrollcommand=vsb_hanime1.set)
        self.tree_hanime1.bind("<MouseWheel>", lambda e: self.tree_hanime1.yview_scroll(int(-1 * (e.delta / 120) * 2), "units"))
        
        self.tree_hanime1.grid(row=0, column=0, sticky='nsew')
        vsb_hanime1.grid(row=0, column=1, sticky='ns')
        self.frame_hanime1.grid_rowconfigure(0, weight=1)
        self.frame_hanime1.grid_columnconfigure(0, weight=1)
        
        # 填充数据
        for author in self.favor_data.get("xpv", []):
            self.tree_xpv.insert("", "end", values=(author,))
        
        for author in self.favor_data.get("iwara", []):
            self.tree_iwara.insert("", "end", values=(author,))
        
        for author in self.favor_data.get("hanime1", []):
            self.tree_hanime1.insert("", "end", values=(author,))
        
        # 绑定双击事件和标签页切换事件
        self.tree_xpv.bind("<Double-1>", self.on_select)
        self.tree_iwara.bind("<Double-1>", self.on_select)
        self.tree_hanime1.bind("<Double-1>", self.on_select)
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_change)

    def on_tab_change(self, event: Optional[tk.Event] = None) -> None:
        """Handles tab change event to update current channel."""
        selected_tab = self.notebook.select()
        if selected_tab == self.frame_xpv._w:  # pyright: ignore[reportAttributeAccessIssue]
            self.current_channel = "xpv"
        elif selected_tab == self.frame_iwara._w:  # pyright: ignore[reportAttributeAccessIssue]
            self.current_channel = "iwara"
        elif selected_tab == self.frame_hanime1._w:  # pyright: ignore[reportAttributeAccessIssue]
            self.current_channel = "hanime1"
    
    def on_select(self, event: Optional[tk.Event] = None) -> None:
        """Handles author selection and closes the window."""
        # 根据当前选中的标签页确定使用哪个tree
        if self.current_channel == "xpv":
            current_tree = self.tree_xpv
        elif self.current_channel == "iwara":
            current_tree = self.tree_iwara
        elif self.current_channel == "hanime1":
            current_tree = self.tree_hanime1
        else:
            self.master.after(0, lambda: Messagebox.show_error("未知渠道", "错误", parent=self))
            return
        
        selected_item = current_tree.selection()
        if not selected_item:
            self.master.after(0, lambda: Messagebox.show_warning("请选择一位作者", "提示", parent=self))
            return
        
        self.selection = current_tree.item(selected_item[0], "values")[0]
        self.destroy()
        if isinstance(self.master, Win_Main):
            # 根据当前渠道设置搜索源
            if self.current_channel == "xpv":
                self.master.combobox_source.set("Xpv")
            elif self.current_channel == "iwara":
                self.master.combobox_source.set("Iwara")
            elif self.current_channel == "hanime1":
                self.master.combobox_source.set("Hanime1")
                
            self.master.entry_search.delete(0, tk.END)
            self.master.entry_search.insert(0, self.selection)
            self.master.selected_author = self.selection
            self.master.start_search()
        else:
            logger.error("无法访问 entry_search 属性, parent 不是 UI 类的实例")
         
    def edit_favor(self) -> None:
        """Opens the favor edit window."""
        Window_Edit = tb.Toplevel()
        Window_Edit.title("编辑收藏夹")
        Window_Edit.geometry("600x700")

        def save_favor(xpv_authors: list[str], iwara_authors: list[str], hanime1_authors: list[str]) -> None:
            """Saves the favor list for both channels."""
            # 去重并去除空字符串
            unique_xpv_authors = list(dict.fromkeys([a.strip() for a in xpv_authors if a.strip()]))
            unique_iwara_authors = list(dict.fromkeys([a.strip() for a in iwara_authors if a.strip()]))
            unique_hanime1_authors = list(dict.fromkeys([a.strip() for a in hanime1_authors if a.strip()]))
            
            # 按名字首字母正序排序
            unique_xpv_authors.sort(key=lambda x: x.lower())
            unique_iwara_authors.sort(key=lambda x: x.lower())
            unique_hanime1_authors.sort(key=lambda x: x.lower())
            
            sm.settings["Favor"] = {
                "xpv": unique_xpv_authors,
                "iwara": unique_iwara_authors,
                "hanime1": unique_hanime1_authors
            }
            sm.save_settings()
            self.favor_data = sm.settings.get("Favor", {"xpv": [], "iwara": [], "hanime1": []})
            
            # 更新两个列表
            self.tree_xpv.delete(*self.tree_xpv.get_children())
            for author in self.favor_data.get("xpv", []):
                self.tree_xpv.insert("", "end", values=(author,))
                
            self.tree_iwara.delete(*self.tree_iwara.get_children())
            for author in self.favor_data.get("iwara", []):
                self.tree_iwara.insert("", "end", values=(author,))
                
            self.tree_hanime1.delete(*self.tree_hanime1.get_children())
            for author in self.favor_data.get("hanime1", []):
                self.tree_hanime1.insert("", "end", values=(author,))
                
            logger.info(f"保存 Xpv: {len(unique_xpv_authors)} 个, Iwara: {len(unique_iwara_authors)} 个, Hanime1: {len(unique_hanime1_authors)} 个收藏夹作者")

        # 创建Notebook用于编辑不同渠道的收藏列表
        notebook_edit = tb.Notebook(Window_Edit)
        notebook_edit.pack(pady=5, padx=10, fill=tk.BOTH, expand=True)
        
        # 创建Xpv标签页
        frame_xpv_edit = tb.Frame(notebook_edit)
        notebook_edit.add(frame_xpv_edit, text="Xpv")
        
        # 创建Iwara标签页
        frame_iwara_edit = tb.Frame(notebook_edit)
        notebook_edit.add(frame_iwara_edit, text="Iwara")
        
        # 创建Hanime1标签页
        frame_hanime1_edit = tb.Frame(notebook_edit)
        notebook_edit.add(frame_hanime1_edit, text="Hanime1")
        
        # 为Xpv标签页创建编辑区域
        tb.Label(frame_xpv_edit, text="每行一个作者名:").pack(anchor=tk.W, pady=(10, 0))
        text_input_xpv = tb.Text(frame_xpv_edit, wrap=tk.WORD)
        text_input_xpv.pack(fill=tk.BOTH, expand=True, pady=5, padx=10)
        for author in self.favor_data.get("xpv", []):
            text_input_xpv.insert(tk.END, author + "\n")
        
        # 为Iwara标签页创建编辑区域
        tb.Label(frame_iwara_edit, text="每行一个作者名:").pack(anchor=tk.W, pady=(10, 0))
        text_input_iwara = tb.Text(frame_iwara_edit, wrap=tk.WORD)
        text_input_iwara.pack(fill=tk.BOTH, expand=True, pady=5, padx=10)
        for author in self.favor_data.get("iwara", []):
            text_input_iwara.insert(tk.END, author + "\n")
            
        # 为Hanime1标签页创建编辑区域
        tb.Label(frame_hanime1_edit, text="每行一个作者名:").pack(anchor=tk.W, pady=(10, 0))
        text_input_hanime1 = tb.Text(frame_hanime1_edit, wrap=tk.WORD)
        text_input_hanime1.pack(fill=tk.BOTH, expand=True, pady=5, padx=10)
        for author in self.favor_data.get("hanime1", []):
            text_input_hanime1.insert(tk.END, author + "\n")

        frame_toolbars = tb.Frame(Window_Edit)
        frame_toolbars.pack(fill=tk.X, pady=5, padx=5)
        tb.Button(frame_toolbars, text="保存", command=lambda: [
            logger.info("保存收藏夹"),
            save_favor(
                text_input_xpv.get("1.0", tk.END).strip().splitlines(),
                text_input_iwara.get("1.0", tk.END).strip().splitlines(),
                text_input_hanime1.get("1.0", tk.END).strip().splitlines()
            ),
            Window_Edit.destroy()
        ]).pack(side='left', padx=5)
        tb.Button(frame_toolbars, text="取消", command=Window_Edit.destroy).pack(side='left', padx=5)

class Win_Main(tb.Window):
    def __init__(self) -> None:
        super().__init__(themename=THEMENAME)
        self.title("Iwaratown")
        self.geometry("1200x600")
        self.video_list: list[stru_iw_video|stru_xpv_video|stru_hanime1_video] = []
        self.url_for_edge_to_open: str = ""
        self.current_author: str = ""

        self.download_queue: queue.Queue[stru_iw_video|stru_xpv_video|stru_xpv_custom|stru_hanime1_video] = queue.Queue()
        self.download_threads: list[threading.Thread] = []

        self.col_map: dict[str, str] = {
            "#1": "date",
            "#2": "title",
            "#3": "state",
            "#5": "view"
        }
        self.sort_col: str = "#1"
        self.sort_reverse: bool = False

        self._init_download_workers()
        self.create_widgets()
    
    def _init_download_workers(self) -> None:
        for _ in range(sm.settings.get("Max_Threads", DEFAULT_SETTINGS["Max_Threads"])):
            thread: threading.Thread = threading.Thread(target=self._download_worker, daemon=True)
            self.download_threads.append(thread)
            thread.start()
    
    def _download_worker(self) -> None:
        logger.debug(f"下载线程启动: {threading.current_thread().name}")
        while True:
            #这里的get会自动断点
            task: stru_iw_video|stru_xpv_video|stru_xpv_custom|stru_hanime1_video = self.download_queue.get()
            logger.info(f"队列还剩下{self.download_queue.qsize()}个任务")
            
            # 使用渠道管理器下载任务
            success: bool = channel_manager.download(task)
            
            if success:
                self.after(0, self.update_tree)
                self.after(0, self.progressbar.step, 1)
            self.download_queue.task_done()

    def create_widgets(self) -> None:
        frame_toolbar = tb.Frame(self)
        frame_toolbar.pack(fill=tk.X, pady=5, padx=5)
        tb.Button(frame_toolbar, text="设置", command=lambda: [
            logger.debug("打开设置窗口"),
            Window_Settings(self)
        ]).pack(side='left', padx=5)
        self.btn_edge = tb.Button(frame_toolbar, text="Edge无痕浏览", state=tk.DISABLED, command= lambda: [self.open_edge_private(self.url_for_edge_to_open)])
        self.btn_edge.pack(side='left', padx=5)
        tb.Button(frame_toolbar, text="收藏夹", command=lambda: [
            logger.debug("打开收藏夹窗口"),
            Window_Favor(self)
        ]).pack(side='left', padx=5)
        # 登录按钮
        self.btn_login = tb.Button(frame_toolbar, text="登录", command=self.on_login_button_click)
        self.btn_login.pack(side='left', padx=5)
        
        # 检查是否已登录并更新按钮状态
        self.update_login_status(bool(sm.settings.get("Iwara_Token", "")))
        self.btn_local = tb.Button(frame_toolbar, text="本地文件", state=tk.DISABLED, command=lambda: [
            logger.debug("打开本地文件夹"),
            self.open_local_folder()
        ])
        self.btn_local.pack(side='left', padx=5)
        tb.Button(frame_toolbar, text="给作者买杯咖啡", command=lambda: [
            self.open_edge_private(MYBILIURL, private=False)
        ]).pack(side='left', padx=5)
        self.entry_custom_url = tb.Entry(frame_toolbar, width=60)
        self.entry_custom_url.pack(side='left', padx=5)
        tb.Button(frame_toolbar, text="自定义下载", 
                  command=self.start_download_custom).pack(side='left', padx=5)
        
        frame_toolbar2 = tb.Frame(self)
        frame_toolbar2.pack(fill=tk.X, pady=5, padx=5)
        tb.Button(frame_toolbar2, text="一键检查更新", command=self.check_updates).pack(side='left', padx=5)
        tb.Button(frame_toolbar2, text="更新Hanime1日期", command=self.update_hanime1_UpdateAt).pack(side='left', padx=5)

        frame_search = tb.Frame(self)
        frame_search.pack(padx=5, pady=5, anchor=tk.NW, fill=tk.X)
        tb.Label(frame_search, text="搜索:").pack(side='left')
        self.entry_search = tb.Entry(frame_search, width=40)
        self.entry_search.pack(side='left', padx=5)
        self.combobox_source = tb.Combobox(frame_search, values=["Iwara", "Xpv", "Hanime1"], width=10)
        self.combobox_source.set("Xpv")
        self.combobox_source.pack(side='left', padx=5)
        self.btn_search = tb.Button(frame_search, text="搜索", command=self.start_search)
        self.btn_search.pack(side='left', padx=5)
        tb.Button(frame_search, text="下载", command=self.start_download).pack(side='left', padx=5)

        frame_list = tb.Frame(self)
        frame_list.pack(padx=5, pady=5, anchor=tk.NW, fill=tk.BOTH, expand=True)
        self.tree = tb.Treeview(frame_list, columns=(
            "date", 
            "title", 
            "state", 
            "link",
            "view"
        ), show='headings', height=18)
        self.tree.heading("date", text="日期", anchor=tk.W)
        self.tree.heading("title", text="标题", anchor=tk.W)
        self.tree.heading("state", text="状态", anchor=tk.W)
        self.tree.heading("link", text="链接", anchor=tk.W)
        self.tree.heading("view", text="观看次数", anchor=tk.W)
        self.tree.column("date", width=140, stretch=False)
        self.tree.column("title", width=540, stretch=True)
        self.tree.column("state", width=80, stretch=False)
        self.tree.column("link", width=80, stretch=False)
        self.tree.column("view", width=80, stretch=False)
        
        vsb = tb.Scrollbar(frame_list, orient="vertical", command=self.tree.yview)
        hsb = tb.Scrollbar(frame_list, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        frame_list.grid_rowconfigure(0, weight=1)
        frame_list.grid_columnconfigure(0, weight=1)
        
        self.tree.bind("<MouseWheel>", lambda e: self.tree.yview_scroll(int(-1 * (e.delta / 120) * 2), "units"))
        self.tree.bind("<Button-1>", self.on_tree_click)
        self.progressbar = tb.Progressbar(frame_list, orient='horizontal', length=200, mode='determinate')
        self.progressbar.grid(row=2, column=0, sticky='ew', pady=5, columnspan=2)

    def update_tree(self) -> None:
        """更新Treeview显示"""
        # 清空现有项
        self.current_author = self.video_list[0].author if self.video_list else ""
        self.tree.delete(*self.tree.get_children())
        
        # 插入新项
        for video in self.video_list:
            video_path: str = os.path.join(video.dpath, video.savetitle + ".mp4")
            # 如果视频的某个属性为空 则从缓存中读取
            if not all([value for value in video.__dict__.values()]):  # 如果视频存在空属性
                cache: dict = cm.get_cache(video.source)[video.url]  # 从缓存中获取视频信息
                for key, value in cache.items():
                    if value and not getattr(video, key):  # 如果缓存值不为空 且 视频属性为空
                        setattr(video, key, value)

            self.tree.insert('', 'end', values=(
                video.updatedAt, 
                video.title, "已下载" if os.path.isfile(video_path) else "未下载", 
                "打开链接",
                video.numViews))
        logger.debug(f"更新Treeview显示 共 {len(self.video_list)} 条记录")

    def on_tree_click(self, event) -> None:
        # 获取点击位置的行和列
        col: str = self.tree.identify_column(event.x)
        row: str = self.tree.identify_row(event.y)

        # 打开视频网页
        if col == "#4" and row:
            if self.video_list:
                url: str = self.video_list[int(self.tree.index(row))].url
                self.open_edge_private(url)

        # 按照当前列的字符串重新排序tree(再点一次反序)
        if col in self.col_map and self.tree.identify_region(event.x, event.y) == "heading":
            col_name: str = self.col_map[col]
            # 切换升降序
            if self.sort_col == col_name:
                self.sort_reverse = not self.sort_reverse
            else:
                self.sort_col = col_name
                self.sort_reverse = False

            if col == "#1":
                # 日期排序
                self.video_list.sort(key=lambda v: v.updatedAt, reverse=self.sort_reverse)
            elif col == "#2":
                # 标题排序
                self.video_list.sort(key=lambda v: v.title, reverse=self.sort_reverse)
            elif col == "#3":
                # 状态排序（已下载/未下载）
                self.video_list.sort(
                    key=lambda v: os.path.isfile(os.path.join(v.dpath, v.title + ".mp4")),
                    reverse=self.sort_reverse
                )
            elif col == "#5":
                # 观看次数排序
                self.video_list.sort(key=lambda v: v.numViews, reverse=self.sort_reverse)
            
            self.after(0, self.update_tree)

    def open_edge_private(self, url: str, private: bool=True) -> None:
        
        if not url:
            self.after(0, lambda: Messagebox.show_warning("没有可用的搜索结果", "提示"))
            return
        logger.info(f"在Edge无痕模式中打开: {url}")
        try:
            if private:
                subprocess.Popen([EDGE_FILE, "--inprivate", url])
            else:
                subprocess.Popen([EDGE_FILE, url])
        except (FileNotFoundError, subprocess.SubprocessError) as e:
            logger.error(f"打开Edge失败: {e}")
    
    def open_local_folder(self) -> None:
        download_path: str = self.video_list[0].dpath
        logger.info(f"打开本地文件夹: {download_path}")
        try:
            os.startfile(download_path)
        except Exception as e:
            logger.error(f"打开本地文件夹失败: {e}")
    
    def on_login_button_click(self) -> None:
        # 检查当前是否已登录
        if sm.settings.get("Iwara_Token", ""):
            # 显示确认对话框
            if Messagebox.yesno("您已登录，是否要退出登录？", "确认") == '确认':
                del sm.settings["Iwara_Token"]
                sm.save_settings()
                self.update_login_status(False)
                Messagebox.show_info("已成功退出登录", "提示", parent=self)
        else:
            # 显示登录窗口
            Window_Login(self)
    
    def update_login_status(self, is_logged_in: bool) -> None:
        """更新登录按钮的显示状态"""
        if is_logged_in:
            self.btn_login.config(text="已登录")
            # ttkbootstrap中设置按钮背景色的方法
            self.btn_login.configure(bootstyle="success")
        else:
            self.btn_login.config(text="登录")
            # 重置按钮样式为默认值
            self.btn_login.configure(bootstyle="primary")
        
        logger.info(f"更新登录状态: {'已登录' if is_logged_in else '未登录'}")
    
    def start_search(self) -> None:
        keyword: str = self.entry_search.get().strip()
        source: str = self.combobox_source.get()
        if not keyword:
            return
        
        logger.info(f"开始在 {source} 搜索: '{keyword}'")
        self.btn_edge.config(state=tk.DISABLED)
        self.btn_local.config(state=tk.DISABLED)
        self.tree.delete(*self.tree.get_children())
        threading.Thread(target=self._perform_search, args=(keyword, source), daemon=True).start()

    def _perform_search(self, keyword: str, source: str) -> None:
        """Executes the search operation in a background thread."""
        try:
            if source == "Iwara":
                # Iwara搜索需要特殊处理，因为需要先搜索作者
                authors: list[stru_iw_author] = Search_Engine.iw_search_author(keyword)
                if not authors:
                    self.after(0, lambda: Messagebox.show_info("未找到相关作者", "提示"))
                    return
                
                if len(authors) == 1:
                    self.selected_author: str = authors[0].username
                    logger.info(f"仅找到一位作者: {self.selected_author}")
                    self.video_list = Search_Engine.iw_search_video(authors[0].id)  # pyright: ignore[reportAttributeAccessIssue]
                    self.url_for_edge_to_open = f"{sm.settings.get('Iwara_Hostname', DEFAULT_SETTINGS['Iwara_Hostname'])}/profile/{self.selected_author}/videos"
                    self.after(0, lambda: self.btn_edge.configure(state=tk.NORMAL))
                    self.after(0, lambda: self.btn_local.configure(state=tk.NORMAL))
                else:
                    author_names: list[str] = [author.username for author in authors]
                    author_selected_event: threading.Event = threading.Event()
                    self.after(0, self.prompt_for_author, author_names, author_selected_event)
                    author_selected_event.wait()

                    if self.selected_author:
                        logger.info(f"用户选择了作者: {self.selected_author}")
                        # 找到对应作者的id
                        selected_author_id: str = ""
                        for author in authors:
                            if author.username == self.selected_author:
                                selected_author_id = author.id
                                break
                        if selected_author_id:
                            self.video_list = Search_Engine.iw_search_video(selected_author_id)  # pyright: ignore[reportAttributeAccessIssue]
                            self.url_for_edge_to_open = f"{sm.settings.get('Iwara_Hostname', DEFAULT_SETTINGS['Iwara_Hostname'])}/profile/{self.selected_author}/videos"
                        else:
                            logger.warning("未找到所选作者的ID")
                            self.video_list = []
                    else:
                        logger.info("用户取消了作者选择")
                        self.video_list = []
            elif source in channel_manager.list_channels():
                # 使用渠道管理器进行搜索
                self.video_list = channel_manager.search(keyword, source)
                if not self.video_list:
                    return
                # 安全地获取第一个视频的furl属性
                self.url_for_edge_to_open = getattr(self.video_list[0], 'furl', '')
                self.selected_author = getattr(self.video_list[0], 'author', '')
            else:
                logger.warning(f"未知的来源: {source}")
                self.video_list = []
            
            if self.url_for_edge_to_open:
                self.after(0, lambda: self.btn_edge.configure(state=tk.NORMAL))
            self.after(0, lambda: self.btn_local.configure(state=tk.NORMAL))

            self.dumpfunction_update_old_title_video()
            if self.video_list:
                self.after(0, self.update_tree)

        except Exception as e:
            logger.error(f"搜索时发生未知错误: {e}")

    def prompt_for_author(self, authors: list[str], event: threading.Event) -> None:
        def author_selection_callback(author: str) -> None:
            self.selected_author = author
            event.set()
        Window_AuthorSelection(self, authors, author_selection_callback)

    def start_download(self) -> None:
        selected_items: tuple[str, ...] = self.tree.selection()
        if not selected_items:
            self.after(0, lambda: Messagebox.show_warning("请先选择要下载的视频", "提示"))
            return

        selected_videos_indices: list[int] = [self.tree.index(item) for item in selected_items]
        download_path: str = self.video_list[selected_videos_indices[0]].dpath
        self.progressbar.configure(maximum=len(selected_items), value=0)

        logger.info(f"开始下载 {len(selected_items)} 个视频到: {download_path} ")
        for i, item_id in enumerate(selected_items):
            video_data: stru_iw_video|stru_xpv_video|stru_hanime1_video = self.video_list[selected_videos_indices[i]]
            self.download_queue.put(video_data)

    def start_download_custom(self) -> None:
        custom_url: str = self.entry_custom_url.get().strip()
        if not custom_url:
            self.after(0, lambda: Messagebox.show_warning("请输入自定义URL", "提示"))
            return
        self.download_queue.put(stru_xpv_custom(data={"url": custom_url}))

    def dumpfunction_update_old_title_video(self) -> None:
        quantity: int = 0
        for video in self.video_list:
            src_title: str = re.sub(r'\s*\[.*?\]\s*', '', video.title, count=1)
            src = os.path.join(video.dpath, f"{src_title}.mp4")
            try:
                if os.path.exists(src):
                    dst = os.path.join(video.dpath, f"{video.title}.mp4")
                    os.rename(src, dst)
                    logger.info(f"更新旧标题视频 {src_title} 为 {video.title}")
                    quantity += 1
            except Exception as e:
                logger.error(f"更新旧标题视频 {src_title} 时发生错误: {e}")
        logger.info(f"更新旧标题视频完成 更新 {quantity} 条")
        self.after(0, self.update_tree)

    def check_updates(self) -> None:
        """一键检查更新功能"""
        logger.info("开始一键检查更新")
        
        # 获取收藏夹中的xpv作者列表
        favor_data: dict[str, list[str]] = sm.settings.get("Favor", {})
        xpv_authors = favor_data.get("xpv", [])
        
        if not xpv_authors:
            Messagebox.show_info("收藏夹中没有Xpv作者", "提示", parent=self)
            return
        
        # 禁用主窗口的某些功能
        self.btn_local.config(state=tk.DISABLED)
        self.btn_edge.config(state=tk.DISABLED)
        self.btn_search.config(state=tk.DISABLED)
        
        # 在后台线程中执行检查更新
        threading.Thread(target=self._check_updates_thread, args=(xpv_authors,), daemon=True).start()

    def _check_updates_thread(self, xpv_authors: list[str]) -> None:
        """检查更新的后台线程"""
        new_videos = []
        
        try:
            # 使用单个线程依次访问每个作者
            for author in xpv_authors:
                logger.info(f"检查作者 {author} 的更新")
                # 获取该作者的所有视频
                videos = Search_Engine.xpv_search_video(author)
                
                if videos:
                    # 从最新的视频开始检索，直到找到已经下载过的视频
                    index: int = 0
                    for video in videos:
                        # 检查视频是否已下载
                        video_path = os.path.join(video.dpath, video.title + ".mp4")
                        if os.path.isfile(video_path):
                            logger.info(f"找到已下载的视频: {video.title}，停止检索该作者")
                            break
                        index += 1
                        # 超过5个视频就停止搜索
                        if index > 5:
                            logger.info(f"超过5个视频未找到已下载视频，停止检索 {author}")
                            break

                        else:
                            # 添加到未下载列表
                            new_videos.append(video)
        
        except Exception as e:
            logger.error(f"检查更新时发生错误: {e}")
            self.after(0, lambda: Messagebox.show_error(f"检查更新时发生错误: {e}", "错误", parent=self))
        
        finally:
            # 恢复主窗口功能
            self.after(0, lambda: self.btn_local.config(state=tk.NORMAL))
            self.after(0, lambda: self.btn_edge.config(state=tk.NORMAL))
            self.after(0, lambda: self.btn_search.config(state=tk.NORMAL))
            
            # 显示结果
            if new_videos:
                logger.info(f"找到 {len(new_videos)} 个未下载的新视频")
                self.after(0, lambda: Window_CheckUpdate(self, new_videos))
            else:
                self.after(0, lambda: Messagebox.show_info("没有找到未下载的新视频", "提示", parent=self))
            
            logger.info("一键检查更新完成")

    def update_hanime1_UpdateAt(self) -> None:
        """更新Hanime1视频的UpdateAt属性"""
        def th() -> None:
            logger.info("开始更新Hanime1视频的UpdateAt属性")
            
            # 获取所有视频
            videos: list[stru_hanime1_video] = [video for video in self.video_list if video.source == "Hanime1"]  # pyright: ignore[reportAssignmentType]
            
            # 更新Hanime1视频的UpdateAt属性
            for video in videos:
                video.update_updatedAt()
                logger.info(f"更新视频 {video.title} 的UpdateAt属性为 {video.updatedAt}")
            
            logger.info("更新Hanime1视频的UpdateAt属性完成")
            cm.set_cache("Hanime1", videos)
            self.after(0, self.update_tree)
        
        # 在后台线程中执行更新
        threading.Thread(target=th, daemon=True).start()
        
if __name__ == "__main__":
    try:
        app = Win_Main()
        app.mainloop()
    except Exception as e:
        logger.critical(f"程序因错误将会退出: {e}")
        input("按任意键继续...")
