import logging
import re
import time
from urllib.parse import urlencode, urljoin

import cloudscraper
from bs4 import BeautifulSoup
import urllib3

# 禁用不安全的HTTPS请求警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from ..core.Channel import Channel, channel_manager
from ..core.Custom_Struc import *
from ..config.Init_Settings import *
from ..config.Settings_Manager import sm
from ..utils.CScraper import scraper_manager
from ..utils.Logger import get_logger

logger: logging.Logger = get_logger("搜索")


class Search_Engine:
    _last_search_timestamp: float = 0
    @staticmethod
    def xpv_search_video(keyword: str, classid: int=21) -> list[stru_xpv_video]:
        current_time: float = time.time()
        while current_time - Search_Engine._last_search_timestamp < 5.5:
            logger.info(f"距离上次搜索过了 {current_time - Search_Engine._last_search_timestamp:.2f}/5.5 秒")
            time.sleep(0.5)
            current_time = time.time()
        Search_Engine._last_search_timestamp = current_time

        post_data: dict[str, str|int] = {
            "classid": classid,
            "show": "title,text,keyboard,ftitle",
            "keyboard": keyword,
            "Submit": ""
        }
        base_url = sm.settings.get("Xpv_Hostname", DEFAULT_SETTINGS["Xpv_Hostname"])
        php_url: str = urljoin(base_url, "/e/search/index.php")

        try:
            logger.info(f"向Xpv发送视频搜索请求: {php_url}")
            logger.debug(f"post_data: {post_data}")
            response = scraper_manager.get_cloud_scraper().get_instance().post(
                url=php_url, data=post_data,
                timeout=5, proxies=PROXIES, verify=sm.settings.get("Check_Cert", DEFAULT_SETTINGS["Check_Cert"])
            )
            logger.debug(f"status_code: {response.status_code}")
            response.raise_for_status()

            redirect_url: str = response.url
            match = re.search(r'searchid=(\d+)', redirect_url)
            if not match:
                logger.error(f"无法从重定向URL中提取搜索ID: {redirect_url}")
                return []
            searchid: str = match.group(1)

            video_list: list[stru_xpv_video] = []

            current_page: int = 0
            current_video_list = []
            for _ in range(MAX_PAGE):
                logger.info(f"获取Xpv搜索结果页面 第{current_page}页: {redirect_url}")
                target_url = urljoin(base_url, f"/e/search/result/index.php?page={current_page}&searchid={searchid}")
                response = scraper_manager.get_cloud_scraper().get_instance().get(
                    url=target_url,
                    timeout=7, proxies=PROXIES, verify=sm.settings.get("Check_Cert", DEFAULT_SETTINGS["Check_Cert"])
                )
                response.raise_for_status()

                soup: BeautifulSoup = BeautifulSoup(response.text, "html.parser")
                # 每个视频的div标签
                current_video_list = soup.find_all("div", class_="col-xs-6 col-sm-4 col-md-3 col-lg-3 list-col col-xl-2")
                if not current_video_list:
                    break
                for div in current_video_list:
                    # div标签下有a标签, 其中有视频链接(href)和标题(title)
                    a_tag = div.find("a", href=True)
                    if a_tag:
                        href: str = str(a_tag["href"])
                        title: str = str(a_tag.get("title", ""))
                        # 提取title中[和]中间的字符串,如果没有则使用unknown
                        author = re.search(r"\[(.*?)\]", title)
                        author = author.group(1) if author else "unknown"
                        # a标签下有img标签, 其中有视频上传日期(隐藏在data-src中,需要加工提取)
                        # src示例: https://gamezy.xunge.cyou/titlep/2025/1107/3rkmgw2vadq7.jpg 需要提取2025 11 07
                        img_tag = a_tag.find("img", src=True)
                        if img_tag:
                            data_src: str = str(img_tag["data-src"])
                            match = re.search(r"/(\d{4})/(\d{2})(\d{2})/", data_src)
                            if match:
                                year, month, day = match.groups()
                                updatedAt = f"{year}-{month}-{day}"
                            else:
                                updatedAt = ""
                        else:
                            updatedAt = ""

                        video_list.append(stru_xpv_video({"title": title, "url": href, "author": author, "furl": target_url, "updatedAt": updatedAt}))
                if len(current_video_list) < 60:
                    break
                current_page += 1
            else:
                logger.warning(f"搜索达到上限, 暂停搜索")
            logger.info(f"成功获取 {len(video_list)} 个视频")
            return video_list
        
        except cloudscraper.exceptions.CloudflareChallengeError as e:
            logger.error(f"Xpv搜索接口返回Cloudflare挑战错误: {e}")
        except Exception as e:
            logger.error(f"处理Xpv搜索结果时发生未知错误: {e}")
        return []

    @staticmethod
    def _parse_hanime1_video_items(soup: BeautifulSoup, get_url: str, params: dict) -> list[stru_hanime1_video]:
        """解析Hanime1搜索结果页面中的视频项
        
        Args:
            soup: BeautifulSoup对象，包含搜索结果页面的HTML
            get_url: 搜索页面的基础URL
            params: 当前请求的参数
            
        Returns:
            解析出的视频列表
        """
        video_list = []
        # 查找所有视频项容器，使用select方法提高效率
        current_video_list = soup.select("div.video-item-container")
        
        for div in current_video_list:
            # div标签本身有标题title, div下的a标签有视频链接href
            title = str(div.get("title", ""))
            # 从title中提取author,如果没有则使用unknown
            author = re.search(r"\[(.*?)\]", title)
            author = author.group(1) if author else "unknown"
            a_tag = div.select_one("a[href]")
            if a_tag and a_tag.has_attr("href"):
                href = str(a_tag["href"])
                # 结合get_url和params, 构造完整的视频链接
                params_string = urlencode(params)
                furl = f"{get_url}?{params_string}"
                video_list.append(stru_hanime1_video({"title": title, "url": href, "author": author, "furl": furl}))
        
        return video_list
    
    @staticmethod
    def _get_hanime1_page_html(url: str) -> str:
        """获取Hanime1页面的HTML内容，优先使用cloudscraper，失败则使用dissionpage
        
        Args:
            url: 要获取的页面URL
            
        Returns:
            页面的HTML内容
        """
        # 使用统一的请求方法，自动处理cloudscraper和dissionpage的切换
        return scraper_manager.get_page_html(url)
    
    @staticmethod
    def hanime1_search_video(keyword: str) -> list[stru_hanime1_video]:
        """搜索Hanime1视频，优化后的逻辑
        
        优化点：
        1. 提取重复的视频信息处理逻辑为单独函数
        2. chromium scraper获取HTML后使用bs4处理，不直接定位元素
        3. 简化cloudscraper和chromium scraper的切换逻辑
        4. 统一数据提取逻辑，减少重复代码
        """
        # query=keyword&type=&genre=&sort=&date=&duration=
        params: dict[str, str|int] = {
            "query": keyword,
            "type": "",
            "genre": "",
            "sort": "最新上傳",
            "date": "",
            "duration": "",
        }
        base_url = sm.settings.get("Hanime1_Hostname", DEFAULT_SETTINGS["Hanime1_Hostname"])
        get_url: str = urljoin(base_url, "/search")

        try:
            video_list: list[stru_hanime1_video] = []
            
            current_page: int = 1
            for _ in range(MAX_PAGE):
                params["page"] = current_page
                logger.info(f"获取Hanime1搜索结果页面 第{current_page}页: {get_url}")
                logger.debug(f"params: {params}")

                # 构建完整的请求URL
                full_url = f"{get_url}?{urlencode(params)}"
                
                try:
                    # 获取页面HTML
                    html = Search_Engine._get_hanime1_page_html(full_url)
                    
                    # 使用bs4解析HTML
                    soup = BeautifulSoup(html, "html.parser")
                    
                    # 解析视频项
                    parsed_videos = Search_Engine._parse_hanime1_video_items(soup, get_url, params)
                    video_list.extend(parsed_videos)
                    
                    # 检查是否还有更多页面
                    if len(parsed_videos) < 60:
                        logger.info(f"当前页只获取到 {len(parsed_videos)} 个视频，停止搜索")
                        break
                    
                    current_page += 1
                except Exception as e:
                    logger.error(f"处理页面失败: {e}")
                    break
            else:
                logger.warning(f"搜索达到上限, 暂停搜索")
            
            logger.info(f"成功获取 {len(video_list)} 个视频")
            return video_list

        except Exception as e:
            logger.error(f"处理Hanime1搜索结果时发生未知错误: {e}")
        return []

# 注册搜索渠道到渠道管理器
def register_search_channels():
    """注册搜索渠道到渠道管理器"""
    from .Download_Engine import Download_Engine
    
    # 注册Xpv渠道
    xpv_channel = Channel(
        name="Xpv",
        hostname_key="Xpv_Hostname",
        download_path_key="Xpv_Download_Path",
        search_method=Search_Engine.xpv_search_video,
        download_methods={
            "default": Download_Engine.xpv_download_video,
            "pic": Download_Engine.xpv_download_comic_pic,
            "video": Download_Engine.xpv_download_community_video
        },
        video_struc=stru_xpv_video,
    )
    channel_manager.register_channel(xpv_channel)
    
    # 注册Hanime1渠道
    hanime1_channel = Channel(
        name="Hanime1",
        hostname_key="Hanime1_Hostname",
        download_path_key="Hanime1_Download_Path",
        search_method=Search_Engine.hanime1_search_video,
        download_methods={
            "default": Download_Engine.hanime1_download
        },
        video_struc=stru_hanime1_video,
    )
    channel_manager.register_channel(hanime1_channel)

# 自动注册渠道
register_search_channels()
