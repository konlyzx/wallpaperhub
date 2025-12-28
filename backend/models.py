from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from .database import Base

class Wallpaper(Base):
    __tablename__ = "wallpapers"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String, nullable=True)
    file_path = Column(String)  # Ruta al archivo en el servidor
    thumbnail_path = Column(String, nullable=True)
    type = Column(String)  # 'video', 'image', 'gif'
    author = Column(String, default="Anonymous")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    downloads = Column(Integer, default=0)
    file_size = Column(Float, nullable=True) # En MB
