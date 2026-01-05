from typing import Optional
from colorama import Fore, Style
import time

class DownloadProgressTracker:
    """下载进度跟踪器"""
    
    def __init__(self, filename: str):
        self.filename = filename
        self.total_size: Optional[int] = None
        self.start_time = time.time()
        self.last_update_time = self.start_time
        self.last_downloaded = 0
        self.is_running = True
        self.completed = False
        self.fps = 0.5
    
    def update(self, downloaded: int):
        """更新下载进度（单线程模式）"""
        current_time = time.time()
        time_diff = current_time - self.last_update_time
        
        # 每秒更新一次显示
        if time_diff >= self.fps:
            speed = (downloaded - self.last_downloaded) / time_diff
            self._display_progress(downloaded, speed)
            self.last_update_time = current_time
            self.last_downloaded = downloaded
    
    def monitor_chunk_progress(self, chunk_progress: list):
        """监控分块下载进度（多线程模式）"""
        while self.is_running and not self.completed:
            current_time = time.time()
            time_diff = current_time - self.last_update_time
            
            if time_diff >= self.fps:
                total_downloaded = sum(chunk_progress)
                speed = (total_downloaded - self.last_downloaded) / time_diff
                
                self._display_progress(total_downloaded, speed)
                
                self.last_update_time = current_time
                self.last_downloaded = total_downloaded
            
            # 检查是否完成
            if self.total_size and self.last_downloaded >= self.total_size:
                self.completed = True
                break
                
            time.sleep(0.1)  # 降低CPU使用率
    
    def _display_progress(self, downloaded: int, speed: float):
        """显示下载进度"""
        speed_str = self._format_speed(speed)
        
        # 先输出空格清行，再输出实际内容，防止残余字符
        clear_line = "\r" + " " * 80 + "\r"
        if self.total_size:
            percent = (downloaded / self.total_size) * 100
            size_str = f"{self._format_size(downloaded)}/{self._format_size(self.total_size)}"
            print(f"{clear_line}{Fore.GREEN}{self.filename}{Style.RESET_ALL}: {Fore.YELLOW}{percent:.1f}%{Style.RESET_ALL} | {Fore.BLUE}{size_str}{Style.RESET_ALL} | {Fore.CYAN}{speed_str}{Style.RESET_ALL}", end="", flush=True)
        else:
            print(f"{clear_line}{Fore.GREEN}{self.filename}{Style.RESET_ALL}: {Fore.BLUE}{self._format_size(downloaded)}{Style.RESET_ALL} | {Fore.CYAN}{speed_str}{Style.RESET_ALL}", end="", flush=True)
    
    def _format_speed(self, speed_bytes: float) -> str:
        """格式化速度显示"""
        if speed_bytes >= 1024 * 1024:
            return f"{speed_bytes / (1024 * 1024):.2f} MB/s"
        elif speed_bytes >= 1024:
            return f"{speed_bytes / 1024:.2f} KB/s"
        else:
            return f"{speed_bytes:.2f} B/s"
    
    def _format_size(self, size_bytes: float) -> str:
        """格式化文件大小显示"""
        if size_bytes == 0:
            return "0B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
            
        return f"{size_bytes:.2f}{size_names[i]}"
    
    def stop(self):
        """停止进度监控"""
        self.is_running = False
    
    def finish(self):
        """完成下载"""
        self.completed = True
        total_time = time.time() - self.start_time
        if self.total_size:
            avg_speed = self.total_size / total_time if total_time > 0 else 0
            speed_str = self._format_speed(avg_speed)
            print(f"\r{Fore.GREEN}{self.filename}{Style.RESET_ALL}: 下载完成! 总时间: {Fore.YELLOW}{total_time:.1f}s{Style.RESET_ALL}, 平均速度: {Fore.CYAN}{speed_str}{Style.RESET_ALL}")
        else:
            print(f"\r{Fore.GREEN}{self.filename}{Style.RESET_ALL}: 下载完成! 总时间: {Fore.YELLOW}{total_time:.1f}s{Style.RESET_ALL}")
