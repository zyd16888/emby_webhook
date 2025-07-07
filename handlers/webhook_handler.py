import aiohttp
import re

from config.settings import EMBY_URL, EMBY_API_KEY, WEBHOOK_CHANNEL_ID, TELEGRAM_BOT_TOKEN
from models import EmbyWebhook
from utils.helpers import parse_emby_date
from utils.logger import Logger


class WebhookHandler():
    def __init__(self):
        super().__init__()
        self.logger = Logger().get_logger()
        self.telegram_api_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

    def clean_html_text(self, text: str) -> str:
        """
        清理 HTML 标签，转换为 Telegram 支持的格式
        """
        if not text:
            return ""
        
        # 替换常见的 HTML 标签
        text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'<p[^>]*>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'</p>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'<[^>]+>', '', text)  # 移除其他 HTML 标签
        
        # 清理多余的换行符
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = text.strip()
        
        return text

    async def send_new_media_notification(self, webhook: EmbyWebhook) -> None:
        """
        通过 Telegram API 发送新媒体通知到指定频道
        """
        if not webhook.Item:
            self.logger.error("Webhook 数据中没有 Item 信息")
            return
            
        item = webhook.Item
        
        # 获取图片URL
        primary_image = None
        if EMBY_URL and EMBY_API_KEY:
            primary_image = item.get_backdrop_url(EMBY_URL, EMBY_API_KEY, 0)

        # 构建消息文本
        message = (
            f"🎬 <b>新片入库</b>\n\n"
            f"📝 <b>标题:</b> {item.Name}\n"
            f"🗓️ <b>发行日期:</b> {parse_emby_date(item.PremiereDate)}\n"
            f"⏱ <b>入库时间:</b> {parse_emby_date(item.DateCreated)}\n"
        )

        if item.Overview:
            # 清理 HTML 标签
            clean_overview = self.clean_html_text(item.Overview)
            if clean_overview:
                message += f"\n📖 <b>简介:</b>\n{clean_overview}\n"

        if item.Studios:
            studios = ', '.join(studio.Name for studio in item.Studios)
            message += f"\n🏢 <b>制作公司:</b> {studios}"

        if item.TagItems:
            tags = ', '.join(tag.Name for tag in item.TagItems)
            message += f"\n🏷 <b>标签:</b> {tags}"

        if item.Genres:
            genres = ', '.join(genre for genre in item.Genres)
            message += f"\n🎞️ <b>类型:</b> {genres}"

        # 发送消息
        try:
            async with aiohttp.ClientSession() as session:
                if primary_image:
                    # 发送图文消息
                    endpoint = f"{self.telegram_api_url}/sendPhoto"
                    data = {
                        "chat_id": WEBHOOK_CHANNEL_ID,
                        "photo": primary_image,
                        "caption": message,
                        "parse_mode": "HTML"
                    }
                else:
                    # 发送纯文本消息
                    endpoint = f"{self.telegram_api_url}/sendMessage"
                    data = {
                        "chat_id": WEBHOOK_CHANNEL_ID,
                        "text": message,
                        "parse_mode": "HTML"
                    }
                
                async with session.post(endpoint, json=data) as response:
                    if not response.ok:
                        response_text = await response.text()
                        self.logger.error(f"发送通知消息失败: {response_text}")
                        
        except Exception as e:
            self.logger.error(f"发送通知消息失败: {str(e)}")
