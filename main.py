import asyncio
import logging
import json
import os
from checkin_manager import CheckinManager
from notifier import Notifier

def setup_logging():
    """配置日志记录"""
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

async def main():
    """主函数"""
    setup_logging()
    logger = logging.getLogger("Main")
    
    # 加载配置
    config_path = os.getenv('CONFIG_PATH', 'config.json')
    if 'CONFIG' in os.environ:
        # 从环境变量加载配置（适用于 GitHub Actions）
        try:
            config = json.loads(os.environ['CONFIG'])
            logger.info("成功从环境变量加载配置")
        except json.JSONDecodeError as e:
            logger.error(f"配置解析失败: {str(e)}")
            return
    else:
        # 从文件加载配置
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            logger.info(f"成功从文件 {config_path} 加载配置")
        except FileNotFoundError:
            logger.error(f"配置文件 {config_path} 不存在")
            return
        except json.JSONDecodeError as e:
            logger.error(f"配置解析失败: {str(e)}")
            return
    
    # 初始化签到管理器
    manager = CheckinManager(config)
    
    # 执行签到
    results = await manager.run_all_checkins()
    
    # 发送通知
    notifier = Notifier(config)
    await notifier.send_notification(results)

if __name__ == "__main__":
    asyncio.run(main())    
