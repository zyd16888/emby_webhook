import aiohttp
import re
import json
import asyncio

from config.settings import EMBY_URL, EMBY_API_KEY, WEBHOOK_CHANNEL_ID, TELEGRAM_BOT_TOKEN
from models import EmbyWebhook
from utils.helpers import parse_emby_date, format_runtime, format_size
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
        text = re.sub(r'<br\s*?>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'<p[^>]*>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'</p>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'<[^>]+>', '', text)  # 移除其他 HTML 标签

        # 清理多余的换行符
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = text.strip()

        return text

    async def get_library_name(self, library_id: str, visited_ids: set = None) -> str:
        """
        通过媒体库ID获取媒体库名称
        """
        if visited_ids is None:
            visited_ids = set()

        # 防止无限递归
        if library_id in visited_ids:
            self.logger.warning(f"检测到循环引用，媒体库ID: {library_id}")
            return "未知媒体库"

        visited_ids.add(library_id)

        if not EMBY_URL or not EMBY_API_KEY:
            return "未知媒体库"

        # 首先尝试通过 Items 端点获取
        url = f"{EMBY_URL}/emby/Items/{library_id}?api_key={EMBY_API_KEY}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.ok:
                        data = await response.json()
                        # 检查是否为媒体库类型
                        if data.get("Type") in ["CollectionFolder", "Folder"]:
                            return data.get("Name", "未知媒体库")
                        # 如果不是媒体库类型，尝试获取其父级
                        parent_id = data.get("ParentId")
                        if parent_id and parent_id != library_id:
                            return await self.get_library_name(parent_id, visited_ids)
                        return data.get("Name", "未知媒体库")
                    else:
                        self.logger.error(f"获取媒体库名称失败: {response.status}")
                        # 如果直接获取失败，尝试通过媒体文件夹列表获取
                        return await self.get_library_name_from_folders(library_id)
        except Exception as e:
            self.logger.error(f"获取媒体库名称时发生错误: {str(e)}")
            # 如果直接获取失败，尝试通过媒体文件夹列表获取
            return await self.get_library_name_from_folders(library_id)

    async def get_library_name_from_folders(self, library_id: str) -> str:
        """
        通过查询媒体文件夹列表获取媒体库名称
        """
        if not EMBY_URL or not EMBY_API_KEY:
            return "未知媒体库"

        url = f"{EMBY_URL}/emby/Library/MediaFolders?api_key={EMBY_API_KEY}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.ok:
                        data = await response.json()
                        items = data.get("Items", [])
                        for item in items:
                            if item.get("Id") == library_id:
                                return item.get("Name", "未知媒体库")
                        return "未知媒体库"
                    else:
                        self.logger.error(f"获取媒体文件夹列表失败: {response.status}")
                        return "未知媒体库"
        except Exception as e:
            self.logger.error(f"获取媒体文件夹列表时发生错误: {str(e)}")
            return "未知媒体库"

    async def send_telegram_message_with_retry(self, session, endpoint, data, max_retries=3):
        """
        发送 Telegram 消息，支持重试和速率限制处理
        """
        for attempt in range(max_retries):
            try:
                async with session.post(endpoint, json=data) as response:
                    if response.status == 429:  # 速率限制错误
                        response_json = await response.json()
                        retry_after = response_json.get('parameters', {}).get('retry_after', 30)
                        self.logger.warning(f"Telegram API 速率限制: 需要等待 {retry_after} 秒")
                        await asyncio.sleep(retry_after)
                        continue  # 重试

                    if not response.ok:
                        response_text = await response.text()
                        self.logger.error(f"发送通知消息失败: {response_text}")
                        # 如果是客户端错误(4xx)，不重试
                        if 400 <= response.status < 500:
                            break

                    return response

            except Exception as e:
                self.logger.error(f"发送通知消息时发生异常: {str(e)}")
                if attempt == max_retries - 1:  # 最后一次尝试
                    raise
                await asyncio.sleep(2 ** attempt)  # 指数退避

        return None

    async def send_new_media_notification(self, webhook: EmbyWebhook) -> None:
        """
        通过 Telegram API 发送新媒体通知到指定频道
        """
        if not webhook.Item:
            self.logger.error("Webhook 数据中没有 Item 信息")
            return

        item = webhook.Item

        # 获取媒体库名称
        # library_name = await self.get_library_name(item.ParentId)

        # 获取图片URL
        image_url = None
        if EMBY_URL and EMBY_API_KEY:
            # 首先尝试获取背景图
            image_url = item.get_backdrop_url(EMBY_URL, EMBY_API_KEY, 0)
            # 如果没有背景图，回退到主封面图
            if not image_url:
                image_url = item.get_primary_image_url(EMBY_URL, EMBY_API_KEY)

        # 构建消息文本
        message = (
            f"🎬 <b>新片入库</b>\n\n"
            f"📝 <b>标题:</b> {item.Name}\n"
            # f"📚 <b>媒体库:</b> {library_name}\n"
            f"🗓️ <b>发行日期:</b> {parse_emby_date(item.PremiereDate)}\n"
            f"⏱ <b>入库时间:</b> {parse_emby_date(item.DateCreated)}\n"
            f"💎 <b>分辨率:</b> {item.Width}x{item.Height}\n"
            f"⏳ <b>时  长:</b> {format_runtime(item.RunTimeTicks)}\n"
            f"📦 <b>大  小:</b> {format_size(item.Size)}\n"
            f"🎞️ <b>类  型:</b> {item.Container.upper() if item.Container else '未知'}"
        )

        if item.Overview:
            # 清理 HTML 标签
            clean_overview = self.clean_html_text(item.Overview)
            if clean_overview:
                message += f"\n\n📖 <b>简介:</b>\n{clean_overview}\n"

        if item.Studios:
            studios = ', '.join(studio.Name for studio in item.Studios)
            message += f"\n🏢 <b>制作公司:</b> {studios}"

        if item.TagItems:
            tags = ', '.join(tag.Name for tag in item.TagItems)
            message += f"\n🏷 <b>标签:</b> {tags}"

        # 构建 Inline Keyboard
        keyboard = {
            "inline_keyboard": [
                [
                    {
                        "text": "在 Emby 中查看",
                        "url": f"{EMBY_URL}/web/index.html#!/item?id={item.Id}&serverId={item.ServerId}"
                    }
                ]
            ]
        }

        # 发送消息
        try:
            async with aiohttp.ClientSession() as session:
                if image_url:
                    # 发送图文消息
                    endpoint = f"{self.telegram_api_url}/sendPhoto"
                    data = {
                        "chat_id": WEBHOOK_CHANNEL_ID,
                        "photo": image_url,
                        "caption": message,
                        "parse_mode": "HTML",
                        # "reply_markup": json.dumps(keyboard)
                    }
                else:
                    # 发送纯文本消息
                    endpoint = f"{self.telegram_api_url}/sendMessage"
                    data = {
                        "chat_id": WEBHOOK_CHANNEL_ID,
                        "text": message,
                        "parse_mode": "HTML",
                        # "reply_markup": json.dumps(keyboard)
                    }

                response = await self.send_telegram_message_with_retry(session, endpoint, data)
                if response and not response.ok:
                    response_text = await response.text()
                    self.logger.error(f"发送通知消息最终失败: {response_text}")

        except Exception as e:
            self.logger.error(f"发送通知消息失败: {str(e)}")
