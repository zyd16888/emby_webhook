import os
from typing import Set

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
# ADMIN_USER_IDS: Set[int] = set(map(int, os.getenv('ADMIN_USER_IDS', '').split(',')))

# Telegram Bot Instance
_TELEGRAM_BOT_INSTANCE = None


def set_telegram_bot_instance(bot):
    global _TELEGRAM_BOT_INSTANCE
    _TELEGRAM_BOT_INSTANCE = bot


def get_telegram_bot_instance():
    return _TELEGRAM_BOT_INSTANCE


# Emby Configuration
EMBY_URL = os.getenv('EMBY_URL', '').rstrip('/')
EMBY_API_KEY = os.getenv('EMBY_API_KEY')
EMBY_SERVERS = os.getenv('EMBY_SERVERS', [])

# Database Configuration
DATABASE_FILE = os.getenv('DATABASE_FILE', "emby_bot.db")
DATABASE_URL = os.getenv('DATABASE_URL', f'sqlite:///data/{DATABASE_FILE}')

# Environment Configuration
APP_ENV = os.getenv('APP_ENV', 'development')


class Environment:
    @staticmethod
    def is_development():
        return APP_ENV == 'development'

    @staticmethod
    def is_production():
        return APP_ENV == 'production'

    @staticmethod
    def is_testing():
        return APP_ENV == 'testing'


# Logging Configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
LOG_DIR = "logs"
LOG_FILE_MAX_BYTES = 10 * 1024 * 1024  # 10MB
LOG_FILE_BACKUP_COUNT = 5

# Registration Configuration
DEFAULT_PASSWORD_LENGTH = 12

# Proxy Configuration
USE_PROXY = os.getenv('USE_PROXY', 'false').lower() == 'true'
PROXY_URL = os.getenv('PROXY_URL', 'socks5://127.0.0.1:7890')

# Webhook Configuration
WEBHOOK_HOST = os.getenv('WEBHOOK_HOST', '0.0.0.0')
WEBHOOK_PORT = int(os.getenv('WEBHOOK_PORT', '8000'))
WEBHOOK_CHANNEL_ID = os.getenv('WEBHOOK_CHANNEL_ID')  # 通知发送的目标频道ID

# Membership Check Configuration
REQUIRED_CHANNEL_ID = int(os.getenv('REQUIRED_CHANNEL_ID', '0'))  # 必须加入的频道ID
REQUIRED_GROUP_ID = int(os.getenv('REQUIRED_GROUP_ID', '0'))  # 必须加入的群组ID

# 需要过滤的群组列表，只有在这些群组中才会自动封禁不在数据库中的用户
FILTERED_GROUP_IDS = [REQUIRED_GROUP_ID] if REQUIRED_GROUP_ID != 0 else []

# Conversation States
ENTERING_ACTIVATION_CODE = 0
ENTERING_USERNAME = 1

# Message Templates
USER_TIPS = os.getenv('USER_TIPS', """💡 温馨提示：
• 可使用 /resetpwd xxxxx 自定义密码
• 请保存好您的登录信息
• Android建议使用 Yamby 客户端
• 如果有任何问题，请稍后重试""")
