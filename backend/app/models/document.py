from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.sql import func
from app.database import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    filepath = Column(Text, nullable=False)
    file_hash = Column(String(64), unique=True)
    file_type = Column(String(10))
    status = Column(String(20), default="pending")
    page_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class MonitoredFolder(Base):
    __tablename__ = "monitored_folders"

    id = Column(Integer, primary_key=True, index=True)
    folder_path = Column(Text, unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
