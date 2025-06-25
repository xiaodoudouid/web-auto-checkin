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
        # OCR配置
        self.ocr_lang = "eng"  # 英文识别（验证码通常为字母数字）
        self.ocr_config = "--psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    
    async def login(self) -> bool:
        """带验证码的登录实现"""
        try:
            # 获取登录页面
            login_url = f"{self.base_url}/user-login.htm"
            async with self.session.get(login_url) as response:
                if response.status != 200:
                    raise Exception(f"获取登录页面失败，状态码: {response.status}")
                text = await response.text()
                soup = BeautifulSoup(text, 'html.parser')
                
                # 查找CSRF令牌
                csrf_token = None
                csrf_input = soup.find('input', {'name': '_token'})
                if csrf_input:
                    csrf_token = csrf_input.get('value')
                
                # 查找验证码图片
                captcha_img = soup.find('img', {'id': 'captcha-img'})  # 根据实际页面调整
                if not captcha_img:
                    captcha_img = soup.find('img', {'class': 'captcha'})  # 备用选择器
                    
                if not captcha_img:
                    logging.warning("未找到验证码图片，尝试无验证码登录")
                else:
                    captcha_url = captcha_img.get('src')
                    if not captcha_url.startswith('http'):
                        captcha_url = f"{self.base_url}{captcha_url}"
                    
                    # 下载验证码图片
                    async with self.session.get(captcha_url) as captcha_response:
                        if captcha_response.status != 200:
                            raise Exception(f"获取验证码图片失败，状态码: {captcha_response.status}")
                        
                        captcha_bytes = await captcha_response.read()
                        captcha_text = self.recognize_captcha(captcha_bytes)
                        logging.info(f"识别的验证码: {captcha_text}")
            
            # 准备登录数据
            login_data = {
                'email': self.username,
                'password': self.password,
                'remember': 'on'
            }
            
            # 添加验证码（如果有）
            if 'captcha_text' in locals():
                login_data['captcha'] = captcha_text  # 根据实际表单字段名调整
            
            # 添加CSRF令牌（如果有）
            if csrf_token:
                login_data['_token'] = csrf_token
            
            # 提交登录请求
            async with self.session.post(login_url, data=login_data) as response:
                if response.status != 200:
                    raise Exception(f"登录请求失败，状态码: {response.status}")
                
                response_text = await response.text()
                if "用户中心" in response_text or "个人中心" in response_text:
                    logging.info(f"{self.name} 登录成功")
                    return True
                else:
                    logging.error(f"{self.name} 登录失败: {response_text}")
                    return False
        
        except Exception as e:
            logging.error(f"{self.name} 登录异常: {str(e)}")
            return False
    
    def recognize_captcha(self, captcha_bytes: bytes) -> str:
        """识别验证码图片"""
        try:
            # 打开图片并预处理
            img = Image.open(BytesIO(captcha_bytes))
            
            # 转换为灰度图
            img = img.convert('L')
            
            # 简单降噪（阈值处理）
            img = img.point(lambda x: 0 if x < 128 else 255, '1')
            
            # 使用Tesseract识别
            text = pytesseract.image_to_string(img, lang=self.ocr_lang, config=self.ocr_config)
            return text.strip().upper()  # 转为大写并去除空格
        
        except Exception as e:
            logging.error(f"验证码识别失败: {str(e)}")
            return ""
    
    async def checkin(self) -> Dict[str, Any]:
        """执行签到"""
        try:
            # 检查是否需要验证码
            async with self.session.get(f"{self.base_url}/user/checkin") as response:
                if response.status != 200:
                    raise Exception(f"获取签到页面失败，状态码: {response.status}")
                
                text = await response.text()
                soup = BeautifulSoup(text, 'html.parser')
                
                # 检查是否需要验证码
                captcha_required = bool(soup.find('img', {'id': 'checkin-captcha'}))
                
                if captcha_required:
                    logging.info("签到需要验证码，尝试识别")
                    captcha_img = soup.find('img', {'id': 'checkin-captcha'})
                    captcha_url = captcha_img.get('src')
                    if not captcha_url.startswith('http'):
                        captcha_url = f"{self.base_url}{captcha_url}"
                    
                    # 下载验证码图片
                    async with self.session.get(captcha_url) as captcha_response:
                        captcha_bytes = await captcha_response.read()
                        captcha_text = self.recognize_captcha(captcha_bytes)
                        logging.info(f"识别的签到验证码: {captcha_text}")
                
                # 执行签到
                checkin_data = {}
                if captcha_required:
                    checkin_data['captcha'] = captcha_text
                
                async with self.session.post(
                    f"{self.base_url}/user/checkin",
                    data=checkin_data
                ) as response:
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
