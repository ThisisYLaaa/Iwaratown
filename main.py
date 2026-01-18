#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Iwaratown主程序入口
"""

import os
import sys

# 添加src目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.ui.UI import main
from src.utils.CScraper import scraper_manager
from src.utils.Logger import get_logger

logger = get_logger(__name__)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.critical(f"主程序运行时出错: {e}")
    finally:
        # 关闭爬虫管理器，释放资源
        scraper_manager.close()
