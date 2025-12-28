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
        self.geometry("800x550")
        # 存储动态创建的控件
        self.hostname_entries: dict[str, tb.Entry] = {}
        self.api_hostname_entries: dict[str, tb.Entry] = {}
        self.download_path_entries: dict[str, tb.Entry] = {}
        self.create_widgets()
        self.fill_entry()

    def create_widgets(self) -> None:
        """Creates the widgets for the settings window."""
        # 动态创建每个频道的设置项
        for channel_name, config in CHANNELS_CONFIG.items():
            # 创建主机名设置
            frame_hostname = tb.Frame(self)
            frame_hostname.pack(anchor=tk.NW, pady=5, padx=10)
            tb.Label(frame_hostname, text=f"{channel_name}主机名:").pack(side='left')
            entry_hostname = tb.Entry(frame_hostname, width=50)
            entry_hostname.pack(side='left', padx=5)
            self.hostname_entries[channel_name] = entry_hostname
            
            # 创建API主机名设置（如果有）
            if "api_hostname_key" in config:
                frame_api_hostname = tb.Frame(self)
                frame_api_hostname.pack(anchor=tk.NW, pady=5, padx=10)
                tb.Label(frame_api_hostname, text=f"{channel_name} API主机名:").pack(side='left')
                entry_api_hostname = tb.Entry(frame_api_hostname, width=50)
                entry_api_hostname.pack(side='left', padx=5)
                self.api_hostname_entries[channel_name] = entry_api_hostname
            
            # 创建下载路径设置
            frame_path = tb.Frame(self)
            frame_path.pack(anchor=tk.NW, pady=5, padx=10)
            tb.Label(frame_path, text=f"{channel_name}下载路径:").pack(side='left')
            entry_path = tb.Entry(frame_path, width=80)
            entry_path.pack(side='left', padx=5)
            tb.Button(frame_path, text="浏览", command=lambda entry=entry_path: self.browse_directory(entry)).pack(side='left')
            self.download_path_entries[channel_name] = entry_path
        
        # 自定义下载路径
        frame_custom_path = tb.Frame(self)
        frame_custom_path.pack(anchor=tk.NW, pady=5, padx=10)
        tb.Label(frame_custom_path, text="自定义下载路径:").pack(side='left')
        self.entry_custom_path = tb.Entry(frame_custom_path, width=80)
        self.entry_custom_path.pack(side='left', padx=5)
        tb.Button(frame_custom_path, text="浏览", command=lambda: self.browse_directory(self.entry_custom_path)).pack(side='left')
        
        # 最大线程数
        frame_max_threads = tb.Frame(self)
        frame_max_threads.pack(anchor=tk.NW, pady=5, padx=10)
        tb.Label(frame_max_threads, text="最大线程数:").pack(side='left')
        self.entry_max_threads = tb.Entry(frame_max_threads, width=5)
        self.entry_max_threads.pack(side='left', padx=5)

        # 检查证书
        frame_check_cert = tb.Frame(self)
        frame_check_cert.pack(anchor=tk.NW, pady=5, padx=10)
        self.check_cert_var = tb.BooleanVar()
        tb.Checkbutton(frame_check_cert, text="检查证书", variable=self.check_cert_var).pack(side='left')

        # 保存按钮
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
        # 填充每个频道的设置
        for channel_name, config in CHANNELS_CONFIG.items():
            # 填充主机名
            if channel_name in self.hostname_entries:
                hostname_key = config["hostname_key"]
                self.hostname_entries[channel_name].insert(0, sm.settings.get(hostname_key, DEFAULT_SETTINGS[hostname_key]))
            
            # 填充API主机名（如果有）
            if channel_name in self.api_hostname_entries and "api_hostname_key" in config:
                api_hostname_key = config["api_hostname_key"]
                self.api_hostname_entries[channel_name].insert(0, sm.settings.get(api_hostname_key, DEFAULT_SETTINGS[api_hostname_key]))
            
            # 填充下载路径
            if channel_name in self.download_path_entries:
                download_path_key = config["download_path_key"]
                self.download_path_entries[channel_name].insert(0, sm.settings.get(download_path_key, DEFAULT_SETTINGS[download_path_key]))
        
        # 填充通用设置
        self.entry_custom_path.insert(0, sm.settings.get("Custom_Download_Path", DEFAULT_SETTINGS["Custom_Download_Path"]))
        self.entry_max_threads.insert(0, str(sm.settings.get("Max_Threads", DEFAULT_SETTINGS["Max_Threads"])))
        self.check_cert_var.set(sm.settings.get("Check_Cert", DEFAULT_SETTINGS["Check_Cert"]))

    def on_close(self) -> None:
        # 保存每个频道的设置
        for channel_name, config in CHANNELS_CONFIG.items():
            # 保存主机名
            if channel_name in self.hostname_entries:
                hostname_key = config["hostname_key"]
                sm.settings[hostname_key] = self.hostname_entries[channel_name].get().strip()
            
            # 保存API主机名（如果有）
            if channel_name in self.api_hostname_entries and "api_hostname_key" in config:
                api_hostname_key = config["api_hostname_key"]
                sm.settings[api_hostname_key] = self.api_hostname_entries[channel_name].get().strip()
            
            # 保存下载路径
            if channel_name in self.download_path_entries:
                download_path_key = config["download_path_key"]
                sm.settings[download_path_key] = self.download_path_entries[channel_name].get().strip()
        
        # 保存通用设置
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
    def __init__(self, master: "Win_Main", new_videos: list[stru_hanime1_video]) -> None:
        super().__init__()
        self.master: "Win_Main" = master  # pyright: ignore[reportIncompatibleVariableOverride]
        self.new_videos = new_videos
        self.sorted_videos: list[stru_hanime1_video] = []  # 添加排序后的视频列表
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
        video: stru_hanime1_video
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

        # 获取所有已注册频道
        self.channels = [channel.lower() for channel in channel_manager.list_channels()]
        # 初始化收藏数据，确保每个频道都有对应的列表
        self.favor_data: dict = sm.settings.get("Favor", {})
        for channel in self.channels:
            if channel not in self.favor_data:
                self.favor_data[channel] = []
        self.current_channel = self.channels[0] if self.channels else ""  # 默认渠道

        # 存储动态创建的组件
        self.frames: dict[str, tb.Frame] = {}
        self.trees: dict[str, tb.Treeview] = {}

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
        
        # 动态创建频道标签页
        for channel in self.channels:
            # 创建标签页框架
            frame = tb.Frame(self.notebook)
            self.frames[channel] = frame
            self.notebook.add(frame, text=channel.capitalize())
            
            # 创建Treeview
            tree = tb.Treeview(frame, columns=("author"), show='headings', height=15)
            tree.heading("author", text="作者")
            tree.column("author", stretch=True)
            
            # 添加滚动条
            vsb = tb.Scrollbar(frame, orient="vertical", command=tree.yview)
            tree.configure(yscrollcommand=vsb.set)
            tree.bind("<MouseWheel>", lambda e, tree=tree: tree.yview_scroll(int(-1 * (e.delta / 120) * 2), "units"))
            
            # 布局
            tree.grid(row=0, column=0, sticky='nsew')
            vsb.grid(row=0, column=1, sticky='ns')
            frame.grid_rowconfigure(0, weight=1)
            frame.grid_columnconfigure(0, weight=1)
            
            # 存储tree实例
            self.trees[channel] = tree
            
            # 填充数据
            for author in self.favor_data.get(channel, []):
                tree.insert("", "end", values=(author,))
            
            # 绑定双击事件
            tree.bind("<Double-1>", self.on_select)
        
        # 绑定标签页切换事件
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_change)

    def on_tab_change(self, event: Optional[tk.Event] = None) -> None:
        """Handles tab change event to update current channel."""
        selected_tab = self.notebook.select()
        # 遍历所有频道，查找对应的frame
        for channel, frame in self.frames.items():
            if selected_tab == frame._w:  # pyright: ignore[reportAttributeAccessIssue]
                self.current_channel = channel
                break
    
    def on_select(self, event: Optional[tk.Event] = None) -> None:
        """Handles author selection and closes the window."""
        # 根据当前渠道获取对应的tree
        current_tree = self.trees.get(self.current_channel)
        if not current_tree:
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
            self.master.combobox_source.set(self.current_channel.capitalize())
            
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

        def save_favor(authors_dict: dict[str, list[str]]) -> None:
            """Saves the favor list for all channels."""
            # 处理每个频道的作者列表
            for channel, authors in authors_dict.items():
                # 去重并去除空字符串
                unique_authors = list(dict.fromkeys([a.strip() for a in authors if a.strip()]))
                # 按名字首字母正序排序
                unique_authors.sort(key=lambda x: x.lower())
                self.favor_data[channel] = unique_authors
            
            # 保存到设置
            sm.settings["Favor"] = self.favor_data
            sm.save_settings()
            
            # 更新所有列表
            for channel, tree in self.trees.items():
                tree.delete(*tree.get_children())
                for author in self.favor_data.get(channel, []):
                    tree.insert("", "end", values=(author,))
                
            logger.info(f"保存了 {len(self.channels)} 个频道的收藏夹作者")

        # 创建Notebook用于编辑不同渠道的收藏列表
        notebook_edit = tb.Notebook(Window_Edit)
        notebook_edit.pack(pady=5, padx=10, fill=tk.BOTH, expand=True)
        
        # 动态创建编辑区域
        text_inputs: dict[str, tb.Text] = {}
        for channel in self.channels:
            # 创建标签页
            frame_edit = tb.Frame(notebook_edit)
            notebook_edit.add(frame_edit, text=channel.capitalize())
            
            # 创建编辑区域
            tb.Label(frame_edit, text="每行一个作者名:").pack(anchor=tk.W, pady=(10, 0))
            text_input = tb.Text(frame_edit, wrap=tk.WORD)
            text_input.pack(fill=tk.BOTH, expand=True, pady=5, padx=10)
            # 填充现有数据
            for author in self.favor_data.get(channel, []):
                text_input.insert(tk.END, author + "\n")
            text_inputs[channel] = text_input

        frame_toolbars = tb.Frame(Window_Edit)
        frame_toolbars.pack(fill=tk.X, pady=5, padx=5)
        
        def on_save():
            logger.info("保存收藏夹")
            # 收集所有频道的作者数据
            authors_dict = {channel: text_input.get("1.0", tk.END).strip().splitlines() for channel, text_input in text_inputs.items()}
            save_favor(authors_dict)
            Window_Edit.destroy()
        
        tb.Button(frame_toolbars, text="保存", command=on_save).pack(side='left', padx=5)
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
        # 获取所有已注册频道，首字母大写显示
        channel_list = [channel.capitalize() for channel in channel_manager.list_channels()]
        self.combobox_source = tb.Combobox(frame_search, values=channel_list, width=10)
        # 默认选择第一个频道或 "Xpv"（如果存在）
        default_channel = "Xpv" if "Xpv" in channel_list else channel_list[0] if channel_list else ""
        self.combobox_source.set(default_channel)
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
        
        # 获取收藏夹中的hanime1作者列表
        favor_data: dict[str, list[str]] = sm.settings.get("Favor", {})
        hanime1_authors = favor_data.get("hanime1", [])
        
        if not hanime1_authors:
            Messagebox.show_info("收藏夹中没有Hanime1作者", "提示", parent=self)
            return
        
        # 禁用主窗口的某些功能
        self.btn_local.config(state=tk.DISABLED)
        self.btn_edge.config(state=tk.DISABLED)
        self.btn_search.config(state=tk.DISABLED)
        
        # 在后台线程中执行检查更新
        threading.Thread(target=self._check_updates_thread, args=(hanime1_authors,), daemon=True).start()

    def _check_updates_thread(self, hanime1_authors: list[str]) -> None:
        """检查更新的后台线程"""
        new_videos: list[stru_hanime1_video] = []
        
        try:
            # 使用单个线程依次访问每个作者
            for author in hanime1_authors:
                logger.info(f"检查作者 {author} 的更新")
                # 获取该作者的所有视频
                videos = Search_Engine.hanime1_search_video(author)
                
                if videos:
                    # 从最新的视频开始检索，直到找到已经下载过的视频
                    index: int = 0
                    for video in videos:
                        # 检查视频是否已下载
                        if any([video.title in t for t in os.listdir(video.dpath)]):
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
            
            # 更新视频日期
            for video in new_videos:
                video._update_updatedAt_from_url()

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
                video._update_updatedAt_from_url()
                logger.info(f"更新视频 {video.title} 的UpdateAt属性为 {video.updatedAt}")
                self.after(0, self.update_tree)
            
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
