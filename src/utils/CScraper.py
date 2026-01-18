from bs4 import BeautifulSoup
import cloudscraper
from DrissionPage import ChromiumPage, ChromiumOptions

import logging
from .Logger import get_logger
logger: logging.Logger = get_logger("CloudFlare爬虫")

_CScraper_instance = None

def get_scraper() -> cloudscraper.CloudScraper:
    global _CScraper_instance
    if _CScraper_instance is None:
        logger.info("创建新的scraper实例")
        _CScraper_instance = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True,
                'mobile': False,
                'version': '142.0.0.0'
            }
        )
    return _CScraper_instance

class ChromiumScraper:
    def __init__(self) -> None:
        self.co = ChromiumOptions().auto_port()
        self.co.incognito(True)
        # co.set_argument('--headless', True)
        # co.set_argument('--no-sandbox')
        # co.set_argument('--disable-gpu')
        self.page = ChromiumPage(self.co)
        self.page.set.window.size(600, 300)

    def get(self, url: str, target_ele: str, timeout: int = 10) -> BeautifulSoup:
        try:
            self.page.get("")  # 清理page数据
        except:
            self.page = ChromiumPage(self.co)
            self.page.set.window.size(600, 300)

        self.page.get(url)
        logger.info(f"等待元素 {target_ele} 出现")
        self.page.wait.ele_displayed(target_ele, timeout=timeout)
        return BeautifulSoup(self.page.html, "html.parser")
    
    def get_download_link(self, url: str) -> str:
        self.page.get("")
        self.page.get(url)
        logger.info("等待下载引导页面出现")
        self.page.wait.ele_displayed("#downloadBtn", timeout=10)
        download_guide_link: str = str(self.page.ele("#downloadBtn").attr("href"))
        self.page.get(download_guide_link)
        logger.info("等待下载链接出现")
        self.page.wait.ele_displayed(".exoclick-popunder juicyads-popunder", timeout=10)
        download_link: str = str(self.page.ele(".exoclick-popunder juicyads-popunder").attr("data-url"))
        return download_link
        

cloud_scraper = get_scraper()
chrome_scraper = ChromiumScraper()
