from Custom_Struc import *

import logging
from Logger import get_logger
logger: logging.Logger = get_logger("搜索")

from Init_Settings import *
from Settings_Manager import Settings_Manager
sm: Settings_Manager = Settings_Manager()

from Iwara_Login import IwaraLogin
iwara_login = IwaraLogin()

from CScraper import get_scraper
scraper = get_scraper()

# 导入渠道管理器
from Channel import channel_manager, Channel

from urllib.parse import urlencode, urljoin
from bs4 import BeautifulSoup
import cloudscraper
import datetime
import requests
import json
import time
import re

# 禁用不安全的HTTPS请求警告
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class Search_Engine:
    @staticmethod
    def iw_search_author(keyword: str) -> list[stru_iw_author]:
        api_url: str = f"{sm.settings.get('Iwara_API_Hostname', DEFAULT_SETTINGS['Iwara_API_Hostname'])}"
        api_url += f"/search?type=users&page=0&query={keyword}"

        try:
            logger.info(f"向Iwara API发送作者搜索请求: {api_url}")
            # 获取认证头
            headers = iwara_login.get_auth_header()
            if headers:
                logger.debug(f"添加认证token到请求头")
            
            response = scraper.get(
                url=api_url,
                headers=headers,
                timeout=5, verify=sm.settings.get("Check_Cert", DEFAULT_SETTINGS["Check_Cert"])
            )
            logger.debug(f"status_code: {response.status_code}")
            response.raise_for_status()
            data: dict = response.json()

            authors: list[stru_iw_author] = []
            user: dict
            for user in data.get("results", []):
                authors.append(stru_iw_author(user))
            logger.info(f"找到 {len(authors)} 个作者")
            return authors
        
        except requests.exceptions.Timeout as e:
            logger.error(f"请求Iwara API超时: {e}")
        except requests.exceptions.ConnectionError as e:
            logger.error(f"连接Iwara API失败: {e}")
        except requests.exceptions.HTTPError as e:
            logger.error(f"Iwara API返回HTTP错误: {e}")
        except requests.exceptions.RequestException as e:
            logger.error(f"请求Iwara API时发生错误: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"解析Iwara API响应JSON失败: {e}")
        except Exception as e:
            logger.error(f"处理Iwara API响应时发生未知错误: {e}")
        return []
    
    @staticmethod
    def iw_search_video(author_id: str) -> list[stru_iw_video]:
        video_list: list[stru_iw_video] = []
        current_page: int = 0
        try:
            for _ in range(100):
                api_url = f"https://api.iwara.tv/videos?rating=all&sort=date&page={current_page}&user={author_id}"
                
                logger.info(f"向Iwara API发送视频列表请求: {api_url}")
                # 获取认证头
                headers = iwara_login.get_auth_header()
                if headers:
                    logger.debug(f"添加认证token到请求头")
                
                response = scraper.get(
                    url=api_url,
                    headers=headers,
                    timeout=30, verify=sm.settings.get("Check_Cert", DEFAULT_SETTINGS["Check_Cert"])
                )
                logger.debug(f"status_code: {response.status_code}")
                response.raise_for_status()
                data: dict = response.json()

                if not data.get("results", []):
                    break
                item: dict
                for item in data.get("results", []):
                    temp = stru_iw_video(item)
                    temp.updatedAt = datetime.datetime.fromisoformat(temp.createdAt.replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M:%S")
                    # temp.createdAt = datetime.datetime.fromisoformat(temp.createdAt.replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M:%S")
                    # temp.updatedAt = datetime.datetime.fromisoformat(temp.updatedAt.replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M:%S")
                    video_list.append(temp)
                if len(data.get("results", [])) < 32:
                    break
                current_page += 1
                        
            logger.info(f"成功获取 {len(video_list)} 个视频")
            return video_list
            
        except requests.exceptions.Timeout as e:
            logger.error(f"请求Iwara API超时: {e}")
        except requests.exceptions.ConnectionError as e:
            logger.error(f"连接Iwara API失败: {e}")
        except requests.exceptions.HTTPError as e:
            logger.error(f"Iwara API返回HTTP错误: {e}")
        except requests.exceptions.RequestException as e:
            logger.error(f"请求Iwara API时发生错误: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"解析Iwara API响应JSON失败: {e}")
        except Exception as e:
            logger.error(f"处理Iwara API响应时发生未知错误: {e}")
        return []

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
            response = scraper.post(
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
            for _ in range(100):
                logger.info(f"获取Xpv搜索结果页面 第{current_page}页: {redirect_url}")
                target_url = urljoin(base_url, f"/e/search/result/index.php?page={current_page}&searchid={searchid}")
                response = scraper.get(
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
    def hanime1_search_video(keyword: str) -> list[stru_hanime1_video]:
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
            
            current_page: int = 0
            current_video_list = []
            for _ in range(100):
                params["page"] = current_page
                logger.info(f"获取Hanime1搜索结果页面 第{current_page}页: {get_url}")
                logger.debug(f"params: {params}")

                response = scraper.get(
                    url=get_url, params=params,
                    timeout=5, proxies=PROXIES, verify=sm.settings.get("Check_Cert", DEFAULT_SETTINGS["Check_Cert"])
                )
                logger.debug(f"status_code: {response.status_code}")
                response.raise_for_status()

                soup: BeautifulSoup = BeautifulSoup(response.text, "html.parser")
                # 每个视频的div标签
                current_video_list = soup.find_all("div", class_="col-xs-6 col-sm-4 col-md-2 search-doujin-videos hidden-xs hover-lighter multiple-link-wrapper")
                if not current_video_list:
                    break
                for div in current_video_list:
                    # div标签下class为"card-mobile-user"的a标签的值为author
                    a_tag = div.find("a", class_="card-mobile-user")
                    if a_tag:
                        author: str = str(a_tag.text.strip())
                    else:
                        author = "unknown"

                    # div标签本身有标题title, div下的a标签有视频链接href
                    title: str = str(div.get("title", ""))
                    a_tag = div.find("a", href=True)
                    if a_tag:
                        href: str = str(a_tag["href"])
                        # 结合get_url和params, 构造完整的视频链接
                        params_string = urlencode(params)
                        furl: str = f"{get_url}?{params_string}"
                        video_list.append(stru_hanime1_video({"title": title, "url": href, "author": author, "furl": furl}))
                if len(current_video_list) < 60:
                    break
                current_page += 1
            else:
                logger.warning(f"搜索达到上限, 暂停搜索")
            logger.info(f"成功获取 {len(video_list)} 个视频")
            return video_list

        except cloudscraper.exceptions.CloudflareChallengeError as e:
            logger.error(f"Hanime1搜索接口返回Cloudflare挑战错误: {e}")
        except Exception as e:
            logger.error(f"处理Hanime1搜索结果时发生未知错误: {e}")
        return []

# Debug
if __name__ == "__main__":
    Search_Engine.hanime1_search_video("PastaPaprika")

# 注册搜索渠道到渠道管理器
def register_search_channels():
    """注册搜索渠道到渠道管理器"""
    from Download_Engine import Download_Engine
    
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
        }
    )
    channel_manager.register_channel(xpv_channel)
    
    # 注册Iwara渠道 - 定义专用搜索函数
    def iwara_search_wrapper(keyword):
        """Iwara搜索包装函数"""
        authors = Search_Engine.iw_search_author(keyword)
        if authors:
            return Search_Engine.iw_search_video(authors[0].id)
        return []
    
    iwara_channel = Channel(
        name="Iwara",
        hostname_key="Iwara_Hostname",
        download_path_key="Iwara_Download_Path",
        search_method=iwara_search_wrapper,
        download_methods={
            "default": Download_Engine.iw_download_video
        }
    )
    channel_manager.register_channel(iwara_channel)
    
    # 注册Hanime1渠道
    hanime1_channel = Channel(
        name="Hanime1",
        hostname_key="Hanime1_Hostname",
        download_path_key="Hanime1_Download_Path",
        search_method=Search_Engine.hanime1_search_video,
        download_methods={
            "default": Download_Engine.hanime1_download
        }
    )
    channel_manager.register_channel(hanime1_channel)
    
    logger.info(f"已注册 {len(channel_manager.list_channels())} 个渠道")

# 自动注册渠道
register_search_channels()
