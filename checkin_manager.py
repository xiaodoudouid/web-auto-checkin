import importlib
import logging
import asyncio
from typing import Dict, List, Any

class CheckinManager:
    def __init__(self, config: Dict[str, Any]):
        self.global_config = config.get('global', {})
        self.site_configs = config.get('sites', [])
        self.plugins = {}
        self.load_plugins()
        
    def load_plugins(self):
        """加载所有可用的签到插件"""
        import os
        plugin_dir = os.path.join(os.path.dirname(__file__), 'plugins')
        for filename in os.listdir(plugin_dir):
            if filename.endswith('.py') and not filename.startswith('__'):
                plugin_name = filename[:-3]
                try:
                    plugin_module = importlib.import_module(f'plugins.{plugin_name}')
                    if hasattr(plugin_module, 'register_plugin'):
                        plugin_class = plugin_module.register_plugin()
                        self.plugins[plugin_name] = plugin_class
                        logging.info(f"成功加载插件: {plugin_name}")
                except Exception as e:
                    logging.error(f"加载插件 {plugin_name} 失败: {str(e)}")
    
    async def run_all_checkins(self):
        """运行所有配置的网站签到任务"""
        results = []
        tasks = []
        
        for site_config in self.site_configs:
            site_type = site_config.get('type')
            if site_type in self.plugins:
                plugin_class = self.plugins[site_type]
                plugin = plugin_class(self.global_config, site_config)
                tasks.append(plugin.run())
            else:
                logging.warning(f"未知的网站类型: {site_type}")
        
        if tasks:
            results = await asyncio.gather(*tasks)
        
        return results    
