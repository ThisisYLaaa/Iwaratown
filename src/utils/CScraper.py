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
        co = ChromiumOptions().auto_port()
        co.incognito(True)
        # co.set_argument('--headless', True)
        # co.set_argument('--no-sandbox')
        # co.set_argument('--disable-gpu')

        self.page = ChromiumPage(co)
    
    def get(self, url: str, target_ele: str, timeout: int = 10) -> BeautifulSoup:
        self.page.get("")  # 清理page数据
        self.page.get(url)
        logger.info(f"等待元素 {target_ele} 出现")
        self.page.wait.ele_displayed(target_ele, timeout=timeout)
        self.page.wait(1)
        return BeautifulSoup(self.page.html, "html.parser")

cloud_scraper = get_scraper()
chrome_scraper = ChromiumScraper()
