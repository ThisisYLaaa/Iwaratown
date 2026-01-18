#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Iwaratown主程序入口
"""

import sys
import os

# 添加src目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.ui.UI import main

if __name__ == "__main__":
    main()
