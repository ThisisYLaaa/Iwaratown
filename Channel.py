from typing import Callable, Dict, List, Any, Optional
import logging
from Logger import get_logger
logger: logging.Logger = get_logger("渠道管理")

class Channel:
    """单个渠道的封装类"""
    
    def __init__(self, name: str, hostname_key: str, download_path_key: str,
                 search_method: Callable, download_methods: Dict[str, Callable]):
        """初始化渠道
        
        Args:
            name: 渠道名称
            hostname_key: 设置中主机名的键
            download_path_key: 设置中下载路径的键
            search_method: 搜索方法
            download_methods: 下载方法字典，键为任务类型，值为下载函数
        """
        self.name = name
        self.hostname_key = hostname_key
        self.download_path_key = download_path_key
        self.search_method = search_method
        self.download_methods = download_methods
    
    def can_handle(self, task: Any) -> bool:
        """判断该渠道是否能处理给定任务"""
        return hasattr(task, 'source') and task.source == self.name
    
    def download(self, task: Any) -> bool:
        """下载任务
        
        Args:
            task: 下载任务对象
        
        Returns:
            bool: 下载是否成功
        """
        # 对于结构化任务，直接使用source判断
        if hasattr(task, 'source') and task.source == self.name:
            # 根据任务类型选择下载方法
            task_type = "default"
            if hasattr(task, 'type'):
                task_type = task.type
            elif hasattr(task, '__class__'):
                task_type = task.__class__.__name__.replace("stru_", "").replace("_", "")
            
            # 尝试获取对应的下载方法
            download_method = self.download_methods.get(task_type)
            if not download_method:
                # 使用默认下载方法
                download_method = self.download_methods.get("default")
            
            if download_method:
                logger.info(f"使用{self.name}渠道的{task_type}方法下载任务")
                return download_method(task)
            else:
                logger.error(f"{self.name}渠道没有找到合适的下载方法，任务类型: {task_type}")
                return False
        
        # 对于自定义URL任务，根据URL特征判断
        if hasattr(task, 'url'):
            from Settings_Manager import Settings_Manager
            from Init_Settings import DEFAULT_SETTINGS
            sm = Settings_Manager()
            hostname = sm.settings.get(self.hostname_key, DEFAULT_SETTINGS[self.hostname_key])
            if hostname in task.url:
                # 尝试使用自定义下载方法
                download_method = self.download_methods.get("custom")
                if download_method:
                    logger.info(f"使用{self.name}渠道的custom方法下载自定义URL")
                    return download_method(task.url)
        
        logger.error(f"{self.name}渠道无法处理该任务")
        return False

class ChannelManager:
    """渠道管理器，管理所有渠道实例"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        """单例模式实现"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化渠道管理器"""
        if not ChannelManager._initialized:
            self.channels: Dict[str, Channel] = {}
            ChannelManager._initialized = True
    
    def register_channel(self, channel: Channel) -> None:
        """注册渠道
        
        Args:
            channel: 要注册的渠道实例
        """
        self.channels[channel.name] = channel
        logger.info(f"渠道 {channel.name} 已注册")
    
    def get_channel(self, name: str) -> Optional[Channel]:
        """获取指定名称的渠道
        
        Args:
            name: 渠道名称
        
        Returns:
            Optional[Channel]: 渠道实例，不存在则返回None
        """
        return self.channels.get(name)
    
    def list_channels(self) -> List[str]:
        """列出所有注册的渠道名称
        
        Returns:
            List[str]: 渠道名称列表
        """
        return list(self.channels.keys())
    
    def download(self, task: Any) -> bool:
        """下载任务，自动选择合适的渠道
        
        Args:
            task: 下载任务对象
        
        Returns:
            bool: 下载是否成功
        """
        # 根据任务的source属性获取渠道
        if hasattr(task, 'source'):
            channel = self.get_channel(task.source)
            if channel:
                return channel.download(task)
        
        # 对于没有source属性的任务，尝试匹配所有渠道
        for channel in self.channels.values():
            if channel.can_handle(task):
                return channel.download(task)
        
        logger.error(f"没有找到可以处理该任务的渠道")
        return False
    
    def search(self, keyword: str, channel_name: str) -> List[Any]:
        """搜索视频
        
        Args:
            keyword: 搜索关键词
            channel_name: 渠道名称
        
        Returns:
            List[Any]: 搜索结果列表
        """
        channel = self.get_channel(channel_name)
        if channel:
            return channel.search_method(keyword)
        logger.error(f"渠道 {channel_name} 不存在")
        return []

# 创建全局渠道管理器实例
channel_manager = ChannelManager()
