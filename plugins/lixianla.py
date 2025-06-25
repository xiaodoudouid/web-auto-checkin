import aiohttp
import asyncio
import logging
import base64
from io import BytesIO
from PIL import Image
import pytesseract
from bs4 import BeautifulSoup
from plugins.base_plugin import BasePlugin

class LixianlaPlugin(BasePlugin):
    def __init__(self, global_config, site_config):
        super().__init__(global_config, site_config)
        self.base_url = "https://lixianla.com"
        self.username = site_config.get('config', {}).get('username', '')
        self.password = site_config.get('config', {}).get('password', '')
        # OCR配置（增强数字字母识别）
        self.ocr_lang = "eng"
        self.ocr_config = "--psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        self.captcha_attempts = 3  # 验证码重试次数
    
    async def login(self) -> bool:
        """带验证码的登录实现（含重试机制）"""
        for attempt in range(self.captcha_attempts):
            try:
                # 获取登录页面
                login_url = f"{self.base_url}/user-login.htm"
                async with self.session.get(login_url) as response:
                    if response.status != 200:
                        raise Exception(f"获取登录页面失败，状态码: {response.status}")
                    text = await response.text()
                    soup = BeautifulSoup(text, 'html.parser')
                    
                    # 查找CSRF令牌
                    csrf_token = self._get_csrf_token(soup)
                    
                    # 查找验证码图片
                    captcha_img, captcha_url = self._get_captcha_url(soup)
                    if not captcha_url:
                        logging.info("未检测到验证码，尝试无验证码登录")
                        captcha_text = ""
                    else:
                        # 下载验证码图片
                        captcha_text = await self._recognize_captcha(captcha_url)
                        if not captcha_text:
                            logging.warning(f"第{attempt+1}次验证码识别失败，重试中...")
                            continue
                
                # 准备登录数据
                login_data = {
                    'email': self.username,
                    'password': self.password,
                    'remember': 'on'
                }
                
                # 添加验证码和CSRF
                if captcha_text:
                    login_data['verify_code'] = captcha_text  # 假设实际字段为verify_code
                if csrf_token:
                    login_data['_token'] = csrf_token
                
                logging.info(f"登录数据: {login_data}")  # 打印提交的登录数据
                
                # 提交登录请求
                async with self.session.post(login_url, data=login_data) as response:
                    if response.status != 200:
                        raise Exception(f"登录请求失败，状态码: {response.status}")
                    
                    response_text = await response.text()
                    if "用户中心" in response_text or "个人中心" in response_text:
                        logging.info(f"{self.name} 登录成功（尝试{attempt+1}次）")
                        return True
                    elif "验证码错误" in response_text:
                        logging.warning(f"第{attempt+1}次验证码错误，重试中...")
                    else:
                        logging.error(f"登录失败: {response_text[:200]}")
                        return False
            
            except Exception as e:
                logging.error(f"登录尝试{attempt+1}异常: {str(e)}")
        
        logging.error(f"{self.name} 登录失败（{self.captcha_attempts}次验证码尝试均失败）")
        return False
    
    def _get_csrf_token(self, soup: BeautifulSoup) -> str:
        """获取CSRF令牌（支持多种可能的字段名）"""
        csrf_input = soup.find('input', {'name': ['_token', 'csrf_token', 'token']})
        return csrf_input.get('value') if csrf_input else ""
    
    def _get_captcha_url(self, soup: BeautifulSoup) -> (BeautifulSoup, str):
        """获取验证码图片URL（支持多种选择器）"""
        selectors = [
            ('img', {'id': 'captcha-img'}),
            ('img', {'class': 'captcha-image'}),
            ('img', {'alt': '验证码'})
        ]
        
        for tag, attrs in selectors:
            img = soup.find(tag, attrs)
            if img:
                url = img.get('src')
                if url and not url.startswith('http'):
                    url = f"{self.base_url}{url}"
                return img, url
        return None, ""
    
    async def _recognize_captcha(self, captcha_url: str) -> str:
        """识别验证码（含图片预处理）"""
        try:
            async with self.session.get(captcha_url) as response:
                if response.status != 200:
                    raise Exception(f"获取验证码图片失败，状态码: {response.status}")
                
                captcha_bytes = await response.read()
                img = Image.open(BytesIO(captcha_bytes))
                
                # 增强处理（灰度化、降噪、锐化）
                img = img.convert('L')  # 灰度化
                img = img.point(lambda p: p > 180 and 255)  # 高阈值去噪
                img = img.filter(ImageFilter.SHARPEN)  # 锐化
                
                # 保存图片用于调试（GitHub Actions中可查看）
                with open(f"captcha_{int(time.time())}.png", "wb") as f:
                    img.save(f)
                
                # 识别验证码
                text = pytesseract.image_to_string(img, lang=self.ocr_lang, config=self.ocr_config)
                text = text.strip().upper()  # 标准化处理
                
                logging.info(f"识别的验证码: {text}")
                return text if len(text) >= 4 else ""  # 至少4位有效字符
        
        except Exception as e:
            logging.error(f"验证码识别异常: {str(e)}")
            return ""
    
    async def checkin(self) -> Dict[str, Any]:
        """执行签到（含验证码处理）"""
        try:
            checkin_url = f"{self.base_url}/user/checkin"
            async with self.session.get(checkin_url) as response:
                if response.status != 200:
                    raise Exception(f"获取签到页面失败，状态码: {response.status}")
                
                text = await response.text()
                soup = BeautifulSoup(text, 'html.parser')
                
                # 检查是否需要验证码
                captcha_img, captcha_url = self._get_captcha_url(soup)
                captcha_text = await self._recognize_captcha(captcha_url) if captcha_url else ""
                
                # 执行签到
                checkin_data = {}
                if captcha_text:
                    checkin_data['verify_code'] = captcha_text  # 假设签到验证码字段
                
                async with self.session.post(checkin_url, data=checkin_data) as response:
                    if response.status != 200:
                        raise Exception(f"签到请求失败，状态码: {response.status}")
                    
                    result = await response.json()
                    if result.get('ret') == 1:
                        logging.info(f"{self.name} 签到成功: {result.get('msg')}")
                        return {"success": True, "message": result.get('msg')}
                    else:
                        logging.error(f"{self.name} 签到失败: {result.get('msg')}")
                        return {"success": False, "message": result.get('msg')}
        
        except Exception as e:
            logging.error(f"{self.name} 签到异常: {str(e)}")
            return {"success": False, "message": f"签到异常: {str(e)}"}

def register_plugin():
    """注册插件"""
    return LixianlaPlugin
