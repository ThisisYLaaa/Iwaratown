import os

DEFAULT_SETTINGS: dict = {}

# 写死的配置
STVERSION: str = "1.0.1"
SETTINGS_FILE: str = f"iwtn_settings_{STVERSION}.json"
EDGE_FILE: str = "msedge.exe"
THEMENAME: str = "darkly"
MYBILIURL: str = "https://space.bilibili.com/616045770"
Miao: bool = True

DEFAULT_SETTINGS["Ver"] = STVERSION
DEFAULT_SETTINGS["ForceUsingXpxHostname"] = True
DEFAULT_SETTINGS["Xpv_Pic_Download_RelativePath"] = "#Pics"
DEFAULT_HEADERS: dict = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
    # Iwara不可以用Accept-Encoding
}

DEFAULT_SETTINGS["Favor"] = {
    "xpv": [],
    "iwara": []
}

# 这个后缀是固定的 未来可能会改变
IWARA_SHA_POSTFIX: str = "_5nFp9kmbNnHdAFhaqMvt"

PROXIES: dict = {
    "http": "http://127.0.0.1:10809",
    "https": "http://127.0.0.1:10809"
}

# 需要在UI.py/_download_worker中对应值和方法
XPV_CUSTOM_MAP: dict = {
    "moeupup": "pic",
    "showinfo": "video"
}

# 可配置的配置
DEFAULT_SETTINGS["Xpv_Hostname"] = "https://www.xpicvid.com"
DEFAULT_SETTINGS["Iwara_Hostname"] = "https://www.iwara.tv"
DEFAULT_SETTINGS["Iwara_API_Hostname"] = "https://api.iwara.tv"
DEFAULT_SETTINGS["Xpv_Download_Path"] = os.path.join(os.path.expanduser("~"), "Xpv_Downloads")
DEFAULT_SETTINGS["Iwara_Download_Path"] = os.path.join(os.path.expanduser("~"), "Iwara_Downloads")
DEFAULT_SETTINGS["Custom_Download_Path"] = os.path.join(os.path.expanduser("~"), "Custom_Downloads")
DEFAULT_SETTINGS["Max_Threads"] = 8
DEFAULT_SETTINGS["Check_Cert"] = True
