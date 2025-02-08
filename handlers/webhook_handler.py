import aiohttp

from config.settings import EMBY_URL, EMBY_API_KEY, WEBHOOK_CHANNEL_ID, TELEGRAM_BOT_TOKEN
from models import EmbyWebhook
from utils.helpers import parse_emby_date
from utils.logger import Logger


class WebhookHandler():
    def __init__(self):
        super().__init__()
        self.logger = Logger().get_logger()
        self.telegram_api_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

    async def send_new_media_notification(self, webhook: EmbyWebhook) -> None:
        """
        通过 Telegram API 发送新媒体通知到指定频道
        """
        item = webhook.Item
        # 获取图片URL
        primary_image = item.get_backdrop_url(EMBY_URL, EMBY_API_KEY, 0)

        # 构建消息文本
        message = (
            f"🎬 <b>新片入库</b>\n\n"
            f"📝 <b>标题:</b> {item.Name}\n"
            f"🗓️ <b>发行日期:</b> {parse_emby_date(item.PremiereDate)}\n"
            f"⏱ <b>入库时间:</b> {parse_emby_date(item.DateCreated)}\n"
        )

        if item.Overview:
            message += f"\n📖 <b>简介:</b>\n{item.Overview}\n"

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
