from Init_Settings import *

from Settings_Manager import Settings_Manager
sm: Settings_Manager = Settings_Manager()

from typing import Any
import datetime
import re

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
        self.title: str = "".join([f"[{datetime.datetime.fromisoformat(self.createdAt.replace("Z", "+00:00")).strftime("%Y-%m-%d")}]", data.get("title", "").strip()])
        self.title = re.sub(r'[\\/*?:"<>|]', "_", self.title)
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
        self.title: str = "".join([f"[{self.updatedAt}]", data.get("title", "").strip()])
        self.title = re.sub(r'[\\/*?:"<>|]', "_", self.title)
        self.dpath: str = sm.settings.get("Xpv_Download_Path", DEFAULT_SETTINGS["Xpv_Download_Path"])
        self.dpath = os.path.join(self.dpath, self.author)

    def get(self, key: str, default: Any = None) -> Any:
        return self.__dict__.get(key, default)

class stru_xpv_custom:
    def __init__(self, data: dict):
        self.url: str = data.get('url', '')
        self.type:str = self.get_type()
    
    def get_type(self) -> str:
        """video: 社区帖子; pic: 图片"""
        if any([x in self.url for x in XPV_CUSTOM_MAP.keys()]):
            return XPV_CUSTOM_MAP[next(x for x in XPV_CUSTOM_MAP.keys())]
        return "Unknown"
    
    def get(self, key: str, default: Any = None) -> Any:
        return self.__dict__.get(key, default)
