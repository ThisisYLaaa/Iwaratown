import os

# 写死的配置
STVERSION: str = "1.0.1"
SETTINGS_FILE: str = f"iwtn_settings_{STVERSION}.json"
CACHE_FILE: str = f"iwtn_cache_{STVERSION}.json"
EDGE_FILE: str = "msedge.exe"
THEMENAME: str = "darkly"
MYBILIURL: str = "https://space.bilibili.com/616045770"
MAX_PAGE: int = 20
Miao: bool = True

DEFAULT_HEADERS: dict = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
}

CHANNELS_CONFIG = {
    "Xpv": {
        "hostname_key": "Xpv_Hostname",
        "download_path_key": "Xpv_Download_Path",
        "default_hostname": "https://www.xpicvid.com",
        "default_download_path": os.path.join(os.path.expanduser("~"), "Xpv_Downloads")
    },
    "Hanime1": {
        "hostname_key": "Hanime1_Hostname",
        "download_path_key": "Hanime1_Download_Path",
        "default_hostname": "https://hanime1.me",
        "default_download_path": os.path.join(os.path.expanduser("~"), "Hanime1_Downloads")
    }
}

PROXIES: dict = {
    "http": "http://127.0.0.1:7897",
    "https": "http://127.0.0.1:7897"
}

# Hanime1 元素检测配置
HANIME1_ELEMENTS = {
    "SEARCH_RESULTS": ".horizontal-row",
    "DOWNLOAD_BUTTON": "#downloadBtn",
    "DOWNLOAD_LINK": ".exoclick-popunder juicyads-popunder"
}

# 需要在UI.py/_download_worker中对应值和方法
XPV_CUSTOM_MAP: dict = {
    "moeupup": "pic",
    "showinfo": "video"
}

# 可配置的配置 - 保持向后兼容性
DEFAULT_SETTINGS: dict = {
    "Ver": STVERSION,
    "Xpv_Pic_Download_RelativePath": "#Pics",
    "Favor": {
        "xpv": [],
        "hanime1": [],
    },
    "Custom_Download_Path": os.path.join(os.path.expanduser("~"), "Custom_Downloads"),
    "Max_Threads": 8,
    "Check_Cert": True
}

# 添加渠道配置到默认设置
for channel_name, config in CHANNELS_CONFIG.items():
    DEFAULT_SETTINGS[config["hostname_key"]] = config["default_hostname"]
    DEFAULT_SETTINGS[config["download_path_key"]] = config["default_download_path"]
