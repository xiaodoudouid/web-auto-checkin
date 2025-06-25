from abc import ABC, abstractmethod
import aiohttp
import logging
from typing import Dict, Any

class BasePlugin(ABC):
    def __init__(self, global_config: Dict[str, Any], site_config: Dict[str, Any]):
        self.global_config = global_config
        self.site_config = site_config
        self.name = site_config.get('name', site_config.get('type', 'UnknownSite'))
        self.session = aiohttp.ClientSession(
            headers=self.get_headers(),
            timeout=aiohttp.ClientTimeout(total=global_config.get('timeout', 30))
        )
    
    def get_headers(self):
        """获取通用请求头"""
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6',
            'Connection': 'keep-alive',
        }
    
    @abstractmethod
    async def login(self) -> bool:
        """执行登录操作，返回登录是否成功"""
        pass
    
    @abstractmethod
    async def checkin(self) -> Dict[str, Any]:
        """执行签到操作，返回包含签到结果的字典"""
        pass
    
    async def run(self) -> Dict[str, Any]:
        """运行完整的签到流程"""
        try:
            logging.info(f"开始 {self.name} 签到任务")
            success = await self.login()
            if success:
                result = await self.checkin()
                result['site'] = self.name
                return result
            return {"success": False, "message": "登录失败", "site": self.name}
        except Exception as e:
            logging.error(f"{self.name} 签到过程中发生异常: {str(e)}")
            return {"success": False, "message": f"发生异常: {str(e)}", "site": self.name}
        finally:
            await self.session.close()    