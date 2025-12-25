import datetime, os, re
from typing import Any
from bs4 import BeautifulSoup

from CScraper import get_scraper
scraper = get_scraper()

from Logger import get_logger
logger = get_logger("视频")

from Init_Settings import *
from Settings_Manager import Settings_Manager

# 初始化设置管理器
sm: Settings_Manager = Settings_Manager()

class stru_iw_author:
    def __init__(self, data: dict):
        self.id: str = data.get("id", "")
        self.name: str = data.get("name", "Unknown").strip()
        self.username: str = data.get("username", "Unknown").strip()
        self.status: str = data.get("status", "active").strip()
        self.role: str = data.get("role", "user").strip()
        self.followedBy: bool = data.get("followedBy", False)
        self.following: bool = data.get("following", False)
        self.friend: bool = data.get("friend", False)
        self.premium: bool = data.get("premium", False)
        self.creatorProgram: bool = data.get("creatorProgram", False)
        self.seenAt: str = data.get("seenAt", "").strip()
        self.avatar: dict = data.get("avatar", {})
        self.createdAt: str = data.get("createdAt", "").strip()

    def get_avatar_url(self) -> str:
        return f"https://www.iwara.tv/profile/{self.username}/videos"

class stru_iw_video:
    def __init__(self, data: dict):
        self.status: str = data.get("status", "active").strip()
        self.rating: str = data.get("rating", "ecchi").strip()
        self.liked: bool = data.get("liked", False)
        self.numLikes: int = data.get("numLikes", 0)
        self.file: dict = data.get("file", {})
        self.user: stru_iw_author = stru_iw_author(data.get("user", {}))
        self.createdAt: str = data.get("createdAt", "").strip()

        self.source: str = "Iwara"
        self.id: str = data.get("id", "")
        self.url: str = self.get_video_path_url()
        self.author: str = self.user.username
        self.updatedAt: str = data.get("updatedAt", "").strip()
        self.numViews: int = data.get("numViews", 0)
        self.title: str = re.sub(r'[\\/*?:"<>|]', "_", data.get("title", "").strip())
        self.savetitle: str = "".join([f"[{datetime.datetime.fromisoformat(self.createdAt.replace("Z", "+00:00")).strftime("%Y-%m-%d")}]", data.get("title", "").strip()])
        self.savetitle = re.sub(r'[\\/*?:"<>|]', "_", self.savetitle)
        self.dpath: str = sm.settings.get("Iwara_Download_Path", DEFAULT_SETTINGS["Iwara_Download_Path"])
        self.dpath = os.path.join(self.dpath, self.author)

    def get_video_path_url(self) -> str:
        return f"https://www.iwara.tv/video/{self.id}"
    
    def get(self, key: str, default: Any = None) -> Any:
        return self.__dict__.get(key, default)

class stru_xpv_video:
    def __init__(self, data: dict):
        self.furl: str = data.get("furl", "").strip()

        self.source: str = "Xpv"
        self.url: str = f"{sm.settings['Xpv_Hostname']}{data.get('url', '')}"
        self.author: str = data.get("author", "").strip()
        self.updatedAt: str = data.get("updatedAt", "").strip()
        self.updatedAt = datetime.datetime.fromisoformat(self.updatedAt.replace("Z", "+00:00")).strftime("%Y-%m-%d")
        self.numViews: int = data.get("numViews", 0)
        self.title: str = re.sub(r'[\\/*?:"<>|]', "_", data.get("title", "").strip())
        self.savetitle: str = "".join([f"[{self.updatedAt}]", data.get("title", "").strip()])
        self.savetitle = re.sub(r'[\\/*?:"<>|]', "_", self.savetitle)
        self.dpath: str = sm.settings.get("Xpv_Download_Path", DEFAULT_SETTINGS["Xpv_Download_Path"])
        self.dpath = os.path.join(self.dpath, self.author)

    def get(self, key: str, default: Any = None) -> Any:
        return self.__dict__.get(key, default)
    
    def get_updatedAt_timestamp(self) -> float:
        return datetime.datetime.fromisoformat(self.updatedAt.replace("Z", "+00:00")).timestamp()

class stru_xpv_custom:
    def __init__(self, data: dict):
        self.url: str = data.get('url', '')
        self.type: str = self.get_type()
        self.source: str = "Xpv"  # 添加source属性，确保渠道管理器能识别
    
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
        self.furl: str = data.get("furl", "").strip()
        self.title: str = data.get("title", "").strip()
        self.title = re.sub(r'[\\/*?:"<>|]', "_", self.title)
        self.savetitle: str = self.title
        self.url: str = data.get("url", "").strip()

        self.source: str = "Hanime1"
        self.author: str = data.get("author", "").strip()
        self.updatedAt: str = data.get("updatedAt", "").strip()  # 一般没有
        self.numViews: int = data.get("numViews", 0)
        
        self.dpath: str = sm.settings.get("Hanime1_Download_Path", DEFAULT_SETTINGS["Hanime1_Download_Path"])
        self.dpath = os.path.join(self.dpath, self.author)

        self.get_updatedAt_from_file()

    def get(self, key: str, default: Any = None) -> Any:
        return self.__dict__.get(key, default)
    
    def get_updatedAt_from_file(self) -> None:
        # 如果存在本地文件 则日期为本地文件名中字符串规则符合YYYY-MM-DD的部分
        for file in os.listdir(self.dpath):
            if file.endswith(".mp4") and self.title in file:
                save_path = os.path.join(self.dpath, file)
                logger.info(f"找到本地文件: {save_path}")
                break
        else:
            save_path = os.path.join(self.dpath, f"{self.title}.mp4")
        
        if os.path.exists(save_path):
            temp = re.search(r"\d{4}-\d{2}-\d{2}", os.path.basename(save_path))
            if temp: self.updatedAt = temp.group()
            else: self.updatedAt = ""
        
        self.update_savetitle(self.updatedAt)
    
    def update_savetitle(self, updatedAt: str):
        self.updatedAt = updatedAt
        self.savetitle = "".join([f"[{self.updatedAt}]", self.title])
        self.savetitle = re.sub(r'[\\/*?:"<>|]', "_", self.savetitle)

        # 更新旧标题
        save_path = os.path.join(self.dpath, f"{self.title}.mp4")
        if os.path.exists(save_path):
            os.rename(save_path, os.path.join(self.dpath, f"{self.savetitle}.mp4"))
    
    def update_updatedAt(self) -> None:
        if self.updatedAt:
            return
        
        try:
            # 访问一下视频页面 获取视频信息
            response = scraper.get(
                url=self.url,
                timeout=5, proxies=PROXIES, verify=sm.settings.get("Check_Cert", DEFAULT_SETTINGS["Check_Cert"])
            )
            response.raise_for_status()
            # 解析视频信息
            soup = BeautifulSoup(response.text, "html.parser")
            div_info = soup.find("div", class_="video-details-wrapper hidden-sm hidden-md hidden-lg hidden-xl")
            if not div_info:
                logger.error(f"无法解析视频信息: {self.url}")
                return
            temp = re.search(r"\d{4}-\d{2}-\d{2}", div_info.text)
            if temp: self.update_savetitle(temp.group())

        except Exception as e:
            logger.error(f"访问视频页面失败 {self.url}: {e}")
