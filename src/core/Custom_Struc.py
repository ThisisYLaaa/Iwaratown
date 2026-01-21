import datetime
import os
import re
from typing import Any, cast

from bs4 import BeautifulSoup

from ..config.Init_Settings import *
from ..config.Settings_Manager import sm, cm
from ..utils.CScraper import scraper_manager
from ..utils.Logger import get_logger

logger = get_logger("Custom_Struc")

class stru_xpv_video:
    def __init__(self, data: dict):
        # 频道必须
        self.furl: str = data.get("furl", "").strip()
        self.source: str = "Xpv"
        self.url: str = f"{sm.settings['Xpv_Hostname']}{data.get('url', '')}"
        self.title: str = re.sub(r'[\/*?:"<>|]', "_", data.get("title", "").strip())
        self.updatedAt: str = data.get("updatedAt", "").strip()
        self.updatedAt = datetime.datetime.fromisoformat(self.updatedAt.replace("Z", "+00:00")).strftime("%Y-%m-%d")
        self.savetitle: str = "".join([f"[{self.updatedAt}]", data.get("title", "").strip()])
        self.savetitle = re.sub(r'[\/*?:"<>|]', "_", self.savetitle)
        self.author: str = data.get("author", "").strip()
        self.numViews: int = data.get("numViews", 0)
        self.dpath: str = sm.settings.get("Xpv_Download_Path", DEFAULT_SETTINGS["Xpv_Download_Path"])
        self.dpath = os.path.join(self.dpath, self.author)

    def get(self, key: str, default: Any = None) -> Any:
        return self.__dict__.get(key, default)
    
    def get_updatedAt_timestamp(self) -> float:
        return datetime.datetime.fromisoformat(self.updatedAt.replace("Z", "+00:00")).timestamp()

class stru_xpv_custom:
    def __init__(self, data: dict):
        # xpv变种
        self.url: str = data.get('url', '')
        self.type: str = self.get_type()
        self.source: str = "Xpv"  # 添加source属性，确保渠道管理器能识别
        self.dpath: str = ""  # 不需要
    
    def get_type(self) -> str:
        """video: 社区帖子; pic: 图片"""
        for k, v in XPV_CUSTOM_MAP.items():
            if k in self.url:
                return v
        return "Unknown"
    
    def get(self, key: str, default: Any = None) -> Any:
        return self.__dict__.get(key, default)

class stru_hanime1_video:
    def __init__(self, data: dict):
        # 频道必须
        self.furl: str = data.get("furl", "").strip()
        self.source: str = "Hanime1"
        self.url: str = data.get("url", "").strip()
        self.title: str = data.get("title", "").strip()
        self.title = re.sub(r'[\/*?:"<>|]', "_", self.title)
        self.updatedAt: str = ""  # 一般没有
        self.savetitle: str = ""  # 一般没有
        self.author: str = data.get("author", "").strip()
        self.numViews: int = data.get("numViews", 0)
        self.dpath: str = sm.settings.get("Hanime1_Download_Path", DEFAULT_SETTINGS["Hanime1_Download_Path"])
        self.dpath = os.path.join(self.dpath, self.author)

        # 如果视频的某个属性为空 则从缓存中读取
        if not all([value for value in self.__dict__.values()]):  # 如果视频存在空属性
            cache: dict = cm.get_cache(self.source).get(self.url, {})  # 从缓存中获取视频信息
            for key, value in cache.items():
                if value and not getattr(self, key):  # 如果缓存值不为空 且 视频属性为空
                    setattr(self, key, value)

        # 如果缓存没有, 则从文件名中提取日期
        self._update_updatedAt_from_file()
        self._rename_video_file()

    def get(self, key: str, default: Any = None) -> Any:
        return self.__dict__.get(key, default)
    
    def _extract_date_from_filename(self, filename: str) -> str:
        """从文件名中提取YYYY-MM-DD格式的日期"""
        match = re.search(r"\d{4}-\d{2}-\d{2}", filename)
        return match.group() if match else ""
    
    def _find_local_video_file(self) -> str:
        """查找本地视频文件，返回文件路径，如果不存在返回空字符串"""
        if not os.path.exists(self.dpath):
            return ""

        # 首先尝试查找带日期前缀的文件
        matching_files = [os.path.join(self.dpath, t) for t in os.listdir(self.dpath) if self.title in t]
        
        if matching_files:
            return matching_files[0]  # 返回第一个匹配的文件

        return ""  # 未找到匹配的文件
    
    def _update_savetitle(self, updatedAt: str) -> None:
        """更新savetitle，仅当提供了有效日期时"""
        if not updatedAt:
            return

        self.updatedAt = updatedAt
        self.savetitle = f"[{updatedAt}]{self.title}"
        self.savetitle = re.sub(r'[\/*?:"<>|]', "_", self.savetitle)
    
    def _rename_video_file(self) -> None:
        """重命名视频文件，支持多种旧文件名格式"""
        if not self.updatedAt:
            return
        
        if not os.path.exists(self.dpath):
            return
        
        old_path = os.path.join(self.dpath, f"{self.title}.mp4")
        new_path = os.path.join(self.dpath, f"{self.savetitle}.mp4")
        if os.path.exists(new_path) or not os.path.exists(old_path):
            return
        try:
            os.rename(old_path, new_path)
            logger.debug(f"重命名文件: {old_path} -> {new_path}")
        except Exception as e:
            logger.error(f"重命名文件失败 {old_path} -> {new_path}: {e}")
    
    def _update_updatedAt_from_file(self) -> bool:
        """从本地文件中更新updatedAt，成功返回True，否则返回False"""
        video_path = self._find_local_video_file()
        if not video_path:
            return False
        
        filename = os.path.basename(video_path)
        date = self._extract_date_from_filename(filename)
        if date:
            self._update_savetitle(date)
            return True
        
        return False
    
    def _update_updatedAt_from_url(self) -> bool:
        """从URL中更新updatedAt，成功返回True，否则返回False"""
        if self.updatedAt:
            return True
        
        try:
            # 定义日期信息提取函数，减少重复代码
            def extract_date_from_chromium() -> str:
                # 获取唯一的Chrome实例
                main_page = scraper_manager.get_main_chromium_page()
                
                # 新建标签页
                logger.info(f"新建标签页，访问: {self.url}")
                new_tab = main_page.new_tab()
                
                try:
                    # 在新标签页中访问网页
                    new_tab.get(self.url)
                    
                    # 等待视频详情元素出现 - 使用更可靠的选择器，避免hidden类影响
                    # 选择器说明：.video-details-wrapper是包含视频详情的容器，不使用hidden-*类以提高兼容性
                    logger.info("等待元素 .video-details-wrapper 出现")
                    # 使用tag:div@@class:video-details-wrapper语法，模糊匹配class包含video-details-wrapper的div元素
                    video_details_selector = "tag:div@@class:video-details-wrapper"
                    new_tab.wait.ele_displayed(video_details_selector, timeout=10)
                    
                    # 提取日期信息 - 直接在视频详情容器内查找包含日期的元素
                    div_info = new_tab.ele(video_details_selector)
                    div_text: str = cast(str, div_info.text)
                    return self._extract_date_from_filename(div_text)
                finally:
                    # 确保标签页被关闭
                    tabs = main_page.get_tabs()
                    if len(tabs) > 1:
                        logger.info("关闭标签页")
                        try:
                            new_tab.close()
                        except:
                            pass
            
            # 检查cloudscraper是否已失败
            if scraper_manager.is_cs_failed():
                logger.info(f"cloudscraper已失败，直接使用dissionpage: {self.url}")
                # 直接使用dissionpage
                date = extract_date_from_chromium()
                if date:
                    self._update_savetitle(date)
                    self._rename_video_file()
                    return True
                return False
            else:
                # Hanime1首先尝试使用cloudscraper
                logger.info(f"首先尝试使用cloudscraper爬取Hanime1: {self.url}")
                try:
                    response = scraper_manager.get_cloud_scraper().get_response(self.url, timeout=10)
                    if response.status_code == 403:
                        logger.warning(f"cloudscraper返回403，切换到dissionpage")
                        # 设置cloudscraper失败标志
                        scraper_manager.set_cs_failed(True)
                        # 使用dissionpage
                        date = extract_date_from_chromium()
                        if date:
                            self._update_savetitle(date)
                            self._rename_video_file()
                            return True
                        return False
                    else:
                        response.raise_for_status()
                        # 使用cloudscraper返回的内容解析
                        soup = BeautifulSoup(response.text, "html.parser")
                        # 使用更可靠的选择器，模糊匹配class包含video-details-wrapper的div元素
                        div_info = soup.select_one("div.video-details-wrapper")
                        if div_info:
                            date = self._extract_date_from_filename(div_info.text)
                            if date:
                                self._update_savetitle(date)
                                self._rename_video_file()
                                return True
                except Exception as e:
                    logger.warning(f"cloudscraper爬取失败: {e}")
                    # 非403错误，继续使用cloudscraper，不切换
                    # 使用dissionpage作为备选方案
                    date = extract_date_from_chromium()
                    if date:
                        self._update_savetitle(date)
                        self._rename_video_file()
                        return True
                    return False
            
        except Exception as e:
            logger.error(f"访问视频页面失败 {self.url}: {e}")
        
        return False
    
    def update_date_from_chromium_tab(self, tab) -> bool:
        """从Chromium标签页中更新日期信息"""
        try:
            # 等待视频详情元素出现 - 使用更可靠的选择器，避免hidden类影响
            logger.info("等待元素 .video-details-wrapper 出现")
            # 使用tag:div@@class:video-details-wrapper语法，模糊匹配class包含video-details-wrapper的div元素
            video_details_selector = "tag:div@@class:video-details-wrapper"
            tab.wait.ele_displayed(video_details_selector, timeout=10)
            
            # 提取日期信息 - 直接在视频详情容器内查找包含日期的元素
            div_info = tab.ele(video_details_selector)
            date = self._extract_date_from_filename(div_info.text)
            if date:
                self._update_savetitle(date)
                return True
            return False
        except Exception as e:
            logger.error(f"从标签页提取日期失败: {e}")
            return False
    
    def get_updatedAt_timestamp(self) -> float:
        """将YYYY-MM-DD格式的日期转换为时间戳"""
        try:
            if self.updatedAt:
                return datetime.datetime.strptime(self.updatedAt, "%Y-%m-%d").timestamp()
            else:
                # 如果没有日期，返回一个较早的时间戳
                return 0.0
        except ValueError:
            # 如果日期格式不正确，返回一个较早的时间戳
            return 0.0
    