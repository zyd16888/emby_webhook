import json
from datetime import datetime
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request

from config.settings import (
    WEBHOOK_HOST,
    WEBHOOK_PORT,
    get_telegram_bot_instance
)
from handlers.webhook_handler import WebhookHandler
from models.webhook import EmbyWebhook
from utils.logger import Logger

# 配置日志
logger = Logger().get_logger()

# 创建 webhook handler
webhook_handler = WebhookHandler()

# 创建存储目录
NOTIFICATION_DIR = Path("../notifications")
NOTIFICATION_DIR.mkdir(exist_ok=True)


def save_notification(event_type: str, data: dict):
    """将通知保存到文件"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = NOTIFICATION_DIR / f"{event_type}_{timestamp}.json"

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def create_webhook_app() -> FastAPI:
    """创建并配置 FastAPI 应用"""
    app = FastAPI(title="Emby Bot & Webhook Server")

    @app.post("/webhook")
    async def webhook(request: Request):
        """接收 Emby 的 Webhook 通知"""
        try:
            # 获取原始JSON数据
            data = await request.json()

            # 记录原始数据用于调试
            logger.info(f"原始数据: {json.dumps(data, ensure_ascii=False)}")

            # 使用Pydantic模型解析数据
            webhook_data = EmbyWebhook.model_validate(data)

            # 保存原始通知数据
            save_notification(webhook_data.Event, data)

            # 根据事件类型处理
            if webhook_data.Event == 'library.new':
                await webhook_handler.send_new_media_notification(webhook_data)

            return {
                "status": "success",
                "message": f"Successfully processed {webhook_data.Event} event",
                "title": webhook_data.Title
            }

        except Exception as e:
            logger.error(f"处理webhook时发生错误: {str(e)}")
            return {"status": "error", "message": str(e)}

    @app.get("/")
    async def root():
        """服务器状态检查"""
        return {"status": "running"}

    return app


async def run_emby_webhook_server():
    """运行 Webhook 服务器"""
    app = create_webhook_app()
    config = uvicorn.Config(
        app,
        host=WEBHOOK_HOST,
        port=WEBHOOK_PORT,
        reload=True
    )
    server = uvicorn.Server(config)
    await server.serve()
