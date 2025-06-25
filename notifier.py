import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import aiohttp
import asyncio
from typing import List, Dict

class Notifier:
    def __init__(self, config):
        self.config = config
        self.notification_config = config.get('notification', {})
    
    async def send_notification(self, results: List[Dict]):
        """发送通知"""
        if not results:
            logging.info("没有签到结果需要通知")
            return
        
        # 准备通知内容
        success_count = sum(1 for r in results if r.get('success'))
        failed_count = len(results) - success_count
        
        content = "### 自动签到结果汇总\n\n"
        content += f"✅ 成功: {success_count} 个\n"
        content += f"❌ 失败: {failed_count} 个\n\n"
        
        for result in results:
            status = "✅" if result.get('success') else "❌"
            content += f"{status} {result.get('site', '未知网站')}: {result.get('message', '无信息')}\n"
        
        # 发送邮件通知
        if self.notification_config.get('email_enabled', False):
            await self._send_email(content)
        
        # 发送Telegram通知
        if self.notification_config.get('telegram_enabled', False):
            await self._send_telegram(content)
    
    async def _send_email(self, content: str):
        """发送邮件通知"""
        try:
            # 获取配置
            email_config = self.notification_config.get('email', {})
            host = email_config.get('host', os.getenv('EMAIL_HOST'))
            port = email_config.get('port', int(os.getenv('EMAIL_PORT', 587)))
            user = email_config.get('user', os.getenv('EMAIL_USER'))
            password = email_config.get('password', os.getenv('EMAIL_PASSWORD'))
            recipients = email_config.get('recipients', os.getenv('EMAIL_RECIPIENTS', '')).split(',')
            
            if not all([host, port, user, password, recipients]):
                logging.error("邮件通知配置不完整")
                return
            
            # 创建邮件
            msg = MIMEMultipart()
            msg['From'] = user
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = "自动签到结果通知"
            
            # 添加内容
            msg.attach(MIMEText(content, 'plain', 'utf-8'))
            
            # 发送邮件
            with smtplib.SMTP(host, port) as server:
                server.starttls()
                server.login(user, password)
                server.send_message(msg)
            
            logging.info("邮件通知发送成功")
        except Exception as e:
            logging.error(f"邮件通知发送失败: {str(e)}")
    
    async def _send_telegram(self, content: str):
        """发送Telegram通知"""
        try:
            # 获取配置
            telegram_config = self.notification_config.get('telegram', {})
            bot_token = telegram_config.get('bot_token', os.getenv('TELEGRAM_BOT_TOKEN'))
            chat_id = telegram_config.get('chat_id', os.getenv('TELEGRAM_CHAT_ID'))
            
            if not bot_token or not chat_id:
                logging.error("Telegram通知配置不完整")
                return
            
            # 发送消息
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            data = {
                'chat_id': chat_id,
                'text': content,
                'parse_mode': 'Markdown'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=data) as response:
                    if response.status == 200:
                        logging.info("Telegram通知发送成功")
                    else:
                        logging.error(f"Telegram通知发送失败，状态码: {response.status}")
        except Exception as e:
            logging.error(f"Telegram通知发送失败: {str(e)}")    
