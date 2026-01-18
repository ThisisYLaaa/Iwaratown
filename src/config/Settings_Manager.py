import json
import logging

from core.Custom_Struc import *
from .Init_Settings import *
from utils.Logger import get_logger

logger: logging.Logger = get_logger("设置")

class Settings_Manager:
    _Settings_Manager_instance = None
    _Settings_Manager_initialized = False

    def __new__(cls):
        if cls._Settings_Manager_instance is None:
            cls._Settings_Manager_instance = super(Settings_Manager, cls).__new__(cls)
        return cls._Settings_Manager_instance

    def __init__(self) -> None:
        if Settings_Manager._Settings_Manager_initialized:
            return
        self.settings: dict = {}
        self.load_settings()
        Settings_Manager._Settings_Manager_initialized = True
    
    def load_settings(self) -> None:
        """加载设置"""
        logger.info("加载设置")
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                self.settings = json.load(f)
            # 添加缺失的设置项
            for key, default_value in DEFAULT_SETTINGS.items():
                if key not in self.settings:
                    self.settings[key] = default_value
            
            logger.info("设置加载成功")
            return
        except FileNotFoundError:
            logger.error("设置文件未找到")
        except json.JSONDecodeError:
            logger.error("设置文件格式错误")
        except Exception as e:
            logger.error(f"加载设置时发生未知错误: {e}")
        self.settings = DEFAULT_SETTINGS.copy()
        logger.info("使用默认设置")
        self.save_settings()
    
    def save_settings(self) -> None:
        """保存设置"""
        logger.info("💾 保存设置")
        try:
            # 去掉最后一个/
            if self.settings.get("Xpv_Hostname", "").endswith('/'):
                self.settings["Xpv_Hostname"] = self.settings["Xpv_Hostname"][:-1]
            if self.settings.get("Hanime1_Hostname", "").endswith('/'):
                self.settings["Hanime1_Hostname"] = self.settings["Hanime1_Hostname"][:-1]
            
            with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4, ensure_ascii=False)
            logger.info("设置保存成功")
        except PermissionError as e:
            logger.error(f"保存设置时权限错误: {e}")
        except IOError as e:
            logger.error(f"保存设置时IO错误: {e}")
        except Exception as e:
            logger.error(f"保存设置时发生未知错误: {e}")

class Cache_Manager:
    _Cache_Manager_instance = None
    _Cache_Manager_initialized = False

    def __new__(cls):
        if cls._Cache_Manager_instance is None:
            cls._Cache_Manager_instance = super(Cache_Manager, cls).__new__(cls)
        return cls._Cache_Manager_instance

    def __init__(self) -> None:
        if Cache_Manager._Cache_Manager_initialized:
            return
        self.cache: dict[str, dict[str, dict]] = {}
        Cache_Manager._Cache_Manager_initialized = True
        self.load_cache()

    def load_cache(self) -> None:
        """加载缓存"""
        logger.info("加载缓存")
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                self.cache = json.load(f)
            logger.info("缓存加载成功")
        except FileNotFoundError:
            logger.error("缓存文件未找到")
        except json.JSONDecodeError:
            logger.error("缓存文件格式错误")
        except Exception as e:
            logger.error(f"加载缓存时发生未知错误: {e}")
            self.cache = {}
    
    def save_cache(self) -> None:
        """保存缓存"""
        logger.info("保存缓存")
        try:
            with open(CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, indent=4, ensure_ascii=False)
            logger.info("缓存保存成功")
        except PermissionError as e:
            logger.error(f"保存缓存时权限错误: {e}")
        except IOError as e:
            logger.error(f"保存缓存时IO错误: {e}")
        except Exception as e:
            logger.error(f"保存缓存时发生未知错误: {e}")
    
    def get_cache(self, channel_name: str) -> dict:
        """获取指定渠道的缓存
        
        Args:
            channel_name: 渠道名称
            
        Returns:
            dict: 渠道的缓存字典
        """
        return self.cache.get(channel_name, {})
    
    def set_cache(self, channel_name: str, cache: list) -> None:
        """设置指定渠道的缓存
        
        Args:
            channel_name: 渠道名称
            cache: 要设置的缓存字典
        """
        # 将视频类转换成字典
        cache_dict = {}
        for video in cache:
            cache_dict[video.url] = video.__dict__
        
        # 别改这个
        url: str
        cache_video: dict
        for url, cache_video in cache_dict.items():
            if not channel_name in self.cache.keys():
                self.cache[channel_name] = {}
            if not url in self.cache[channel_name].keys():
                self.cache[channel_name][url] = cache_video
                continue
            for key, value in cache_video.items():
                if value:
                    self.cache[channel_name][url][key] = value
                else:
                    pass
        self.save_cache()


sm: Settings_Manager = Settings_Manager()
cm: Cache_Manager = Cache_Manager()
