import aiohttp
import asyncio
import logging
from bs4 import BeautifulSoup
from plugins.base_plugin import BasePlugin

class V2exPlugin(BasePlugin):
    def __init__(self, global_config, site_config):
        super().__init__(global_config, site_config)
        self.base_url = "https://www.v2ex.com"
        self.cookies = site_config.get('config', {}).get('cookies', {})
        
        # 设置cookies
        for key, value in self.cookies.items():
            self.session.cookie_jar.update_cookies({key: value})
    
    async def login(self):
        """检查是否已登录"""
        try:
            async with self.session.get(f"{self.base_url}/mission/daily") as response:
                if response.status != 200:
                    raise Exception(f"获取登录状态失败，状态码: {response.status}")
                text = await response.text()
                
                # 检查是否已登录
                if "每日登录奖励" in text:
                    logging.info(f"{self.name} 已登录")
                    return True
                else:
                    logging.error(f"{self.name} 未登录或Cookie已过期")
                    return False
        except Exception as e:
            logging.error(f"{self.name} 登录状态检查异常: {str(e)}")
            return False
    
    async def checkin(self):
        """执行签到"""
        try:
            # 先获取签到页面，提取token
            async with self.session.get(f"{self.base_url}/mission/daily") as response:
                if response.status != 200:
                    raise Exception(f"获取签到页面失败，状态码: {response.status}")
                text = await response.text()
                soup = BeautifulSoup(text, 'html.parser')
                
                # 查找签到链接
                checkin_link = None
                for a in soup.find_all('a'):
                    if 'once' in a.get('href', '') and 'daily' in a.get('href', ''):
                        checkin_link = a.get('href')
                        break
                
                if not checkin_link:
                    # 检查是否已经签到
                    if "已领取" in text:
                        logging.info(f"{self.name} 今天已经签到过了")
                        return {"success": True, "message": "今天已经签到过了"}
                    else:
                        logging.error(f"{self.name} 未找到签到链接")
                        return {"success": False, "message": "未找到签到链接"}
                
                # 执行签到
                async with self.session.get(f"{self.base_url}{checkin_link}") as checkin_response:
                    if checkin_response.status != 200:
                        raise Exception(f"签到请求失败，状态码: {checkin_response.status}")
                    checkin_text = await checkin_response.text()
                    
                    if "领取每日奖励" in checkin_text:
                        logging.info(f"{self.name} 签到成功")
                        return {"success": True, "message": "签到成功"}
                    elif "已领取" in checkin_text:
                        logging.info(f"{self.name} 今天已经签到过了")
                        return {"success": True, "message": "今天已经签到过了"}
                    else:
                        logging.error(f"{self.name} 签到失败，未知响应")
                        return {"success": False, "message": "签到失败，未知响应"}
        except Exception as e:
            logging.error(f"{self.name} 签到异常: {str(e)}")
            return {"success": False, "message": f"签到异常: {str(e)}"}

def register_plugin():
    return V2exPlugin    