import logging

from bs4 import BeautifulSoup
import cloudscraper
from DrissionPage import ChromiumOptions, ChromiumPage

from ..config.Init_Settings import HANIME1_ELEMENTS
from ..utils.Logger import get_logger

logger: logging.Logger = get_logger("爬虫管理器")


class CloudScraper:
    """CloudScraper类，专门处理cloudscraper相关功能"""
    
    def __init__(self):
        """初始化CloudScraper实例"""
        self.scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True,
                'mobile': False,
                'version': '142.0.0.0'
            }
        )
    
    def get_soup(self, url: str, timeout: int = 10) -> BeautifulSoup:
        """
        使用cloudscraper获取网页soup对象
        
        Args:
            url: 要爬取的URL
            timeout: 超时时间
            
        Returns:
            BeautifulSoup对象
        """
        logger.info(f"使用cloudscraper爬取: {url}")
        response = self.scraper.get(url, timeout=timeout)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")
    
    def get_response(self, url: str, timeout: int = 10):
        """
        使用cloudscraper获取网页响应对象
        
        Args:
            url: 要爬取的URL
            timeout: 超时时间
            
        Returns:
            Response对象
        """
        logger.info(f"使用cloudscraper获取响应: {url}")
        return self.scraper.get(url, timeout=timeout)
    
    def get_instance(self):
        """获取底层cloudscraper实例"""
        return self.scraper


class ChromiumScraper:
    """ChromiumScraper类，专门处理DrissionPage相关功能"""
    
    def __init__(self):
        """初始化ChromiumScraper实例"""
        # 不再创建Chrome实例，使用ScraperManager提供的唯一Chrome实例
        pass
    
    def get_download_link(self, video, timeout: int = 20) -> str:
        """
        使用ChromiumScraper获取下载链接
        
        Args:
            video: 视频对象，包含视频信息
            timeout: 超时时间
            
        Returns:
            下载链接字符串
        """
        # 获取唯一的Chrome实例
        main_page = scraper_manager.get_main_chromium_page()
        
        # 新建标签页
        logger.info(f"新建标签页，获取下载链接: {video.url}")
        new_tab = main_page.new_tab()
        
        try:
            # 在新标签页中访问网页
            new_tab.get(video.url)

            logger.info("等待下载引导页面出现")
            new_tab.wait.ele_displayed(f"#{HANIME1_ELEMENTS['DOWNLOAD_BUTTON']}", timeout=timeout)
            download_guide_link: str = str(new_tab.ele(f"#{HANIME1_ELEMENTS['DOWNLOAD_BUTTON']}").attr("href"))
            
            new_tab.get(download_guide_link)
            logger.info("等待下载链接出现")
            new_tab.wait.ele_displayed(f".{HANIME1_ELEMENTS['DOWNLOAD_LINK']}", timeout=timeout)
            download_link: str = str(new_tab.ele(f".{HANIME1_ELEMENTS['DOWNLOAD_LINK']}").attr("data-url"))
            
            # 获取标签页数量
            tabs = main_page.get_tabs()
            
            # 如果标签页数量大于1，关闭当前标签页
            if len(tabs) > 1:
                logger.info("关闭标签页")
                new_tab.close()
            
            return download_link
        except Exception as e:
            # 确保标签页被关闭
            tabs = main_page.get_tabs()
            if len(tabs) > 1:
                try:
                    new_tab.close()
                except:
                    pass
            raise e

 
class ScraperManager:
    """爬虫管理器，统一管理不同类型的爬虫实例"""
    
    # 使用类变量存储单例实例
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        """单例模式实现"""
        if cls._instance is None:
            cls._instance = super(ScraperManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化ScraperManager实例"""
        # 只初始化一次
        if not hasattr(self, '_initialized'):
            logger.info("创建新的ScraperManager实例")
            self.cloud_scraper = CloudScraper()
            
            # 初始化chromium_page为None，延迟创建
            self.chromium_page: ChromiumPage = None  # pyright: ignore[reportAttributeAccessIssue]
            
            # 添加cloudscraper失败标志，简化命名
            self.cs_failed = False
            self._initialized = True
    
    def get_cloud_scraper(self) -> CloudScraper:
        """获取CloudScraper实例"""
        return self.cloud_scraper
    
    def get_main_chromium_page(self):
        """获取唯一的Chrome浏览器实例，添加了延迟初始化和连接检查"""
        # 延迟初始化ChromiumPage
        if self.chromium_page is None:
            logger.info("初始化dissionpage")
            co = ChromiumOptions().auto_port()
            co.incognito(True)
            self.chromium_page = ChromiumPage(co)
            self.chromium_page.set.window.size(600, 300)
        else:
            # 检查ChromiumPage连接状态
            try:
                # 尝试访问浏览器属性，检查连接是否正常
                self.chromium_page.get_tabs()
            except Exception as e:
                logger.warning(f"检测到Chrome连接断开: {e}，重新创建实例")
                # 连接断开，重新创建ChromiumPage实例
                try:
                    # 先尝试关闭旧实例
                    self.chromium_page.close()
                except:
                    pass
                # 创建新实例
                logger.info("重新初始化dissionpage")
                co = ChromiumOptions().auto_port()
                co.incognito(True)
                self.chromium_page = ChromiumPage(co)
                self.chromium_page.set.window.size(600, 300)
        return self.chromium_page
    
    def create_chromium_scraper(self) -> ChromiumScraper:
        """创建一个新的ChromiumScraper实例"""
        logger.info("创建新的ChromiumScraper实例")
        return ChromiumScraper()
    
    def get_chromium_scraper(self) -> ChromiumScraper:
        """获取ChromiumScraper实例（兼容旧代码）"""
        return self.create_chromium_scraper()
    
    def set_cs_failed(self, failed: bool):
        """设置cloudscraper失败标志"""
        self.cs_failed = failed
    
    def is_cs_failed(self) -> bool:
        """检查cloudscraper是否失败"""
        return self.cs_failed
    
    def get_page_html(self, url: str) -> str:
        """获取页面HTML，自动处理cloudscraper和dissionpage的切换逻辑
        
        Args:
            url: 要获取的页面URL
            
        Returns:
            页面的HTML内容
        """
        if not self.cs_failed:
            try:
                logger.info(f"尝试使用cloudscraper获取页面: {url}")
                response = self.cloud_scraper.get_response(url, timeout=10)
                if response.status_code == 403:
                    logger.warning("cloudscraper返回403，切换到dissionpage")
                    self.cs_failed = True
                else:
                    response.raise_for_status()
                    return response.text
            except Exception as e:
                logger.warning(f"cloudscraper获取页面失败: {e}")
                # 非403错误，继续使用cloudscraper，不切换
                raise
        
        # 使用dissionpage获取HTML
        logger.info(f"使用dissionpage获取页面: {url}")
        main_page = self.get_main_chromium_page()
        
        # 新建标签页
        new_tab = main_page.new_tab()
        
        try:
            # 在新标签页中访问网页
            new_tab.get(url)
            
            # 等待页面加载完成
            new_tab.wait.ele_displayed(f".{HANIME1_ELEMENTS['SEARCH_RESULTS']}", timeout=10)
            
            # 获取页面HTML
            html = new_tab.html
            return html
        finally:
            # 确保标签页被关闭
            tabs = main_page.get_tabs()
            if len(tabs) > 1:
                logger.info("关闭标签页")
                try:
                    new_tab.close()
                except:
                    pass
    
    def close(self):
        """关闭所有爬虫实例"""
        logger.info("关闭所有爬虫实例")
        # 关闭唯一的Chrome实例
        if hasattr(self, 'chromium_page') and self.chromium_page is not None:
            try:
                logger.info("关闭唯一的Chrome实例")
                self.chromium_page.close()
            except Exception as e:
                logger.warning(f"关闭Chrome实例失败: {e}")


# 创建全局爬虫管理器实例
scraper_manager = ScraperManager()
