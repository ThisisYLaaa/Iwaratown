import hashlib
import json
import logging
import os
import re
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin

import cloudscraper
from bs4 import BeautifulSoup
import yt_dlp

from core.Custom_Struc import *
from core.DownloadProgressTracker import DownloadProgressTracker
from config.Init_Settings import *
from core.Iwara_Login import il
from utils.Logger import get_logger
logger: logging.Logger = get_logger("下载")
from config.Settings_Manager import sm, cm
from utils.CScraper import scraper

class Download_Engine:
    @staticmethod
    def xpv_download_video(video: stru_xpv_video) -> bool:
        base_url: str = urljoin(video.url, "/").rstrip("/")
        try:
            logger.info(f"获取视频页面: {video.url}")
            response = scraper.get(
                url=video.url,
                timeout=5, verify=sm.settings.get("Check_Cert", DEFAULT_SETTINGS["Check_Cert"])
            )
            logger.debug(f"status_code: {response.status_code}")
            response.raise_for_status()

            soup: BeautifulSoup = BeautifulSoup(response.text, "html.parser")
            """旧版 不再适用
            # video标签代表视频文件
            video_tag = soup.find("video")
            if not video_tag:
                logger.error("未找到视频文件标签")
                return False
            # 视频文件URL通常在src属性中
            video_file_url = video_tag.get("src")
            if not video_file_url:
                logger.error("视频文件标签中未找到src属性")
                return False
            # 视频文件URL不会是相对路径 因为视频文件URL指向另一个主机名
            """
            # 在script标签中查找视频地址
            script_tag = soup.find("script")
            if not script_tag:
                logger.error("未找到script标签")
                return False
            json_str: str = script_tag.string.strip() if script_tag.string else ""
            json_str = ''.join(ch for ch in json_str if ch.isprintable()).replace("\\", "")
            video_info = json.loads(json_str)
            video_file_url = video_info["contentUrl"]
            if not video_file_url:
                logger.error("视频文件标签中未找到contentUrl属性")
                return False
            logger.debug(f"video_file_url: {video_file_url}")
        except cloudscraper.exceptions.CloudflareChallengeError as e:
            logger.error(f"视频URL返回Cloudflare挑战错误: {e}")
            return False
        except Exception as e:
            logger.error(f"下载视频时发生未知错误: {e}")
            return False
        
        try:
            os.makedirs(video.dpath, exist_ok=True)
            save_path = os.path.join(video.dpath, f"{video.savetitle}.mp4")

            headers = DEFAULT_HEADERS.copy()
            headers["Referer"] = f"{base_url}/"
            headers["Accept"] = "video/webm,video/ogg,video/*;q=0.9,application/ogg;q=0.7,audio/*;q=0.6,*/*;q=0.5"
            headers["Accept-Language"] = "zh-CN,zh;q=0.9,en;q=0.8"
            headers["Accept-Encoding"] = "gzip, deflate, br"
            headers["Range"] = "bytes=0-"
            headers["DNT"] = "1"
            headers["Connection"] = "keep-alive"
            headers["Sec-Fetch-Dest"] = "video"
            headers["Sec-Fetch-Mode"] = "no-cors"
            headers["Sec-Fetch-Site"] = "cross-site"
            headers["Cache-Control"] = "no-cache"
            headers["Pragma"] = "no-cache"

            logger.info(f"开始下载视频: {video.savetitle}")
            logger.debug(f"headers: {headers}")
            ydl_opts: dict = {
                "format": "bestvideo+bestaudio/best",
                "outtmpl": save_path,
                "nocheckcertificate": True,
                "useragent": headers["User-Agent"],
                "referer": headers["Referer"],
                "http_headers": headers,
                "quiet": True,
                "no_warnings": True,
                "logtostderr": True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:  # pyright: ignore[reportArgumentType]
                ydl.download([video_file_url])
            logger.info(f"视频下载完成: {video.savetitle}")
            return True
        except OSError as e:
            logger.error(f"文件操作错误: {e}")
            return False
        except Exception as e:
            logger.error(f"下载视频时发生未知错误: {e}")
            return False

    @staticmethod
    def xpv_download_community_video(video_page_url: str) -> bool:
        base_url: str = urljoin(video_page_url, "/").rstrip("/")
        try:
            logger.info(f"获取视频页面: {video_page_url}")
            response = scraper.get(
                url=video_page_url,
                timeout=5, verify=sm.settings.get("Check_Cert", DEFAULT_SETTINGS["Check_Cert"])
            )
            logger.debug(f"status_code: {response.status_code}")
            response.raise_for_status()

            soup: BeautifulSoup = BeautifulSoup(response.text, "html.parser")
            video_tag = soup.find("video")
            if not video_tag:
                logger.error("未找到视频文件标签")
                return False
            # video标签下有source标签, 其中有视频链接(src)
            source_tag = video_tag.find("source")
            if not source_tag:
                logger.error("未找到视频文件source标签")
                return False
            video_file_url: str = str(source_tag.get("src", ""))
            if not video_file_url:
                logger.error("视频文件source标签中未找到src属性")
                return False
            logger.debug(f"video_file_url: {video_file_url}")
            
            #<div class="tweet-content"> </div>
            video_title = soup.find("div", class_="tweet-content")
            if video_title:
                video_title = video_title.text.strip()
            else:
                video_title = None
        except cloudscraper.exceptions.CloudflareChallengeError as e:
            logger.error(f"视频URL返回Cloudflare挑战错误: {e}")
            return False
        except Exception as e:
            logger.error(f"下载视频时发生未知错误: {e}")
            return False

        try:
            safe_title: str = re.sub(r'[\\/*?:"<>|]', "_", video_title or video_file_url.split("/")[-1].split(".")[0])
            save_dir: str = sm.settings.get("Custom_Download_Path", DEFAULT_SETTINGS["Custom_Download_Path"])
            os.makedirs(save_dir, exist_ok=True)
            save_path = os.path.join(save_dir, f"{safe_title}.mp4")

            headers = DEFAULT_HEADERS.copy()
            headers["Referer"] = f"{base_url}/"
            headers["Accept"] = "video/webm,video/ogg,video/*;q=0.9,application/ogg;q=0.7,audio/*;q=0.6,*/*;q=0.5"
            headers["Accept-Language"] = "zh-CN,zh;q=0.9,en;q=0.8"
            headers["Accept-Encoding"] = "gzip, deflate, br"
            headers["Range"] = "bytes=0-"
            headers["DNT"] = "1"
            headers["Connection"] = "keep-alive"
            headers["Sec-Fetch-Dest"] = "video"
            headers["Sec-Fetch-Mode"] = "no-cors"
            headers["Sec-Fetch-Site"] = "cross-site"
            headers["Cache-Control"] = "no-cache"
            headers["Pragma"] = "no-cache"

            # 使用requests直接下载视频并显示进度
            logger.info(f"开始下载视频: {safe_title}")
            
            # 发起请求获取视频内容
            response = scraper.get(video_file_url, headers=headers, timeout=30, stream=True)
            response.raise_for_status()
            
            # 获取文件总大小
            total_size = int(response.headers.get('content-length', 0))
            
            # 创建进度跟踪器
            tracker = DownloadProgressTracker(safe_title)
            tracker.total_size = total_size
            
            # 下载并写入文件
            downloaded = 0
            with open(save_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
                        f.flush()
                        downloaded += len(chunk)
                        tracker.update(downloaded)
            
            tracker.finish()
            
            if os.path.getsize(save_path) < 100000:  # 大于100KB才可能是视频文件
                logger.error("文件太小，不可能是视频")
                os.remove(save_path)
                return False
            # 检查文件类型
            with open(save_path, 'rb') as f:
                header = f.read(100)
                if b'ftyp' in header or b'moov' in header or b'mdat' in header:
                    logger.info("检测到有效的MP4视频文件结构")
                    logger.info(f"视频下载完成: {save_path}")
                    return True
                elif b'<!DOCTYPE' in header or b'<html' in header:
                    logger.error("下载的是HTML页面")
                    os.remove(save_path)
                    return False
                else:
                    logger.warning("文件类型未知，但大小正常")
                    return True
        
        except subprocess.TimeoutExpired:
            logger.error("下载超时")
            return False
        except OSError as e:
            logger.error(f"文件操作错误: {e}")
            return False
        except Exception as e:
            logger.error(f"下载视频时发生未知错误: {e}")
            return False

    @staticmethod
    def iw_download_video(video: stru_iw_video) -> bool:
        # 获取视频信息
        api_url: str = f"https://api.iwara.tv/video/{video.id}"
        
        try:
            logger.info(f"获取视频信息: {api_url}")
            
            # 获取认证头
            headers = il.get_auth_header()
            if headers:
                logger.debug("已添加登录token到请求头")
            
            response = scraper.get(
                url=api_url,
                headers=headers,
                timeout=5, verify=sm.settings.get("Check_Cert", DEFAULT_SETTINGS["Check_Cert"])
            )
            logger.debug(f"status_code: {response.status_code}")
            response.raise_for_status()

            data: dict = response.json()
            
        except Exception as e:
            logger.error(f"获取视频信息时发生未知错误: {e}")
            return False

        # 获取文件URL和相关参数
        url = data.get('fileUrl')
        if not url:
            logger.error("视频信息中缺少fileUrl")
            return False
            
        file_id = data['file']['id']
        expires = url.split('/')[4].split('?')[1].split('&')[0].split('=')[1]

        # 计算哈希值
        SHA_postfix = IWARA_SHA_POSTFIX
        SHA_key = file_id + "_" + expires + SHA_postfix
        hash_value = hashlib.sha1(SHA_key.encode('utf-8')).hexdigest()

        headers = {"X-Version": hash_value}

        # 获取视频资源列表
        try:
            # 获取认证头
            resources_headers = il.get_auth_header()
            if resources_headers:
                logger.debug("已添加登录token到资源请求头")
                
            resources_response = scraper.get(
                url=url, 
                headers=resources_headers,
                timeout=5, verify=sm.settings.get("Check_Cert", DEFAULT_SETTINGS["Check_Cert"])
            )
            logger.debug(f"resources status_code: {resources_response.status_code}")
            resources_response.raise_for_status()
            
            resources = resources_response.json()
        except Exception as e:
            logger.error(f"获取视频资源时发生错误: {e}")
            return False

        # 按质量排序资源，优先选择Source质量
        resources_by_quality = [None for _ in range(10)]
        for resource in resources:
            if resource['name'] == 'Source':
                resources_by_quality[0] = resource
            elif resource['name'] == '1080':
                resources_by_quality[1] = resource
            elif resource['name'] == '720':
                resources_by_quality[2] = resource
            elif resource['name'] == '480':
                resources_by_quality[3] = resource
            elif resource['name'] == '360':
                resources_by_quality[4] = resource

        # 寻找可用的资源
        selected_resource = None
        for resource in resources_by_quality:
            if resource is not None:
                selected_resource = resource
                break
        
        # 如果没有找到Source质量，则使用第一个可用资源
        if selected_resource is None and resources:
            selected_resource = resources[0]
            
        if selected_resource is None:
            logger.error("未找到可用的视频资源")
            return False

        # 构造下载链接
        download_link = "https:" + selected_resource['src']['download']
        file_type = selected_resource['type'].split('/')[1]
        
        save_path = os.path.join(video.dpath, f"{video.savetitle}.{file_type}")

        # 检查文件是否已存在
        if os.path.exists(save_path):
            logger.info(f"视频 {video.id} 已经下载，跳过下载")
            return True

        # 创建目录
        os.makedirs(video.dpath, exist_ok=True)

        # 下载视频
        logger.info(f"开始下载视频: {video.savetitle}")
        try:
            # 获取认证头
            download_headers = il.get_auth_header()
            if download_headers:
                logger.debug("已添加登录token到下载请求头")
                
            response = scraper.get(download_link, headers=download_headers, timeout=30, stream=True)
            response.raise_for_status()
            
            # 获取文件总大小
            total_size = int(response.headers.get('content-length', 0))
            
            # 创建进度跟踪器
            tracker = DownloadProgressTracker(video.savetitle)
            tracker.total_size = total_size
            
            downloaded = 0
            with open(save_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
                        f.flush()
                        downloaded += len(chunk)
                        tracker.update(downloaded)
            
            tracker.finish()
            logger.info(f"视频下载完成: {save_path}")
            return True
        except Exception as e:
            # 如果下载失败，删除可能创建的不完整文件
            if os.path.exists(save_path):
                os.remove(save_path)
            logger.error(f"下载视频失败: {video.savetitle}, 错误: {e}")
            return False

    @staticmethod
    def xpv_download_comic_pic(pic_page_url: str) -> bool:
        pic_file_urls: list = []
        try:
            logger.info(f"获取图片页面: {pic_page_url}")
            response = scraper.get(
                url=pic_page_url,
                timeout=5, verify=sm.settings.get("Check_Cert", DEFAULT_SETTINGS["Check_Cert"])
            )
            logger.debug(f"status_code: {response.status_code}")
            response.raise_for_status()

            soup: BeautifulSoup = BeautifulSoup(response.text, "html.parser")
            img_elements = soup.select("img.comic_img")
            title_element = soup.select_one("html body.photo_cus_body div#wrapper div.container div.row div div.panel.panel-default div.panel-heading div.pull-left")
            title: str = title_element.text.strip() if title_element else "Untitled"

            if img_elements:
                for img_element in img_elements:
                    img_url: str | None = img_element.get("data-src")  # pyright: ignore[reportAssignmentType]
                    if img_url:
                        pic_file_urls.append(img_url)
            else:
                logger.error("未找到图片URL")

            logger.info(f"共找到 {len(pic_file_urls)} 张图片")
            logger.info(f"标题: {title}")
        
        except Exception as e:
            logger.error(f"获取html失败: {e}")
            return False
        
        # 下载图片到./pics/
        if not pic_file_urls:
            logger.error("没有找到图片URL")
            return False
            
        # 创建保存目录
        save_dir = os.path.join(
            sm.settings.get("Xpv_Download_Path", DEFAULT_SETTINGS["Xpv_Download_Path"]), \
            sm.settings.get("Xpv_Pic_Download_RelativePath", DEFAULT_SETTINGS["Xpv_Pic_Download_RelativePath"]), \
            re.sub(r'[\\/*?:"<>|]', "_", title)
        )
        os.makedirs(save_dir, exist_ok=True)
        
        # 使用DownloadProgressTracker显示进度
        def download_image(url: str, index: int) -> bool:
            """下载单张图片"""
            try:
                # 从URL获取文件名
                filename = url.split("/")[-1]
                if not filename:
                    filename = f"image_{index}.jpg"
                    
                save_path = os.path.join(save_dir, filename)
                
                # 如果文件已存在，跳过下载
                if os.path.exists(save_path):
                    logger.info(f"文件已存在，跳过下载: {filename}")
                    return True
                
                headers: dict = {
                    "referer": f"{sm.settings.get("Xpv_Hostname", DEFAULT_SETTINGS["Xpv_Hostname"])}/"
                }
                # 下载图片
                response = scraper.get(
                    url=url, headers=headers,
                    timeout=30, verify=sm.settings.get("Check_Cert", DEFAULT_SETTINGS["Check_Cert"])
                )
                response.raise_for_status()
                
                # 保存图片
                with open(save_path, "wb") as f:
                    f.write(response.content)
                    
                # logger.debug(f"下载完成: {filename}")
                return True
            except Exception as e:
                logger.error(f"下载图片失败 {url}: {e}")
                return False
        
        # 使用多线程下载图片
        logger.info("开始多线程下载图片...")
        max_workers = 5  # 最大线程数
        success_count = 0
        
        # 创建进度跟踪器
        tracker = DownloadProgressTracker(title)
        tracker.total_size = len(pic_file_urls)
        
        try:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # 提交所有下载任务
                future_to_index = {
                    executor.submit(download_image, url, i): i 
                    for i, url in enumerate(pic_file_urls)
                }
                
                # 监控下载进度
                chunk_progress = [0] * len(pic_file_urls)
                
                # 使用线程监控进度
                progress_thread = threading.Thread(
                    target=tracker.monitor_chunk_progress, 
                    args=(chunk_progress,)
                )
                progress_thread.daemon = True
                progress_thread.start()
                
                # 等待所有任务完成
                for future in as_completed(future_to_index):
                    index = future_to_index[future]
                    try:
                        if future.result():
                            success_count += 1
                            chunk_progress[index] = 1
                    except Exception as e:
                        logger.error(f"下载任务出错: {e}")
                        chunk_progress[index] = 1  # 即使出错也标记为完成
                        
            # 停止进度监控
            tracker.stop()
            tracker.finish()
            
            logger.info(f"下载完成: {success_count}/{len(pic_file_urls)} 张图片下载成功")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"多线程下载过程中发生错误: {e}")
            tracker.stop()
            return False
    
    @staticmethod
    def hanime1_download(video: stru_hanime1_video) -> bool:
        """下载Hanime1视频"""
        # 更新日期
        video._update_updatedAt_from_url()

        try:
            # 检查目录是否存在
            os.makedirs(video.dpath, exist_ok=True)
            
            # 构建保存路径
            save_path = os.path.join(video.dpath, f"{video.savetitle}.mp4")
            
            # 如果文件已存在，跳过下载
            if os.path.exists(save_path):
                logger.info(f"文件已存在，跳过下载: {video.savetitle}")
                return True
            
            # 下载视频 yt-dlp
            opts = {
                "outtmpl": save_path,
                "quiet": True,
                "nocheckcertificate": not sm.settings.get("Check_Cert", DEFAULT_SETTINGS["Check_Cert"]),
            }
            with yt_dlp.YoutubeDL(opts) as ydl:  # pyright: ignore[reportArgumentType]
                ydl.download([video.url])
                
            logger.info(f"下载完成: {video.savetitle}")
            return True
        except Exception as e:
            logger.error(f"下载视频失败 {video.url}: {e}")
            return False
