from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ExternalUrl(BaseModel):
    Name: str
    Url: str


class Studio(BaseModel):
    Name: str
    Id: int


class Tag(BaseModel):
    Name: str
    Id: int


class ImageTag(BaseModel):
    Primary: Optional[str] = None
    Thumb: Optional[str] = None


class ProviderIds(BaseModel):
    MetaTube: Optional[str] = None


class GenreItem(BaseModel):
    Name: str
    Id: int


class MediaItem(BaseModel):
    Name: str
    OriginalTitle: Optional[str] = None
    ServerId: str
    Id: str
    DateCreated: str
    Container: str
    SortName: str
    PremiereDate: str
    ExternalUrls: List[ExternalUrl] = Field(default_factory=lambda: [])
    Path: str
    OfficialRating: Optional[str] = None
    Overview: Optional[str] = None
    Taglines: List[str] = Field(default_factory=lambda: [])
    Genres: List[str] = Field(default_factory=lambda: [])
    RunTimeTicks: Optional[int] = None
    Size: int
    FileName: str
    Bitrate: int
    ProductionYear: Optional[int] = None
    RemoteTrailers: List[str] = Field(default_factory=lambda: [])
    ProviderIds: Optional[dict] = None
    IsFolder: bool
    ParentId: str
    Type: str
    Studios: List[Studio] = Field(default_factory=lambda: [])
    GenreItems: List[GenreItem] = Field(default_factory=lambda: [])
    TagItems: List[Tag] = Field(default_factory=lambda: [])
    PrimaryImageAspectRatio: Optional[float] = None
    ImageTags: Optional[ImageTag] = None
    BackdropImageTags: List[str] = Field(default_factory=lambda: [])
    MediaType: str
    Width: Optional[int] = None
    Height: Optional[int] = None

    def format_info(self) -> str:
        """返回格式化的媒体信息"""
        return f"""
新增媒体文件:
- 名称: {self.Name}
- 原始标题: {self.OriginalTitle or ''}
- 概述: {self.Overview or ''}
- 类型: {self.Type}
- 格式: {self.Container}
- 路径: {self.Path}
- 大小: {self.Size:,} bytes
- 分辨率: {self.Width}x{self.Height if self.Width and self.Height else '未知'}
- 比特率: {self.Bitrate}
- 发行日期: {self.PremiereDate.strftime('%Y-%m-%d') if self.PremiereDate else '未知'}
- 入库日期: {self.DateCreated.strftime('%Y-%m-%d %H:%M:%S')}
- 年份: {self.ProductionYear or '未知'}
- 制作公司: {', '.join(studio.Name for studio in self.Studios)}
- 标签: {', '.join(tag.Name for tag in self.TagItems)}
        """.strip()

    def get_primary_image_url(self, server_url: str, api_key: str) -> Optional[str]:
        """获取主要封面图的URL"""
        if not self.ImageTags or 'Primary' not in self.ImageTags:
            return None
        return f"{server_url}/emby/Items/{self.Id}/Images/Primary?api_key={api_key}"

    def get_backdrop_url(self, server_url: str, api_key: str, index: int = 0) -> Optional[str]:
        """获取背景图的URL"""
        if not self.BackdropImageTags or index >= len(self.BackdropImageTags):
            return None
        return f"{server_url}/emby/Items/{self.Id}/Images/Backdrop/{index}?api_key={api_key}"

    def get_thumbnail_url(self, server_url: str, api_key: str) -> Optional[str]:
        """获取缩略图URL"""
        if not self.ImageTags or 'Thumb' not in self.ImageTags:
            return None
        return f"{server_url}/emby/Items/{self.Id}/Images/Thumb?api_key={api_key}"
