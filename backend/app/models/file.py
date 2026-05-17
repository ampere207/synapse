"""Uploaded file model"""
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer
from sqlalchemy.sql import func
from app.core.database import Base


class UploadedFile(Base):
    """Uploaded file model"""
    __tablename__ = "uploaded_files"

    id = Column(String(36), primary_key=True, index=True)
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    meeting_id = Column(String(36), ForeignKey("meetings.id"), nullable=True, index=True)
    uploaded_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)  # "transcript", "summary", "audio"
    file_size = Column(Integer, nullable=False)
    supabase_path = Column(String(512), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
