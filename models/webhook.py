from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from .media import MediaItem
from .server import ServerInfo


class EmbyWebhook(BaseModel):
    Title: str
    Description: Optional[str] = None
    Date: datetime
    Event: str
    Item: Optional[MediaItem] = None
    Server: ServerInfo
