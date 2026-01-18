import datetime
import os
import re
from typing import Any

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
        
        soup = None
        
        try:
            # 根据视频来源选择爬虫策略
            if self.source == "Hanime1":
                # 检查hanime1 cloudscraper是否已失败
                if scraper_manager.is_hanime1_cloudscraper_failed():
                    logger.info(f"hanime1 cloudscraper已失败，直接使用chromium scraper: {self.url}")
                    # 直接使用chromium scraper
                    try:
                        soup = scraper_manager.get_chromium_scraper().get_soup(
                            self.url,
                            10
                        )
                    except Exception as ce:
                        logger.error(f"chromium scraper爬取失败: {ce}")
                        return False
                else:
                    # Hanime1首先尝试使用cloudscraper
                    logger.info(f"首先尝试使用cloudscraper爬取Hanime1: {self.url}")
                    try:
                        response = scraper_manager.get_cloud_scraper().get_response(self.url, timeout=10)
                        if response.status_code == 403:
                            logger.warning(f"cloudscraper返回403，切换到chromium scraper")
                            # 设置cloudscraper失败标志
                            scraper_manager.set_hanime1_cloudscraper_failed(True)
                            # 使用chromium scraper
                            soup = scraper_manager.get_chromium_scraper().get_soup(
                            self.url,
                            10
                        )
                        else:
                            response.raise_for_status()
                            soup = BeautifulSoup(response.text, "html.parser")
                    except Exception as e:
                        logger.warning(f"cloudscraper爬取失败: {e}，切换到chromium scraper")
                        # 设置cloudscraper失败标志
                        scraper_manager.set_hanime1_cloudscraper_failed(True)
                        # 使用chromium scraper
                        try:
                            soup = scraper_manager.get_chromium_scraper().get_soup(
                                self.url,
                                10
                            )
                        except Exception as ce:
                            logger.error(f"chromium scraper爬取失败: {ce}")
                            return False
            else:
                # 其他网站直接使用cloudscraper
                logger.info(f"使用cloudscraper爬取{self.source}: {self.url}")
                response = scraper_manager.get_cloud_scraper().get_response(self.url, timeout=10)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, "html.parser")
            
            if soup is None:
                logger.error(f"无法获取页面内容: {self.url}")
                return False
            
            div_info = soup.find("div", class_="video-details-wrapper hidden-sm hidden-md hidden-lg hidden-xl")
            if not div_info:
                logger.error(f"无法解析视频信息: {self.url}")
                return False
            
            date = self._extract_date_from_filename(div_info.text)
            if date:
                self._update_savetitle(date)
                self._rename_video_file()
                return True
            
        except Exception as e:
            logger.error(f"访问视频页面失败 {self.url}: {e}")
        
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
    