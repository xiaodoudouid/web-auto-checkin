import json
import logging
import asyncio
from checkin_manager import CheckinManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("checkin.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("Main")

async def main():
    """主函数"""
    try:
        # 从环境变量加载配置
        config_json = __import__('os').getenv('CONFIG', '{}')
        config = json.loads(config_json)
        logger.info("成功从环境变量加载配置")
        
        # 初始化签到管理器
        checkin_manager = CheckinManager(config)
        
        # 执行所有签到任务
        results = await checkin_manager.run_all_checkins()
        
        # 输出结果
        for result in results:
            status = "✅" if result.get("success") else "❌"
            logger.info(f"{status} {result.get('site', '未知站点')}: {result.get('message', '无消息')}")
            
    except Exception as e:
        logger.error(f"执行签到任务时发生错误: {str(e)}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())
