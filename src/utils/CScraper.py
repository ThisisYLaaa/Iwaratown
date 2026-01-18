from bs4 import BeautifulSoup
import cloudscraper
from DrissionPage import ChromiumPage, ChromiumOptions

import logging
from .Logger import get_logger
from config.Init_Settings import HANIME1_ELEMENTS
logger: logging.Logger = get_logger("爬虫管理器")


class CloudScraper:
    """CloudScraper类，专门处理cloudscraper相关功能"""
    
    # 延迟初始化单例
    _instance = None
    _initialized = False
    
    def __new__(cls):
        """单例模式实现"""
        if cls._instance is None:
            cls._instance = super(CloudScraper, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化CloudScraper实例"""
        if not CloudScraper._initialized:
            logger.info("创建新的CloudScraper实例")
            self.scraper = cloudscraper.create_scraper(
                browser={
                    'browser': 'chrome',
                    'platform': 'windows',
                    'desktop': True,
                    'mobile': False,
                    'version': '142.0.0.0'
                }
            )
            CloudScraper._initialized = True
    
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
    
    # 延迟初始化单例
    _instance = None
    _initialized = False
    
    def __new__(cls):
        """单例模式实现"""
        if cls._instance is None:
            cls._instance = super(ChromiumScraper, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化ChromiumScraper实例"""
        if not ChromiumScraper._initialized:
            logger.info("创建新的ChromiumScraper实例")
            co = ChromiumOptions().auto_port()
            co.incognito(True)
            self.page = ChromiumPage(co)
            self.page.set.window.size(600, 300)
            ChromiumScraper._initialized = True
    
    def get_soup(self, url: str, timeout: int = 10) -> BeautifulSoup:
        """
        使用ChromiumScraper获取网页soup对象
        
        Args:
            url: 要爬取的URL
            timeout: 超时时间
            
        Returns:
            BeautifulSoup对象
        """
        max_retries = 2
        for retry in range(max_retries):
            try:
                self._clean_page()
                logger.info(f"使用ChromiumScraper爬取: {url}")
                self.page.get(url)
                
                # 自动选择目标元素选择器
                if "search" in url.lower():
                    target_ele = HANIME1_ELEMENTS["SEARCH_RESULTS"]
                else:
                    target_ele = HANIME1_ELEMENTS["VIDEO_DETAILS"]
                
                logger.info(f"等待元素 {target_ele} 出现")
                self.page.wait.ele_displayed(target_ele, timeout=timeout)
                return BeautifulSoup(self.page.html, "html.parser")
            except Exception as e:
                logger.warning(f"ChromiumScraper.get_soup失败: {e}，正在重试 ({retry + 1}/{max_retries})")
                # 重新创建ChromiumPage实例
                self._init_chromium_page()
        # 重试次数用完，抛出异常
        raise Exception(f"ChromiumScraper.get_soup多次尝试失败: {url}")
    
    def get_download_link(self, url: str, timeout: int = 20) -> str:
        """
        使用ChromiumScraper获取下载链接
        
        Args:
            url: 要爬取的URL
            timeout: 超时时间
            
        Returns:
            下载链接字符串
        """
        max_retries = 2
        for retry in range(max_retries):
            try:
                self._clean_page()
                logger.info(f"使用ChromiumScraper获取下载链接: {url}")
                self.page.get(url)
                
                logger.info("等待下载引导页面出现")
                self.page.wait.ele_displayed(HANIME1_ELEMENTS["DOWNLOAD_BUTTON"], timeout=timeout)
                download_guide_link: str = str(self.page.ele(HANIME1_ELEMENTS["DOWNLOAD_BUTTON"]).attr("href"))
                
                self.page.get(download_guide_link)
                logger.info("等待下载链接出现")
                self.page.wait.ele_displayed(HANIME1_ELEMENTS["DOWNLOAD_LINK"], timeout=timeout)
                download_link: str = str(self.page.ele(HANIME1_ELEMENTS["DOWNLOAD_LINK"]).attr("data-url"))
                return download_link
            except Exception as e:
                logger.warning(f"ChromiumScraper.get_download_link失败: {e}，正在重试 ({retry + 1}/{max_retries})")
                # 重新创建ChromiumPage实例
                self._init_chromium_page()
        # 重试次数用完，抛出异常
        raise Exception(f"ChromiumScraper.get_download_link多次尝试失败: {url}")
    
    def _init_chromium_page(self):
        """初始化ChromiumPage实例"""
        logger.info("创建新的ChromiumPage实例")
        co = ChromiumOptions().auto_port()
        co.incognito(True)
        self.page = ChromiumPage(co)
        self.page.set.window.size(600, 300)
    
    def _clean_page(self):
        """清理page数据"""
        try:
            self.page.get("")
        except Exception as e:
            logger.warning(f"清理page数据失败: {e}，重新创建实例")
            # 重新创建ChromiumPage实例
            self._init_chromium_page()
    



class ScraperManager:
    """爬虫管理器，统一管理不同类型的爬虫实例"""
    
    def __init__(self):
        self.cloud_scraper = CloudScraper()
        self.chromium_scraper = ChromiumScraper()
    
    def get_cloud_scraper(self) -> CloudScraper:
        """获取CloudScraper实例"""
        return self.cloud_scraper
    
    def get_chromium_scraper(self) -> ChromiumScraper:
        """获取ChromiumScraper实例"""
        return self.chromium_scraper


# 创建全局爬虫管理器实例
scraper_manager = ScraperManager()



