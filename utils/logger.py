import functools
import logging
import os
import sys
import time
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Callable, Optional

from config.settings import LOG_DIR, LOG_FILE_MAX_BYTES, LOG_FILE_BACKUP_COUNT, LOG_FORMAT, LOG_LEVEL


class Logger:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.initialized = True
            self.setup_logger()

    def setup_logger(self, log_level: int = getattr(logging, LOG_LEVEL)):
        """设置日志配置"""
        # 创建logs目录
        if not os.path.exists(LOG_DIR):
            os.makedirs(LOG_DIR)

        # 生成日志文件名
        current_date = datetime.now().strftime("%Y-%m-%d")
        log_file = os.path.join(LOG_DIR, f"emby_bot_{current_date}.log")

        # 创建logger
        self.logger = logging.getLogger('EmbyBot')
        self.logger.setLevel(log_level)

        # 清除现有的处理器
        if self.logger.handlers:
            self.logger.handlers.clear()

        # 创建文件处理器
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=LOG_FILE_MAX_BYTES,
            backupCount=LOG_FILE_BACKUP_COUNT,
            encoding='utf-8'
        )
        file_handler.setLevel(log_level)

        # 创建控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)

        # 设置日志格式
        formatter = logging.Formatter(LOG_FORMAT)
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # 添加处理器
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def get_logger(self) -> logging.Logger:
        """获取logger实例"""
        return self.logger


# 创建装饰器
def log_decorator(level: str = 'info', message: Optional[str] = None):
    """
    日志装饰器
    :param level: 日志级别 ('debug', 'info', 'warning', 'error', 'critical')
    :param message: 自定义日志消息
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = Logger().get_logger()
            log_func = getattr(logger, level.lower())

            # 生成日志消息
            func_name = func.__name__
            custom_msg = message or f"Executing function: {func_name}"

            try:
                # 记录开始时间
                start_time = time.time()

                # 记录函数开始
                log_func(f"{custom_msg} - Started")

                # 执行函数
                result = func(*args, **kwargs)

                # 计算执行时间
                execution_time = time.time() - start_time

                # 记录函数结束
                log_func(f"{custom_msg} - Completed in {execution_time:.2f} seconds")

                return result

            except Exception as e:
                # 记录异常
                logger.error(f"{custom_msg} - Failed with error: {str(e)}", exc_info=True)
                raise

        return wrapper

    return decorator


def async_log_decorator(level: str = 'info', message: Optional[str] = None):
    """
    异步函数的日志装饰器
    :param level: 日志级别 ('debug', 'info', 'warning', 'error', 'critical')
    :param message: 自定义日志消息
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            logger = Logger().get_logger()
            log_func = getattr(logger, level.lower())

            # 生成日志消息
            func_name = func.__name__
            custom_msg = message or f"Executing async function: {func_name}"

            try:
                # 记录开始时间
                start_time = time.time()

                # 记录函数开始
                log_func(f"{custom_msg} - Started")

                # 执行异步函数
                result = await func(*args, **kwargs)

                # 计算执行时间
                execution_time = time.time() - start_time

                # 记录函数结束
                log_func(f"{custom_msg} - Completed in {execution_time:.2f} seconds")

                return result

            except Exception as e:
                # 记录异常
                logger.error(f"{custom_msg} - Failed with error: {str(e)}", exc_info=True)
                raise

        return wrapper

    return decorator
