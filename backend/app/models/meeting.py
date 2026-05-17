"""Meeting model"""
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Boolean, Text
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class MeetingStatusEnum(str, enum.Enum):
    """Meeting status"""
    DRAFT = "draft"
    LIVE = "live"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class Meeting(Base):
    """Meeting model"""
    __tablename__ = "meetings"

    id = Column(String(36), primary_key=True, index=True)
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(MeetingStatusEnum), default=MeetingStatusEnum.DRAFT, nullable=False, index=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # No special table args required currently
    __table_args__ = ()
