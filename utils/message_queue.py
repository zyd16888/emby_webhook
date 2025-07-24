import asyncio
import json
from collections import deque
from typing import Dict, Any
from datetime import datetime

from utils.logger import Logger

logger = Logger().get_logger()


class MessageQueue:
    """消息队列系统，用于解耦 webhook 接收和 Telegram 消息发送"""
    
    def __init__(self):
        self.queue = deque()
        self._lock = asyncio.Lock()
        self._worker_task = None
        self._running = False
        
    async def add_message(self, message_data: Dict[Any, Any]) -> None:
        """添加消息到队列"""
        async with self._lock:
            # 添加时间戳
            message_data['queued_at'] = datetime.now().isoformat()
            self.queue.append(message_data)
            logger.info(f"消息已添加到队列，当前队列长度: {len(self.queue)}")
            
    async def start_processing(self):
        """启动后台处理任务"""
        if not self._running:
            self._running = True
            self._worker_task = asyncio.create_task(self._process_queue())
            logger.info("消息队列处理器已启动")
            
    async def stop_processing(self):
        """停止后台处理任务"""
        self._running = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
            logger.info("消息队列处理器已停止")
            
    async def _process_queue(self):
        """后台处理队列中的消息"""
        from handlers.webhook_handler import WebhookHandler
        
        webhook_handler = WebhookHandler()
        
        while self._running:
            try:
                # 检查队列是否有消息
                async with self._lock:
                    if self.queue:
                        message_data = self.queue.popleft()
                    else:
                        message_data = None
                        
                if message_data:
                    logger.info(f"处理队列中的消息，剩余队列长度: {len(self.queue)}")
                    # 处理消息
                    await self._process_message(webhook_handler, message_data)
                else:
                    # 如果队列为空，短暂休眠
                    await asyncio.sleep(0.1)
                    
            except Exception as e:
                logger.error(f"处理队列消息时发生错误: {str(e)}")
                await asyncio.sleep(1)  # 发生错误时短暂休眠
                
    async def _process_message(self, webhook_handler, message_data):
        """处理单个消息"""
        try:
            # 从消息数据重建 EmbyWebhook 对象
            from models.webhook import EmbyWebhook
            webhook = EmbyWebhook.model_validate(message_data['webhook_data'])
            
            # 发送通知
            await webhook_handler.send_new_media_notification(webhook)
            
        except Exception as e:
            logger.error(f"处理消息时发生错误: {str(e)}")
            # 可以在这里实现重试逻辑或死信队列