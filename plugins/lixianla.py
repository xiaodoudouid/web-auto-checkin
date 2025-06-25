import aiohttp
import asyncio
import logging
from bs4 import BeautifulSoup
from plugins.base_plugin import BasePlugin

class LixianlaPlugin(BasePlugin):
    def __init__(self, global_config, site_config):
        super().__init__(global_config, site_config)
        self.base_url = "https://lixianla.com"
        self.username = site_config.get('config', {}).get('username', '')
        self.password = site_config.get('config', {}).get('password', '')
    
    async def login(self) -> bool:
        try:
            # 更新为新的登录页面URL
            async with self.session.get(f"{self.base_url}/user-login.htm") as response:
                if response.status != 200:
                    raise Exception(f"获取登录页面失败，状态码: {response.status}")
                text = await response.text()
                soup = BeautifulSoup(text, 'html.parser')
                
                # 查找CSRF令牌
                csrf_token = None
                csrf_input = soup.find('input', {'name': '_token'})
                if csrf_input:
                    csrf_token = csrf_input.get('value')
                
                # 准备登录数据
                login_data = {
                    'email': self.username,
                    'password': self.password,
                    'remember': 'on'
                }
                
                if csrf_token:
                    login_data['_token'] = csrf_token
            
            # 执行登录请求
            async with self.session.post(
                f"{self.base_url}/user-login.htm",  # 确认实际的登录提交URL
                data=login_data
            ) as response:
                if response.status != 200:
                    raise Exception(f"登录失败，状态码: {response.status}")
                
                # 检查登录是否成功
                response_text = await response.text()
                if "用户中心" in response_text or "个人中心" in response_text:
                    logging.info(f"{self.name} 登录成功")
                    return True
                else:
                    logging.error(f"{self.name} 登录失败，可能是用户名或密码错误")
                    return False
        
        except Exception as e:
            logging.error(f"{self.name} 登录异常: {str(e)}")
            return False
    
    async def checkin(self) -> Dict[str, Any]:
        try:
            # 执行签到请求
            async with self.session.get(f"{self.base_url}/user/checkin") as response:
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
    """注册插件的函数，必须实现"""
    return LixianlaPlugin
