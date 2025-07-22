from datetime import timezone, datetime, timedelta
from typing import Optional

from utils.logger import Logger

logger = Logger().get_logger()


def parse_emby_date(date_str: str) -> datetime:
    """Parse Emby date format to datetime object and convert to UTC+8"""
    tz_utc8 = timezone(timedelta(hours=8))

    try:
        # 移除多余的小数位数，只保留6位微秒
        if '.' in date_str:
            main_part, fraction = date_str.split('.')
            if '+' in fraction:
                fraction, timezone_str = fraction.split('+')
                fraction = fraction[:6]  # 只保留6位微秒
                date_str = f"{main_part}.{fraction}+{timezone_str}"
            elif 'Z' in fraction:
                fraction = fraction.replace('Z', '')
                fraction = fraction[:6]  # 只保留6位微秒
                date_str = f"{main_part}.{fraction}+00:00"

        # 解析为UTC时间
        utc_time = datetime.fromisoformat(date_str.replace('Z', '+00:00'))

        # 转换为UTC+8
        return utc_time.astimezone(tz_utc8)
    except Exception as e:
        logger.error(f"Error parsing date {date_str}: {e}")
        return datetime.now(tz_utc8)


def escape_markdown_v2(text: str) -> str:
    """Escape special characters for Markdown V2 format"""
    need_escape = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in need_escape:
        text = text.replace(char, f'\\{char}')
    return text


def format_runtime(ticks: Optional[int]) -> str:
    """将 RunTimeTicks 转换为 HH:MM:SS 格式"""
    if ticks is None:
        return "未知"
    seconds = ticks / 10_000_000
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def format_size(size_bytes: Optional[int]) -> str:
    """将字节转换为 GB 或 MB"""
    if size_bytes is None:
        return "未知"
    gb = size_bytes / (1024**3)
    if gb >= 1:
        return f"{gb:.2f} GB"
    mb = size_bytes / (1024**2)
    return f"{mb:.2f} MB"
