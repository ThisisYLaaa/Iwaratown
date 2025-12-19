import json
import logging

from Init_Settings import *
from Logger import get_logger

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
            
            # 确保Iwara_Token字段存在
            if "Iwara_Token" not in self.settings:
                self.settings["Iwara_Token"] = None
                
            logger.info("设置加载成功")
            return
        except FileNotFoundError:
            logger.error("设置文件未找到")
        except json.JSONDecodeError:
            logger.error("设置文件格式错误")
        except Exception as e:
            logger.error(f"加载设置时发生未知错误: {e}")
        self.settings = DEFAULT_SETTINGS.copy()
        self.settings["Iwara_Token"] = None
        logger.info("使用默认设置")
        self.save_settings()
    
    def save_settings(self) -> None:
        """保存设置"""
        logger.info("💾 保存设置")
        try:
            # 去掉最后一个/
            if self.settings.get("Xpv_Hostname", "").endswith('/'):
                self.settings["Xpv_Hostname"] = self.settings["Xpv_Hostname"][:-1]
            if self.settings.get("Iwara_Hostname", "").endswith('/'):
                self.settings["Iwara_Hostname"] = self.settings["Iwara_Hostname"][:-1]
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
            
    def get_iwara_token(self) -> str:
        """获取Iwara登录token
        
        Returns:
            str: 存储的token，如果没有则返回None
        """
        return self.settings.get("Iwara_Token", "")
    
    def set_iwara_token(self, token: str) -> None:
        """设置Iwara登录token
        
        Args:
            token: 要存储的token，设置为None可清除token
        """
        self.settings["Iwara_Token"] = token
        logger.info(f"已{'保存' if token else '清除'}Iwara登录token")
        self.save_settings()
    
    def has_valid_token(self) -> bool:
        """检查是否有有效的token
        
        Returns:
            bool: 如果token存在且不为空，返回True，否则返回False
        """
        token = self.get_iwara_token()
        return token is not None and token.strip() != ""
