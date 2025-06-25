import importlib
import logging
import asyncio
from typing import Dict, List, Any


# checkin_manager.py

def load_plugins(self):
    """加载所有可用的签到插件"""
    import os
    plugin_dir = os.path.join(os.path.dirname(__file__), 'plugins')
    logging.info(f"开始加载插件，插件目录: {plugin_dir}")
    
    for filename in os.listdir(plugin_dir):
        if filename.endswith('.py') and not filename.startswith('__'):
            plugin_name = filename[:-3]
            logging.info(f"尝试加载插件: {plugin_name}")
            
            try:
                plugin_module = importlib.import_module(f'plugins.{plugin_name}')
                if hasattr(plugin_module, 'register_plugin'):
                    plugin_class = plugin_module.register_plugin()
                    self.plugins[plugin_name] = plugin_class
                    logging.info(f"成功加载插件: {plugin_name}，注册类型: {plugin_name}")
                else:
                    logging.warning(f"插件 {plugin_name} 缺少 register_plugin 函数")
            except Exception as e:
                logging.error(f"加载插件 {plugin_name} 失败: {str(e)}")
    
    # 打印已加载的插件列表
    logging.info(f"已加载的插件: {list(self.plugins.keys())}")
    
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
