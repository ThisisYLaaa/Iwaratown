from utils.CScraper import cloud_scraper
from requests.auth import AuthBase
import json

from config.Settings_Manager import sm
from config.Init_Settings import DEFAULT_SETTINGS

api_url = sm.settings.get("Iwara_API_Hostname", DEFAULT_SETTINGS["Iwara_API_Hostname"])

class BearerAuth(AuthBase):
    """Bearer Authentication for API requests"""
    def __init__(self, token):
        self.token = token

    def __call__(self, r):
        r.headers['Authorization'] = 'Bearer ' + self.token
        return r

class IwaraLogin:
    """
    Iwara平台登录类，处理用户认证和token管理
    提供登录、检查token有效性、刷新token等功能
    """
    def __init__(self):
        self.scraper = cloud_scraper
        self.api_url: str = api_url
        self.token: str = ""
        self.user_info: dict = {}
        self._is_logged_in: bool = False
        # 初始化时检查登录状态
        self._check_login_status()
    
    def _check_login_status(self):
        """检查当前登录状态并更新内部标志"""
        self._is_logged_in = self.token != "" and self.check_token_validity()
    
    def is_logged_in(self) -> bool:
        """
        检查用户是否已登录
        
        Returns:
            bool: 是否已登录
        """
        # 再次检查以确保状态是最新的
        self._check_login_status()
        return self._is_logged_in

    def login(self, email: str, password: str) -> tuple:
        """
        登录Iwara平台
        
        Args:
            email (str): 用户邮箱
            password (str): 用户密码
            
        Returns:
            tuple: (成功状态, 消息, token)
        """
        url = self.api_url + '/user/login'
        payload = {'email': email, 'password': password}
        
        try:
            # 发送登录请求
            response = self.scraper.post(url, json=payload)
            
            # 检查响应状态
            if response.status_code == 200:
                try:
                    data = response.json()
                    self.token = data.get('token')
                    
                    if self.token:
                        # 获取用户信息
                        self.user_info = self._get_user_info()
                        # 更新登录状态标志
                        self._is_logged_in = True
                        print('登录成功')
                        return True, '登录成功', self.token
                    else:
                        print('登录失败: 未获取到token')
                        return False, '登录失败: 未获取到token', None
                        
                except json.JSONDecodeError:
                    print('登录失败: 无效的响应格式')
                    return False, '登录失败: 无效的响应格式', None
            else:
                error_msg = f'登录失败: HTTP状态码 {response.status_code}'
                print(error_msg)
                # 提供更友好的错误消息
                if response.status_code == 401:
                    error_msg = '用户名或密码错误'
                elif response.status_code == 429:
                    error_msg = '请求过于频繁，请稍后再试'
                elif response.status_code >= 500:
                    error_msg = '服务器错误，请稍后再试'
                return False, error_msg, None
                
        except Exception as e:
            error_msg = f'登录失败: {str(e)}'
            print(error_msg)
            return False, error_msg, None

    def _get_user_info(self) -> dict:
        """
        获取当前登录用户的信息
        
        Returns:
            dict: 用户信息字典，失败时返回None
        """
        if not self.token:
            return {}
            
        url = self.api_url + '/user/profile'
        
        try:
            response = self.scraper.get(url, auth=BearerAuth(self.token))
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f'获取用户信息失败: HTTP状态码 {response.status_code}')
                return {}
                
        except Exception as e:
            print(f'获取用户信息失败: {str(e)}')
            return {}

    def check_token_validity(self) -> bool:
        """
        检查当前token是否有效
        
        Returns:
            bool: token有效返回True，无效或未设置返回False
        """
        if not self.token:
            return False
            
        url = self.api_url + '/user/profile'
        
        try:
            response = self.scraper.get(url, auth=BearerAuth(self.token))
            is_valid = response.status_code == 200
            # 如果token无效，更新登录状态标志
            if not is_valid:
                self._is_logged_in = False
            return is_valid
            
        except Exception:
            self._is_logged_in = False
            return False

    def logout(self):
        """
        登出操作，清除token和用户信息
        """
        self.token = ""
        self.user_info = {}
        self._is_logged_in = False
        print('已登出')

    def get_token(self) -> str:
        """
        获取当前token
        
        Returns:
            str: 当前token，未登录时返回None
        """
        # 验证token是否有效
        if self.token and not self.check_token_validity():
            return ""
        return self.token
    
    def get_auth_header(self) -> dict:
        """
        获取认证请求头
        
        Returns:
            dict: 包含Authorization头的字典，如果没有有效的token则返回空字典
        """
        token = self.get_token()
        if token:
            return {"Authorization": f"Bearer {token}"}
        return {}

    def get_user_info(self) -> dict:
        """
        获取用户信息
        
        Returns:
            dict: 用户信息，未登录时返回None
        """
        # 如果token有效但用户信息为None，尝试重新获取
        if self.is_logged_in() and self.user_info is None:
            self.user_info = self._get_user_info()
        return self.user_info

il: IwaraLogin = IwaraLogin()

