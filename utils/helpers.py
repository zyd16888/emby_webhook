from datetime import timezone, datetime, timedelta

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
