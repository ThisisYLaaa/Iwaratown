import cloudscraper

import logging
from Logger import get_logger
logger: logging.Logger = get_logger("CloudFlare爬虫")

_CScraper_instance = None

def get_scraper():
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
