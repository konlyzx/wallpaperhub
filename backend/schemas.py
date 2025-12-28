from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class WallpaperBase(BaseModel):
    title: str
    description: Optional[str] = None
    type: str
    author: Optional[str] = "Anonymous"

class WallpaperCreate(WallpaperBase):
    pass

class WallpaperResponse(WallpaperBase):
    id: int
    file_path: str
    thumbnail_path: Optional[str] = None
    created_at: datetime
    downloads: int
    file_size: Optional[float] = None

    class Config:
        from_attributes = True
